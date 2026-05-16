from __future__ import annotations

import logging

from rgbapp.application.ports import TelemetryOutputPort
from rgbapp.application.telemetry import Telemetry


log = logging.getLogger(__name__)


class DryRunOutputAdapter(TelemetryOutputPort):
    async def start(self) -> None:
        log.info("Dry run output enabled")

    async def publish(self, telemetry: Telemetry) -> None:
        log.info(
            "Telemetry power=%s power_raw=%s state=%s",
            telemetry.power,
            telemetry.power_raw,
            telemetry.state,
        )

    async def publish_state(self, state: str, trainer_connected: bool) -> None:
        log.info("Telemetry state=%s trainer_connected=%s", state, trainer_connected)

    async def stop(self) -> None:
        log.info("Dry run output stopped")


class CompositeOutputAdapter(TelemetryOutputPort):
    def __init__(self, outputs: list[TelemetryOutputPort]):
        self.outputs = outputs

    async def start(self) -> None:
        for output in self.outputs:
            await output.start()

    async def publish(self, telemetry: Telemetry) -> None:
        for output in self.outputs:
            await output.publish(telemetry)

    async def publish_state(self, state: str, trainer_connected: bool) -> None:
        for output in self.outputs:
            await output.publish_state(state, trainer_connected)

    async def stop(self) -> None:
        for output in reversed(self.outputs):
            await output.stop()
