"""Config flow for Mygren Heat Pump integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    DOMAIN,
)
from .mygren_api import MygrenAPI, MygrenAPIError, MygrenAuthError, MygrenConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)


async def validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by attempting to connect.

    Returns dict with title for the config entry.
    Raises CannotConnect or InvalidAuth on failure.
    """
    host = data[CONF_HOST].rstrip("/")

    # Auto-add https:// if no scheme provided
    if not host.startswith(("http://", "https://")):
        host = f"https://{host}"

    api = MygrenAPI(
        host=host,
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        verify_ssl=data.get(CONF_VERIFY_SSL, False),
    )

    try:
        telemetry = await api.test_connection()
        hostname = telemetry.get("hostname", "Mygren Heat Pump")
    except MygrenAuthError as err:
        raise InvalidAuth from err
    except MygrenConnectionError as err:
        raise CannotConnect from err
    except MygrenAPIError as err:
        raise CannotConnect from err
    finally:
        await api.close()

    return {"title": hostname, "host": host}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mygren Heat Pump."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            else:
                # Use normalized host for unique ID
                await self.async_set_unique_id(info["host"])
                self._abort_if_unique_id_configured()

                # Store the normalized host
                user_input[CONF_HOST] = info["host"]

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
