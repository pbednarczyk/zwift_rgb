import struct
from typing import Optional, Sequence

from bleak import BleakClient, BleakScanner

CPS_SVC = "00001818-0000-1000-8000-00805f9b34fb"
CPS_CHAR = "00002a63-0000-1000-8000-00805f9b34fb"
FTMS_SVC = "00001826-0000-1000-8000-00805f9b34fb"
FTMS_CHAR_INDOOR = "00002ad2-0000-1000-8000-00805f9b34fb"

BLE_TRAINER_NAME_KEYWORDS: Sequence[str] = (
    "kickr",
    "zwift",
    "elite",
    "tacx",
    "wahoo",
    "jetblack",
    "magene",
    "stages",
)


def parse_cps(data: bytes) -> Optional[float]:
    if len(data) < 4:
        return None
    return float(struct.unpack_from("<h", data, 2)[0])


def parse_ftms(data: bytes) -> Optional[float]:
    if len(data) < 4:
        return None
    return float(struct.unpack_from("<h", data, len(data) - 2)[0])


async def find_ble_device(address: Optional[str], name_hint: Optional[str]):
    if address:
        return address
    devices = await BleakScanner.discover(timeout=6.0)
    name_hint_l = (name_hint or "").lower()
    for device in devices:
        name = (device.name or "").lower()
        if not name:
            continue
        if name_hint_l and name_hint_l in name:
            return device
        if not name_hint_l and any(keyword in name for keyword in BLE_TRAINER_NAME_KEYWORDS):
            return device
    raise RuntimeError("BLE trainer not found. Set ble.address or ble.name_hint in config.yaml.")


async def choose_char(client: BleakClient, prefer: str) -> tuple[str, bool]:
    services = getattr(client, "services", None)
    if not services:
        services = await client.get_services()

    available_notify_chars: set[str] = set()
    for service in services:
        for char in getattr(service, "characteristics", []) or []:
            properties = {str(prop).lower() for prop in getattr(char, "properties", []) or []}
            if "notify" in properties or "indicate" in properties:
                available_notify_chars.add(str(getattr(char, "uuid", "")).lower())

    prefer = (prefer or "cps").lower()
    candidates = (
        [(CPS_CHAR, True), (FTMS_CHAR_INDOOR, False)]
        if prefer == "cps"
        else [(FTMS_CHAR_INDOOR, False), (CPS_CHAR, True)]
    )
    for uuid, use_cps in candidates:
        if uuid.lower() in available_notify_chars:
            return uuid, use_cps

    raise RuntimeError(
        "Trainer exposes no supported power notification characteristic. "
        f"Expected CPS {CPS_CHAR} or FTMS {FTMS_CHAR_INDOOR}; "
        f"notify characteristics: {sorted(available_notify_chars)}"
    )
