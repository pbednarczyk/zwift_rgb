from __future__ import annotations

import logging

from rgbapp.application.ports import Hsv, TelemetryOutputPort
from rgbapp.application.telemetry import Telemetry


log = logging.getLogger(__name__)


class TuyaLegacyOutputAdapter(TelemetryOutputPort):
    def __init__(self, lights, mapping_service, transition_policy, clock):
        self.lights = lights
        self.mapping = mapping_service
        self.transition = transition_policy
        self.clock = clock

    async def start(self) -> None:
        log.info("Tuya legacy output enabled")

    async def publish(self, telemetry: Telemetry) -> None:
        hsv_tuple = self.mapping.watts_to_hsv(telemetry.power)
        target = Hsv(*hsv_tuple)
        await self.transition.apply(self.lights, target, self.clock)

    async def publish_state(self, state: str, trainer_connected: bool) -> None:
        log.info("Tuya legacy state=%s trainer_connected=%s", state, trainer_connected)

    async def stop(self) -> None:
        log.info("Tuya legacy output stopped")
