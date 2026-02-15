"""Support for Mygren Heat Pump climate control (MaR v4+ only).

The Mygren MaR v4 firmware uses string-based program names fetched from
the ``available_programs`` list in the /api/telemetry response.

Example programs: ["Off", "Manual_comfort", "Cooling_comfort"]

Program → HVAC-mode mapping
----------------------------
  "Off"                          → HVACMode.OFF
  Programs containing "Manual"   → HVACMode.HEAT
  Programs containing "Cooling"  → HVACMode.COOL

Temperature control
-------------------
Both *Manual_comfort* and *Cooling_comfort* regulate the heating /
cooling circuit using the interior-sensor thermostat with the
``comfort`` set-point (desired room temperature).

The ``manual`` value (system output temperature) is exposed
separately via a Number entity for advanced tuning.

Optimistic updates
------------------
When the user changes temperature or HVAC mode, the entity immediately
reflects the new value in the UI (optimistic state).  The next
coordinator refresh then confirms the actual device state and clears
the optimistic override.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device import mygren_device_info
from .models import MygrenConfigEntry

_LOGGER = logging.getLogger(__name__)

# ── helpers ───────────────────────────────────────────────────────

_MODE_MATCHERS: dict[str, Any] = {
    "off":     lambda p: p == "Off",
    "manual":  lambda p: "Manual" in p,
    "cooling": lambda p: "Cooling" in p,
}


def _find_program(available: list[str], target: str) -> str | None:
    """Return the first program from *available* that matches *target*."""
    matcher = _MODE_MATCHERS.get(target)
    if matcher is None:
        return None
    for prog in available:
        if isinstance(prog, str) and matcher(prog):
            return prog
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MygrenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren climate based on a config entry."""
    data = entry.runtime_data

    async_add_entities([MygrenClimate(data.coordinator, data.api, entry)])


class MygrenClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Mygren climate device (MaR v4+)."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_has_entity_name = True
    _attr_name = "Heating"
    _enable_turn_on_off_backwards_compat = False

    def __init__(self, coordinator, api, entry) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = mygren_device_info(
            entry, sw_version=coordinator.data.get("mar_version", "Unknown")
        )
        # Optimistic state — None means "use coordinator data"
        self._optimistic_target_temp: float | None = None
        self._optimistic_hvac_mode: HVACMode | None = None

    def _handle_coordinator_update(self) -> None:
        """Clear optimistic state when coordinator delivers fresh data."""
        self._optimistic_target_temp = None
        self._optimistic_hvac_mode = None
        super()._handle_coordinator_update()

    # ── available programs helper ─────────────────────────────────

    def _available_programs(self) -> list[str]:
        """Return the available_programs list from telemetry."""
        progs = self.coordinator.data.get("available_programs", [])
        return progs if isinstance(progs, list) else []

    # ── HVAC modes ────────────────────────────────────────────────

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Build the HVAC-mode list dynamically from available_programs."""
        modes: list[HVACMode] = [HVACMode.OFF]

        for prog in self._available_programs():
            if not isinstance(prog, str) or prog == "Off":
                continue
            if "Manual" in prog and HVACMode.HEAT not in modes:
                modes.append(HVACMode.HEAT)
            elif "Cooling" in prog and HVACMode.COOL not in modes:
                modes.append(HVACMode.COOL)

        return modes

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode (optimistic if pending)."""
        if self._optimistic_hvac_mode is not None:
            return self._optimistic_hvac_mode

        if not self.coordinator.data.get("hp_enabled"):
            return HVACMode.OFF

        program = self.coordinator.data.get("program", "")

        if program == "Off":
            return HVACMode.OFF
        if isinstance(program, str) and "Cooling" in program:
            return HVACMode.COOL
        if isinstance(program, str) and "Manual" in program:
            return HVACMode.HEAT

        _LOGGER.debug("Unknown program '%s', reporting OFF", program)
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        if not self.coordinator.data.get("hp_enabled"):
            return HVACAction.OFF

        program = self.coordinator.data.get("program", "")
        if program == "Off":
            return HVACAction.OFF

        if self.coordinator.data.get("cooling"):
            if self.coordinator.data.get("compressor"):
                return HVACAction.COOLING
            return HVACAction.IDLE

        if self.coordinator.data.get("heating") or self.coordinator.data.get("heatneed"):
            if self.coordinator.data.get("compressor"):
                return HVACAction.HEATING
            return HVACAction.IDLE

        return HVACAction.IDLE

    # ── temperature ───────────────────────────────────────────────

    @property
    def current_temperature(self) -> float | None:
        """Return the current interior temperature."""
        temp = self.coordinator.data.get("Tint")
        if temp is not None and temp != 0:
            return temp
        return self.coordinator.data.get("Tbuf") or None

    @property
    def target_temperature(self) -> float | None:
        """Return the comfort set-point (optimistic if pending)."""
        if self._optimistic_target_temp is not None:
            return self._optimistic_target_temp
        return self.coordinator.data.get("comfort")

    @property
    def min_temp(self) -> float:
        """Return the minimum settable temperature."""
        return self.coordinator.data.get("comfort_setmin", 15)

    @property
    def max_temp(self) -> float:
        """Return the maximum settable temperature."""
        return self.coordinator.data.get("comfort_setmax", 35)

    @property
    def target_temperature_step(self) -> float:
        """Return the temperature step."""
        return 0.5

    # ── commands ───────────────────────────────────────────────────

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target (comfort) temperature with optimistic update."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        # Optimistic: update UI immediately
        self._optimistic_target_temp = float(temperature)
        self.async_write_ha_state()

        await self._api.set_comfort_temperature(int(temperature))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode with optimistic update."""
        # Optimistic: update UI immediately
        self._optimistic_hvac_mode = hvac_mode
        self.async_write_ha_state()

        available = self._available_programs()

        if hvac_mode == HVACMode.OFF:
            prog = _find_program(available, "off")
            if prog:
                await self._api.set_program(prog)
            else:
                await self._api.set_heatpump_enabled(False)
                await self.coordinator.async_request_refresh()
                return
            await self._api.set_heatpump_enabled(True)

        elif hvac_mode == HVACMode.HEAT:
            await self._api.set_heatpump_enabled(True)
            prog = _find_program(available, "manual")
            if prog:
                await self._api.set_program(prog)
            else:
                _LOGGER.warning("No Manual program found in %s", available)

        elif hvac_mode == HVACMode.COOL:
            await self._api.set_heatpump_enabled(True)
            prog = _find_program(available, "cooling")
            if prog:
                await self._api.set_program(prog)
            else:
                _LOGGER.warning("No Cooling program found in %s", available)

        await self.coordinator.async_request_refresh()

    # ── extra attributes ──────────────────────────────────────────

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "program": self.coordinator.data.get("program"),
            "available_programs": self.coordinator.data.get("available_programs"),
            "system_destination": self.coordinator.data.get("system_dest"),
            "manual_output_temp": self.coordinator.data.get("manual"),
            "buffer_min": self.coordinator.data.get("bufmin"),
            "buffer_max": self.coordinator.data.get("bufmax"),
            "heating_curve": self.coordinator.data.get("curve"),
            "curve_shift": self.coordinator.data.get("shift"),
            "comfort_setting": self.coordinator.data.get("comfort"),
            "compressor_runtime": self.coordinator.data.get("cruntime"),
            "compressor_starts": self.coordinator.data.get("cstartcnt"),
            "external_temp": self.coordinator.data.get("Text"),
            "external_temp_avg": self.coordinator.data.get("TextAvg"),
            "internal_temp": self.coordinator.data.get("Tint"),
            "internal_temp_avg": self.coordinator.data.get("TintAvg"),
        }
