"""
🔌 Porty aplikacyjne (interfejsy): definiują „jak rozmawiamy” z otoczeniem.

To czyste kontrakty (Protocols) — implementacje dostarcza warstwa infrastruktury.
Zalety:
- testowalność (można wstrzykiwać fake/mocks),
- luźne powiązanie (DIP — zależność od abstrakcji, nie konkretów),
- wymienność adapterów bez dotykania logiki biznesowej.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Protocol


@dataclass(frozen=True)
class Hsv:
    """🎨 Prosty obiekt koloru w HSV (Hue/Saturation/Value).

    - `h_deg`: odcień w stopniach (0..360), np. czerwony ≈ 0°, zielony ≈ 120°.
    - `s_pct`: nasycenie w procentach (0..100).
    - `v_pct`: jasność w procentach (0..100).
    """
    h_deg: float
    s_pct: float
    v_pct: float


class PowerSourcePort(Protocol):
    """⚡ Źródło mocy — dostarcza strumień wartości w watach (async)."""

    async def stream(self) -> AsyncIterator[float]:
        """Asynchroniczny strumień mocy (waty) — `async for` po kolejnych próbkach."""
        ...


class LightSinkPort(Protocol):
    """💡 Odbiornik światła — przyjmuje polecenia ustawienia koloru/animacji."""

    async def set_color(self, hsv: Hsv) -> None:
        """Ustaw kolor natychmiast (bez animacji)."""
        ...

    async def fade_to(self, hsv: Hsv, steps: int, total_ms: float) -> None:
        """Płynne przejście do koloru docelowego (liczba kroków i całkowity czas)."""
        ...


class ClockPort(Protocol):
    """⏱️ Abstrakcja zegara — dzięki temu w testach możemy sterować czasem."""

    async def sleep_ms(self, ms: float) -> None:
        """Uśpij na podaną liczbę milisekund (async)."""
        ...
