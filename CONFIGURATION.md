# Local configuration

This project intentionally does not track `config.yaml`.

`config.yaml` contains local Tuya device identifiers, local keys, IP addresses, and BLE device hints. Treat it as a machine-local secret file.

## Setup

1. Copy `config.example.yaml` to `config.yaml`.
2. Fill in local Tuya values from `python -m tinytuya wizard`.
3. Adjust BLE and mapping settings for this machine.

PowerShell:

```powershell
Copy-Item config.example.yaml config.yaml
```

## Git rules

- Commit `config.example.yaml`.
- Do not commit `config.yaml`.
- Do not commit `.env` files.

If real Tuya keys were already pushed to a shared repository, rotate the Tuya local keys or recreate/re-pair the devices. Removing the file from the current commit prevents future exposure, but it does not erase secrets from existing Git history.
