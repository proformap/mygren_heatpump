# Example Configurations and Automations

This file contains example configurations and automations you can use with the Mygren Heat Pump integration.

## Dashboard Cards

### Climate Control Card

```yaml
type: thermostat
entity: climate.heating
name: Heating Control
```

### Water Heater Card

```yaml
type: thermostat
entity: water_heater.hot_water
name: Hot Water
```

### Temperature Overview Card

```yaml
type: entities
title: Temperature Overview
entities:
  - entity: sensor.external_temperature
    name: Outside
  - entity: sensor.buffer_temperature
    name: Buffer
  - entity: sensor.hot_water_temperature
    name: Hot Water
  - entity: sensor.heating_in_temperature
    name: Heating In
  - entity: sensor.heating_out_temperature
    name: Heating Out
```

### System Status Card

```yaml
type: entities
title: Heat Pump Status
entities:
  - entity: binary_sensor.online
    name: Online
  - entity: binary_sensor.heat_pump_running
    name: Running
  - entity: binary_sensor.compressor
    name: Compressor
  - entity: binary_sensor.heating_active
    name: Heating
  - entity: binary_sensor.cooling_active
    name: Cooling
  - entity: sensor.control_state
    name: State
```

### Detailed Information Card

```yaml
type: entities
title: Heat Pump Details
entities:
  - entity: sensor.compressor_runtime
    name: Runtime
  - entity: sensor.compressor_start_count
    name: Start Count
  - entity: sensor.heating_curve
    name: Heating Curve
  - entity: sensor.heating_curve_shift
    name: Curve Shift
  - entity: binary_sensor.power_error
    name: Power Error
```

### Temperature History Graph

```yaml
type: history-graph
title: Temperature History
entities:
  - entity: sensor.external_temperature
    name: Outside
  - entity: sensor.buffer_temperature
    name: Buffer
  - entity: sensor.hot_water_temperature
    name: Hot Water
hours_to_show: 24
refresh_interval: 0
```

## Automations

### Low Hot Water Temperature Alert

```yaml
automation:
  - alias: "Low Hot Water Temperature Alert"
    description: "Notify when hot water temperature drops below threshold"
    trigger:
      - platform: numeric_state
        entity_id: sensor.hot_water_temperature
        below: 35
        for:
          minutes: 10
    condition:
      - condition: state
        entity_id: binary_sensor.hot_water_enabled
        state: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Low Hot Water Temperature"
          message: "Hot water is at {{ states('sensor.hot_water_temperature') }}°C"

### Heat Pump Error Notification

```yaml
automation:
  - alias: "Heat Pump Error Alert"
    description: "Notify when heat pump encounters an error"
    trigger:
      - platform: state
        entity_id: binary_sensor.power_error
        to: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Heat Pump Error"
          message: "Power error detected on heat pump"
          data:
            priority: high
            ttl: 0
```

### Nighttime Hot Water Heating

```yaml
automation:
  - alias: "Nighttime Hot Water Boost"
    description: "Increase hot water temperature at night for morning use"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: 48

  - alias: "Daytime Hot Water Economy"
    description: "Reduce hot water temperature during the day"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: 42
```

### Vacation Mode

```yaml
automation:
  - alias: "Heat Pump Vacation Mode"
    description: "Reduce temperatures when vacation mode is active"
    trigger:
      - platform: state
        entity_id: input_boolean.vacation_mode
        to: "on"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating
        data:
          temperature: 18
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: 35

  - alias: "Heat Pump Return from Vacation"
    description: "Restore normal temperatures when returning"
    trigger:
      - platform: state
        entity_id: input_boolean.vacation_mode
        to: "off"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating
        data:
          temperature: 22
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: 45
```

### Cold Weather Protection

```yaml
automation:
  - alias: "Freeze Protection"
    description: "Increase heating when external temperature drops significantly"
    trigger:
      - platform: numeric_state
        entity_id: sensor.external_temperature
        below: -5
    condition:
      - condition: state
        entity_id: binary_sensor.heat_pump_enabled
        state: "on"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating
        data:
          temperature: 24
      - service: notify.mobile_app_your_phone
        data:
          message: "Freeze protection activated. Temperature: {{ states('sensor.external_temperature') }}°C"
