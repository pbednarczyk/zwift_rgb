# 🚀 Uruchamianie aplikacji - Poradnik

Stworzyłem kilka sposobów na łatwe uruchamianie aplikacji bez ręcznego wpisywania komend:

---

## **Option 1: Shortcut na pulpicie** ⭐ (Najłatwiej!)

### Krok 1 - Jedno kliknięcie:
```
SETUP-DESKTOP-SHORTCUT.bat
```

Uruchom ten plik z katalogu projektu **jeden raz** - stworzył ci shortcut na pulpicie.

### Krok 2 - Od teraz:
Po prostu kliknięcie ikonki 🚴 na pulpicie = aplikacja startuje!

---

## **Option 2: Bezpośrednie uruchomienie w terminalu**

Jeśli wolisz terminal z ładnym UI, uruchom:
```
RUN.ps1
```

(wymaga PowerShell, więcej informacji niż batch)

---

## **Option 3: Cichy batch file**

Jeśli chcesz klassęć batch file:
```
RUN.bat
```

Lub ukryty (bez widocznego okna terminalu):
```
RUN-SILENT.vbs
```

---

## 📋 Podsumowanie plików:

| Plik | Zastosowanie | Pokazuje terminal? |
|------|--------------|-------------------|
| `RUN.bat` | Prosty, standardowy | TAK ✓ |
| `RUN.ps1` | Ładny UI, więcej info | TAK ✓ |
| `RUN-SILENT.vbs` | Cichy start | NIE |
| `SETUP-DESKTOP-SHORTCUT.bat` | Tworzy shortcut na pulpicie | TAK (jedno-czasowo) |

---

## 🛠️ Setup - Pierwsze uruchomienie:

1. **Otwórz PowerShell w katalogu projektu**
2. **Uruchom:**
   ```powershell
   SETUP-DESKTOP-SHORTCUT.bat
   ```
3. **Gotowe!** - Teraz masz shortcut na pulpicie

---

## 💡 Zaawansowane: Jeśli chcesz customize'ować...

Edytuj dowolny z tych plików:
- `RUN.bat` - zmień komunikaty, dodaj logowanie
- `RUN.ps1` - dokładnie dostosuj output, kolory, zachowanie
- `RUN-SILENT.vbs` - zmień `0` na `1` w ostatniej linii aby pokazać okno

---

## ❓ FAQ

**P: Aplikacja po starcie od razu się wyłącza?**
- Sprawdź czy `config.yaml` jest prawidłowo skonfigurowany
- Sprawdź BLE device i Tuya devices w configu

**P: Mogę kliknąć shortcut zaraz po instalacji?**
- Tak! Skrypt automatycznie:
  1. Zmienia katalog
  2. Aktywuje `.venv`
  3. Uruchamia `app.main`

**P: Shortcut nie działa?**
- Usuń go z pulpitu i uruchom `SETUP-DESKTOP-SHORTCUT.bat` jeszcze raz

---

**Enjoy! 🎉**
