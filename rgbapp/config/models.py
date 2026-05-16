"""
🧱 Typowane modele konfiguracji (Pydantic) — walidacja i autouzupełnianie.

Definiujemy schemat `config.yaml` w kodzie, co:
- ułatwia walidację 🚦,
- daje podpowiedzi w IDE 📎,
- pozwala budować zależności w composition root bez „ręcznego” sprawdzania pól.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, NonNegativeFloat, PositiveFloat, field_validator


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


class MqttConfig(BaseModel):
    """MQTT output settings for telemetry publishing."""

    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str = "zwift_rgb"
    topic_prefix: str = "zwift"
    qos: int = 0
    retain: bool = False
    publish_interval_ms: PositiveFloat = 500

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        host = (value or "").strip()
        if "://" in host or "/" in host:
            raise ValueError(
                "MQTT_HOST must be a broker hostname or IP only, for example "
                "'homeassistant.local'. Do not use 'http://...' or the Home Assistant UI URL."
            )
        if ":" in host:
            raise ValueError("Put the MQTT port in MQTT_PORT, not in MQTT_HOST.")
        return host


class AppConfig(BaseModel):
    """📒 Główny model konfiguracji aplikacji."""

    output_mode: Literal["mqtt", "tuya_legacy", "both", "dry_run"] = "mqtt"
    tuya_devices: List[DeviceConfig] = Field(default_factory=list)
    ftp: PositiveFloat = 260
    ble: BleConfig
    mqtt: MqttConfig = MqttConfig()
    smoothing: SmoothingConfig = SmoothingConfig()
    mapping: MappingConfig = MappingConfig()
    transitions: TransitionsConfig = TransitionsConfig()
