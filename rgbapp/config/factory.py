"""
🏗️ Fabryka konfiguracji: wczytaj YAML i zwróć zwalidowany `AppConfig`.

Obsługa zarówno Pydantic v2 (`model_validate`) jak i v1 (`parse_obj`) dla zgodności.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import ValidationError
import yaml

from .models import AppConfig


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
    try:
        return AppConfig.model_validate(raw)  # pydantic v2
    except AttributeError:
        # pydantic v1 fallback
        return AppConfig.parse_obj(raw)
    except ValidationError as e:
        raise RuntimeError(f"Błędna konfiguracja: {e}")
