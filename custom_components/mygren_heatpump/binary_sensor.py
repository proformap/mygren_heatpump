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
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Mygren binary sensor entity."""

    value_fn: Callable[[dict], bool] | None = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Core operational binary sensors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPERATIONAL_BINARY_SENSORS: tuple[MygrenBinarySensorEntityDescription, ...] = (
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
        key="systemneedheat",
        name="System Needs Heat",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(
            data.get("systemneedheat") or data.get("heatneed")
        ),
    ),
    MygrenBinarySensorEntityDescription(
        key="coolneed",
        name="System Needs Cooling",
        device_class=BinarySensorDeviceClass.COLD,
        value_fn=lambda data: bool(data.get("coolneed")),
    ),
    MygrenBinarySensorEntityDescription(
        key="heatneed",
        name="Heat Needed",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: bool(data.get("heatneed")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tariff_installed",
        name="Tariff Installed",
        icon="mdi:power-plug",
        value_fn=lambda data: bool(
            data.get("tariff_installed") or data.get("hdoinstalled")
        ),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Error / fault binary sensors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERROR_BINARY_SENSORS: tuple[MygrenBinarySensorEntityDescription, ...] = (
    MygrenBinarySensorEntityDescription(
        key="pw_error",
        name="Power Error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: bool(data.get("pw_error")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hp_failure",
        name="Heat Pump Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: bool(data.get("hp_failure")),
    ),
    MygrenBinarySensorEntityDescription(
        key="high_secondary_in",
        name="High Secondary In",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:thermometer-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: bool(data.get("high_secondary_in")),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Diagnostic: Control / state binary sensors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIAGNOSTIC_BINARY_SENSORS: tuple[MygrenBinarySensorEntityDescription, ...] = (
    MygrenBinarySensorEntityDescription(
        key="hpcanstart",
        name="Heat Pump Can Start",
        icon="mdi:play-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("hpcanstart")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hpcanstop",
        name="Heat Pump Can Stop",
        icon="mdi:stop-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("hpcanstop")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hp_forcedpause",
        name="Heat Pump Forced Pause",
        icon="mdi:pause-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(
            data.get("hp_forcedpause") or data.get("hpforcedstop")
        ),
    ),
    MygrenBinarySensorEntityDescription(
        key="primary_forced_run",
        name="Primary Forced Run",
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("primary_forced_run")),
    ),
    MygrenBinarySensorEntityDescription(
        key="hwthermostat1",
        name="HW Thermostat 1",
        icon="mdi:thermostat",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("hwthermostat1")),
    ),
    MygrenBinarySensorEntityDescription(
        key="swthermostat1",
        name="SW Thermostat 1",
        icon="mdi:thermostat",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("swthermostat1")),
    ),
    # ── Circulation pumps ─────────────────────────────────────────
    MygrenBinarySensorEntityDescription(
        key="cpprimary",
        name="Circulation Pump Primary",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cpprimary")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cppreprimary",
        name="Circulation Pump Pre-Primary",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cppreprimary")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cpsecondary",
        name="Circulation Pump Secondary",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cpsecondary")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cpsystem",
        name="Circulation Pump System",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cpsystem")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cptuv",
        name="Circulation Pump TUV",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cptuv")),
    ),
    MygrenBinarySensorEntityDescription(
        key="cpradiator",
        name="Circulation Pump Radiator",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("cpradiator")),
    ),
    # ── Three-way valves ──────────────────────────────────────────
    MygrenBinarySensorEntityDescription(
        key="twv_sec_01",
        name="Three-Way Valve Secondary 01",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("twv_sec_01")),
    ),
    MygrenBinarySensorEntityDescription(
        key="twv_sec_02",
        name="Three-Way Valve Secondary 02",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("twv_sec_02")),
    ),
    MygrenBinarySensorEntityDescription(
        key="twv_cooling",
        name="Three-Way Valve Cooling",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("twv_cooling")),
    ),
    # ── Mixing valve ──────────────────────────────────────────────
    MygrenBinarySensorEntityDescription(
        key="mixup",
        name="Mixing Valve Up",
        icon="mdi:valve-open",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("mixup")),
    ),
    MygrenBinarySensorEntityDescription(
        key="mixdown",
        name="Mixing Valve Down",
        icon="mdi:valve-closed",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("mixdown")),
    ),
    # ── Scheduler states ──────────────────────────────────────────
    MygrenBinarySensorEntityDescription(
        key="program_sched_active",
        name="Program Scheduler Active",
        icon="mdi:calendar-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("program_sched_active")),
    ),
    MygrenBinarySensorEntityDescription(
        key="tuv_sched_active",
        name="Hot Water Scheduler Active",
        icon="mdi:calendar-check",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("tuv_sched_active")),
    ),
    # ── Radiator ──────────────────────────────────────────────────
    MygrenBinarySensorEntityDescription(
        key="radiatorinstalled",
        name="Radiator Installed",
        icon="mdi:radiator",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: bool(data.get("radiatorinstalled")),
    ),
)

# ── Combine all binary sensor types ──────────────────────────────
BINARY_SENSOR_TYPES: tuple[MygrenBinarySensorEntityDescription, ...] = (
    *OPERATIONAL_BINARY_SENSORS,
    *ERROR_BINARY_SENSORS,
    *DIAGNOSTIC_BINARY_SENSORS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren binary sensor based on a config entry."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        MygrenBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_TYPES
    )


class MygrenBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Mygren binary sensor."""

    entity_description: MygrenBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, entry):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )

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
