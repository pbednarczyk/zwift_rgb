"""
🧠 Warstwa aplikacji — mapowanie mocy → kolor.

Ten serwis otacza polityki domenowe prostym API zależnym od konfiguracji:
- tryb „zones” (progi %FTP z configu),
- tryb „gradient” (linia kolorów 0..100% FTP).
"""

from typing import Tuple, Optional, List

from rgbapp.domain.color import ZoneMapper, gradient_hsv


class ColorMappingService:
    """📐 Zamienia waty na HSV zgodnie z wybraną polityką (zones/gradient)."""
    def __init__(self, ftp: float, mode: str, zones: Optional[List[tuple]] = None):
        self.ftp = max(1.0, float(ftp))  # zabezpieczenie przed dzieleniem przez zero
        self.mode = (mode or "zones").lower()
        self.zones_mapper = ZoneMapper(zones or [])

    def watts_to_hsv(self, watts: float) -> Tuple[float,float,float]:
        # Przelicz waty → %FTP (ułamki poniżej 0 ścinamy do 0)
        pct = max(0.0, watts) / self.ftp * 100.0
        if self.mode == "zones" and self.zones_mapper.zones:
            return self.zones_mapper.map_pct_to_hsv(pct)
        # Fallback na gradient, jeśli nie zdefiniowano stref
        return gradient_hsv(pct)
