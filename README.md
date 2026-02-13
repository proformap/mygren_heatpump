# Mygren Heat Pump Integration for Home Assistant

Custom Home Assistant integration for **Mygren geo-thermal heat pumps** running **MaR firmware v4+**.

> **Breaking change in v2.0:** This release drops support for MaR v3 (integer-based programs).
> If your heat pump still runs MaR v3 firmware, use the [v1.x release](https://github.com/proformap/mygren_heatpump/releases/tag/v.1.1.1).

## Features

* **Climate Control** — HVAC modes derived dynamically from the API `available_programs` list; no hardcoded presets
* **Water Heater** — Control hot water (TÚV) temperature and enable/disable
* **Temperature Sensors** — All system temperatures (primary, secondary, system, buffer, external, interior, discharge)
* **Binary Sensors** — Compressor status, heat pump running, heating/cooling, failures, tariff
* **Number Controls** — Heating curve (1–9) and curve shift (−5 to +5)
* **Switches** — Hot water scheduler, program scheduler, tariff watching
* **Status Monitoring** — Program mode, compressor runtime & starts, system state

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

Online, Compressor, Heat Pump Running, Heating Active, Cooling Active, HP Enabled, Hot Water Enabled, Hot Water Needs Heat, Buffer Needs Heat, Power Error, HP Can Start, HP Failure, HP Forced Pause, Tariff Installed, System Needs Heat, System Needs Cooling.

### Status Sensors

Control State, Program Mode, System Destination Temp, Compressor Runtime, Compressor Start Count, System Runtime, Heating Curve, Curve Shift, Comfort Temperature, Manual Temperature.

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

**Cannot Connect** — Verify host includes `https://`, check network, check firewall. Most installs use self-signed certs — uncheck *Verify SSL*.

**Invalid Authentication** — Verify username/password. Default user is `admin`.

**Entities Not Updating** — Check heat pump is online, check HA logs for errors.

**"Unknown program" warnings** — Your firmware may have programs not yet mapped. Open an issue with your `available_programs` list.

## Upgrading from v1.x

v2.0 removes MaR v3 support and the Comfort/Eco preset modes. After upgrading:

1. Restart Home Assistant
2. Any automations using `preset_mode` service calls should be migrated to use `hvac_mode` instead
3. The climate card will no longer show the preset dropdown

## License

MIT

## Disclaimer

Unofficial integration — not affiliated with or endorsed by Mygren / AI Trade s.r.o. Use at your own risk.
