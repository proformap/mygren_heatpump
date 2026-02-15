"""The Mygren Heat Pump integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import MygrenConfigEntry, MygrenRuntimeData
from .mygren_api import MygrenAPI, MygrenAPIError, MygrenAuthError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.CLIMATE,
    Platform.WATER_HEATER,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: MygrenConfigEntry) -> bool:
    """Set up Mygren Heat Pump from a config entry."""
    api = MygrenAPI(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
    )

    # Authenticate first
    try:
        await api.authenticate()
    except MygrenAPIError as err:
        _LOGGER.error("Failed to authenticate with Mygren API: %s", err)
        await api.close()
        return False

    async def async_update_data() -> dict:
        """Fetch data from the heat pump API."""
        try:
            return await api.get_telemetry()
        except MygrenAuthError:
            # Token expired — re-authenticate and retry
            _LOGGER.debug("Token expired during update, re-authenticating")
            try:
                await api.authenticate()
                return await api.get_telemetry()
            except MygrenAPIError as err:
                raise UpdateFailed(f"Auth refresh failed: {err}") from err
        except MygrenAPIError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Mygren Heat Pump",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MygrenRuntimeData(api=api, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MygrenConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.api.close()

    return unload_ok
