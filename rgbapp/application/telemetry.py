from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class Telemetry:
    power: int
    power_raw: int
    state: str
    trainer_connected: bool
    source: str
    timestamp: str
    cadence: Optional[int] = None
    hr: Optional[int] = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "power": self.power,
            "power_raw": self.power_raw,
            "state": self.state,
            "trainer_connected": self.trainer_connected,
            "source": self.source,
            "timestamp": self.timestamp,
        }
        if self.cadence is not None:
            payload["cadence"] = self.cadence
        if self.hr is not None:
            payload["hr"] = self.hr
        return payload


class TelemetryProcessor:
    def __init__(self, smoother, source_name: str = "zwift_rgb"):
        self.smoother = smoother
        self.source_name = source_name

    def process_power(self, power_raw: float, state: str = "active") -> Optional[Telemetry]:
        smoothed = self.smoother.add(float(power_raw))
        if smoothed is None:
            return None
        raw_int = max(0, round(float(power_raw)))
        power_int = max(0, round(float(smoothed)))
        effective_state = state if raw_int > 0 else "paused"
        return Telemetry(
            power=power_int,
            power_raw=raw_int,
            state=effective_state,
            trainer_connected=True,
            source=self.source_name,
            timestamp=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        )
