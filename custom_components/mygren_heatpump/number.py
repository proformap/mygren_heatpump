"""Support for Mygren Heat Pump number entities.

Optimistic updates: value changes are reflected in the UI immediately.
The coordinator background refresh then confirms the actual device state.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry
from .optimistic import PendingValue, rollback_on_error

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenNumberEntityDescription(NumberEntityDescription):
    """Describes Mygren number entity."""

    value_fn: Callable[[dict], float | None] | None = None
    # Telemetry fields holding the pump's own limits, if it reports them
    min_key: str | None = None
    max_key: str | None = None


NUMBER_TYPES: tuple[MygrenNumberEntityDescription, ...] = (
    MygrenNumberEntityDescription(
        key="curve",
        name="Heating Curve",
        icon="mdi:chart-line",
        native_min_value=1,
        native_max_value=9,
        native_step=1,
        mode=NumberMode.SLIDER,
        min_key="curve_setmin",
        max_key="curve_setmax",
        value_fn=lambda data: data.get("curve"),
    ),
    MygrenNumberEntityDescription(
        key="shift",
        name="Curve Shift",
        icon="mdi:arrows-horizontal",
        native_min_value=-5,
        native_max_value=5,
        native_step=1,
        mode=NumberMode.SLIDER,
        min_key="shift_setmin",
        max_key="shift_setmax",
        value_fn=lambda data: data.get("shift"),
    ),
    MygrenNumberEntityDescription(
        key="manual",
        name="Manual Output Temperature",
        icon="mdi:thermometer-lines",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=15,
        native_max_value=40,
        native_step=1,
        mode=NumberMode.BOX,
        min_key="manual_setmin",
        max_key="manual_setmax",
        value_fn=lambda data: data.get("manual"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren number based on a config entry."""
    data = entry.runtime_data

    async_add_entities(
        MygrenNumber(data.coordinator, data.api, description, entry)
        for description in NUMBER_TYPES
    )


class MygrenNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Mygren number entity."""

    entity_description: MygrenNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, description, entry):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )
        # Value shown until telemetry confirms it
        self._pending = PendingValue()

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state once telemetry confirms it or it times out."""
        if self.entity_description.value_fn:
            actual = self.entity_description.value_fn(self.coordinator.data)
            self._pending.settle(
                lambda value: actual is not None and int(actual) == int(value)
            )
        super()._handle_coordinator_update()

    def _limit(self, key: str | None, default: float) -> float:
        """Return a limit reported by the pump, or the default."""
        value = self.coordinator.data.get(key) if key else None
        return value if value is not None else default

    @property
    def native_min_value(self) -> float:
        """Return the minimum value."""
        description = self.entity_description
        return self._limit(description.min_key, description.native_min_value)

    @property
    def native_max_value(self) -> float:
        """Return the maximum value."""
        description = self.entity_description
        return self._limit(description.max_key, description.native_max_value)

    @property
    def native_value(self) -> float | None:
        """Return the current value (optimistic if pending)."""
        if self._pending.value is not None:
            return self._pending.value
        if self.entity_description.value_fn:
            value = self.entity_description.value_fn(self.coordinator.data)
            return float(value) if value is not None else None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value with optimistic update."""
        # Optimistic: update UI immediately
        self._pending.set(value)
        self.async_write_ha_state()

        int_value = int(value)

        async with rollback_on_error(self, self._pending):
            if self.entity_description.key == "curve":
                await self._api.set_curve(int_value)
            elif self.entity_description.key == "shift":
                await self._api.set_shift(int_value)
            elif self.entity_description.key == "manual":
                await self._api.set_manual_temperature(int_value)

        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None
