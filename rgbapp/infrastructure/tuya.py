"""
💡 Niskopoziomowy adapter Tuya: ustawianie koloru DP24 z fallbackiem do HSV 0..255.

Zasada działania:
- Preferujemy DP24 (precyzyjne HSV → kodowane hex),
- Jeśli urządzenie nie obsługuje DP24, używamy `set_colour(H,S,V)` (0..255),
- Zapamiętujemy ostatnio ustawiony kolor i „podpis” (signature), aby nie spamować
  tych samych wartości i umożliwić płynny fade.
"""

import time
from typing import Optional, Tuple

import tinytuya
from rgbapp.domain.color import hsv_to_dp24


class TuyaLight:
    """🔌 Sterowanie żarówką Tuya (DP24 + fallback HSV 0..255)."""

    def __init__(self, dev_cfg: dict):
        # Dane urządzenia z configu (ID/KEY/IP/Wersja/DPS)
        self.name = dev_cfg.get("name", "Light")
        self.dps = dev_cfg.get("dps_map", {})
        self.dev = tinytuya.BulbDevice(dev_cfg["id"], dev_cfg["ip"], dev_cfg["key"])
        self.dev.set_version(float(dev_cfg.get("version", "3.5")))
        # Usprawnienia połączenia TCP
        if hasattr(self.dev, "set_socketPersistent"):
            self.dev.set_socketPersistent(True)
        if hasattr(self.dev, "set_socketRetryLimit"):
            self.dev.set_socketRetryLimit(1)
        # Ostatni kolor/podpis (do anti-spam i fade)
        self._last_signature: Optional[tuple[int, int, int]] = None
        self._last_hsv: Optional[Tuple[float, float, float]] = None
        # Spróbuj włączyć i przełączyć w tryb „colour” (jeśli się nie uda, pomijamy)
        try:
            self.dev.set_status(True, self.dps.get("power", 20))
        except Exception:
            pass
        try:
            self.dev.set_value(self.dps.get("mode", 21), "colour")
        except Exception:
            pass

    def _send_once(self, h_deg: float, s_pct: float, v_pct: float):
        """📨 Wyślij jednorazowo kolor HSV (próba DP24 → fallback 0..255)."""
        sig = (int(round(h_deg)), int(round(s_pct)), int(round(v_pct)))
        if sig == self._last_signature:
            return  # nic nie rób, jeśli to samo co poprzednio (anti-spam)
        # Najpierw DP24 (dokładne HSV w hex)
        try:
            payload = hsv_to_dp24(h_deg, s_pct, v_pct)
            self.dev.set_value(self.dps.get("color", 24), payload)
            self._last_signature = sig
            self._last_hsv = (h_deg, s_pct, v_pct)
            return
        except Exception:
            pass  # jeśli DP24 nie zadziała, spróbuj trybu żarówkowego 0..255
        # Fallback: `set_colour(H,S,V)` w skali 0..255
        try:
            h_255 = max(0, min(255, int(round((h_deg % 360) / 360.0 * 255))))
            s_255 = max(0, min(255, int(round(s_pct / 100.0 * 255))))
            v_255 = max(0, min(255, int(round(v_pct / 100.0 * 255))))
            self.dev.set_colour(h_255, s_255, v_255)
            self._last_signature = sig
            self._last_hsv = (h_deg, s_pct, v_pct)
            return
        except Exception:
            pass

    def send_hsv(self, h_deg: float, s_pct: float, v_pct: float):
        """🎯 Natychmiastowe ustawienie HSV (bez animacji)."""
        self._send_once(h_deg, s_pct, v_pct)

    def send_hsv_fade(
        self,
        h_deg: float,
        s_pct: float,
        v_pct: float,
        steps: int = 5,
        total_ms: float = 300.0,
    ):
        """🌟 Płynna zmiana z ostatniego HSV do docelowego w `steps` krokach.

        Uwaga: wiele szybkich komend może obciążyć urządzenie — dobierz parametry rozsądnie.
        """
        try:
            steps = max(1, int(steps))
            dt = max(0.0, float(total_ms)) / steps / 1000.0
        except Exception:
            steps = 1
            dt = 0.0
        start = self._last_hsv
        if not start:
            # Brak znanego punktu startowego — ustaw od razu cel
            self._send_once(h_deg, s_pct, v_pct)
            return
        h0, s0, v0 = start
        # Równomierny krok między startem a celem
        dh = (h_deg - h0) / steps
        ds = (s_pct - s0) / steps
        dv = (v_pct - v0) / steps
        for i in range(1, steps + 1):
            hi = h0 + dh * i
            si = s0 + ds * i
            vi = v0 + dv * i
            self._send_once(hi, si, vi)
            if dt > 0:
                time.sleep(dt)

