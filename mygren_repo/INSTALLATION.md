# Installation Guide

## Prerequisites

- Home Assistant 2023.1.0 or newer
- Access to your Mygren heat pump's IP address
- Valid username and password for your heat pump

## Method 1: HACS Installation (Recommended)

### Step 1: Install HACS
If you haven't already, install HACS (Home Assistant Community Store) by following the [official HACS installation guide](https://hacs.xyz/docs/setup/download).

### Step 2: Add Custom Repository

1. Open Home Assistant
2. Navigate to **HACS** → **Integrations**
3. Click the **three dots** (⋮) in the top right corner
4. Select **Custom repositories**
5. Add the following:
   - **Repository**: `https://github.com/yourusername/mygren_heatpump`
   - **Category**: Integration
6. Click **Add**

### Step 3: Install the Integration

1. In HACS, search for "Mygren Heat Pump"
2. Click on the integration
3. Click **Download**
4. Restart Home Assistant

### Step 4: Configure the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Mygren Heat Pump"
4. Enter your configuration:
   ```
   Host: http://192.168.1.100  (replace with your heat pump's IP)
   Username: admin              (your heat pump username)
   Password: your_password      (your heat pump password)
   ```
5. Click **Submit**

## Method 2: Manual Installation

### Step 1: Download Files

Download the latest release or clone this repository:
```bash
git clone https://github.com/yourusername/mygren_heatpump.git
```

### Step 2: Copy Files

Copy the `mygren_heatpump` folder to your Home Assistant `custom_components` directory:

```bash
# If using Home Assistant OS or Supervised
cp -r mygren_heatpump /config/custom_components/

# If using Docker
docker cp mygren_heatpump homeassistant:/config/custom_components/
```

Your directory structure should look like:
```
config/
├── custom_components/
│   └── mygren_heatpump/
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── mygren_api.py
│       ├── config_flow.py
│       ├── sensor.py
│       ├── binary_sensor.py
│       ├── climate.py
│       ├── water_heater.py
│       ├── strings.json
│       └── translations/
│           └── en.json
```

### Step 3: Restart Home Assistant

Restart Home Assistant to load the new integration.

### Step 4: Add Integration

Follow Step 4 from Method 1 above.

## Finding Your Heat Pump IP Address

### Option 1: Check Your Router
1. Log into your router's admin interface
2. Look for connected devices
3. Find the device named "mygren-v3" or similar

### Option 2: Use Network Scanner
Use a network scanning tool like:
- Fing (mobile app)
- Advanced IP Scanner (Windows)
- Angry IP Scanner (cross-platform)

### Option 3: Check Heat Pump Display
Some Mygren heat pumps display the IP address on the built-in display panel.

## Default Credentials

The default username for Mygren heat pumps is typically:
- **Username**: `admin`
- **Password**: Check your heat pump documentation or installation manual

⚠️ **Security Note**: It's recommended to change the default password for security reasons.

## Verifying Installation

After installation, you should see:

1. **Device in Integrations**: Settings → Devices & Services → Mygren Heat Pump
2. **Climate Entity**: `climate.heating`
3. **Water Heater Entity**: `water_heater.hot_water`
4. **Multiple Sensors**: Various temperature and status sensors
5. **Binary Sensors**: Status indicators like compressor running, heating active, etc.

## Troubleshooting

### Integration Not Appearing
- Clear browser cache
- Restart Home Assistant again
- Check logs: Settings → System → Logs

### Cannot Connect Error
- Verify IP address is correct
- Ensure heat pump is on the same network
- Try accessing `http://YOUR_IP/api/` in a web browser
- Check firewall settings

### Authentication Failed
- Verify username and password
- Try default credentials if unsure
- Contact your installer for credentials

### Entities Not Updating
- Check if heat pump is online: `binary_sensor.online`
- Review Home Assistant logs for errors
- Verify network connectivity

### Missing Entities
- Some entities may not appear if the heat pump doesn't support that feature
- Check if the feature is enabled on your heat pump

## Getting Help

If you encounter issues:

1. **Check Logs**: Settings → System → Logs → Filter for "mygren"
2. **Enable Debug Logging**: Add to `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.mygren_heatpump: debug
   ```
3. **Create an Issue**: Include logs and configuration details
4. **Community Forum**: Post in Home Assistant Community forums

## Next Steps

After successful installation:

1. **Create Dashboards**: Add climate and water heater cards to your dashboard
2. **Set Up Automations**: Create automations based on temperature or status
3. **Monitor Energy**: Track compressor runtime and starts
4. **Configure Alerts**: Get notified of errors or unusual conditions

## Example Automation

```yaml
automation:
  - alias: "Hot Water Temperature Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.hot_water_temperature
        below: 35
    action:
      - service: notify.mobile_app
        data:
          message: "Hot water temperature is low: {{ states('sensor.hot_water_temperature') }}°C"
```

## Uninstallation

To remove the integration:

1. Go to **Settings** → **Devices & Services**
2. Find "Mygren Heat Pump"
3. Click the **three dots** (⋮)
4. Select **Delete**
5. (Optional) Remove files from `custom_components/mygren_heatpump/`
6. Restart Home Assistant
