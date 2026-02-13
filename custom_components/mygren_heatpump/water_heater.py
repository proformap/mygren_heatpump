"""Support for Mygren Heat Pump water heater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATE_HEATING = "heating"
STATE_IDLE = "idle"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren water heater based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities([MygrenWaterHeater(coordinator, api, entry)])


class MygrenWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Representation of a Mygren water heater (TUV)."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_operation_list = ["auto", "off"]

    def __init__(self, coordinator, api, entry):
        """Initialize the water heater."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Hot Water"
        self._attr_unique_id = f"{entry.entry_id}_water_heater"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mygren (AI Trade s.r.o.)",
            "model": "Geo Heat Pump",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get("Ttuv")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self.coordinator.data.get("tuv_set")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self.coordinator.data.get("tuv_setmin", 30)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self.coordinator.data.get("tuv_setmax", 50)

    @property
    def current_operation(self) -> str:
        """Return current operation (auto or off)."""
        if self.coordinator.data.get("tuv_enabled"):
            return "auto"
        return "off"

    @property
    def state(self) -> str:
        """Return the current state."""
        if not self.coordinator.data.get("tuv_enabled"):
            return STATE_OFF
        if self.coordinator.data.get("tuvneedheat"):
            return STATE_HEATING
        return STATE_IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        temperature = int(temperature)

        if temperature < self.min_temp or temperature > self.max_temp:
            _LOGGER.error(
                "Temperature %s out of range (%s-%s)",
                temperature, self.min_temp, self.max_temp,
            )
            return

        await self._api.set_tuv_temperature(temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode."""
        enabled = operation_mode == "auto"
        await self._api.set_tuv_enabled(enabled)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "tuv_min_hysteresis": self.coordinator.data.get("tuvmin"),
            "tuv_max_hysteresis": self.coordinator.data.get("tuvmax"),
            "schedule_enabled": self.coordinator.data.get("tuv_sched_enabled"),
            "schedule_active": self.coordinator.data.get("tuv_sched_active"),
            "schedule_value": self.coordinator.data.get("tuv_sched_value"),
            "tuv_gradient": self.coordinator.data.get("tuvgradient"),
        }
