"""
🎆 Polityki przejść (animacje): jak „dojeżdżamy” do koloru docelowego.

Strategia (Strategy Pattern): różne implementacje tego samego kontraktu `TransitionPolicy`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from .ports import LightSinkPort, Hsv, ClockPort


class TransitionPolicy(Protocol):
    """Kontrakt: zastosuj przejście do `target` dla listy świateł."""

    async def apply(self, lights: list[LightSinkPort], target: Hsv, clock: ClockPort) -> None:
        ...


@dataclass
class Uniform(TransitionPolicy):
    """🎯 Jednoczesna zmiana koloru na wszystkich urządzeniach (bez animacji)."""

    async def apply(self, lights: list[LightSinkPort], target: Hsv, clock: ClockPort) -> None:
        await asyncio.gather(*(l.set_color(target) for l in lights))


@dataclass
class Fade(TransitionPolicy):
    """🌟 Płynne przejście (fade) do koloru docelowego na wszystkich urządzeniach."""

    steps: int
    total_ms: float

    async def apply(self, lights: list[LightSinkPort], target: Hsv, clock: ClockPort) -> None:
        await asyncio.gather(*(l.fade_to(target, self.steps, self.total_ms) for l in lights))


@dataclass
class StaggeredWave(TransitionPolicy):
    """🌊 Fala: urządzenia zmieniają kolor sekwencyjnie z opóźnieniem.

    Używa „wewnętrznej” polityki (np. Uniform lub Fade) dla pojedynczego urządzenia,
    ale przesuwa ją w czasie dla kolejnych lamp.
    """

    per_device_delay_ms: float
    inner: TransitionPolicy

    async def apply(self, lights: list[LightSinkPort], target: Hsv, clock: ClockPort) -> None:
        tasks = []
        for i, l in enumerate(lights):
            async def job(L=l, idx=i):
                await clock.sleep_ms(self.per_device_delay_ms * idx)
                await self.inner.apply([L], target, clock)
            tasks.append(asyncio.create_task(job()))
        await asyncio.gather(*tasks)
