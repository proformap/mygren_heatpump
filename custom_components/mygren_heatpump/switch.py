"""Support for Mygren Heat Pump switches."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

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
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren switch based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities(
        MygrenSwitch(coordinator, api, description, entry)
        for description in SWITCH_TYPES
    )


class MygrenSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Mygren switch."""

    entity_description: MygrenSwitchEntityDescription

    def __init__(self, coordinator, api, description, entry):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mygren (AI Trade s.r.o.)",
            "model": "Geo Heat Pump",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self.entity_description.key == "tuv_scheduler_enabled":
            await self._api.set_tuv_scheduler_enabled(True)
        elif self.entity_description.key == "program_scheduler_enabled":
            await self._api.set_program_scheduler_enabled(True)
        elif self.entity_description.key == "tariff_watch":
            await self._api.set_tariff_watch(True)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
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
