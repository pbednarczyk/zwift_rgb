from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional

from rgbapp.application.ports import TelemetryOutputPort
from rgbapp.application.telemetry import Telemetry


log = logging.getLogger(__name__)


class MqttOutputAdapter(TelemetryOutputPort):
    def __init__(self, cfg, client_factory: Optional[Callable[[], Any]] = None):
        self.cfg = cfg
        self.client_factory = client_factory
        self.client = None
        self.connected = False
        self._last_publish = 0.0
        self._last_state: str | None = None
        self._last_not_connected_log = 0.0
        self._lock = asyncio.Lock()

    @property
    def prefix(self) -> str:
        return str(self.cfg.topic_prefix).strip("/")

    def topic(self, suffix: str) -> str:
        return f"{self.prefix}/{suffix}"

    async def start(self) -> None:
        if self.client is not None:
            return
        try:
            self.client = self.client_factory() if self.client_factory else self._build_paho_client()
            if getattr(self.cfg, "username", None):
                self.client.username_pw_set(self.cfg.username, self.cfg.password or None)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.reconnect_delay_set(min_delay=1, max_delay=30)
            log.info("Connecting to MQTT broker %s:%s as %s", self.cfg.host, self.cfg.port, self.cfg.client_id)
            self.client.connect_async(self.cfg.host, int(self.cfg.port), keepalive=30)
            self.client.loop_start()
        except Exception:
            log.exception("Failed to start MQTT output")

    def _build_paho_client(self):
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("Missing MQTT dependency. Install paho-mqtt.") from exc
        return mqtt.Client(client_id=self.cfg.client_id)

    def _on_connect(self, client, userdata, flags, rc, *args) -> None:
        self.connected = rc == 0
        if self.connected:
            log.info("MQTT connected")
        else:
            log.error("MQTT connection failed with rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc, *args) -> None:
        self.connected = False
        if rc == 0:
            log.info("MQTT disconnected")
        else:
            log.warning("MQTT disconnected unexpectedly rc=%s; reconnect is enabled", rc)

    async def publish(self, telemetry: Telemetry) -> None:
        now = time.monotonic()
        min_interval = float(self.cfg.publish_interval_ms) / 1000.0
        state_changed = telemetry.state != self._last_state
        if not state_changed and now - self._last_publish < min_interval:
            return
        self._last_publish = now
        self._last_state = telemetry.state
        payload = telemetry.to_payload()
        async with self._lock:
            await self._publish(self.topic("power"), str(telemetry.power))
            await self._publish(self.topic("power_raw"), str(telemetry.power_raw))
            await self._publish(self.topic("state"), telemetry.state)
            if telemetry.cadence is not None:
                await self._publish(self.topic("cadence"), str(telemetry.cadence))
            if telemetry.hr is not None:
                await self._publish(self.topic("hr"), str(telemetry.hr))
            await self._publish(self.topic("telemetry"), json.dumps(payload, separators=(",", ":")))

    async def publish_state(self, state: str, trainer_connected: bool) -> None:
        self._last_state = state
        async with self._lock:
            await self._publish(self.topic("state"), state)

    async def _publish(self, topic: str, payload: str) -> None:
        if self.client is None:
            return
        if not self.connected:
            now = time.monotonic()
            if now - self._last_not_connected_log >= 10.0:
                log.warning("MQTT is not connected; dropping publishes until reconnect")
                self._last_not_connected_log = now
            return
        try:
            result = self.client.publish(topic, payload, qos=int(self.cfg.qos), retain=bool(self.cfg.retain))
            rc = getattr(result, "rc", 0)
            if rc not in (0, None):
                log.warning("MQTT publish failed topic=%s rc=%s", topic, rc)
        except Exception:
            log.exception("MQTT publish error topic=%s", topic)

    async def stop(self) -> None:
        if self.client is None:
            return
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            log.exception("Failed to stop MQTT output")
        finally:
            self.client = None