```

### Compressor Excessive Starts Alert

```yaml
automation:
  - alias: "Excessive Compressor Starts Alert"
    description: "Alert if compressor starts too frequently"
    trigger:
      - platform: state
        entity_id: sensor.compressor_start_count
    condition:
      - condition: template
        value_template: >
          {{ (states('sensor.compressor_start_count') | int - 
              state_attr('automation.excessive_compressor_starts_alert', 'last_triggered_count') | default(0) | int) > 10 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Excessive Compressor Starts"
          message: "Compressor has started {{ states('sensor.compressor_start_count') }} times. Check system."
```

### Daily Status Report

```yaml
automation:
  - alias: "Daily Heat Pump Report"
    description: "Send daily summary of heat pump performance"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Heat Pump Daily Report"
          message: |
            Status: {{ states('sensor.control_state') }}
            Compressor Runtime: {{ states('sensor.compressor_runtime') }}s
            Starts Today: {{ states('sensor.compressor_start_count') }}
            Buffer Temp: {{ states('sensor.buffer_temperature') }}°C
            Hot Water: {{ states('sensor.hot_water_temperature') }}°C
            Outside: {{ states('sensor.external_temperature') }}°C
```

## Input Helpers

Create these input helpers for use with automations:

```yaml
input_boolean:
  vacation_mode:
    name: Vacation Mode
    icon: mdi:airplane

input_number:
  heat_pump_eco_temperature:
    name: Economy Temperature
    min: 15
    max: 25
    step: 0.5
    unit_of_measurement: "°C"
    icon: mdi:thermometer

  heat_pump_comfort_temperature:
    name: Comfort Temperature
    min: 18
    max: 28
    step: 0.5
    unit_of_measurement: "°C"
    icon: mdi:thermometer
```

## Template Sensors

### Coefficient of Performance (COP) Estimate

```yaml
template:
  - sensor:
      - name: "Heat Pump COP Estimate"
        unit_of_measurement: ""
        state: >
          {% set temp_out = states('sensor.secondary_out_temperature') | float %}
          {% set temp_in = states('sensor.secondary_in_temperature') | float %}
          {% set temp_ext = states('sensor.external_temperature') | float %}
          {% if temp_out > temp_in and temp_ext != 0 %}
            {{ ((temp_out - temp_in) / (temp_out - temp_ext) * 10) | round(2) }}
          {% else %}
            0
          {% endif %}
```

### Heat Pump Efficiency Status

```yaml
template:
  - binary_sensor:
      - name: "Heat Pump Running Efficiently"
        state: >
          {{ states('sensor.heat_pump_cop_estimate') | float > 3.0 }}
        icon: >
          {% if is_state('binary_sensor.heat_pump_running_efficiently', 'on') %}
            mdi:check-circle
          {% else %}
            mdi:alert-circle
          {% endif %}
```

### Heating Demand

```yaml
template:
  - sensor:
      - name: "Heating Demand"
        unit_of_measurement: "%"
        state: >
          {% set current = states('sensor.buffer_temperature') | float %}
          {% set target = states('climate.heating') | float %}
          {% set diff = target - current %}
          {% if diff > 0 %}
            {{ (diff / target * 100) | round(0) }}
          {% else %}
            0
          {% endif %}
```

## Scripts

### Quick Temperature Boost

```yaml
script:
  heat_pump_boost:
    alias: "Heat Pump Temperature Boost"
    sequence:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating
        data:
          temperature: "{{ states('climate.heating') | float + 2 }}"
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: "{{ states('water_heater.hot_water') | float + 3 }}"
      - delay:
          hours: 2
      - service: climate.set_temperature
        target:
          entity_id: climate.heating
        data:
          temperature: "{{ states('input_number.heat_pump_comfort_temperature') }}"
      - service: water_heater.set_temperature
        target:
          entity_id: water_heater.hot_water
        data:
          temperature: 45
```

## Lovelace Dashboard Example

Complete dashboard configuration:

```yaml
title: Heat Pump Control
views:
  - title: Overview
    cards:
      - type: vertical-stack
        cards:
          - type: thermostat
            entity: climate.heating
          - type: thermostat
            entity: water_heater.hot_water

      - type: entities
        title: Current Status
        entities:
          - entity: binary_sensor.online
          - entity: binary_sensor.heat_pump_running
          - entity: binary_sensor.compressor
          - entity: sensor.control_state

      - type: history-graph
        entities:
          - sensor.external_temperature
          - sensor.buffer_temperature
          - sensor.hot_water_temperature
        hours_to_show: 24

  - title: Detailed
    cards:
      - type: entities
        title: Temperatures
        entities:
          - sensor.primary_in_temperature
          - sensor.primary_out_temperature
          - sensor.secondary_in_temperature
          - sensor.secondary_out_temperature
          - sensor.heating_in_temperature
          - sensor.heating_out_temperature

      - type: entities
        title: Statistics
        entities:
          - sensor.compressor_runtime
          - sensor.compressor_start_count
          - sensor.system_runtime
          - sensor.heating_curve
          - sensor.heating_curve_shift
```

## Note

Remember to replace `mobile_app_your_phone` with your actual notify service name.
You can find your notify services by going to Developer Tools → Services and searching for "notify".
