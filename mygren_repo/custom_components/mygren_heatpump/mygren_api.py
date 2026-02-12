"""API client for Mygren Heat Pump."""
from __future__ import annotations

import logging
from typing import Any

import requests
from requests.exceptions import RequestException, Timeout

from .const import (
    API_LOGIN,
    API_TELEMETRY,
    API_DAEMONLOG,
    API_RUNLOG,
    API_TUV,
    API_TUV_SET,
    API_TUV_ENABLED,
    API_TUV_SCHEDULER_ENABLED,
    API_TUV_SCHEDULER,
    API_PROGRAM,
    API_PROGRAM_PROGRAM,
    API_PROGRAM_CURVE,
    API_PROGRAM_SHIFT,
    API_PROGRAM_MANUAL,
    API_PROGRAM_COMFORT,
    API_PROGRAM_SCHEDULER_ENABLED,
    API_PROGRAM_SCHEDULER,
    API_HEATPUMP,
    API_HEATPUMP_ENABLED,
    API_HEATPUMP_TARIFF,
    API_HEATPUMP_TARIFF_WATCH,
)

_LOGGER = logging.getLogger(__name__)


class MygrenAPIError(Exception):
    """Base exception for Mygren API errors."""


class MygrenAuthError(MygrenAPIError):
    """Exception for authentication errors."""


class MygrenConnectionError(MygrenAPIError):
    """Exception for connection errors."""


