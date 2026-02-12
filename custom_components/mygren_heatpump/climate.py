"""Support for Mygren Heat Pump climate control."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
    PRESET_COMFORT,
    PRESET_ECO,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren climate based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities([MygrenClimate(coordinator, api, entry)])


class MygrenClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Mygren climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO]

    def __init__(self, coordinator, api, entry):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Heating"
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mygren",
            "model": "Heat Pump",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        # Try Tint (internal), fallback to Tbuf (buffer)
        return self.coordinator.data.get("Tint") or self.coordinator.data.get("Tbuf")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        program = self.coordinator.data.get("program", "")
        
        # Handle both string and numeric program values
        if isinstance(program, str):
            # String format: "Manual_comfort", "Off", "Cooling_comfort", etc.
            if "Manual" in program or "Cooling" in program:
                return self.coordinator.data.get("manual")
            else:
                return self.coordinator.data.get("comfort")
        else:
            # Numeric format (legacy): 0=Off, 1=Auto, 2=Manual
            if program == 2:
                return self.coordinator.data.get("manual")
            else:
                return self.coordinator.data.get("comfort")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        program = self.coordinator.data.get("program", "")
        
        if isinstance(program, str) and "Manual" in program:
            return self.coordinator.data.get("manual_setmin", 15)
        else:
            return self.coordinator.data.get("comfort_setmin", 15)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        program = self.coordinator.data.get("program", "")
        
        if isinstance(program, str) and "Manual" in program:
            return self.coordinator.data.get("manual_setmax", 40)
        else:
            return self.coordinator.data.get("comfort_setmax", 35)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current hvac mode."""
        if not self.coordinator.data.get("hp_enabled"):
            return HVACMode.OFF

        program = self.coordinator.data.get("program", "")
        
        # Handle string program format
        if isinstance(program, str):
            if program == "Off":
                return HVACMode.OFF
            elif "Manual" in program:
                return HVACMode.HEAT
            elif "Cooling" in program:
                return HVACMode.COOL
            else:
                return HVACMode.AUTO
        else:
            # Numeric format (legacy)
            if program == 0:
                return HVACMode.OFF
            elif program == 2:
                return HVACMode.HEAT
            else:
                return HVACMode.AUTO

    @property
    def hvac_action(self) -> HVACAction:
        """Return current hvac action."""
        if not self.coordinator.data.get("hp_enabled"):
            return HVACAction.OFF

        if self.coordinator.data.get("cooling"):
            if self.coordinator.data.get("compressor"):
                return HVACAction.COOLING
            return HVACAction.IDLE

        if self.coordinator.data.get("heating"):
            if self.coordinator.data.get("compressor"):
                return HVACAction.HEATING
            return HVACAction.IDLE

        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Return current preset mode."""
        program = self.coordinator.data.get("program", "")
        
        if isinstance(program, str):
            # String format
            if "Manual" in program or "Cooling" in program:
                return PRESET_COMFORT
            elif program != "Off":
                return PRESET_ECO
        else:
            # Numeric format (legacy)
            if program == 1:
                return PRESET_ECO
            elif program == 2:
                return PRESET_COMFORT
        
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        temperature = int(temperature)

        # Validate temperature range
        if temperature < self.min_temp or temperature > self.max_temp:
            _LOGGER.error(
                "Temperature %s out of range (%s-%s)",
                temperature,
                self.min_temp,
                self.max_temp,
            )
            return

        # Set temperature based on current mode
        program = self.coordinator.data.get("program", 0)
        
        if program == 2:  # Manual mode
            await self.hass.async_add_executor_job(
                self._api.set_manual_temperature, temperature
            )
        else:  # Comfort temperature for auto mode
            await self.hass.async_add_executor_job(
                self._api.set_comfort_temperature, temperature
            )
            
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        if hvac_mode == HVACMode.OFF:
            # Disable heat pump
            await self.hass.async_add_executor_job(
                self._api.set_heatpump_enabled, False
            )
        elif hvac_mode == HVACMode.HEAT:
            # Enable heat pump and set manual program
            await self.hass.async_add_executor_job(
                self._api.set_heatpump_enabled, True
            )
            await self.hass.async_add_executor_job(
                self._api.set_program, 2  # Manual mode
            )
        elif hvac_mode == HVACMode.AUTO:
            # Enable heat pump and set auto/ekvithermal program
            await self.hass.async_add_executor_job(
                self._api.set_heatpump_enabled, True
            )
            await self.hass.async_add_executor_job(
                self._api.set_program, 1  # Auto/Ekvithermal mode
            )
            
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode == PRESET_ECO:
            # Set to auto/ekvithermal program
            await self.hass.async_add_executor_job(
                self._api.set_program, 1
            )
        elif preset_mode == PRESET_COMFORT:
            # Set to manual program
            await self.hass.async_add_executor_job(
                self._api.set_program, 2
            )
            
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "program": self.coordinator.data.get("program"),
            "available_programs": self.coordinator.data.get("available_programs"),
            "system_destination": self.coordinator.data.get("system_dest") or self.coordinator.data.get("heat_dest"),
            "buffer_min": self.coordinator.data.get("bufmin"),
            "buffer_max": self.coordinator.data.get("bufmax"),
            "heating_curve": self.coordinator.data.get("curve"),
            "curve_shift": self.coordinator.data.get("shift"),
            "comfort_setting": self.coordinator.data.get("comfort"),
            "manual_setting": self.coordinator.data.get("manual"),
            "compressor_runtime": self.coordinator.data.get("cruntime"),
            "compressor_starts": self.coordinator.data.get("cstartcnt"),
            "external_temp": self.coordinator.data.get("Text"),
            "external_temp_avg": self.coordinator.data.get("TextAvg"),
            "internal_temp": self.coordinator.data.get("Tint"),
            "internal_temp_avg": self.coordinator.data.get("TintAvg"),
        }
