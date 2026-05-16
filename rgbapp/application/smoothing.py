"""
🧱 Mały „builder” wygładzacza — trzyma domenę (PowerSmoother) z dala od inicjalizacji.

Trzymamy to w warstwie application, żeby w przyszłości łatwiej podmienić strategię
bez grzebania w domenie (np. EMA zamiast średniej prostej). 
"""

from typing import Optional
from rgbapp.domain.power import PowerSmoother


def build_smoother(window_seconds: float, max_update_hz: float) -> PowerSmoother:
    # Tworzy i zwraca obiekt domenowy do wygładzania mocy
    return PowerSmoother(window_seconds=window_seconds, max_update_hz=max_update_hz)
