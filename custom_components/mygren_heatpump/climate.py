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

No preset modes are exposed — the climate card shows only the
HVAC-mode selector and the target temperature.
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
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ── helpers ───────────────────────────────────────────────────────

# Map a *target* mode keyword to a predicate that matches an
# available_programs entry.
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
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mygren climate based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities([MygrenClimate(coordinator, api, entry)])


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
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mygren (AI Trade s.r.o.)",
            "model": "SMARTHUB 06",
            "sw_version": coordinator.data.get("mar_version", "Unknown"),
        }

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
        """Return current HVAC mode based on the active program string."""
        if not self.coordinator.data.get("hp_enabled"):
            return HVACMode.OFF

        program = self.coordinator.data.get("program", "")

        if program == "Off":
            return HVACMode.OFF
        if isinstance(program, str) and "Cooling" in program:
            return HVACMode.COOL
        if isinstance(program, str) and "Manual" in program:
            return HVACMode.HEAT

        # Unknown program string — treat as OFF
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
        # Fallback to buffer temperature
        return self.coordinator.data.get("Tbuf") or None

    @property
    def target_temperature(self) -> float | None:
        """Return the comfort (room) set-point."""
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
        """Set new target (comfort) temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        await self._api.set_comfort_temperature(int(temperature))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode by selecting the matching program."""
        available = self._available_programs()

        if hvac_mode == HVACMode.OFF:
            prog = _find_program(available, "off")
            if prog:
                await self._api.set_program(prog)
            else:
                # No "Off" program — disable heatpump instead
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
