# Preset media OpenFatture 2025

- `OBS_OF-1440p60.json`: preset OBS Studio per registrazioni 2560×1440@60fps con mastering ProRes.
- `resolve_of_timeline.yaml`: preset DaVinci Resolve per timeline UHD con export multipli.

Import istruzioni:
1. OBS → Profilo > Importa, seleziona JSON.
2. Resolve → Project Manager > Presets > Importa, seleziona YAML (convertito via script `scripts/resolve_import.py` se necessario).

Aggiorna versione nel nome file quando modifichi parametri chiave (bitrate, fps, color space).
