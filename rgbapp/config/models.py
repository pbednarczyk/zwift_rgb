"""
🧱 Typowane modele konfiguracji (Pydantic) — walidacja i autouzupełnianie.

Definiujemy schemat `config.yaml` w kodzie, co:
- ułatwia walidację 🚦,
- daje podpowiedzi w IDE 📎,
- pozwala budować zależności w composition root bez „ręcznego” sprawdzania pól.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, NonNegativeFloat, PositiveFloat


class DeviceConfig(BaseModel):
    """🧩 Jedno urządzenie Tuya sterowane po LAN."""

    name: str                      # nazwa przyjazna
    id: str                        # Device ID (z tinytuya wizard)
    key: str                       # Local Key (z tinytuya wizard)
    ip: str                        # lokalny adres IP urządzenia
    version: float = 3.5           # wersja protokołu (np. 3.3/3.5)
    dps_map: Dict[str, int] = Field(
        default_factory=lambda: {"power": 20, "mode": 21, "color": 24}
    )


class BleConfig(BaseModel):
    """📡 Konfiguracja BLE — jak szukać i z czym się łączyć."""

    prefer: str = "cps"            # preferowana charakterystyka: cps | ftms
    address: Optional[str] = None  # MAC/UUID trenażera (jeśli znany)
    name_hint: Optional[str] = None# fragment nazwy do heurystyki


class SmoothingConfig(BaseModel):
    """🫧 Parametry wygładzania mocy."""

    window_seconds: PositiveFloat = 0.25
    max_update_hz: PositiveFloat = 10


class ZoneConfig(BaseModel):
    """🎯 Strefa mapowania: próg %FTP i kolor (nazwa lub [R,G,B])."""

    up_to_pct: Optional[float] = None
    color: Union[str, List[int]]


class MappingConfig(BaseModel):
    """🧠 Mapowanie mocy do koloru."""

    mode: str = "zones"  # zones | gradient
    colors_rgb: Dict[str, List[int]] = Field(default_factory=dict)
    zones: List[ZoneConfig] = Field(default_factory=list)


class TransitionsConfig(BaseModel):
    """🎆 Efekty przejść koloru."""

    mode: str = "uniform"  # uniform | fade | staggered_wave
    fade_steps: int = 0
    fade_total_ms: NonNegativeFloat = 0
    wave_delay_ms: NonNegativeFloat = 60


class AppConfig(BaseModel):
    """📒 Główny model konfiguracji aplikacji."""

    tuya_devices: List[DeviceConfig]
    ftp: PositiveFloat = 260
    ble: BleConfig
    smoothing: SmoothingConfig = SmoothingConfig()
    mapping: MappingConfig = MappingConfig()
    transitions: TransitionsConfig = TransitionsConfig()