class MygrenAPI:
    """API client for Mygren Heat Pump."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize the API client."""
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.token: str | None = None
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
        })

    def _get_url(self, endpoint: str) -> str:
        """Build full URL for endpoint."""
        return f"{self.host}{endpoint}"

    def authenticate(self) -> bool:
        """Authenticate and get JWT token."""
        try:
            response = self.session.post(
                self._get_url(API_LOGIN),
                json={
                    "username": self.username,
                    "password": self.password,
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                _LOGGER.info("Successfully authenticated with Mygren API")
                return True
            elif response.status_code == 401:
                raise MygrenAuthError("Invalid username or password")
            else:
                raise MygrenAPIError(f"Authentication failed: {response.status_code}")

        except Timeout as err:
            raise MygrenConnectionError(f"Connection timeout: {err}") from err
        except RequestException as err:
            raise MygrenConnectionError(f"Connection error: {err}") from err

    def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated request to API."""
        if not self.token:
            self.authenticate()

        try:
            if method.upper() == "GET":
                response = self.session.get(
                    self._get_url(endpoint),
                    timeout=10,
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    self._get_url(endpoint),
                    json=data,
                    timeout=10,
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    self._get_url(endpoint),
                    json=data,
                    timeout=10,
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    self._get_url(endpoint),
                    timeout=10,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Handle 401 - token expired, re-authenticate
            if response.status_code == 401:
                _LOGGER.info("Token expired, re-authenticating")
                self.authenticate()
                # Retry request
                return self._make_request(method, endpoint, data)

            response.raise_for_status()
            return response.json()

        except Timeout as err:
            raise MygrenConnectionError(f"Request timeout: {err}") from err
        except RequestException as err:
            raise MygrenConnectionError(f"Request error: {err}") from err

    # Telemetry endpoints
    def get_telemetry(self) -> dict[str, Any]:
        """Get all telemetry data from heat pump."""
        return self._make_request("GET", API_TELEMETRY)

    def get_daemon_log(self) -> dict[str, Any]:
        """Get daemon log."""
        return self._make_request("GET", API_DAEMONLOG)

    def get_run_log(self) -> dict[str, Any]:
        """Get run log."""
        return self._make_request("GET", API_RUNLOG)

    # TUV (Hot Water) endpoints
    def get_tuv_data(self) -> dict[str, Any]:
        """Get hot water (TUV) data."""
        return self._make_request("GET", API_TUV)

    def get_tuv_set(self) -> dict[str, Any]:
        """Get hot water target temperature."""
        return self._make_request("GET", API_TUV_SET)

    def set_tuv_temperature(self, temperature: int) -> dict[str, Any]:
        """Set hot water target temperature."""
        return self._make_request(
            "PUT",
            API_TUV_SET,
            data={"value": temperature}
        )

    def get_tuv_enabled(self) -> dict[str, Any]:
        """Get hot water enabled state."""
        return self._make_request("GET", API_TUV_ENABLED)

    def set_tuv_enabled(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable hot water heating."""
        return self._make_request(
            "PUT",
            API_TUV_ENABLED,
            data={"value": 1 if enabled else 0}
        )

    def get_tuv_scheduler_enabled(self) -> dict[str, Any]:
        """Get hot water scheduler enabled state."""
        return self._make_request("GET", API_TUV_SCHEDULER_ENABLED)

    def set_tuv_scheduler_enabled(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable hot water scheduler."""
        return self._make_request(
            "PUT",
            API_TUV_SCHEDULER_ENABLED,
            data={"value": 1 if enabled else 0}
        )

    # Program endpoints
    def get_program_data(self) -> dict[str, Any]:
        """Get program data."""
        return self._make_request("GET", API_PROGRAM)

    def get_program(self) -> dict[str, Any]:
        """Get selected program."""
        return self._make_request("GET", API_PROGRAM_PROGRAM)

    def set_program(self, program: int) -> dict[str, Any]:
        """Set program (0=off, 1=auto, 2=manual)."""
        return self._make_request(
            "PUT",
            API_PROGRAM_PROGRAM,
            data={"value": program}
        )

    def get_curve(self) -> dict[str, Any]:
        """Get heating curve number."""
        return self._make_request("GET", API_PROGRAM_CURVE)

    def set_curve(self, curve: int) -> dict[str, Any]:
        """Set heating curve (1-9)."""
        return self._make_request(
            "PUT",
            API_PROGRAM_CURVE,
            data={"value": curve}
        )

    def get_shift(self) -> dict[str, Any]:
        """Get curve shift value."""
        return self._make_request("GET", API_PROGRAM_SHIFT)

    def set_shift(self, shift: int) -> dict[str, Any]:
        """Set curve shift value (-5 to +5)."""
        return self._make_request(
            "PUT",
            API_PROGRAM_SHIFT,
            data={"value": shift}
        )

    def get_manual_temperature(self) -> dict[str, Any]:
        """Get manual program output temperature."""
        return self._make_request("GET", API_PROGRAM_MANUAL)

    def set_manual_temperature(self, temperature: int) -> dict[str, Any]:
        """Set manual program output temperature."""
        return self._make_request(
            "PUT",
            API_PROGRAM_MANUAL,
            data={"value": temperature}
        )

    def get_comfort_temperature(self) -> dict[str, Any]:
        """Get comfort temperature."""
        return self._make_request("GET", API_PROGRAM_COMFORT)

    def set_comfort_temperature(self, temperature: int) -> dict[str, Any]:
        """Set comfort temperature."""
        return self._make_request(
            "PUT",
            API_PROGRAM_COMFORT,
            data={"value": temperature}
        )

    def set_program_scheduler_enabled(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable program scheduler."""
        return self._make_request(
            "PUT",
            API_PROGRAM_SCHEDULER_ENABLED,
            data={"value": 1 if enabled else 0}
        )

    # Heatpump endpoints
    def get_heatpump_data(self) -> dict[str, Any]:
        """Get heat pump data."""
        return self._make_request("GET", API_HEATPUMP)

    def get_heatpump_enabled(self) -> dict[str, Any]:
        """Get heat pump enabled state."""
        return self._make_request("GET", API_HEATPUMP_ENABLED)

    def set_heatpump_enabled(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable heat pump."""
        return self._make_request(
            "PUT",
            API_HEATPUMP_ENABLED,
            data={"value": 1 if enabled else 0}
        )

    def get_tariff(self) -> dict[str, Any]:
        """Get actual tariff state."""
        return self._make_request("GET", API_HEATPUMP_TARIFF)

    def get_tariff_watch(self) -> dict[str, Any]:
        """Get tariff watch state."""
        return self._make_request("GET", API_HEATPUMP_TARIFF_WATCH)

    def set_tariff_watch(self, enabled: bool) -> dict[str, Any]:
        """Enable or disable tariff watching."""
        return self._make_request(
            "PUT",
            API_HEATPUMP_TARIFF_WATCH,
            data={"value": 1 if enabled else 0}
        )
