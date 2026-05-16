"""
📡 Adapter niskopoziomowy BLE (stałe i proste funkcje pomocnicze).

Uwaga: To NIE jest port aplikacyjny — tutaj tylko stałe UUID i wspólne utilsy,
które wykorzystują wyższe adaptery (`ble_port.py`).
"""

import struct
from typing import Optional, Sequence

from bleak import BleakClient, BleakScanner

# UUID usług/characteristics wg standardu BLE ⛓️
CPS_SVC = "00001818-0000-1000-8000-00805f9b34fb"         # Cycling Power Service
CPS_CHAR = "00002a63-0000-1000-8000-00805f9b34fb"        # Cycling Power Measurement
FTMS_SVC = "00001826-0000-1000-8000-00805f9b34fb"        # Fitness Machine Service
FTMS_CHAR_INDOOR = "00002ad2-0000-1000-8000-00805f9b34fb"# Indoor Bike Data

# Heurystyka rozpoznawania trenażerów po nazwie (gdy brak name_hint)
BLE_TRAINER_NAME_KEYWORDS: Sequence[str] = (
    "kickr", "zwift", "elite", "tacx", "wahoo", "jetblack", "magene", "stages"
)


def parse_cps(data: bytes) -> Optional[float]:
    """📥 Parsuje CPS: Instantaneous Power (int16 LE) od offsetu 2.

    Zwraca waty jako float albo None, gdy pakiet za krótki.
    """
    if len(data) < 4:
        return None
    return float(struct.unpack_from("<h", data, 2)[0])


def parse_ftms(data: bytes) -> Optional[float]:
    """📥 Parsuje FTMS: w praktyce moc bywa w dwóch ostatnich bajtach (int16 LE)."""
    if len(data) < 4:
        return None
    return float(struct.unpack_from("<h", data, len(data)-2)[0])


async def find_ble_device(address: Optional[str], name_hint: Optional[str]):
    """🔎 Znajdź urządzenie BLE: po adresie (jeśli podany) albo po nazwie.

    - Gdy `address` jest znany → zwracamy go od razu.
    - W przeciwnym razie skanujemy i dopasowujemy po `name_hint` lub heurystyce.
    """
    if address:
        return address
    devices = await BleakScanner.discover(timeout=6.0)
    name_hint_l = (name_hint or "").lower()
    for d in devices:
        n = (d.name or "").lower()
        if not n:
            continue
        if name_hint_l and name_hint_l in n:
            return d
        if not name_hint_l and any(k in n for k in BLE_TRAINER_NAME_KEYWORDS):
            return d
    raise RuntimeError("Nie znaleziono urządzenia BLE — ustaw address lub name_hint w config.yaml.")


async def choose_char(client: BleakClient, prefer: str) -> tuple[str, bool]:
    """⚙️ Wybierz charakterystykę do subskrypcji: CPS (preferowane) lub FTMS.

    Używa właściwości `client.services` (zalecane przez bleak). Jeśli lista
    usług jest pusta, przyjmujemy brak CPS i wybieramy FTMS (lub preferencję).

    Zwraca: (uuid_char, use_cps: bool)
    """
    svcs = getattr(client, "services", None)
    has_cps = False
    if svcs:
        try:
            has_cps = any(getattr(s, "uuid", None) == CPS_SVC for s in svcs)
        except Exception:
            has_cps = False
    use_cps = (prefer.lower() == "cps" and has_cps) or (not has_cps)
    char = CPS_CHAR if use_cps else FTMS_CHAR_INDOOR
    return char, use_cps
