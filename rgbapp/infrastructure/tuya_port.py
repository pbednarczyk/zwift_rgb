import asyncio
from typing import Optional

from rgbapp.application.ports import LightSinkPort, Hsv
from .tuya import TuyaLight


class TuyaLightSink(LightSinkPort):
    """Adapter asynchroniczny LightSink dla TuyaLight (blokujące I/O w wątku)."""
    def __init__(self, dev_cfg: dict):
        self.dev = TuyaLight(dev_cfg)

    async def set_color(self, hsv: Hsv) -> None:
        await asyncio.to_thread(self.dev.send_hsv, hsv.h_deg, hsv.s_pct, hsv.v_pct)

    async def fade_to(self, hsv: Hsv, steps: int, total_ms: float) -> None:
        await asyncio.to_thread(self.dev.send_hsv_fade, hsv.h_deg, hsv.s_pct, hsv.v_pct, steps, total_ms)

