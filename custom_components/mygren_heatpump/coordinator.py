"""Data update coordinator for Mygren Heat Pump."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .mygren_api import MygrenAPI, MygrenAPIError, MygrenAuthError

_LOGGER = logging.getLogger(__name__)


class MygrenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data fetching from Mygren heat pump."""

    def __init__(self, hass: HomeAssistant, api: MygrenAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the heat pump API."""
        try:
            return await self.api.get_telemetry()
        except MygrenAuthError as err:
            # Token might be expired; try to re-authenticate once
            _LOGGER.debug("Auth error during update, re-authenticating: %s", err)
            try:
                await self.api.authenticate()
                return await self.api.get_telemetry()
            except MygrenAPIError as err2:
                raise UpdateFailed(f"Authentication failed: {err2}") from err2
        except MygrenAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
