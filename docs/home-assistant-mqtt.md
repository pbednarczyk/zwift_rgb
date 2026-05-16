# Home Assistant MQTT setup

`zwift_rgb` publishes trainer telemetry only. Home Assistant should calculate FTP percentage,
zones, colors, and light automations.

The app does not publish FTP, percent FTP, zone, or color fields.

## MQTT topics

With `MQTT_TOPIC_PREFIX=zwift`:

| Topic | Payload |
| --- | --- |
| `zwift/power` | Smoothed power in watts, for example `287` |
| `zwift/power_raw` | Raw trainer power in watts, for example `312` |
| `zwift/state` | `active`, `paused`, `stopped`, or `disconnected` |
| `zwift/telemetry` | JSON telemetry payload |

Telemetry JSON:

```json
{
  "power": 287,
  "power_raw": 312,
  "state": "active",
  "trainer_connected": true,
  "source": "zwift_rgb",
  "timestamp": "2026-05-16T20:15:30+02:00"
}
```

## MQTT sensors

```yaml
mqtt:
  sensor:
    - name: "Zwift Power"
      unique_id: zwift_power
      state_topic: "zwift/power"
      unit_of_measurement: "W"
      device_class: power
      state_class: measurement

    - name: "Zwift Power Raw"
      unique_id: zwift_power_raw
      state_topic: "zwift/power_raw"
      unit_of_measurement: "W"
      device_class: power
      state_class: measurement

    - name: "Zwift State"
      unique_id: zwift_state
      state_topic: "zwift/state"
```

## FTP percentage and zones in Home Assistant

This example uses Garmin Connect FTP from `sensor.garmin_connect_ftp_cycling`.

```yaml
template:
  - sensor:
      - name: "Zwift Percent FTP"
        unique_id: zwift_percent_ftp
        unit_of_measurement: "%"
        state: >
          {% set power = states('sensor.zwift_power') | float(0) %}
          {% set ftp = states('sensor.garmin_connect_ftp_cycling') | float(0) %}
          {% if ftp > 0 %}
            {{ ((power / ftp) * 100) | round(0) }}
          {% else %}
            0
          {% endif %}

      - name: "Zwift Power Zone"
        unique_id: zwift_power_zone
        state: >
          {% set pct = states('sensor.zwift_percent_ftp') | float(0) %}
          {% if pct <= 61 %}recovery
          {% elif pct <= 76 %}endurance
          {% elif pct <= 90 %}tempo
          {% elif pct <= 105 %}threshold
          {% elif pct <= 118 %}vo2max
          {% else %}anaerobic
          {% endif %}
```

## Example light automation

```yaml
automation:
  - alias: Zwift lights by power zone
    mode: restart
    trigger:
      - platform: state
        entity_id: sensor.zwift_power_zone
    action:
      - choose:
          - conditions: "{{ is_state('sensor.zwift_power_zone', 'recovery') }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.zwift_lights
                data:
                  rgb_color: [255, 255, 255]
          - conditions: "{{ is_state('sensor.zwift_power_zone', 'endurance') }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.zwift_lights
                data:
                  rgb_color: [0, 0, 255]
          - conditions: "{{ is_state('sensor.zwift_power_zone', 'tempo') }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.zwift_lights
                data:
                  rgb_color: [0, 255, 0]
          - conditions: "{{ is_state('sensor.zwift_power_zone', 'threshold') }}"
            sequence:
              - service: light.turn_on
                target:
                  entity_id: light.zwift_lights
                data:
                  rgb_color: [255, 255, 0]
        default:
          - service: light.turn_on
            target:
              entity_id: light.zwift_lights
            data:
              rgb_color: [255, 0, 0]
```

## Running zwift_rgb in MQTT mode

Environment variables override `config.yaml`:

`MQTT_HOST` is the MQTT broker host, not the Home Assistant web UI URL. Use
`homeassistant.local` or an IP address, with `MQTT_PORT=1883` for a normal Mosquitto broker.
Do not use `http://homeassistant.local:8123`.

```powershell
$env:ZWIFT_OUTPUT_MODE = "mqtt"
$env:MQTT_HOST = "homeassistant.local"
$env:MQTT_PORT = "1883"
$env:MQTT_USERNAME = "mqtt-user"
$env:MQTT_PASSWORD = "mqtt-password"
$env:MQTT_TOPIC_PREFIX = "zwift"
python -m app.main
```
