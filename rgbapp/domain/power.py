"""
📈 Wygładzanie mocy (rolling average) + ograniczenie częstotliwości aktualizacji.

Dlaczego to potrzebne?
- Czujniki BLE potrafią „szumieć” i wysyłać próbki bardzo często.
- Uśrednianie w krótkim oknie wygładza skoki, a `max_update_hz` ogranicza
  jak często „wypuszczamy” wartość dalej (mniej spamu do lamp 💡).
"""

from typing import Optional, List, Tuple
import time


class PowerSmoother:
    """🫧 Uśrednia próbki z ostatniego `window_seconds` i emituje nie częściej niż `max_update_hz`."""
    def __init__(self, window_seconds: float, max_update_hz: float):
        # Minimalne bezpieczne wartości, by uniknąć dzielenia przez zero itd.
        self.window_s = max(0.05, float(window_seconds))
        self.max_update_hz = max(2.0, float(max_update_hz))
        # Lista par: (timestamp, watts)
        self.samples: List[Tuple[float, float]] = []
        # Kiedy ostatni raz zwróciliśmy wartość (throttle)
        self._last_push = 0.0

    def add(self, watts: float) -> Optional[float]:
        """➕ Dodaj próbkę mocy; zwróć uśrednioną wartość co `1/max_update_hz` sekundy.

        Zwraca:
        - float: uśredniona moc gotowa do dalszego przetwarzania,
        - None: jeśli jeszcze nie czas na kolejną emisję.
        """
        now = time.time()
        self.samples.append((now, watts))
        # Usuń próbki starsze niż okno
        cutoff = now - self.window_s
        self.samples = [s for s in self.samples if s[0] >= cutoff]
        if not self.samples:
            return 0.0  # przy pustej liście zwracamy 0.0 (bez None) by nie „zawiesić” potoku
        # Średnia arytmetyczna z okna
        avg = sum(v for _, v in self.samples)/len(self.samples)
        # Ogranicz częstotliwość emisji (throttle)
        if now - self._last_push >= 1.0 / self.max_update_hz:
            self._last_push = now
            return avg
        return None
