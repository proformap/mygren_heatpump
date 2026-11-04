"""Tests the integration's logic against minimal stand-ins for Home Assistant.

Run from anywhere, with no packages to install:

    python3 -B tests/test_integration.py

These tests replace Home Assistant, aiohttp and the heat pump with stand-ins,
so they don't prove the integration works on a real installation. Test changes
on Home Assistant as well.
"""
import asyncio
from dataclasses import dataclass
import enum
from pathlib import Path
import sys
import time
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    mod.__path__ = []
    sys.modules[name] = mod
    return mod


class HomeAssistantError(Exception):
    pass


class ConfigEntryNotReady(HomeAssistantError):
    pass


class UpdateFailed(HomeAssistantError):
    pass


class Named:
    def __getattr__(self, name):
        return name


class Platform(Named):
    pass


class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_method, update_interval):
        self.update_method = update_method

    async def async_config_entry_first_refresh(self):
        try:
            self.data = await self.update_method()
        except UpdateFailed as err:
            raise ConfigEntryNotReady(str(err)) from err

    def __class_getitem__(cls, item):
        return cls


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def _handle_coordinator_update(self):
        pass

    def async_write_ha_state(self):
        pass


class HVACMode(str, enum.Enum):
    OFF = "off"
    HEAT = "heat"
    COOL = "cool"


@dataclass
class Description:
    key: str = ""
    name: str = None
    icon: str = None
    device_class: str = None
    entity_category: str = None
    entity_registry_enabled_default: bool = True
    native_min_value: float = None
    native_max_value: float = None
    native_step: float = None
    mode: str = None
    native_unit_of_measurement: str = None
    state_class: str = None


module("aiohttp", ClientTimeout=lambda total: None, ClientSession=object,
       TCPConnector=object, ClientError=Exception, ClientSSLError=Exception)
module("homeassistant")
module("homeassistant.const", Platform=Platform(), EntityCategory=Named(),
       UnitOfTemperature=Named(), STATE_OFF="off")
module("homeassistant.config_entries", ConfigEntry=object)
module("homeassistant.core", HomeAssistant=object)
module("homeassistant.exceptions", HomeAssistantError=HomeAssistantError,
       ConfigEntryNotReady=ConfigEntryNotReady)
module("homeassistant.helpers")
module("homeassistant.helpers.entity_platform", AddEntitiesCallback=object)
module("homeassistant.helpers.update_coordinator",
       DataUpdateCoordinator=DataUpdateCoordinator, UpdateFailed=UpdateFailed,
       CoordinatorEntity=CoordinatorEntity)
module("homeassistant.components")
module("homeassistant.components.climate", ClimateEntity=object,
       ClimateEntityFeature=mock.MagicMock(), HVACMode=HVACMode, HVACAction=Named())
module("homeassistant.components.water_heater", WaterHeaterEntity=object,
       WaterHeaterEntityFeature=mock.MagicMock())
module("homeassistant.components.number", NumberEntity=object,
       NumberEntityDescription=Description, NumberMode=Named(),
       NumberDeviceClass=Named())
module("homeassistant.components.sensor", SensorEntity=object,
       SensorEntityDescription=Description, SensorDeviceClass=Named(),
       SensorStateClass=Named())
module("homeassistant.components.switch", SwitchEntity=object,
       SwitchEntityDescription=Description)
module("homeassistant.components.binary_sensor", BinarySensorEntity=object,
       BinarySensorEntityDescription=Description, BinarySensorDeviceClass=Named())

# models.py uses Python 3.12 syntax. Replacing it lets the tests run on older
# versions of Python too.
PKG = "custom_components.mygren_heatpump"
module(PKG + ".models", MygrenConfigEntry=object,
       MygrenRuntimeData=lambda api, coordinator: types.SimpleNamespace(
           api=api, coordinator=coordinator))

import custom_components.mygren_heatpump as integration  # noqa: E402
from custom_components.mygren_heatpump import (  # noqa: E402
    binary_sensor, climate, const, number, sensor, switch, water_heater,
)
from custom_components.mygren_heatpump.mygren_api import (  # noqa: E402
    MygrenAuthError, MygrenConnectionError,
)


