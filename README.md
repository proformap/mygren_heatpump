# Mygren Heat Pump Integration for Home Assistant

Custom integration for Mygren S06 heat pumps, allowing monitoring and control through Home Assistant.

## Features

- **Climate Control**: Control heating temperature and monitor heating status
- **Water Heater**: Control hot water (TUV) temperature
- **Temperature Sensors**: Monitor all system temperatures (primary, secondary, buffer, external, etc.)
- **Binary Sensors**: Track compressor status, heat pump running state, heating/cooling activity
- **Status Monitoring**: View system state, runtime statistics, and error conditions

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `mygren_heatpump` directory to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Mygren Heat Pump"
4. Enter your heat pump connection details:
   - **Host**: The IP address or hostname of your heat pump (e.g., `http://192.168.1.100`)
   - **Username**: Your heat pump username (default: `admin`)
   - **Password**: Your heat pump password

## Available Entities

### Climate
- `climate.heating` - Main heating control with AUTO, HEAT, and OFF modes
  - AUTO mode: Ekvithermal curve-based control
  - HEAT mode: Manual temperature control
  - Preset modes: Comfort and Eco

### Water Heater
- `water_heater.hot_water` - Hot water (TUV) control
  - Set temperature (30-50°C)
  - Enable/disable operation

### Number Controls
- `number.heating_curve` - Heating curve selection (1-9)
- `number.curve_shift` - Curve shift adjustment (-5 to +5)

### Switches
- `switch.hot_water_scheduler` - Enable/disable hot water schedule
- `switch.tariff_watching` - Enable/disable tariff monitoring

### Temperature Sensors
- Primary In/Out Temperature
- Secondary In/Out Temperature
- Heating In/Out Temperature
- Hot Water Temperature
- Buffer Temperature
- External Temperature (current and average)
- Discharge Temperature
- Ekvithermal Temperature

### Binary Sensors
- Online Status
- Compressor Running
- Heat Pump Running
- Heating Active
- Cooling Active
- Heat Pump Enabled
- Hot Water Enabled
- Hot Water Needs Heat
- Buffer Needs Heat
- Power Error
- And more...

### Status Sensors
- Control State
- Compressor Runtime
- Compressor Start Count
- System Runtime
- Heating Curve
- Heating Curve Shift
- Program Mode

## API Endpoints Used

This integration uses the following Mygren API endpoints:

**Authentication & Info:**
- `/api/login` - Authentication (POST)
- `/api/resources` - List available endpoints (GET)

**Monitoring:**
- `/api/telemetry` - Read all runtime variables (GET)
- `/api/daemonlog` - System messages log (GET)
- `/api/runlog` - System run log (GET)

**Hot Water (TUV) Control:**
- `/api/tuv` - Read hot water variables (GET)
- `/api/tuv/set` - Set hot water temperature (GET, PUT)
- `/api/tuv/enabled` - Enable/disable hot water heating (GET, PUT)
- `/api/tuv/scheduler/enabled` - Enable/disable hot water scheduler (GET, PUT)
- `/api/tuv/scheduler/[id]` - Manage hot water schedules (GET, PUT, POST, DELETE)

**Program Control:**
- `/api/program` - Collection of program variables (GET)
- `/api/program/program` - Selected program (GET, PUT)
- `/api/program/curve` - Ekvithermal curve number (GET, PUT)
- `/api/program/shift` - Curve shift value (GET, PUT)
- `/api/program/manual` - Manual program temperature (GET, PUT)
- `/api/program/comfort` - Comfort temperature (GET, PUT)
- `/api/program/scheduler/enabled` - Enable/disable program scheduler (GET, PUT)
- `/api/program/scheduler/[id]` - Manage program schedules (GET, PUT, POST, DELETE)

**Heat Pump Control:**
- `/api/heatpump` - Collection of heat pump info (GET)
- `/api/heatpump/enabled` - Enable/disable heat pump (GET, PUT)
- `/api/heatpump/tariff` - Actual tariff state (GET)
- `/api/heatpump/tariff/watch` - Watch tariff ON/OFF (GET, PUT)

## Operating Modes

The integration supports three heating modes:

1. **OFF** - Heat pump disabled
2. **AUTO** - Ekvithermal curve-based control (Eco preset)
   - Temperature automatically adjusted based on external temperature
   - Uses heating curve (1-9) and shift (-5 to +5) settings
3. **HEAT** - Manual temperature control (Comfort preset)
   - Fixed temperature setpoint

### Presets
- **Eco** - Automatic ekvithermal control (Program 1)
- **Comfort** - Manual temperature control (Program 2)

## Features Implemented

✅ **Full Climate Control** - Set mode (Auto/Heat/Off), temperature, and presets  
✅ **Water Heater Control** - Temperature and enable/disable  
✅ **Heating Curve Adjustment** - Change curve and shift values  
✅ **Scheduler Control** - Enable/disable hot water scheduler  
✅ **Tariff Management** - Enable/disable tariff watching  
✅ **Complete Monitoring** - All temperatures and status sensors  
✅ **Real-time Updates** - 30-second polling interval

## Troubleshooting

### Cannot Connect
- Verify the host address is correct and includes `http://` or `https://`
- Ensure your heat pump is accessible on your network
- Check firewall settings

### Invalid Authentication
- Verify username and password are correct
- The default username is typically `admin`

### Entities Not Updating
- Check if the heat pump is online
- Verify network connectivity
- Check Home Assistant logs for errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## API Documentation

The Mygren heat pump uses a REST API with JWT authentication. Key features:

- **Authentication**: JWT tokens via `/api/login`
- **Data Format**: JSON
- **Update Interval**: 30 seconds (configurable)
- **Local Access**: Integration communicates directly with the heat pump

## License

This project is licensed under the MIT License.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Mygren. Use at your own risk.

## Support

For issues and feature requests, please use the GitHub issue tracker.
