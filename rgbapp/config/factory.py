"""
🏗️ Fabryka konfiguracji: wczytaj YAML i zwróć zwalidowany `AppConfig`.

Obsługa zarówno Pydantic v2 (`model_validate`) jak i v1 (`parse_obj`) dla zgodności.
"""

from __future__ import annotations

from pathlib import Path
import os
from typing import Any, List, Optional, Tuple

from pydantic import ValidationError
import yaml

from .models import AppConfig


def _env_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _apply_env_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    raw = dict(raw or {})
    mqtt = dict(raw.get("mqtt") or {})
    env_map = {
        "MQTT_HOST": ("host", str),
        "MQTT_PORT": ("port", int),
        "MQTT_USERNAME": ("username", str),
        "MQTT_PASSWORD": ("password", str),
        "MQTT_CLIENT_ID": ("client_id", str),
        "MQTT_TOPIC_PREFIX": ("topic_prefix", str),
        "MQTT_QOS": ("qos", int),
        "MQTT_RETAIN": ("retain", _env_bool),
        "MQTT_PUBLISH_INTERVAL_MS": ("publish_interval_ms", float),
    }
    if os.getenv("ZWIFT_OUTPUT_MODE"):
        raw["output_mode"] = os.environ["ZWIFT_OUTPUT_MODE"].strip().lower()
    for env_name, (field_name, caster) in env_map.items():
        if env_name in os.environ:
            value = os.environ[env_name]
            mqtt[field_name] = caster(value) if value != "" else None
    if mqtt:
        raw["mqtt"] = mqtt
    return raw


def load_app_config(path: str = "config.yaml") -> AppConfig:
    """📥→✅ Wczytaj YAML i zwaliduj na modelu AppConfig.

    Podnosi `RuntimeError` z czytelnym opisem, gdy konfiguracja jest błędna.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise RuntimeError(
            f"Brak pliku konfiguracji: {path}. "
            "Skopiuj config.example.yaml do config.yaml i uzupelnij lokalne dane."
        )

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    raw = _apply_env_overrides(raw)
    try:
        return AppConfig.model_validate(raw)  # pydantic v2
    except AttributeError:
        # pydantic v1 fallback
        return AppConfig.parse_obj(raw)
    except ValidationError as e:
        raise RuntimeError(f"Błędna konfiguracja: {e}")
