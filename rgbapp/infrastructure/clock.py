"""
⏱️ Zegar systemowy — prosta implementacja portu ClockPort.

W testach można ją zastąpić „fałszywym” zegarem, który nie śpi naprawdę.
"""

import asyncio
from rgbapp.application.ports import ClockPort


class SystemClock(ClockPort):
    async def sleep_ms(self, ms: float) -> None:
        # Zamień milisekundy na sekundy i śpij asynchronicznie (nie blokuj event‑loopa)
        await asyncio.sleep(max(0.0, ms) / 1000.0)
