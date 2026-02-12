"""Support for Mygren Heat Pump number entities."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenNumberEntityDescription(NumberEntityDescription):
    """Describes Mygren number entity."""

    value_fn: Callable[[dict], float | None] | None = None
    set_fn: Callable | None = None


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
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren number based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = [
        MygrenNumber(coordinator, api, description, entry)
        for description in NUMBER_TYPES
    ]

    async_add_entities(entities)


class MygrenNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Mygren number entity."""

    entity_description: MygrenNumberEntityDescription

    def __init__(self, coordinator, api, description, entry):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mygren",
            "model": "Heat Pump",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.entity_description.value_fn:
            value = self.entity_description.value_fn(self.coordinator.data)
            return float(value) if value is not None else None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        int_value = int(value)
        
        if self.entity_description.key == "curve":
            await self.hass.async_add_executor_job(
                self._api.set_curve, int_value
            )
        elif self.entity_description.key == "shift":
            await self.hass.async_add_executor_job(
                self._api.set_shift, int_value
            )
            
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None
