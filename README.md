# Zwift RGB

`zwift_rgb` listens to trainer/Zwift power data, keeps the existing power smoothing, and
publishes telemetry to MQTT. Home Assistant is now responsible for FTP, percent FTP,
power zones, colors, light automations, and AI integrations.

Default flow:

```text
trainer/Zwift -> zwift_rgb -> MQTT -> Home Assistant -> lights/automation
```

Legacy Tuya output is still available with `output_mode: tuya_legacy` or together with
MQTT using `output_mode: both`.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
output_mode: mqtt
ble:
  prefer: cps
  address: null
  name_hint: "KICKR"
mqtt:
  host: localhost
  port: 1883
  username: null
  password: null
  client_id: zwift_rgb
  topic_prefix: zwift
  qos: 0
  retain: false
  publish_interval_ms: 500
```

Run:

```powershell
python -m app.main
```

Environment variables override `config.yaml`:

```powershell
$env:ZWIFT_OUTPUT_MODE = "mqtt"
$env:MQTT_HOST = "homeassistant.local"
$env:MQTT_PORT = "1883"
$env:MQTT_USERNAME = "mqtt-user"
$env:MQTT_PASSWORD = "mqtt-password"
$env:MQTT_TOPIC_PREFIX = "zwift"
python -m app.main
```

`MQTT_HOST` must be the MQTT broker host only. Do not use the Home Assistant UI URL
`http://homeassistant.local:8123`; use `MQTT_HOST=homeassistant.local` and
`MQTT_PORT=1883`.

## Output modes

- `mqtt`: publish telemetry only. Does not build or connect Tuya.
- `dry_run`: log telemetry only. No MQTT and no Tuya.
- `tuya_legacy`: old local Tuya color control path.
- `both`: publish MQTT telemetry and also run the legacy Tuya output.

## MQTT topics

With the default prefix `zwift`:

- `zwift/power`: smoothed power in watts.
- `zwift/power_raw`: raw trainer power in watts.
- `zwift/state`: `active`, `paused`, `stopped`, or `disconnected`.
- `zwift/telemetry`: JSON with `power`, `power_raw`, `state`, `trainer_connected`,
  `source`, and `timestamp`.

The MQTT telemetry payload intentionally does not include FTP, percent FTP, zone, or color.

## Home Assistant

See [docs/home-assistant-mqtt.md](docs/home-assistant-mqtt.md) for MQTT sensors,
template sensors using `sensor.garmin_connect_ftp_cycling`, and an example light automation.

## Legacy Tuya

Tuya configuration, FTP, color mapping, and transitions are only used by `tuya_legacy` and
`both`. They are ignored in `mqtt` and `dry_run`.
