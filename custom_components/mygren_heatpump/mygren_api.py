"""Async API client for Mygren Heat Pump.

Key fixes over v1.x:
- Uses aiohttp instead of synchronous requests (proper HA async pattern)
- SSL verification disabled by default for self-signed certificates (ROOT CAUSE fix)
- PUT payloads send raw JSON values, not wrapped in {"value": ...}
- Proper token refresh with 401 retry logic
- Configurable SSL verification
"""
from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

import aiohttp

from .const import (
    API_HEATPUMP_ENABLED,
    API_HEATPUMP_TARIFF_WATCH,
    API_LOGIN,
    API_PROGRAM_COMFORT,
    API_PROGRAM_CURVE,
    API_PROGRAM_MANUAL,
    API_PROGRAM_PROGRAM,
    API_PROGRAM_SHIFT,
    API_TELEMETRY,
    API_TUV_ENABLED,
    API_TUV_SCHEDULER_ENABLED,
    API_TUV_SET,
    API_PROGRAM_SCHEDULER_ENABLED,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


class MygrenAPIError(Exception):
    """Base exception for Mygren API errors."""


class MygrenAuthError(MygrenAPIError):
    """Exception for authentication errors."""


class MygrenConnectionError(MygrenAPIError):
    """Exception for connection errors."""


class MygrenAPI:
    """Async API client for the Mygren heat pump REST API.

    The Mygren heat pump exposes a local HTTPS REST API (lighttpd + PHP)
    authenticated via JWT Bearer tokens. Most installations use self-signed
    certificates, so SSL verification is disabled by default.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        verify_ssl: bool = False,
    ) -> None:
        """Initialize the API client."""
        # Normalize host URL
        self._host = host.rstrip("/")
        if not self._host.startswith(("http://", "https://")):
            self._host = f"https://{self._host}"

        self._username = username
        self._password = password
        self._token: str | None = None
        self._verify_ssl = verify_ssl

        # SSL context: False = skip verification (self-signed certs)
        if not verify_ssl:
            self._ssl_context: ssl.SSLContext | bool = False
        else:
            self._ssl_context = None  # Use default SSL context

        self._session = session
        self._own_session = session is None

    @property
    def host(self) -> str:
        """Return the host URL."""
        return self._host

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self._ssl_context)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=REQUEST_TIMEOUT,
            )
            self._own_session = True
        return self._session

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session and not self._session.closed:
            await self._session.close()

    def _url(self, endpoint: str) -> str:
        """Build full URL for an API endpoint."""
        return f"{self._host}{endpoint}"

    async def authenticate(self) -> str:
        """Authenticate with the heat pump and obtain a JWT token.

        Returns:
            The JWT token string.

        Raises:
            MygrenAuthError: If credentials are invalid (401).
            MygrenConnectionError: If the heat pump is unreachable.
        """
        session = await self._get_session()
        url = self._url(API_LOGIN)
        payload = {
            "username": self._username,
            "password": self._password,
        }

        _LOGGER.debug("Authenticating with %s", url)

        try:
            async with session.post(
                url,
                json=payload,
                ssl=self._ssl_context,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    token = data.get("token")
                    if not token:
                        raise MygrenAuthError(
                            "Login succeeded but no token in response"
                        )
                    self._token = token
                    _LOGGER.debug("Authentication successful")
                    return self._token

                if resp.status == 401:
                    raise MygrenAuthError("Invalid username or password")

                body = await resp.text()
                raise MygrenAPIError(
                    f"Login returned HTTP {resp.status}: {body}"
                )

        except MygrenAPIError:
            raise
        except aiohttp.ClientSSLError as err:
            _LOGGER.error("SSL error connecting to %s: %s", url, err)
            raise MygrenConnectionError(
                f"SSL error: {err}. If using self-signed certificate, "
                f"disable SSL verification in integration settings."
            ) from err
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.error("Connection error to %s: %s", url, err)
            raise MygrenConnectionError(
                f"Cannot connect to {self._host}: {err}"
            ) from err

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token."""
        if self._token is None:
            await self.authenticate()

    def _auth_headers(self) -> dict[str, str]:
        """Return headers with Bearer token."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Any = None,
        retry_auth: bool = True,
    ) -> Any:
        """Make an authenticated API request with automatic token refresh.

        For PUT requests, `data` is sent as the raw JSON body (not wrapped
        in an object). The Mygren API expects simple values for scalar
        endpoints, e.g. PUT /api/tuv/set with body `43`.
        """
        await self._ensure_token()
        session = await self._get_session()
        url = self._url(endpoint)

        _LOGGER.debug("API %s %s (data=%s)", method, url, data)

        try:
            kwargs: dict[str, Any] = {
                "headers": self._auth_headers(),
                "ssl": self._ssl_context,
            }

            # Send data as raw JSON body
            if data is not None:
                kwargs["json"] = data

            async with session.request(method, url, **kwargs) as resp:
                # Token expired — re-authenticate and retry once
                if resp.status == 401 and retry_auth:
                    _LOGGER.debug("Token expired, re-authenticating")
                    self._token = None
                    await self.authenticate()
                    return await self._request(
                        method, endpoint, data, retry_auth=False
                    )

                if resp.status in (200, 201):
                    text = await resp.text()
                    if not text or not text.strip():
                        return {}
                    return await resp.json(content_type=None)

                if resp.status == 401:
                    raise MygrenAuthError("Authentication failed")

                if resp.status == 400:
                    body = await resp.text()
                    _LOGGER.error(
                        "Bad request %s %s: %s", method, endpoint, body
                    )
                    raise MygrenAPIError(
                        f"Bad request to {endpoint}: {body}"
                    )

                if resp.status == 503:
                    body = await resp.text()
                    _LOGGER.warning(
                        "Service unavailable %s: %s", endpoint, body
                    )
                    raise MygrenConnectionError(
                        f"Heat pump service unavailable: {body}"
                    )

                body = await resp.text()
                raise MygrenAPIError(
                    f"HTTP {resp.status} from {method} {endpoint}: {body}"
                )

        except MygrenAPIError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as err:
            raise MygrenConnectionError(
                f"Connection error during {method} {endpoint}: {err}"
            ) from err

    # ── Telemetry ──────────────────────────────────────────────────

    async def get_telemetry(self) -> dict[str, Any]:
        """Get all runtime telemetry variables."""
        return await self._request("GET", API_TELEMETRY)

    # ── TUV (Hot Water) ───────────────────────────────────────────

    async def set_tuv_temperature(self, temperature: int) -> Any:
        """Set hot water target temperature."""
        return await self._request("PUT", API_TUV_SET, data=temperature)

    async def set_tuv_enabled(self, enabled: bool) -> Any:
        """Enable or disable hot water heating."""
        return await self._request(
            "PUT", API_TUV_ENABLED, data=1 if enabled else 0
        )

    async def set_tuv_scheduler_enabled(self, enabled: bool) -> Any:
        """Enable or disable hot water scheduler."""
        return await self._request(
            "PUT", API_TUV_SCHEDULER_ENABLED, data=1 if enabled else 0
        )

    # ── Program ───────────────────────────────────────────────────

    async def set_program(self, program: str | int) -> Any:
        """Set the active heating program.

        Newer firmware (v4+) uses string values:
            "Off", "Manual_comfort", "Cooling_comfort"
        Older firmware uses integers:
            0=Off, 1=Auto/Ekvithermal, 2=Manual
        """
        return await self._request("PUT", API_PROGRAM_PROGRAM, data=program)

    async def set_curve(self, curve: int) -> Any:
        """Set the ekvithermal curve number (1-9)."""
        return await self._request("PUT", API_PROGRAM_CURVE, data=curve)

    async def set_shift(self, shift: int) -> Any:
        """Set the ekvithermal curve shift (-5 to +5)."""
        return await self._request("PUT", API_PROGRAM_SHIFT, data=shift)

    async def set_manual_temperature(self, temperature: int) -> Any:
        """Set manual program output temperature."""
        return await self._request("PUT", API_PROGRAM_MANUAL, data=temperature)

    async def set_comfort_temperature(self, temperature: int) -> Any:
        """Set comfort temperature."""
        return await self._request("PUT", API_PROGRAM_COMFORT, data=temperature)

    async def set_program_scheduler_enabled(self, enabled: bool) -> Any:
        """Enable or disable program scheduler."""
        return await self._request(
            "PUT", API_PROGRAM_SCHEDULER_ENABLED, data=1 if enabled else 0
        )

    # ── Heatpump ──────────────────────────────────────────────────

    async def set_heatpump_enabled(self, enabled: bool) -> Any:
        """Enable or disable the heat pump."""
        return await self._request(
            "PUT", API_HEATPUMP_ENABLED, data=1 if enabled else 0
        )

    async def set_tariff_watch(self, enabled: bool) -> Any:
        """Enable or disable tariff watching."""
        return await self._request(
            "PUT", API_HEATPUMP_TARIFF_WATCH, data=1 if enabled else 0
        )

    # ── Connection test ───────────────────────────────────────────

    async def test_connection(self) -> dict[str, Any]:
        """Test connection: authenticate and fetch telemetry."""
        await self.authenticate()
        return await self.get_telemetry()
