"""Support for Mygren Heat Pump binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Mygren binary sensor entity."""

    value_fn: Callable[[dict], bool] | None = None


BINARY_SENSOR_TYPES: tuple[MygrenBinarySensorEntityDescription, ...] = (
    MygrenBinarySensorEntityDescription(
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda data: bool(data.get("online")),
    ),
    MygrenBinarySensorEntityDescription(
        key="compressor",
        name="Compressor",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
        value_fn=lambda data: bool(data.get("compressor")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hprun",
        name="Heat Pump Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:heat-pump",
        value_fn=lambda data: bool(data.get("hprun")),
    ),
    MygrenBinarySensorEntityDescription(
        key="heating",
        name="Heating Active",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(data.get("heating")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cooling",
        name="Cooling Active",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=lambda data: bool(data.get("cooling")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hp_enabled",
        name="Heat Pump Enabled",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:power",
        value_fn=lambda data: bool(data.get("hp_enabled")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tuv_enabled",
        name="Hot Water Enabled",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-boiler",
        value_fn=lambda data: bool(data.get("tuv_enabled")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tuvneedheat",
        name="Hot Water Needs Heat",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(data.get("tuvneedheat")),
    ),
    MygrenBinarySensorEntityDescription(
        key="bufneedheat",
        name="Buffer Needs Heat",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(data.get("bufneedheat")),
    ),
    MygrenBinarySensorEntityDescription(
        key="pw_error",
        name="Power Error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: bool(data.get("pw_error")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hpcanstart",
        name="Heat Pump Can Start",
        icon="mdi:play-circle",
        value_fn=lambda data: bool(data.get("hpcanstart")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hpcanstop",
        name="Heat Pump Can Stop",
        icon="mdi:stop-circle",
        value_fn=lambda data: bool(data.get("hpcanstop")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hdoinstalled",
        name="HDO Installed",
        icon="mdi:power-plug",
        value_fn=lambda data: bool(data.get("hdoinstalled") or data.get("tariff_installed")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tariff_watch",
        name="Tariff Watching",
        icon="mdi:cash-clock",
        value_fn=lambda data: bool(data.get("tariff_watch") or data.get("watchhdo")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tuv_sched_enabled",
        name="Hot Water Schedule Enabled",
        icon="mdi:calendar-clock",
        value_fn=lambda data: bool(data.get("tuv_sched_enabled")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tuv_sched_active",
        name="Hot Water Schedule Active",
        icon="mdi:calendar-check",
        value_fn=lambda data: bool(data.get("tuv_sched_active")),
    ),
    MygrenBinarySensorEntityDescription(
        key="program_sched_enabled",
        name="Program Schedule Enabled",
        icon="mdi:calendar-clock",
        value_fn=lambda data: bool(data.get("program_sched_enabled")),
    ),
    MygrenBinarySensorEntityDescription(
        key="program_sched_active",
        name="Program Schedule Active",
        icon="mdi:calendar-check",
        value_fn=lambda data: bool(data.get("program_sched_active")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hp_failure",
        name="Heat Pump Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: bool(data.get("hp_failure")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hp_forcedpause",
        name="Heat Pump Forced Pause",
        icon="mdi:pause-circle",
        value_fn=lambda data: bool(data.get("hp_forcedpause") or data.get("hpforcedstop")),
    ),
    MygrenBinarySensorEntityDescription(
        key="systemneedheat",
        name="System Needs Heat",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(data.get("systemneedheat") or data.get("heatneed")),
    ),
    MygrenBinarySensorEntityDescription(
        key="coolneed",
        name="System Needs Cooling",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=lambda data: bool(data.get("coolneed")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren binary sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        MygrenBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class MygrenBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Mygren binary sensor."""

    entity_description: MygrenBinarySensorEntityDescription

    def __init__(self, coordinator, description, entry):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
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
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return bool(self.coordinator.data.get(self.entity_description.key))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
