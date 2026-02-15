# Mygren Heat Pump Integration for Home Assistant

Custom Home Assistant integration for **Mygren geo-thermal heat pumps** running **MaR firmware v4+**.

> **Breaking change in v2.0:** This release drops support for MaR v3 (integer-based programs).
> If your heat pump still runs MaR v3 firmware, use the [v1.x release].

## About

[Mygren](https://www.mygren.eu/) is a monitoring and control system (MaR — Meranie a Regulácia) developed by **AI Trade s.r.o.** for ground-source (geothermal) heat pumps. The **SMARTHUB S06** controller runs on an embedded Linux board and exposes a local REST API over HTTPS, providing full read/write access to the heat pump's operating parameters.

This integration connects Home Assistant to your Mygren heat pump over your **local network** — no cloud, no internet dependency. It polls the `/api/telemetry` endpoint for all runtime data and uses authenticated PUT requests to change settings.

**Supported hardware:**
- Mygren SMARTHUB S06 controller
- Ground-source (water/water or brine/water) heat pumps managed by Mygren MaR v4.x firmware
- Installations with or without buffer tank, hot water (TÚV) boiler, radiator circuit, and tariff relay

## Features

* **Climate Control** — HVAC modes derived dynamically from the API `available_programs` list; no hardcoded presets
* **Water Heater** — Control hot water (TUV) temperature and enable/disable
* **Temperature Sensors** — All system temperatures (primary, secondary, system, buffer, external, interior, discharge)
* **Binary Sensors** — Compressor, pumps, valves, heating/cooling, failures, tariff
* **Number Controls** — Heating curve (1–9) and curve shift (−5 to +5)
* **Switches** — Hot water scheduler, program scheduler, tariff watching
* **Diagnostic Sensors** — Software versions, runtimes (formatted as d/h/m/s), start counts, system load, error counters, circulation pump states, three-way valve positions
* **Optimistic Updates** — UI reflects changes immediately when you adjust temperature, mode, or switches — no waiting for the next poll cycle
* **Device Info** — "Visit" link to the heat pump's service desk web interface

## Requirements

* Mygren heat pump with **MaR v4.x** firmware (string-based program names)
* Heat pump accessible over the local network (HTTPS)

## Installation

### HACS (Recommended)

1. Open HACS → Integrations
2. ⋮ → Custom repositories → add this repo URL as **Integration**
3. Install **Mygren Heat Pump**
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/mygren_heatpump` directory into your HA `custom_components/`
2. Restart Home Assistant

## Configuration

1. **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Mygren Heat Pump**
3. Enter connection details:
   | Field | Description |
   |---|---|
   | Host | IP or hostname, e.g. `https://192.168.1.100` |
   | Username | Default: `admin` |
   | Password | Your heat pump password |
   | Verify SSL | Uncheck for self-signed certs (most installs) |

## Removing the Integration

1. Go to **Settings → Devices & Services**
2. Find the **Mygren S06 Heat Pump** integration card
3. Click the three-dot menu (⋮) and select **Delete**
4. Confirm the deletion
5. Restart Home Assistant (recommended)

This removes all entities, devices, and stored credentials associated with the integration. Your heat pump continues to operate normally on its own — the integration is read/write but the heat pump does not depend on Home Assistant.

## How Data is Updated

The integration polls the heat pump's `/api/telemetry` endpoint every **30 seconds** over HTTPS on your local network. This single API call returns all runtime variables — temperatures, states, counters, versions — in one JSON response.

When you make changes through the HA UI (temperature, mode, switches), the integration sends a PUT request to the relevant API endpoint and immediately updates the entity state **optimistically** — you see the change in the UI within milliseconds. The next poll cycle then confirms the actual device state.

## Climate Entity

The climate entity (`climate.heating`) maps the MaR v4 **`available_programs`** to HVAC modes at runtime — no configuration needed.

### HVAC Mode Mapping

| API Program | HVAC Mode | Description |
|---|---|---|
| `"Off"` | **Off** | Heating/cooling circuit off; buffer held at minimum |
| `"Manual_comfort"` | **Heat** | Heating with interior thermostat; comfort set-point controls room temperature |
| `"Cooling_comfort"` | **Cool** | Cooling with interior thermostat; output fixed at 19 °C |

Only modes whose programs are present in `available_programs` are shown — the list adapts automatically to each installation.

### Temperature Control

The target temperature on the climate card is the **comfort (room) set-point** — the desired interior temperature. Both `Manual_comfort` and `Cooling_comfort` use the interior sensor thermostat to turn the circuit on/off relative to this value.

The **system output temperature** (`manual`) is a separate advanced setting exposed via the *Number* entity `number.heating_curve` and can also be adjusted through the manual temperature number entity.

### No Presets

This version intentionally **does not expose preset modes** (Comfort / Eco). Program selection is done entirely through the HVAC mode picker.

## Available Entities

### Climate

* `climate.heating` — Main heating/cooling control (modes: Off, Heat, Cool)

### Water Heater

* `water_heater.hot_water` — Hot water (TÚV) temperature and on/off

### Number Controls

* `number.heating_curve` — Ekvithermal curve selection (1–9)
* `number.curve_shift` — Curve shift adjustment (−5 to +5)

### Switches

* `switch.hot_water_scheduler` — Enable/disable hot water schedule
* `switch.program_scheduler` — Enable/disable program schedule
* `switch.tariff_watching` — Enable/disable tariff monitoring

### Temperature Sensors

| Entity | Telemetry key |
|---|---|
| Primary In/Out | `Tprimary_in`, `Tprimary_out` |
| Secondary In/Out | `Tsecondary_in`, `Tsecondary_out` |
| System In/Out | `Tsystem_in`, `Tsystem_out` |
| Interior / Avg | `Tint`, `TintAvg` |
| Hot Water | `Ttuv` |
| Buffer | `Tbuf` |
| External / Avg | `Text`, `TextAvg` |
| Discharge | `Tdischarge` |
| Ekvithermal | `Tekviterm` |

### Binary Sensors

**Operational:** Online, Compressor, Heat Pump Running, Heating Active, Cooling Active, HP Enabled, Hot Water Enabled, Hot Water Needs Heat, Buffer Needs Heat, Heat Needed, System Needs Heat, System Needs Cooling, Tariff Installed.

**Errors (diagnostic):** Power Error, Heat Pump Failure, High Secondary In.

**Control state (diagnostic):** HP Can Start, HP Can Stop, HP Forced Pause, Primary Forced Run, HW Thermostat 1, SW Thermostat 1, Program Scheduler Active, Hot Water Scheduler Active, Radiator Installed.

**Circulation pumps (diagnostic):** Primary, Pre-Primary, Secondary, System, TUV, Radiator.

**Valves (diagnostic):** Three-Way Valve Secondary 01/02, Three-Way Valve Cooling, Mixing Valve Up/Down.

### Status & Diagnostic Sensors

**Operational:** Control State, Program Mode, System Destination Temp, Heating Curve, Curve Shift, Comfort Temperature, Manual Temperature, Hot Water Target Temperature, Hot Water Gradient, Buffer Gradient, Tariff State, Phases.

**Runtimes & counters (diagnostic):** System Runtime (raw seconds + formatted d/h/m/s), System Uptime (raw + formatted), System Start Count, System Start Time, Compressor Runtime (raw + formatted), Compressor Start Count, Compressor Start Time, Compressor Stop Time, Sensor Error Count, System Load.

**Software versions (diagnostic):** Display Version, Hostname, OS Version, Binaries Version, MaR Version, OWM Version, CM Version.

**Limits (diagnostic):** Buffer Min/Max Temperature, Hot Water Hysteresis Min/Max.

> Entities marked *(diagnostic)* appear under the "Diagnostic" section on the device page in HA. They are not shown on the default dashboard but can be added manually.

## API Endpoints Used

### Authentication & Info

| Endpoint | Methods | Description |
|---|---|---|
| `/api/login` | POST | JWT token generation |
| `/api/resources` | GET | List all available endpoints |

### Monitoring

| Endpoint | Methods | Description |
|---|---|---|
| `/api/telemetry` | GET | All runtime variables (includes `available_programs`) |
| `/api/daemonlog` | GET | System messages log |
| `/api/runlog` | GET | Periodic variable log |

### Hot Water (TÚV)

| Endpoint | Methods | Description |
|---|---|---|
| `/api/tuv` | GET | Hot water variable collection |
| `/api/tuv/set` | GET, PUT | Target temperature |
| `/api/tuv/enabled` | GET, PUT | Enable/disable |
| `/api/tuv/scheduler/enabled` | GET, PUT | Scheduler on/off |
| `/api/tuv/scheduler/[id]` | GET, PUT, POST, DELETE | Schedule entries |

### Program Control

| Endpoint | Methods | Description |
|---|---|---|
| `/api/program` | GET | Program variable collection |
| `/api/program/program` | GET, PUT | Active program (string) |
| `/api/program/curve` | GET, PUT | Ekvithermal curve (1–9) |
| `/api/program/shift` | GET, PUT | Curve shift (−5 to +5) |
| `/api/program/manual` | GET, PUT | System output temperature |
| `/api/program/comfort` | GET, PUT | Interior target temperature |
| `/api/program/scheduler/enabled` | GET, PUT | Program scheduler on/off |
| `/api/program/scheduler/[id]` | GET, PUT, POST, DELETE | Schedule entries |

### Heat Pump Control

| Endpoint | Methods | Description |
|---|---|---|
| `/api/heatpump` | GET | Heat pump info collection |
| `/api/heatpump/enabled` | GET, PUT | Enable/disable heat pump |
| `/api/heatpump/tariff` | GET | Current tariff state |
| `/api/heatpump/tariff/watch` | GET, PUT | Tariff watching on/off |

## Troubleshooting

**Cannot Connect** — Verify the host includes `https://` (the heat pump only serves HTTPS). Check that HA can reach the heat pump on your network. Most Mygren installations use self-signed certificates — make sure *Verify SSL* is unchecked.

**Invalid Authentication** — Verify username and password. The default username is `admin`. If you changed the password on the heat pump's service desk, use the new one.

**Entities show "Unavailable"** — The heat pump may be offline, in maintenance mode, or unreachable. Check HA logs (`Logger: custom_components.mygren_heatpump`) for specific error messages. API status code `503` means the MaR control loop is not running (starting up, in service mode, or crashed) — see the MaR system codes documentation for details.

**"Unknown program" warnings in logs** — Your firmware may have program names not yet mapped to HVAC modes. Open a GitHub issue with your `available_programs` list from the telemetry response.

**SSL errors** — If you see `aiohttp.ClientSSLError`, the heat pump's certificate is self-signed (normal). Uncheck *Verify SSL* in the integration configuration. If you previously had it checked, you'll need to remove and re-add the integration.

## Known Limitations

- **MaR v3 not supported** — v2.x only works with MaR v4+ firmware (string-based program names). For v3 (integer programs), use the v1.x release.
- **Single device per entry** — each config entry connects to one heat pump. For multiple heat pumps, add the integration multiple times.
- **Scheduler management not implemented** — the TUV and program scheduler entries (`/scheduler/[id]` endpoints) are not yet exposed. Schedulers can be enabled/disabled via switches, but individual schedule entries must be managed through the heat pump's service desk.
- **No auto-discovery** — the heat pump must be configured manually with its IP/hostname.
- **Polling only** — the heat pump API does not support push notifications or WebSockets. Data is refreshed every 30 seconds.
- **External/buffer temperatures** — some installations may report `0` for `Text`, `TextAvg`, or `Tbuf` if the corresponding sensors are not physically installed. These entities will show as "Unavailable".

## Automation Examples

### Notify when compressor starts

```yaml
automation:
  - alias: "Notify on compressor start"
    trigger:
      - platform: state
        entity_id: binary_sensor.aus_porazik_hainburg_compressor
        from: "off"
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Heat Pump"
          message: "Compressor started"
```

### Lower hot water temperature at night

```yaml
automation:
  - alias: "TUV night setback"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.aus_porazik_hainburg_hot_water
        data:
          temperature: 38

  - alias: "TUV morning recovery"
    trigger:
      - platform: time
        at: "05:00:00"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.aus_porazik_hainburg_hot_water
        data:
          temperature: 43
```

### Alert on heat pump failure

```yaml
automation:
  - alias: "Heat pump failure alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.aus_porazik_hainburg_heat_pump_failure
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Heat Pump Failure"
          message: "Heat pump has reported a failure — check the service desk."
```

## Upgrading from v2.0.3 to v2.2.0

v2.2.0 is a non-breaking upgrade from v2.0.3. All existing entity IDs, automations, and scripts continue to work. Here's what changes:

**Entity display names change** — v2.2.0 adds `has_entity_name` to all entity platforms. HA will now show entity names as `{device name} {entity name}` (e.g. "aus-porazik-hainburg Primary In Temperature" instead of just "Primary In Temperature"). Your `entity_id` strings stay the same — only the friendly name displayed in the UI changes. If you've customized entity names through the UI, your customizations take priority and are not affected.

**~30 new entities appear** — New diagnostic entities are added for circulation pumps, valves, software versions, runtimes, timestamps, limits, and more. Most of these are **disabled by default** — they're registered in HA but don't generate state updates or appear in dashboards until you manually enable them. To enable: go to the device page → click on the disabled entity → toggle "Enable".

Entities enabled by default in v2.2.0 that were not present in v2.0.3: `hp_failure`, `high_secondary_in`, `pw_error` (error alerts), `heatneed`, `cruntime`, `cstartcnt`.

**Optimistic updates** — Temperature, mode, and switch changes now reflect in the UI immediately instead of waiting for the next 30-second poll. No configuration needed — this is automatic.

**Upgrade steps:**

1. Install v2.2.0 via HACS (or copy the files manually)
2. Restart Home Assistant
3. Check your device page — new entities appear under "Diagnostic"
4. Optionally enable any disabled entities you want to track
5. No changes needed to existing automations or scripts

## Upgrading from v1.x to v2.x

v2.0 removes MaR v3 support and the Comfort/Eco preset modes. After upgrading:

1. Restart Home Assistant
2. Any automations using `preset_mode` service calls should be migrated to use `hvac_mode` instead
3. The climate card will no longer show the preset dropdown

## License

MIT

## Disclaimer

Unofficial integration — not affiliated with or endorsed by Mygren / AI Trade s.r.o. Use at your own risk.
