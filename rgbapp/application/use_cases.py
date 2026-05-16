from __future__ import annotations

import asyncio
import logging

from .ports import ClockPort, Hsv, LightSinkPort, PowerSourcePort, TelemetryOutputPort
from .telemetry import TelemetryProcessor


log = logging.getLogger(__name__)


class StreamPowerToLightsUseCase:
    def __init__(
        self,
        source: PowerSourcePort,
        lights: list[LightSinkPort],
        mapping_service,
        transition_policy,
        smoother,
        ftp_watts: float,
    ):
        self.source = source
        self.lights = lights
        self.mapping = mapping_service
        self.transition = transition_policy
        self.smoother = smoother
        self.ftp = max(1.0, float(ftp_watts))

    async def run(self, clock: ClockPort) -> None:
        async for watts in self.source.stream():
            value = self.smoother.add(watts)
            if value is None:
                continue
            hsv_tuple = self.mapping.watts_to_hsv(value)
            target = Hsv(*hsv_tuple)
            try:
                print(f"W:{value:.0f}W -> HSV({target.h_deg:.0f},{target.s_pct:.0f}%,{target.v_pct:.0f}%)")
            except Exception:
                pass
            await self.transition.apply(self.lights, target, clock)


class StreamPowerToTelemetryUseCase:
    def __init__(
        self,
        source: PowerSourcePort,
        output: TelemetryOutputPort,
        processor: TelemetryProcessor,
        reconnect_delay_seconds: float = 5.0,
    ):
        self.source = source
        self.output = output
        self.processor = processor
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self._last_state: str | None = None
        self._seen_first_sample = False

    async def _publish_state(self, state: str, trainer_connected: bool) -> None:
        if self._last_state != state:
            log.info("Trainer state changed: %s", state)
            self._last_state = state
        await self.output.publish_state(state, trainer_connected)

    async def run(self, clock: ClockPort) -> None:
        await self.output.start()
        try:
            while True:
                try:
                    async for watts in self.source.stream():
                        if not self._seen_first_sample:
                            log.info("First trainer power sample received")
                            self._seen_first_sample = True
                        telemetry = self.processor.process_power(watts, state="active")
                        if telemetry is None:
                            continue
                        if self._last_state != telemetry.state:
                            log.info("Trainer state changed: %s", telemetry.state)
                            self._last_state = telemetry.state
                        await self.output.publish(telemetry)
                    await self._publish_state("stopped", trainer_connected=False)
                    break
                except Exception:
                    log.exception("Power stream stopped unexpectedly; retrying BLE in %.1fs", self.reconnect_delay_seconds)
                    await self._publish_state("disconnected", trainer_connected=False)
                    self._seen_first_sample = False
                    await asyncio.sleep(self.reconnect_delay_seconds)
                    continue
        finally:
            await self.output.stop()