def make_coordinator(data):
    return types.SimpleNamespace(
        data=data, last_update_success=True,
        async_request_refresh=mock.AsyncMock(),
    )


ENTRY = types.SimpleNamespace(entry_id="e", title="t", data={"host": "https://x"})


def make_entity(cls, data, *args):
    return cls(make_coordinator(data), mock.AsyncMock(), *args, ENTRY)


def poll(entity, data):
    entity.coordinator.data = data
    entity._handle_coordinator_update()


class Setup(unittest.TestCase):
    def run_setup(self, api):
        entry = types.SimpleNamespace(
            data={"host": "x", "username": "u", "password": "p"}
        )
        with mock.patch.object(integration, "MygrenAPI", return_value=api):
            return asyncio.run(integration.async_setup_entry(mock.MagicMock(), entry))

    def test_unreachable_pump_retries_and_closes_session(self):
        api = mock.AsyncMock()
        api.authenticate.side_effect = MygrenConnectionError("offline")
        with self.assertRaises(ConfigEntryNotReady):
            self.run_setup(api)
        api.close.assert_awaited_once()

    def test_wrong_password_does_not_retry(self):
        api = mock.AsyncMock()
        api.authenticate.side_effect = MygrenAuthError("bad")
        self.assertFalse(self.run_setup(api))
        api.close.assert_awaited_once()

    def test_failed_first_refresh_closes_session(self):
        api = mock.AsyncMock()
        api.get_telemetry.side_effect = MygrenConnectionError("offline")
        with self.assertRaises(ConfigEntryNotReady):
            self.run_setup(api)
        api.close.assert_awaited_once()


class Comfort(unittest.TestCase):
    def setUp(self):
        self.entity = make_entity(climate.MygrenClimate, {"comfort": 21.0})

    def test_step_is_a_tenth(self):
        self.assertEqual(self.entity.target_temperature_step, 0.1)

    def test_sends_tenths_unchanged(self):
        asyncio.run(self.entity.async_set_temperature(temperature=21.3))
        self.entity._api.set_comfort_temperature.assert_awaited_once_with(21.3)
        self.assertEqual(self.entity.target_temperature, 21.3)

    def test_only_exact_tenth_confirms(self):
        asyncio.run(self.entity.async_set_temperature(temperature=21.3))
        poll(self.entity, {"comfort": 21.0})
        self.assertEqual(self.entity._pending_target.value, 21.3)
        poll(self.entity, {"comfort": 21.3})
        self.assertIsNone(self.entity._pending_target.value)

    def test_failed_write_rolls_back(self):
        self.entity._api.set_comfort_temperature.side_effect = MygrenConnectionError("x")
        with self.assertRaises(HomeAssistantError):
            asyncio.run(self.entity.async_set_temperature(temperature=25))
        self.assertEqual(self.entity.target_temperature, 21.0)
        self.entity.coordinator.async_request_refresh.assert_awaited_once()

    def test_unconfirmed_value_times_out(self):
        asyncio.run(self.entity.async_set_temperature(temperature=25))
        poll(self.entity, {"comfort": 21.0})
        self.assertEqual(self.entity.target_temperature, 25.0)
        later = time.monotonic() + const.OPTIMISTIC_TIMEOUT + 1
        with mock.patch("time.monotonic", return_value=later):
            poll(self.entity, {"comfort": 21.0})
        self.assertEqual(self.entity.target_temperature, 21.0)


