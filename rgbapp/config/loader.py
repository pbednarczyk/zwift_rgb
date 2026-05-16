"""
🧾 Prosty loader YAML i wyciąganie stref mapowania z configu.

Uwaga: to narzędzia „luźne” (nie pydantic). Do walidacji używamy modeli w `config.models`.
"""

from typing import List, Tuple, Optional


def extract_zones(mapping_cfg: dict) -> List[Tuple[Optional[float], Tuple[int,int,int]]]:
    """🧩 Wyciągnij strefy `zones` w postaci listy (próg %, kolor RGB).

    Obsługuje kolory zarówno przez nazwę (`colors_rgb.name`) jak i bezpośrednie [R,G,B].
    """
    zones: List[Tuple[Optional[float], Tuple[int,int,int]]] = []
    colors = mapping_cfg.get("colors_rgb", {})
    zones_cfg = mapping_cfg.get("zones")
    if zones_cfg and isinstance(zones_cfg, list):
        for z in zones_cfg:
            if not isinstance(z, dict):
                continue
            thr = z.get("up_to_pct", z.get("threshold_pct"))
            col = z.get("color")
            rgb: Optional[Tuple[int,int,int]] = None
            if isinstance(col, str):
                base = colors.get(col.lower())
                if isinstance(base, list) and len(base) == 3:
                    rgb = (int(base[0]), int(base[1]), int(base[2]))
            elif isinstance(col, (list, tuple)) and len(col) == 3:
                rgb = (int(col[0]), int(col[1]), int(col[2]))
            if rgb is None:
                continue
            if thr is not None:
                try:
                    thr = float(thr)
                except Exception:
                    thr = None
            zones.append((thr, rgb))
    return zones
