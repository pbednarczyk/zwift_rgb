# 🚴‍♀️ Zwift → Tuya RGB (LAN) ✨

Steruj kolorem żarówek Tuya/LSC po LAN wprost z mocy trenażera BLE. Zero chmury, zero nakładek — czysty lokalny flow.

- 💡 Tuya LAN: DP24 (HSV) z automatycznym fallbackiem do `set_colour(0..255)`
- 📶 BLE CPS/FTMS: Wahoo/KICKR, Tacx, Elite, Zwift Hub, Magene, Stages itd.
- 🎨 Mapowanie mocy: strefy `zones` z `config.yaml` lub płynny `gradient`
- 🫧 Wygładzanie: okno czasowe + limit częstotliwości aktualizacji
- 🧱 Architektura: DDD (domain / application / infrastructure / config)

---

## 🚀 Szybki start

1) Utwórz środowisko i zainstaluj zależności

```
python -m venv .venv
.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

2) Zdobądź Device ID / Local Key / IP (Tuya Local)

```
python -m tinytuya wizard
```
- Zaloguj się danymi z aplikacji: LSC Smart Connect / Tuya Smart / Smart Life.
- Przepisz `id`, `localKey`, `ip` do `config.yaml` w sekcji `tuya_devices`.
- Jeśli kreator poprosi o „Cloud Project” w Tuya IoT — zaakceptuj (jednorazowo).

3) Skonfiguruj mapowanie i BLE w `config.yaml`
- Ustaw `mapping.mode: zones` lub `gradient`.
- Dla `zones` zdefiniuj progi i kolory w `mapping.zones`.
- Podaj `ble.name_hint` lub `ble.address` (MAC) trenażera.

4) Odpal 🚦

```
python -m app.main
```

---

## 🧩 Konfiguracja (`config.yaml`)

- `tuya_devices`: lista urządzeń Tuya sterowanych po LAN
  - `name`: dowolna nazwa
  - `id` / `key` / `ip` / `version`: dane z `tinytuya wizard`
  - `dps_map`: numery DPS, typowo `{ power: 20, mode: 21, color: 24 }`
- `ftp`: Twoje FTP (W) do przeliczeń na %FTP
- `ble`:
  - `prefer`: `cps` (domyślne) lub `ftms`
  - `address`: MAC/UUID urządzenia (opcjonalnie)
  - `name_hint`: fragment nazwy urządzenia, by łatwo je znaleźć
- `smoothing`:
  - `window_seconds`: długość okna uśredniania (np. `0.25`)
  - `max_update_hz`: maks. częstotliwość aktualizacji (np. `10`)
- `mapping`:
  - `mode`: `zones` lub `gradient`
  - `colors_rgb`: nazwy kolorów i wartości [R,G,B]
  - `zones`: kolejno sprawdzane progi (pierwszy pasujący wygrywa)

Przykład (strefy podobne do Zwift):

```
mapping:
  mode: zones
  colors_rgb:
    white:  [255,255,255]
    blue:   [0,0,255]
    green:  [0,255,0]
    yellow: [255,255,0]
    orange: [255,64,0]
    red:    [255,0,0]
  zones:
    - up_to_pct: 61
      color: white
    - up_to_pct: 76
      color: blue
    - up_to_pct: 90
      color: green
    - up_to_pct: 105
      color: yellow
    - up_to_pct: 118
      color: orange
    - up_to_pct: null  # reszta (>=118%)
      color: red
```

---

## 🏗️ Architektura (DDD)

- `rgbapp/domain`: wartości i reguły domenowe
  - `color.py`: `rgb_to_hsv_deg`, `hsv_to_dp24`, `ZoneMapper`, `gradient_hsv`
  - `power.py`: `PowerSmoother`
- `rgbapp/application`: orkiestracja logiki domenowej
  - `mapping.py`: `ColorMappingService` (W → HSV)
  - `smoothing.py`: builder `PowerSmoother`
- `rgbapp/infrastructure`: adaptery IO
  - `ble.py`: skanowanie, wybór `CPS/FTMS`, `parse_cps/parse_ftms`
  - `tuya.py`: `TuyaLight` (DP24 + fallback HSV 0..255)
- `rgbapp/config`: wczytywanie i przetwarzanie konfiguracji
  - `models.py`: typowane modele (Pydantic)
  - `factory.py`: `load_app_config` (walidacja YAML → modele)
  - `loader.py`: `extract_zones` (wygodny ekstraktor stref)
- Wejście: `app/main.py`

---

## 🛠️ Wskazówki i rozwiązywanie problemów

- 🔌 Tuya LAN: urządzenie musi mieć Wi‑Fi i włączone sterowanie LAN (większość LSC/Tuya tak działa). BT‑Mesh nie zadziała.
- 🌐 Sieć: jeśli lampka nie reaguje, sprawdź IP w `config.yaml` i czy nie zmieniło się po restarcie routera.
- 🧪 DP24 vs. HSV: jeśli urządzenie nie wspiera DP24, używany jest automatycznie fallback `set_colour(0..255)`.
- 🛰️ BLE: gdy `name_hint` jest puste, skrypt spróbuje rozpoznać trenażer po nazwie (Kickr, Tacx, Elite, Zwift, Magene, Stages…).
- 🧯 Timeouty: jeśli BLE zrywa połączenie, spróbuj zbliżyć komputer/adapter BT i ograniczyć zakłócenia.

---

## 📦 Wymagania

```
bleak==0.22.3
tinytuya==1.12.9
pyyaml==6.0.2
pydantic>=2.0.0
```

---

## 🙌 Podziękowania

- Społeczność open‑source za `tinytuya` i `bleak` 💙
- Zwift i producenci trenażerów za wspieranie BLE CPS/FTMS 🚲

Miłego kręcenia i kolorowych interwałów! 🌈
