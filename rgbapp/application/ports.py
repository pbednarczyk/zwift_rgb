from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from .telemetry import Telemetry


@dataclass(frozen=True)
class Hsv:
    h_deg: float
    s_pct: float
    v_pct: float


class PowerSourcePort(Protocol):
    async def stream(self) -> AsyncIterator[float]:
        ...


class LightSinkPort(Protocol):
    async def set_color(self, hsv: Hsv) -> None:
        ...

    async def fade_to(self, hsv: Hsv, steps: int, total_ms: float) -> None:
        ...


class ClockPort(Protocol):
    async def sleep_ms(self, ms: float) -> None:
        ...


class TelemetryOutputPort(Protocol):
    async def start(self) -> None:
        ...

    async def publish(self, telemetry: Telemetry) -> None:
        ...

    async def publish_state(self, state: str, trainer_connected: bool) -> None:
        ...

    async def stop(self) -> None:
        ...
