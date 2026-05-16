"""
🎨 Warstwa domeny — kolory i mapowanie mocy → barwy.

Ten moduł zawiera wyłącznie „czystą” logikę (bez sieci, bez sprzętu):
- konwersje kolorów RGB → HSV i odwrotnie DP24 (format Tuya),
- prostą politykę mapowania strefowego (progi %FTP → kolor),
- gradient niebieski → czerwony dla 0..100% FTP.

Nie ma tu importów z bibliotek I/O — dzięki temu łatwo to testować 🧪.
"""

from typing import Tuple, Optional, List


def rgb_to_hsv_deg(r:int,g:int,b:int) -> Tuple[float,float,float]:
    """🔁 RGB (0..255) → HSV w jednostkach (stopnie, %, %).

    Zwraca krotkę: (h_deg 0..360, s_pct 0..100, v_pct 0..100).

    Jak to liczymy:
    - Normalizujemy RGB do zakresu 0..1.
    - Szukamy maksimum i minimum, aby policzyć „różnicę” (szerokość barwy) ➗.
    - W zależności, który kanał dominuje (R/G/B), obliczamy odcień w stopniach.
    - Nasycenie to proporcja „różnicy” do maksimum, a wartość (jasność) to samo maksimum.
    """
    r1,g1,b1 = r/255.0, g/255.0, b/255.0
    mx, mn = max(r1,g1,b1), min(r1,g1,b1)
    d = mx - mn  # szerokość barwy
    if d == 0:
        h = 0.0  # odcień nieokreślony → traktujemy jako 0° (czerwony)
    elif mx == r1:
        h = (60 * ((g1-b1)/d) + 360) % 360
    elif mx == g1:
        h = (60 * ((b1-r1)/d) + 120) % 360
    else:
        h = (60 * ((r1-g1)/d) + 240) % 360
    s = 0.0 if mx == 0 else (d / mx) * 100.0
    v = mx * 100.0
    return (h, s, v)


def hsv_to_dp24(h_deg: float, s_pct: float, v_pct: float) -> str:
    """🧩 Konwersja HSV → DP24 (format Tuya): HHHHSSSSVVVV w hex.

    - H: 0..360 (stopnie),
    - S: 0..1000 (nasycenie % * 10),
    - V: 0..1000 (jasność % * 10).
    """
    h = max(0, min(360, int(round(h_deg))))
    s = max(0, min(1000, int(round(s_pct * 10))))
    v = max(0, min(1000, int(round(v_pct * 10))))
    return f"{h:04x}{s:04x}{v:04x}"


class ZoneMapper:
    """🗺️ Prosta polityka: progi %FTP → kolor RGB (następnie HSV).

    Przeglądamy strefy po kolei i wybieramy pierwszą, której próg spełnia warunek.
    Ostatnia strefa może mieć próg `None` → „reszta”.
    """
    def __init__(self, zones: List[Tuple[Optional[float], Tuple[int,int,int]]]):
        self.zones = zones

    def map_pct_to_hsv(self, pct_ftp: float) -> Tuple[float,float,float]:
        # Iteruj po strefach — pierwszy pasujący próg wygrywa 🏁
        for thr, rgb in self.zones:
            if thr is None or pct_ftp < thr:
                return rgb_to_hsv_deg(*rgb)
        # Gdyby nie było „reszty”, weź ostatnią strefę jako bezpieczny fallback
        return rgb_to_hsv_deg(*self.zones[-1][1])


def gradient_hsv(pct_ftp: float) -> Tuple[float,float,float]:
    """🌈 Gradient: 0% = niebieski (240°) → 100% = czerwony (0°).

    Powyżej 100% przyjmujemy odcień 0° (czerwony alarm 🚨).
    """
    hue = 240.0 - 240.0*min(max(pct_ftp,0.0)/100.0, 1.0) if pct_ftp <= 100.0 else 0.0
    return (hue, 100.0, 100.0)
