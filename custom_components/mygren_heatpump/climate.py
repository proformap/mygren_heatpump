"""Support for Mygren Heat Pump climate control.

The Mygren heat pump has evolved its program naming across firmware versions:

Old firmware (v3.x): program is an integer 0/1/2
    0 = Off, 1 = Auto (ekvithermal), 2 = Manual

New firmware (v4.x): program is a string from available_programs
    e.g. "Off", "Manual_comfort", "Cooling_comfort"
    Note: v4.x has NO auto/ekvithermal program — all available modes
    are listed in the telemetry "available_programs" array.

This climate entity handles both firmware versions.
"""
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


def _is_string_program(data: dict) -> bool:
    """Return True if this firmware uses string-based programs."""
    return isinstance(data.get("program"), str)


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
            "manufacturer": "Mygren (AI Trade s.r.o.)",
            "model": "SMARTHUB 06",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF, HVACMode.HEAT]

        # Check if cooling is available in the available programs
        available = self.coordinator.data.get("available_programs", [])
        if isinstance(available, list):
            for prog in available:
                if isinstance(prog, str) and "Cooling" in prog:
                    modes.append(HVACMode.COOL)
                    break

        # Auto is only available on older firmware with integer programs
        if not _is_string_program(self.coordinator.data):
            modes.append(HVACMode.AUTO)
        else:
            # v4+ firmware may have auto if program list includes non-manual/cooling
            for prog in available:
                if isinstance(prog, str) and prog not in ("Off",) and "Manual" not in prog and "Cooling" not in prog:
                    modes.append(HVACMode.AUTO)
                    break

        return modes

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        # Prefer interior temp, fallback to buffer
        temp = self.coordinator.data.get("Tint")
        if temp is not None and temp != 0:
            return temp
        return self.coordinator.data.get("Tbuf")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        program = self.coordinator.data.get("program", "")

        if isinstance(program, str):
            if "Manual" in program or "Cooling" in program:
                return self.coordinator.data.get("manual")
            return self.coordinator.data.get("comfort")
        else:
            if program == 2:
                return self.coordinator.data.get("manual") or self.coordinator.data.get("heat")
            return self.coordinator.data.get("comfort")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        program = self.coordinator.data.get("program", "")

        if isinstance(program, str) and ("Manual" in program or "Cooling" in program):
            return self.coordinator.data.get("manual_setmin", 15)
        elif isinstance(program, int) and program == 2:
            return self.coordinator.data.get("manual_setmin") or self.coordinator.data.get("heat_setmin", 15)
        return self.coordinator.data.get("comfort_setmin", 15)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        program = self.coordinator.data.get("program", "")

        if isinstance(program, str) and ("Manual" in program or "Cooling" in program):
            return self.coordinator.data.get("manual_setmax", 40)
        elif isinstance(program, int) and program == 2:
            return self.coordinator.data.get("manual_setmax") or self.coordinator.data.get("heat_setmax", 40)
        return self.coordinator.data.get("comfort_setmax", 35)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self.coordinator.data.get("hp_enabled"):
            return HVACMode.OFF

        program = self.coordinator.data.get("program", "")

        if isinstance(program, str):
            if program == "Off":
                return HVACMode.OFF
            if "Cooling" in program:
                return HVACMode.COOL
            if "Manual" in program:
                return HVACMode.HEAT
            # Any other string program → AUTO
            return HVACMode.AUTO
        else:
            if program == 0:
                return HVACMode.OFF
            if program == 2:
                return HVACMode.HEAT
            return HVACMode.AUTO

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
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
            if "Manual" in program or "Cooling" in program:
                return PRESET_COMFORT
            if program != "Off":
                return PRESET_ECO
        else:
            if program == 1:
                return PRESET_ECO
            if program == 2:
                return PRESET_COMFORT
        return None

    def _get_program_for_mode(self, target: str) -> str | int:
        """Map a target mode name to the correct program value.

        Uses the available_programs list from the API to find the right value.
        """
        available = self.coordinator.data.get("available_programs", [])

        if isinstance(available, list) and available:
            # v4+ firmware — use string program names
            for prog in available:
                if not isinstance(prog, str):
                    continue
                if target == "off" and prog == "Off":
                    return prog
                if target == "manual" and "Manual" in prog:
                    return prog
                if target == "cooling" and "Cooling" in prog:
                    return prog
                if target == "auto" and prog not in ("Off",) and "Manual" not in prog and "Cooling" not in prog:
                    return prog

            # Fallback: first matching or first available
            if target == "off":
                return "Off"
            if target == "manual" and len(available) > 1:
                return available[1]  # Usually Manual_comfort
            return available[0]
        else:
            # Legacy integer programs
            if target == "off":
                return 0
            if target == "auto":
                return 1
            return 2  # manual

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        temperature = int(temperature)
        program = self.coordinator.data.get("program", "")

        if isinstance(program, str) and ("Manual" in program or "Cooling" in program):
            await self._api.set_manual_temperature(temperature)
        elif isinstance(program, int) and program == 2:
            await self._api.set_manual_temperature(temperature)
        else:
            await self._api.set_comfort_temperature(temperature)

        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.set_heatpump_enabled(False)
        elif hvac_mode == HVACMode.HEAT:
            await self._api.set_heatpump_enabled(True)
            program = self._get_program_for_mode("manual")
            await self._api.set_program(program)
        elif hvac_mode == HVACMode.COOL:
            await self._api.set_heatpump_enabled(True)
            program = self._get_program_for_mode("cooling")
            await self._api.set_program(program)
        elif hvac_mode == HVACMode.AUTO:
            await self._api.set_heatpump_enabled(True)
            program = self._get_program_for_mode("auto")
            await self._api.set_program(program)

        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode == PRESET_ECO:
            program = self._get_program_for_mode("auto")
            await self._api.set_program(program)
        elif preset_mode == PRESET_COMFORT:
            program = self._get_program_for_mode("manual")
            await self._api.set_program(program)

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
