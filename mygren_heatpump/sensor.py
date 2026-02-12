"""Support for Mygren Heat Pump sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class MygrenSensorEntityDescription(SensorEntityDescription):
    """Describes Mygren sensor entity."""

    value_fn: Callable[[dict], any] | None = None


SENSOR_TYPES: tuple[MygrenSensorEntityDescription, ...] = (
    # Temperature sensors
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
    # Status sensors
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
        key="cruntime",
        name="Compressor Runtime",
        icon="mdi:timer",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("cruntime"),
    ),
    MygrenSensorEntityDescription(
        key="cstartcnt",
        name="Compressor Start Count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("cstartcnt"),
    ),
    MygrenSensorEntityDescription(
        key="sruntime",
        name="System Runtime",
        icon="mdi:timer",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("sruntime"),
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        MygrenSensor(coordinator, description, entry)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class MygrenSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Mygren sensor."""

    entity_description: MygrenSensorEntityDescription

    def __init__(self, coordinator, description, entry):
        """Initialize the sensor."""
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
    def native_value(self):
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None
