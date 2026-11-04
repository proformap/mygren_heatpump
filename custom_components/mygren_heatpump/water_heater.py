"""Support for Mygren Heat Pump water heater.

Optimistic updates: temperature and operation mode changes are
reflected in the UI immediately.  The coordinator background refresh
then confirms the actual device state.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import UnitOfTemperature, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry
from .optimistic import PendingValue, rollback_on_error

_LOGGER = logging.getLogger(__name__)

STATE_HEATING = "heating"
STATE_IDLE = "idle"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren water heater based on a config entry."""
    data = entry.runtime_data

    async_add_entities([MygrenWaterHeater(data.coordinator, data.api, entry)])


class MygrenWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Representation of a Mygren water heater (TUV)."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_operation_list = ["auto", "off"]
    # The pump only accepts whole degrees for hot water
    _attr_target_temperature_step = 1

    def __init__(self, coordinator, api, entry):
        """Initialize the water heater."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Hot Water"
        self._attr_unique_id = f"{entry.entry_id}_water_heater"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )
        # Values shown until telemetry confirms them
        self._pending_target = PendingValue()
        self._pending_operation = PendingValue()

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state only when coordinator data confirms the change."""
        data = self.coordinator.data

        actual_target = data.get("tuv_set")
        self._pending_target.settle(
            lambda target: actual_target is not None and int(actual_target) == target
        )

        actual_enabled = data.get("tuv_enabled")
        self._pending_operation.settle(
            lambda operation: actual_enabled is not None
            and bool(actual_enabled) == (operation == "auto")
        )

        super()._handle_coordinator_update()

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get("Ttuv")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach (optimistic if pending)."""
        if self._pending_target.value is not None:
            return self._pending_target.value
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
        """Return current operation (optimistic if pending)."""
        if self._pending_operation.value is not None:
            return self._pending_operation.value
        if self.coordinator.data.get("tuv_enabled"):
            return "auto"
        return "off"

    @property
    def state(self) -> str:
        """Return the current state."""
        # Use optimistic operation for immediate feedback
        operation = self.current_operation
        if operation == "off":
            return STATE_OFF
        if self.coordinator.data.get("tuvneedheat"):
            return STATE_HEATING
        return STATE_IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature with optimistic update."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        temperature = round(float(temperature))

        if temperature < self.min_temp or temperature > self.max_temp:
            _LOGGER.error(
                "Temperature %s out of range (%s-%s)",
                temperature, self.min_temp, self.max_temp,
            )
            return

        # Optimistic: update UI immediately
        self._pending_target.set(temperature)
        self.async_write_ha_state()

        async with rollback_on_error(self, self._pending_target):
            await self._api.set_tuv_temperature(temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode with optimistic update."""
        # Optimistic: update UI immediately
        self._pending_operation.set(operation_mode)
        self.async_write_ha_state()

        enabled = operation_mode == "auto"
        async with rollback_on_error(self, self._pending_operation):
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
