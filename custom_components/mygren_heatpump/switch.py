"""Support for Mygren Heat Pump switches.

Optimistic updates: switch toggles are reflected in the UI immediately.
The coordinator background refresh then confirms the actual device state.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenSwitchEntityDescription(SwitchEntityDescription):
    """Describes Mygren switch entity."""

    value_fn: Callable[[dict], bool] | None = None


SWITCH_TYPES: tuple[MygrenSwitchEntityDescription, ...] = (
    MygrenSwitchEntityDescription(
        key="tuv_scheduler_enabled",
        name="Hot Water Scheduler",
        icon="mdi:calendar-clock",
        value_fn=lambda data: bool(data.get("tuv_sched_enabled")),
    ),
    MygrenSwitchEntityDescription(
        key="program_scheduler_enabled",
        name="Program Scheduler",
        icon="mdi:calendar-clock",
        value_fn=lambda data: bool(data.get("program_sched_enabled")),
    ),
    MygrenSwitchEntityDescription(
        key="tariff_watch",
        name="Tariff Watching",
        icon="mdi:cash-clock",
        value_fn=lambda data: bool(
            data.get("tariff_watch") or data.get("watchhdo")
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren switch based on a config entry."""
    data = entry.runtime_data

    async_add_entities(
        MygrenSwitch(data.coordinator, data.api, description, entry)
        for description in SWITCH_TYPES
    )


class MygrenSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Mygren switch."""

    entity_description: MygrenSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, api, description, entry):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )
        # Optimistic state — None means "use coordinator data"
        self._optimistic_state: bool | None = None

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state when coordinator delivers fresh data."""
        self._optimistic_state = None
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on (optimistic if pending)."""
        if self._optimistic_state is not None:
            return self._optimistic_state
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on with optimistic update."""
        # Optimistic: update UI immediately
        self._optimistic_state = True
        self.async_write_ha_state()

        if self.entity_description.key == "tuv_scheduler_enabled":
            await self._api.set_tuv_scheduler_enabled(True)
        elif self.entity_description.key == "program_scheduler_enabled":
            await self._api.set_program_scheduler_enabled(True)
        elif self.entity_description.key == "tariff_watch":
            await self._api.set_tariff_watch(True)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off with optimistic update."""
        # Optimistic: update UI immediately
        self._optimistic_state = False
        self.async_write_ha_state()

        if self.entity_description.key == "tuv_scheduler_enabled":
            await self._api.set_tuv_scheduler_enabled(False)
        elif self.entity_description.key == "program_scheduler_enabled":
            await self._api.set_program_scheduler_enabled(False)
        elif self.entity_description.key == "tariff_watch":
            await self._api.set_tariff_watch(False)

        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
