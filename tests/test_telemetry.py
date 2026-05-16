import asyncio
import json
import os
import unittest
from pathlib import Path

from rgbapp.application.telemetry import Telemetry, TelemetryProcessor
from rgbapp.application.use_cases import StreamPowerToTelemetryUseCase
from rgbapp.config.factory import load_app_config
from rgbapp.config.models import MqttConfig
from rgbapp.infrastructure.mqtt import MqttOutputAdapter


class FixedSmoother:
    def __init__(self, value):
        self.value = value
        self.inputs = []

    def add(self, watts):
        self.inputs.append(watts)
        return self.value


class FakeMqttClient:
    def __init__(self):
        self.published = []
        self.username = None
        self.on_connect = None
        self.on_disconnect = None
        self.started = False

    def username_pw_set(self, username, password=None):
        self.username = (username, password)

    def reconnect_delay_set(self, min_delay, max_delay):
        self.reconnect_delay = (min_delay, max_delay)

    def connect_async(self, host, port, keepalive=30):
        self.connection = (host, port, keepalive)

    def loop_start(self):
        self.started = True

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, payload, qos, retain))

        class Result:
            rc = 0

        return Result()

    def loop_stop(self):
        self.started = False

    def disconnect(self):
        self.disconnected = True


class FakeSource:
    def __init__(self, values):
        self.values = values

    async def stream(self):
        for value in self.values:
            yield value


class FakeOutput:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.telemetry = []
        self.states = []

    async def start(self):
        self.started = True

    async def publish(self, telemetry):
        self.telemetry.append(telemetry)

    async def publish_state(self, state, trainer_connected):
        self.states.append((state, trainer_connected))

    async def stop(self):
        self.stopped = True


class FakeClock:
    async def sleep_ms(self, ms):
        await asyncio.sleep(0)


class TelemetryTests(unittest.TestCase):
    def test_payload_does_not_include_ftp_zone_or_color(self):
        telemetry = Telemetry(
            power=287,
            power_raw=312,
            state="active",
            trainer_connected=True,
            source="zwift_rgb",
            timestamp="2026-05-16T20:15:30+02:00",
        )

        payload = telemetry.to_payload()

        self.assertEqual(payload["power"], 287)
        self.assertEqual(payload["power_raw"], 312)
        for forbidden in ("ftp", "percent_ftp", "zone", "color_hex"):
            self.assertNotIn(forbidden, payload)

    def test_processor_maps_raw_and_smoothed_power(self):
        smoother = FixedSmoother(286.6)
        processor = TelemetryProcessor(smoother)

        telemetry = processor.process_power(312.2)

        self.assertIsNotNone(telemetry)
        self.assertEqual(telemetry.power_raw, 312)
        self.assertEqual(telemetry.power, 287)
        self.assertEqual(telemetry.state, "active")

    def test_zero_power_is_paused(self):
        processor = TelemetryProcessor(FixedSmoother(0))

        telemetry = processor.process_power(0)

        self.assertEqual(telemetry.state, "paused")


class MqttOutputTests(unittest.IsolatedAsyncioTestCase):
    async def test_mqtt_publishes_expected_topics(self):
        client = FakeMqttClient()
        cfg = MqttConfig(
            host="mqtt.local",
            port=1883,
            username="user",
            password="secret",
            topic_prefix="zwift",
            publish_interval_ms=1,
        )
        adapter = MqttOutputAdapter(cfg, client_factory=lambda: client)

        await adapter.start()
        adapter.connected = True
        await adapter.publish(
            Telemetry(
                power=287,
                power_raw=312,
                state="active",
                trainer_connected=True,
                source="zwift_rgb",
                timestamp="2026-05-16T20:15:30+02:00",
            )
        )

        topics = {topic: payload for topic, payload, _, _ in client.published}
        self.assertEqual(topics["zwift/power"], "287")
        self.assertEqual(topics["zwift/power_raw"], "312")
        self.assertEqual(topics["zwift/state"], "active")
        telemetry = json.loads(topics["zwift/telemetry"])
        self.assertEqual(telemetry["power"], 287)
        self.assertNotIn("ftp", telemetry)
        self.assertNotIn("percent_ftp", telemetry)
        self.assertNotIn("zone", telemetry)
        self.assertNotIn("color_hex", telemetry)


class UseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_dry_run_style_output_path(self):
        output = FakeOutput()
        processor = TelemetryProcessor(FixedSmoother(100))
        use_case = StreamPowerToTelemetryUseCase(FakeSource([120]), output, processor)

        await use_case.run(FakeClock())

        self.assertTrue(output.started)
        self.assertTrue(output.stopped)
        self.assertEqual(output.telemetry[0].power_raw, 120)
        self.assertEqual(output.telemetry[0].power, 100)
        self.assertEqual(output.states[-1], ("stopped", False))


class ConfigTests(unittest.TestCase):
    def test_env_overrides_mqtt_config(self):
        content = """
output_mode: dry_run
ble:
  prefer: cps
  address: null
  name_hint: KICKR
"""
        old_env = os.environ.copy()
        try:
            os.environ["ZWIFT_OUTPUT_MODE"] = "mqtt"
            os.environ["MQTT_HOST"] = "broker.local"
            os.environ["MQTT_PORT"] = "1884"
            os.environ["MQTT_TOPIC_PREFIX"] = "zwift_test"
            os.environ["MQTT_RETAIN"] = "true"
            path = Path.cwd() / "test_tmp_config.yaml"
            try:
                path.write_text(content, encoding="utf-8")
                cfg = load_app_config(str(path))
            finally:
                if path.exists():
                    path.unlink()
            self.assertEqual(cfg.output_mode, "mqtt")
            self.assertEqual(cfg.mqtt.host, "broker.local")
            self.assertEqual(cfg.mqtt.port, 1884)
            self.assertEqual(cfg.mqtt.topic_prefix, "zwift_test")
            self.assertTrue(cfg.mqtt.retain)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_mqtt_host_rejects_home_assistant_http_url(self):
        with self.assertRaises(ValueError):
            MqttConfig(host="http://homeassistant.local:8123")


if __name__ == "__main__":
    unittest.main()
