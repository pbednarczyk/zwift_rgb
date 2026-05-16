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
    candidates = []
    for device in devices:
        name = (device.name or "").lower()
        if not name:
            continue
        if name_hint_l and name_hint_l in name:
            candidates.append(device)
            continue
        if not name_hint_l and any(keyword in name for keyword in BLE_TRAINER_NAME_KEYWORDS):
            candidates.append(device)
    if candidates:
        return candidates
    raise RuntimeError("BLE trainer not found. Set ble.address or ble.name_hint in config.yaml.")


def has_supported_power_char(services) -> bool:
    available = get_notify_characteristic_uuids(services)
    return CPS_CHAR.lower() in available or FTMS_CHAR_INDOOR.lower() in available


def get_notify_characteristic_uuids(services) -> set[str]:
    available_notify_chars: set[str] = set()
    for service in services:
        for char in getattr(service, "characteristics", []) or []:
            properties = {str(prop).lower() for prop in getattr(char, "properties", []) or []}
            if "notify" in properties or "indicate" in properties:
                available_notify_chars.add(str(getattr(char, "uuid", "")).lower())
    return available_notify_chars


async def select_power_device(device_or_candidates):
    if not isinstance(device_or_candidates, list):
        return device_or_candidates
    last_error = None
    for device in device_or_candidates:
        try:
            async with BleakClient(device, timeout=15.0) as client:
                services = getattr(client, "services", None)
                if not services:
                    services = await client.get_services()
                if has_supported_power_char(services):
                    return device
                last_error = (
                    f"{getattr(device, 'name', None) or device}: "
                    f"notify characteristics {sorted(get_notify_characteristic_uuids(services))}"
                )
        except Exception as exc:
            last_error = f"{getattr(device, 'name', None) or device}: {exc}"
            continue
    raise RuntimeError(
        "No matching BLE device exposes CPS or FTMS power data. "
        f"Last checked device: {last_error}"
    )


async def choose_char(client: BleakClient, prefer: str) -> tuple[str, bool]:
    services = getattr(client, "services", None)
    if not services:
        services = await client.get_services()

    available_notify_chars = get_notify_characteristic_uuids(services)

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
