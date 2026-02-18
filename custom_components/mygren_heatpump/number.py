"""Support for Mygren Heat Pump number entities.

Optimistic updates: value changes are reflected in the UI immediately.
The coordinator background refresh then confirms the actual device state.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenNumberEntityDescription(NumberEntityDescription):
    """Describes Mygren number entity."""

    value_fn: Callable[[dict], float | None] | None = None


NUMBER_TYPES: tuple[MygrenNumberEntityDescription, ...] = (
    MygrenNumberEntityDescription(
        key="curve",
        name="Heating Curve",
        icon="mdi:chart-line",
        native_min_value=1,
        native_max_value=9,
        native_step=1,
        mode=NumberMode.SLIDER,
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
        value_fn=lambda data: data.get("shift"),
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
        # Optimistic state — None means "use coordinator data"
        self._optimistic_value: float | None = None

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state only when coordinator data confirms the change."""
        if self._optimistic_value is not None and self.entity_description.value_fn:
            actual = self.entity_description.value_fn(self.coordinator.data)
            if actual is not None and int(actual) == int(self._optimistic_value):
                self._optimistic_value = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> float | None:
        """Return the current value (optimistic if pending)."""
        if self._optimistic_value is not None:
            return self._optimistic_value
        if self.entity_description.value_fn:
            value = self.entity_description.value_fn(self.coordinator.data)
            return float(value) if value is not None else None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value with optimistic update."""
        # Optimistic: update UI immediately
        self._optimistic_value = value
        self.async_write_ha_state()

        int_value = int(value)

        if self.entity_description.key == "curve":
            await self._api.set_curve(int_value)
        elif self.entity_description.key == "shift":
            await self._api.set_shift(int_value)

        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None
