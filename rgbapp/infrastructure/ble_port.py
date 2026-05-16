"""
📡 Adapter portu źródła mocy (PowerSourcePort) dla BLE (bleak).

Robi trzy rzeczy:
1) Znajduje urządzenie BLE po adresie lub nazwie,
2) Subskrybuje odpowiednią charakterystykę (CPS/FTMS),
3) Tłumaczy powiadomienia BLE na asynchroniczny strumień watów (`async for`).

Wewnątrz używa kolejki, by rozdzielić wątki callbacków BLE od pętli konsumenta.
"""

import asyncio
from typing import AsyncIterator, Optional

from bleak import BleakClient

from rgbapp.application.ports import PowerSourcePort
from .ble import find_ble_device, select_power_device, choose_char, parse_cps, parse_ftms


class BlePowerSource(PowerSourcePort):
    def __init__(self, ble_cfg: dict):
        # Surowy słownik z configu: { prefer, address, name_hint }
        self.ble_cfg = ble_cfg

    async def stream(self) -> AsyncIterator[float]:
        # 1) Wybierz urządzenie BLE (adres lub heurystyka po nazwie)
        hint = self.ble_cfg.get("name_hint")
        prefer = (self.ble_cfg.get("prefer") or "cps").lower()
        print(f"[BLE] Skanuję... (prefer: {prefer}, hint: {hint}) — zacznij kręcić 🚴")
        device_candidates = await find_ble_device(self.ble_cfg.get("address"), hint)
        device = await select_power_device(device_candidates)
        # Kolejka do buforowania watów z callbacka → konsumenta async
        queue: asyncio.Queue[float] = asyncio.Queue(maxsize=100)

        async with BleakClient(device, timeout=15.0) as client:
            # 2) Wybierz charakterystykę do subskrypcji (CPS lub FTMS)
            char, use_cps = await choose_char(client, prefer)
            print(f"[BLE] Połączono. Subskrybuję {'CPS' if use_cps else 'FTMS'} ({char}).")

            def handle(_, data: bytearray):
                # Callback z BLE — szybki parsing i wrzut do kolejki
                watts = (parse_cps if use_cps else parse_ftms)(bytes(data)) or 0.0
                try:
                    queue.put_nowait(watts)
                except asyncio.QueueFull:
                    # Jeśli kolejka pełna: wyrzuć najstarszą wartość i wstaw najnowszą (ważniejsza)
                    _ = queue.get_nowait()
                    queue.put_nowait(watts)

            # 3) Start subskrypcji powiadomień BLE
            await client.start_notify(char, handle)
            print("[BLE] Odbieram dane mocy…")

            try:
                # Strumień async — konsumenci robią `async for watts in source.stream()`
                while True:
                    watts = await queue.get()
                    yield watts
            finally:
                # Zatrzymaj subskrypcję, gdy pętla się kończy
                await client.stop_notify(char)
