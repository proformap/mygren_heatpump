"""Support for Mygren Heat Pump sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry

_LOGGER = logging.getLogger(__name__)


def _fmt_duration(seconds) -> str | None:
    """Format seconds into 'Xd Xh Xm Xs' string."""
    if seconds is None:
        return None
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return None
    if s <= 0:
        return "0s"
    days, rem = divmod(s, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def _fmt_timestamp(epoch) -> datetime | None:
    """Convert Unix epoch seconds to a timezone-aware datetime."""
    if epoch is None:
        return None
    try:
        ts = int(epoch)
    except (TypeError, ValueError):
        return None
    if ts <= 0:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


@dataclass
class MygrenSensorEntityDescription(SensorEntityDescription):
    """Describes Mygren sensor entity."""

    value_fn: Callable[[dict], any] | None = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Temperature sensors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEMPERATURE_SENSORS: tuple[MygrenSensorEntityDescription, ...] = (
    MygrenSensorEntityDescription(
        key="Tprimary_in",
        name="Primary In Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tprimary_in"),
    ),
    MygrenSensorEntityDescription(
        key="Tprimary_out",
        name="Primary Out Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tprimary_out"),
    ),
    MygrenSensorEntityDescription(
        key="Tsecondary_in",
        name="Secondary In Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tsecondary_in"),
    ),
    MygrenSensorEntityDescription(
        key="Tsecondary_out",
        name="Secondary Out Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tsecondary_out"),
    ),
    MygrenSensorEntityDescription(
        key="Tsystem_in",
        name="System In Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tsystem_in") or data.get("Theat_in"),
    ),
    MygrenSensorEntityDescription(
        key="Tsystem_out",
        name="System Out Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tsystem_out") or data.get("Theat_out"),
    ),
    MygrenSensorEntityDescription(
        key="Tint",
        name="Internal Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tint"),
    ),
    MygrenSensorEntityDescription(
        key="TintAvg",
        name="Internal Average Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("TintAvg"),
    ),
    MygrenSensorEntityDescription(
        key="Ttuv",
        name="Hot Water Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Ttuv"),
    ),
    MygrenSensorEntityDescription(
        key="Tbuf",
        name="Buffer Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tbuf"),
    ),
    MygrenSensorEntityDescription(
        key="Text",
        name="External Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Text"),
    ),
    MygrenSensorEntityDescription(
        key="TextAvg",
        name="External Average Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("TextAvg"),
    ),
    MygrenSensorEntityDescription(
        key="Tdischarge",
        name="Discharge Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tdischarge"),
    ),
    MygrenSensorEntityDescription(
        key="Tekviterm",
        name="Ekvithermal Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Tekviterm"),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Operational sensors (program, setpoints, gradients)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPERATIONAL_SENSORS: tuple[MygrenSensorEntityDescription, ...] = (
    MygrenSensorEntityDescription(
        key="mar_state",
        name="Control State",
        icon="mdi:state-machine",
        value_fn=lambda data: data.get("mar_state"),
    ),
    MygrenSensorEntityDescription(
        key="program",
        name="Program Mode",
        icon="mdi:cog",
        value_fn=lambda data: data.get("program"),
    ),
    MygrenSensorEntityDescription(
        key="system_dest",
        name="System Destination Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("system_dest") or data.get("heat_dest"),
    ),
    MygrenSensorEntityDescription(
        key="curve",
        name="Heating Curve",
        icon="mdi:chart-line",
        value_fn=lambda data: data.get("curve"),
    ),
    MygrenSensorEntityDescription(
        key="shift",
        name="Heating Curve Shift",
        icon="mdi:arrows-horizontal",
        value_fn=lambda data: data.get("shift"),
    ),
    MygrenSensorEntityDescription(
        key="comfort",
        name="Comfort Temperature Setting",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("comfort"),
    ),
    MygrenSensorEntityDescription(
        key="manual",
        name="Manual Temperature Setting",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("manual"),
    ),
    MygrenSensorEntityDescription(
        key="tuv_set",
        name="Hot Water Target Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-thermometer",
        value_fn=lambda data: data.get("tuv_set"),
    ),
    MygrenSensorEntityDescription(
        key="tuvgradient",
        name="Hot Water Gradient",
        icon="mdi:trending-up",
        native_unit_of_measurement="°C/min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("tuvgradient"),
    ),
    MygrenSensorEntityDescription(
        key="bufgradient",
        name="Buffer Gradient",
        icon="mdi:trending-up",
        native_unit_of_measurement="°C/min",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("bufgradient"),
    ),
    MygrenSensorEntityDescription(
        key="tariff",
        name="Tariff State",
        icon="mdi:cash-clock",
        value_fn=lambda data: data.get("tariff"),
    ),
    MygrenSensorEntityDescription(
        key="phases",
        name="Phases",
        icon="mdi:flash",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("phases"),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Diagnostic: System info & versions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIAGNOSTIC_VERSION_SENSORS: tuple[MygrenSensorEntityDescription, ...] = (
    MygrenSensorEntityDescription(
        key="display_version",
        name="Display Version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("display_version"),
    ),
    MygrenSensorEntityDescription(
        key="hostname",
        name="Hostname",
        icon="mdi:server",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("hostname"),
    ),
    MygrenSensorEntityDescription(
        key="os_version",
        name="OS Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("os_version"),
    ),
    MygrenSensorEntityDescription(
        key="binaries_version",
        name="Binaries Version",
        icon="mdi:package-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("binaries_version"),
    ),
    MygrenSensorEntityDescription(
        key="mar_version",
        name="MaR Version",
        icon="mdi:cog-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("mar_version"),
    ),
    MygrenSensorEntityDescription(
        key="owm_version",
        name="OWM Version",
        icon="mdi:cog-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("owm_version"),
    ),
    MygrenSensorEntityDescription(
        key="cm_version",
        name="CM Version",
        icon="mdi:cog-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("cm_version"),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Diagnostic: Counters, runtimes, timestamps
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIAGNOSTIC_STATUS_SENSORS: tuple[MygrenSensorEntityDescription, ...] = (
    # ── System runtime / uptime ───────────────────────────────────
    MygrenSensorEntityDescription(
        key="sruntime",
        name="System Runtime",
        icon="mdi:timer-outline",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("sruntime"),
    ),
    MygrenSensorEntityDescription(
        key="sruntime_formatted",
        name="System Runtime Formatted",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_duration(data.get("sruntime")),
    ),
    MygrenSensorEntityDescription(
        key="systemUptime",
        name="System Uptime",
        icon="mdi:clock-check-outline",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _try_int(data.get("systemUptime")),
    ),
    MygrenSensorEntityDescription(
        key="systemUptime_formatted",
        name="System Uptime Formatted",
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_duration(data.get("systemUptime")),
    ),
    MygrenSensorEntityDescription(
        key="systemLoad",
        name="System Load",
        icon="mdi:gauge",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("systemLoad"),
    ),
    MygrenSensorEntityDescription(
        key="sstartcnt",
        name="System Start Count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("sstartcnt"),
    ),
    MygrenSensorEntityDescription(
        key="sstarttime",
        name="System Start Time",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_timestamp(data.get("sstarttime")),
    ),
    # ── Compressor runtime / counters ─────────────────────────────
    MygrenSensorEntityDescription(
        key="cruntime",
        name="Compressor Runtime",
        icon="mdi:timer",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("cruntime"),
    ),
    MygrenSensorEntityDescription(
        key="cruntime_formatted",
        name="Compressor Runtime Formatted",
        icon="mdi:timer",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_duration(data.get("cruntime")),
    ),
    MygrenSensorEntityDescription(
        key="cstartcnt",
        name="Compressor Start Count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("cstartcnt"),
    ),
    MygrenSensorEntityDescription(
        key="cstarttime",
        name="Compressor Start Time",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_timestamp(data.get("cstarttime")),
    ),
    MygrenSensorEntityDescription(
        key="cstoptime",
        name="Compressor Stop Time",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _fmt_timestamp(data.get("cstoptime")),
    ),
    # ── Error counters ────────────────────────────────────────────
    MygrenSensorEntityDescription(
        key="sensorerrorcnt",
        name="Sensor Error Count",
        icon="mdi:alert-circle-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("sensorerrorcnt"),
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Diagnostic: Range limits (read-only setpoint bounds)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIAGNOSTIC_LIMITS_SENSORS: tuple[MygrenSensorEntityDescription, ...] = (
    MygrenSensorEntityDescription(
        key="bufmin",
        name="Buffer Min Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:thermometer-chevron-down",
        value_fn=lambda data: data.get("bufmin"),
    ),
    MygrenSensorEntityDescription(
        key="bufmax",
        name="Buffer Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:thermometer-chevron-up",
        value_fn=lambda data: data.get("bufmax"),
    ),
    MygrenSensorEntityDescription(
        key="tuvmin",
        name="Hot Water Hysteresis Min",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:thermometer-chevron-down",
        value_fn=lambda data: data.get("tuvmin"),
    ),
    MygrenSensorEntityDescription(
        key="tuvmax",
        name="Hot Water Hysteresis Max",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:thermometer-chevron-up",
        value_fn=lambda data: data.get("tuvmax"),
    ),
)

# ── Combine all sensor types ─────────────────────────────────────
SENSOR_TYPES: tuple[MygrenSensorEntityDescription, ...] = (
    *TEMPERATURE_SENSORS,
    *OPERATIONAL_SENSORS,
    *DIAGNOSTIC_VERSION_SENSORS,
    *DIAGNOSTIC_STATUS_SENSORS,
    *DIAGNOSTIC_LIMITS_SENSORS,
)


def _try_int(value) -> int | None:
    """Try to convert a value to int, return None on failure."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren sensor based on a config entry."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        MygrenSensor(coordinator, description, entry)
        for description in SENSOR_TYPES
    )


class MygrenSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mygren sensor."""

    entity_description: MygrenSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, description, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None
