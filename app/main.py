"""
🚀 Composition Root (główne wejście nowej architektury):

Składa aplikację z:
- portów i adapterów (BLE źródło mocy, Tuya wyjścia światła, zegar),
- polityk (mapowanie i przejścia),
- konfiguracji (Pydantic),
- przypadku użycia (use case), który wszystko spina.
"""

import asyncio
import sys
from pathlib import Path

# Umożliwiamy uruchamianie także przez: `python app/main.py`
# (dodajemy katalog projektu do PYTHONPATH, aby importy `rgbapp.*` działały) 🧩
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rgbapp.application.use_cases import StreamPowerToLightsUseCase
from rgbapp.application.mapping import ColorMappingService
from rgbapp.application.smoothing import build_smoother
from rgbapp.application.transitions import Uniform, Fade, StaggeredWave
from rgbapp.infrastructure.ble_port import BlePowerSource
from rgbapp.infrastructure.clock import SystemClock
from rgbapp.infrastructure.tuya_port import TuyaLightSink
from rgbapp.config.factory import load_app_config
from rgbapp.config.loader import extract_zones  # reuse extractor for zones


def build_transition(cfg) -> object:
    """🏗️ Zbuduj politykę przejścia zgodnie z configiem."""
    mode = (cfg.transitions.mode or "uniform").lower()
    if mode == "fade" and cfg.transitions.fade_steps > 0 and cfg.transitions.fade_total_ms > 0:
        return Fade(steps=cfg.transitions.fade_steps, total_ms=cfg.transitions.fade_total_ms)
    if mode == "staggered_wave":
        inner = Uniform()
        if cfg.transitions.fade_steps > 0 and cfg.transitions.fade_total_ms > 0:
            inner = Fade(cfg.transitions.fade_steps, cfg.transitions.fade_total_ms)
        return StaggeredWave(cfg.transitions.wave_delay_ms, inner)
    return Uniform()


async def async_main():
    # 1) Wczytaj i zwaliduj konfigurację
    cfg = load_app_config("config.yaml")

    # 2) Zbuduj porty i adaptery
    source = BlePowerSource(cfg.ble.model_dump())
    lights = [TuyaLightSink(d.model_dump()) for d in cfg.tuya_devices]
    clock = SystemClock()

    # 3) Polityki mapowania i przejść
    zones = extract_zones(cfg.mapping.model_dump())
    mapper = ColorMappingService(ftp=cfg.ftp, mode=cfg.mapping.mode, zones=zones)
    smoother = build_smoother(cfg.smoothing.window_seconds, cfg.smoothing.max_update_hz)
    transition = build_transition(cfg)

    # 4) Przypadek użycia: spina wszystko w pętlę
    uc = StreamPowerToLightsUseCase(
        source=source,
        lights=lights,
        mapping_service=mapper,
        transition_policy=transition,
        smoother=smoother,
        ftp_watts=cfg.ftp,
    )
    await uc.run(clock)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
