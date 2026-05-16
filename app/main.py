import asyncio
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rgbapp.application.smoothing import build_smoother
from rgbapp.application.telemetry import TelemetryProcessor
from rgbapp.application.transitions import Fade, StaggeredWave, Uniform
from rgbapp.application.use_cases import StreamPowerToTelemetryUseCase
from rgbapp.config.factory import load_app_config
from rgbapp.infrastructure.ble_port import BlePowerSource
from rgbapp.infrastructure.clock import SystemClock
from rgbapp.infrastructure.output import CompositeOutputAdapter, DryRunOutputAdapter


log = logging.getLogger(__name__)


def build_transition(cfg) -> object:
    mode = (cfg.transitions.mode or "uniform").lower()
    if mode == "fade" and cfg.transitions.fade_steps > 0 and cfg.transitions.fade_total_ms > 0:
        return Fade(steps=cfg.transitions.fade_steps, total_ms=cfg.transitions.fade_total_ms)
    if mode == "staggered_wave":
        inner = Uniform()
        if cfg.transitions.fade_steps > 0 and cfg.transitions.fade_total_ms > 0:
            inner = Fade(cfg.transitions.fade_steps, cfg.transitions.fade_total_ms)
        return StaggeredWave(cfg.transitions.wave_delay_ms, inner)
    return Uniform()


def build_tuya_legacy_output(cfg, clock):
    from rgbapp.application.mapping import ColorMappingService
    from rgbapp.config.loader import extract_zones
    from rgbapp.infrastructure.tuya_legacy_output import TuyaLegacyOutputAdapter
    from rgbapp.infrastructure.tuya_port import TuyaLightSink

    if not cfg.tuya_devices:
        raise RuntimeError("output_mode requires tuya_devices, but none are configured")
    lights = [TuyaLightSink(d.model_dump()) for d in cfg.tuya_devices]
    zones = extract_zones(cfg.mapping.model_dump())
    mapper = ColorMappingService(ftp=cfg.ftp, mode=cfg.mapping.mode, zones=zones)
    return TuyaLegacyOutputAdapter(
        lights=lights,
        mapping_service=mapper,
        transition_policy=build_transition(cfg),
        clock=clock,
    )


def build_output(cfg, clock):
    mode = cfg.output_mode
    outputs = []
    if mode in {"mqtt", "both"}:
        from rgbapp.infrastructure.mqtt import MqttOutputAdapter

        outputs.append(MqttOutputAdapter(cfg.mqtt))
    if mode in {"tuya_legacy", "both"}:
        outputs.append(build_tuya_legacy_output(cfg, clock))
    if mode == "dry_run":
        outputs.append(DryRunOutputAdapter())
    if not outputs:
        raise RuntimeError(f"Unsupported output_mode: {mode}")
    return outputs[0] if len(outputs) == 1 else CompositeOutputAdapter(outputs)


async def async_main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_app_config("config.yaml")
    log.info("Starting zwift_rgb output_mode=%s", cfg.output_mode)

    source = BlePowerSource(cfg.ble.model_dump())
    clock = SystemClock()
    smoother = build_smoother(cfg.smoothing.window_seconds, cfg.smoothing.max_update_hz)
    processor = TelemetryProcessor(smoother)
    output = build_output(cfg, clock)

    uc = StreamPowerToTelemetryUseCase(source=source, output=output, processor=processor)
    await uc.run(clock)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