class HvacMode(unittest.TestCase):
    DATA = {"hp_enabled": 1, "program": "Manual_comfort",
            "available_programs": ["Off", "Manual_comfort", "Cooling_comfort"]}

    def test_off_keeps_pump_enabled(self):
        entity = make_entity(climate.MygrenClimate, dict(self.DATA))
        asyncio.run(entity.async_set_hvac_mode(HVACMode.OFF))
        entity._api.set_program.assert_awaited_once_with("Off")
        entity._api.set_heatpump_enabled.assert_awaited_once_with(True)

    def test_off_without_off_program_disables_pump(self):
        data = dict(self.DATA, available_programs=["Manual_comfort"])
        entity = make_entity(climate.MygrenClimate, data)
        asyncio.run(entity.async_set_hvac_mode(HVACMode.OFF))
        entity._api.set_program.assert_not_awaited()
        entity._api.set_heatpump_enabled.assert_awaited_once_with(False)
        entity.coordinator.async_request_refresh.assert_awaited_once()

    def test_partial_failure_rolls_back_and_refreshes(self):
        entity = make_entity(climate.MygrenClimate, dict(self.DATA))
        entity._api.set_program.side_effect = MygrenConnectionError("x")
        with self.assertRaises(HomeAssistantError):
            asyncio.run(entity.async_set_hvac_mode(HVACMode.COOL))
        self.assertEqual(entity.hvac_mode, HVACMode.HEAT)
        entity.coordinator.async_request_refresh.assert_awaited_once()


class HotWater(unittest.TestCase):
    def setUp(self):
        data = {"tuv_set": 44, "tuv_setmin": 30, "tuv_setmax": 50, "tuv_enabled": 1}
        self.entity = make_entity(water_heater.MygrenWaterHeater, data)

    def test_step_is_one_degree(self):
        self.assertEqual(self.entity._attr_target_temperature_step, 1)

    def test_sends_whole_degrees(self):
        asyncio.run(self.entity.async_set_temperature(temperature=46.7))
        self.entity._api.set_tuv_temperature.assert_awaited_once_with(47)
        arg = self.entity._api.set_tuv_temperature.await_args.args[0]
        self.assertIsInstance(arg, int)

    def test_confirm_and_failure(self):
        asyncio.run(self.entity.async_set_temperature(temperature=46))
        poll(self.entity, dict(self.entity.coordinator.data, tuv_set=46))
        self.assertIsNone(self.entity._pending_target.value)
        self.entity._api.set_tuv_enabled.side_effect = MygrenConnectionError("x")
        with self.assertRaises(HomeAssistantError):
            asyncio.run(self.entity.async_set_operation_mode("off"))
        self.assertEqual(self.entity.current_operation, "auto")


class SwitchAndNumber(unittest.TestCase):
    def test_pending_off_is_shown_and_rolled_back(self):
        entity = make_entity(
            switch.MygrenSwitch, {"tuv_sched_enabled": 1}, switch.SWITCH_TYPES[0]
        )
        entity.async_write_ha_state = mock.MagicMock(
            side_effect=lambda: self.assertFalse(entity.is_on)
            if entity._pending.value is not None else None
        )
        entity._api.set_tuv_scheduler_enabled.side_effect = MygrenConnectionError("x")
        with self.assertRaises(HomeAssistantError):
            asyncio.run(entity.async_turn_off())
        self.assertTrue(entity.is_on)

    def test_number_rolls_back(self):
        entity = make_entity(number.MygrenNumber, {"curve": 3}, number.NUMBER_TYPES[0])
        entity._api.set_curve.side_effect = MygrenConnectionError("x")
        with self.assertRaises(HomeAssistantError):
            asyncio.run(entity.async_set_native_value(5))
        self.assertEqual(entity.native_value, 3.0)


