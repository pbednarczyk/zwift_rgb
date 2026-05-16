"""
🎯 Przypadek użycia: strumień mocy → kolor na światłach.

To „mózg” aplikacji — łączy porty (źródło mocy, zegar, odbiorniki światła)
z politykami (mapowanie i przejścia). Nie zna BLE, nie zna Tuya — tylko interfejsy.
"""

from __future__ import annotations

from typing import Iterable

from .ports import PowerSourcePort, LightSinkPort, ClockPort, Hsv


class StreamPowerToLightsUseCase:
    """🧩 Spina źródło mocy, mapowanie i odbiorniki przez politykę przejścia (transition)."""

    def __init__(self, source: PowerSourcePort, lights: list[LightSinkPort],
                 mapping_service, transition_policy, smoother, ftp_watts: float):
        # Zależności wstrzyknięte (Dependency Injection) — łatwe testy i podmiana implementacji.
        self.source = source
        self.lights = lights
        self.mapping = mapping_service
        self.transition = transition_policy
        self.smoother = smoother
        self.ftp = max(1.0, float(ftp_watts))

    async def run(self, clock: ClockPort) -> None:
        """🚦 Pętla: czytaj moc → wygładź → zamapuj → zastosuj przejście na światła."""
        async for watts in self.source.stream():
            # 1) Wygładzanie + ograniczenie częstotliwości
            v = self.smoother.add(watts)
            if v is None:
                continue  # jeszcze za wcześnie na kolejną zmianę
            # 2) Mapowanie mocy do HSV (domena)
            hsv_tuple = self.mapping.watts_to_hsv(v)  # (h,s,v)
            target = Hsv(*hsv_tuple)
            # Info dla użytkownika: podgląd konwersji mocy → koloru
            try:
                print(f"W:{v:.0f}W -> HSV({target.h_deg:.0f},{target.s_pct:.0f}%,{target.v_pct:.0f}%)")
            except Exception:
                pass
            # 3) Zastosuj politykę przejścia (uniform/fade/wave)
            await self.transition.apply(self.lights, target, clock)