class UnknownPrograms(unittest.TestCase):
    PROGRAMS = ["Off", "Ekviterm_comfort", "Manual_comfort", "Cooling_comfort"]

    def entity(self, **data):
        base = {"hp_enabled": 1, "available_programs": self.PROGRAMS}
        return make_entity(climate.MygrenClimate, {**base, **data})

    def test_known_programs_keep_their_modes(self):
        self.assertEqual(self.entity(program="Off").hvac_mode, HVACMode.OFF)
        self.assertEqual(self.entity(program="Manual_comfort").hvac_mode, HVACMode.HEAT)
        self.assertEqual(self.entity(program="Cooling_comfort").hvac_mode, HVACMode.COOL)

    def test_unknown_program_is_heating_and_warns_once(self):
        climate._warned_programs.clear()
        with self.assertLogs(climate._LOGGER, "WARNING") as logs:
            for _ in range(3):
                mode = self.entity(program="Mystery").hvac_mode
        self.assertEqual(mode, HVACMode.HEAT)
        self.assertEqual(len(logs.records), 1)

    def test_disabled_pump_is_off_whatever_the_program(self):
        entity = self.entity(program="Manual_comfort", hp_enabled=0)
        self.assertEqual(entity.hvac_mode, HVACMode.OFF)

    def test_missing_program_is_off(self):
        self.assertEqual(self.entity().hvac_mode, HVACMode.OFF)

    def test_current_mode_is_always_offered(self):
        entity = self.entity(program="Mystery", available_programs=["Off"])
        self.assertEqual(entity.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

    def test_mode_list_has_no_duplicates(self):
        entity = self.entity(program="Manual_comfort")
        self.assertEqual(
            entity.hvac_modes, [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        )

    def test_heat_prefers_manual_program(self):
        entity = self.entity(program="Off")
        asyncio.run(entity.async_set_hvac_mode(HVACMode.HEAT))
        entity._api.set_program.assert_awaited_once_with("Manual_comfort")

    def test_heat_uses_unknown_program_without_manual(self):
        entity = self.entity(program="Off", available_programs=["Off", "Ekviterm"])
        asyncio.run(entity.async_set_hvac_mode(HVACMode.HEAT))
        entity._api.set_program.assert_awaited_once_with("Ekviterm")

    def test_off_only_picks_the_off_program(self):
        entity = self.entity(program="Manual_comfort", available_programs=["", "Off"])
        asyncio.run(entity.async_set_hvac_mode(HVACMode.OFF))
        entity._api.set_program.assert_awaited_once_with("Off")


class RoomTemperature(unittest.TestCase):
    def test_uses_interior_sensor(self):
        entity = make_entity(climate.MygrenClimate, {"Tint": 21.4, "Tbuf": 38})
        self.assertEqual(entity.current_temperature, 21.4)

    def test_never_shows_buffer_as_room_temperature(self):
        for data in ({"Tint": 0, "Tbuf": 38}, {"Tbuf": 38}):
            entity = make_entity(climate.MygrenClimate, data)
            self.assertIsNone(entity.current_temperature)


class ManualTemperature(unittest.TestCase):
    DESC = next(d for d in number.NUMBER_TYPES if d.key == "manual")

    def entity(self, data):
        return make_entity(number.MygrenNumber, data, self.DESC)

    def test_uses_limits_from_pump(self):
        entity = self.entity({"manual": 30, "manual_setmin": 20, "manual_setmax": 45})
        self.assertEqual((entity.native_min_value, entity.native_max_value), (20, 45))

    def test_falls_back_to_defaults(self):
        entity = self.entity({"manual": 30})
        self.assertEqual((entity.native_min_value, entity.native_max_value), (15, 40))

    def test_zero_limit_from_pump_is_kept(self):
        entity = self.entity({"manual": 30, "manual_setmin": 0})
        self.assertEqual(entity.native_min_value, 0)

    def test_write_goes_to_manual_endpoint_only(self):
        entity = self.entity({"manual": 30})
        asyncio.run(entity.async_set_native_value(33))
        entity._api.set_manual_temperature.assert_awaited_once_with(33)
        entity._api.set_curve.assert_not_awaited()
        entity._api.set_shift.assert_not_awaited()

    def test_unavailable_when_pump_does_not_report_it(self):
        entity = self.entity({})
        self.assertIsNone(entity.native_value)

    @staticmethod
    def number_for(key, data):
        desc = next(d for d in number.NUMBER_TYPES if d.key == key)
        return make_entity(number.MygrenNumber, data, desc)

    def test_curve_and_shift_fall_back_to_defaults(self):
        curve = self.number_for("curve", {"curve": 3})
        self.assertEqual((curve.native_min_value, curve.native_max_value), (1, 9))
        shift = self.number_for("shift", {"shift": 0})
        self.assertEqual((shift.native_min_value, shift.native_max_value), (-5, 5))

    def test_curve_and_shift_use_limits_from_pump(self):
        curve = self.number_for(
            "curve", {"curve": 3, "curve_setmin": 2, "curve_setmax": 7}
        )
        self.assertEqual((curve.native_min_value, curve.native_max_value), (2, 7))
        shift = self.number_for(
            "shift", {"shift": 0, "shift_setmin": -3, "shift_setmax": 4}
        )
        self.assertEqual((shift.native_min_value, shift.native_max_value), (-3, 4))


class ZeroReadings(unittest.TestCase):
    @staticmethod
    def sensor_for(key, data):
        desc = next(d for d in sensor.SENSOR_TYPES if d.key == key)
        entity = sensor.MygrenSensor(make_coordinator(data), desc, ENTRY)
        return entity

    def test_buffer_and_interior_zero_is_unavailable(self):
        for key in ("Tbuf", "Tint", "TintAvg"):
            entity = self.sensor_for(key, {key: 0})
            self.assertIsNone(entity.native_value)
            self.assertFalse(entity.available)

    def test_buffer_and_interior_real_values_are_kept(self):
        for key in ("Tbuf", "Tint", "TintAvg"):
            entity = self.sensor_for(key, {key: 21.5})
            self.assertEqual(entity.native_value, 21.5)
            self.assertTrue(entity.available)

    def test_external_both_zero_is_unavailable(self):
        for key in ("Text", "TextAvg"):
            entity = self.sensor_for(key, {"Text": 0, "TextAvg": 0})
            self.assertFalse(entity.available)

    def test_external_missing_is_unavailable(self):
        self.assertFalse(self.sensor_for("Text", {}).available)

    def test_real_zero_outdoors_is_kept(self):
        entity = self.sensor_for("Text", {"Text": 0, "TextAvg": 1.4})
        self.assertEqual(entity.native_value, 0)
        self.assertTrue(entity.available)
        entity = self.sensor_for("TextAvg", {"Text": -0.4, "TextAvg": 0})
        self.assertEqual(entity.native_value, 0)
        self.assertTrue(entity.available)

    def test_freezing_outdoors_is_kept(self):
        entity = self.sensor_for("Text", {"Text": -7.2, "TextAvg": -6.1})
        self.assertEqual(entity.native_value, -7.2)

    def test_other_sensors_still_show_zero(self):
        entity = self.sensor_for("Tprimary_in", {"Tprimary_in": 0})
        self.assertEqual(entity.native_value, 0)
        self.assertTrue(entity.available)


class BinarySensors(unittest.TestCase):
    @staticmethod
    def sensor(key, data):
        desc = next(d for d in binary_sensor.BINARY_SENSOR_TYPES if d.key == key)
        return binary_sensor.MygrenBinarySensor(make_coordinator(data), desc, ENTRY)

    def test_missing_fault_is_unavailable(self):
        self.assertFalse(self.sensor("hp_failure", {}).available)

    def test_zero_is_available_and_off(self):
        entity = self.sensor("hp_failure", {"hp_failure": 0})
        self.assertTrue(entity.available)
        self.assertFalse(entity.is_on)

    def test_active_fault_is_on(self):
        self.assertTrue(self.sensor("hp_failure", {"hp_failure": 1}).is_on)

    def test_older_field_names_count_as_present(self):
        self.assertTrue(self.sensor("hp_forcedpause", {"hpforcedstop": 0}).available)
        self.assertTrue(self.sensor("tariff_installed", {"hdoinstalled": 1}).available)
        self.assertTrue(self.sensor("systemneedheat", {"heatneed": 0}).available)

    def test_failed_poll_is_unavailable(self):
        entity = self.sensor("hp_failure", {"hp_failure": 0})
        entity.coordinator.last_update_success = False
        self.assertFalse(entity.available)


if __name__ == "__main__":
    unittest.main(verbosity=1)
