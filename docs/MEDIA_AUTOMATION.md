# Automazione Video & Screenshot (2025)

> Obiettivo: ridurre al minimo la cattura manuale per gli scenari demo, mantenendo qualità e coerenza con il piano media.

## 1. Overview
- **Terminal/CLI** → automatizzabile tramite script di input + registratori headless (es. `vhs`, `terminalizer`, `agg`).
- **Screenshot GUI/Docs** → generabili con browser automation (Playwright) e template Figma API.
- **Voice-over e human touch** → restano manuali (o TTS controllato) per mantenere tono coerente.
- **Post-produzione** → pipeline scriptata (`ffmpeg`, `whisperx`), con controlli QA finali.

## 2. Stack Consigliato
| Area | Tool | Note |
|------|------|------|
| Terminal Recording | [`vhs`](https://github.com/charmbracelet/vhs) | Genera mp4/gif da script `.tape`; gestisce tema, font, dimensioni. |
| CLI Storyboard | `media/automation/*.tape` | Script scenario-driven con commenti; includono `Sleep`, `Type`, `Enter`. |
| Browser Screenshots | [Playwright](https://playwright.dev/python/) (`scripts/capture_docs.py`) | Rendering docs/CLI web (es. HTML export) a risoluzione 2×. |
| Video Post | `ffmpeg`, `ffmpeg-normalize`, `python -m whisperx` | Composizione, normalizzazione audio, generazione sottotitoli. |
| Asset Sync | `make media` (da introdurre) | Orchestratore per sequenza reset → capture → export. |

## 3. Pipeline Automatica (Scenario CLI)
1. `./scripts/reset_demo.sh` → dataset deterministico.
2. `vhs media/automation/scenario_a_onboarding.tape` → `media/output/scenario_a.mp4`.
3. `ffmpeg` overlay callout statici o lower-third (preset in `media/overlays/`).
4. `whisperx --model medium.it` per bozza sottotitoli (se VO registrata).
5. QA: confronto con storyboard e checklist, eventuale registrazione manuale dei segmenti mancanti.

## 4. Pipeline Screenshot
1. `uv run playwright install chromium` (una tantum).
2. `uv run python scripts/capture_screenshots.py --scenario A`:
   - esegue comandi CLI e salva output come testo.
   - Renderizza HTML con highlight e cattura PNG 2560×1440.
   - Per GUI/doc: apre URL local (`mkdocs serve` o file statico) e scatta screenshot sezioni selezionate.
3. Output in `media/screenshots/v2025/*.png` + JSON metadata (timestamp, comando, file origine).

## 5. Esempi Script
- `media/automation/scenario_a_onboarding.tape` → scenario A (setup) totalmente scriptato.
- `media/automation/templates/common.tapeinc` → snippet riutilizzabili (clear, prompt, helper).
- `scripts/capture_screenshots.py` → definisce scenari CLI screenshot + fallback manuale.

> ⚠️ L’esecuzione degli script deve avvenire in ambiente pulito (`git status` pulito, DB demo). Ogni modifica ai comandi va riflessa nello storyboard e nei test automatici (`tests/services/test_media_automation.py`, da creare).

## 6. Limiti & Mitigazioni
- **Latency/Prompt**: alcuni comandi (es. AI) richiedono input manuale o API key reali → usare flag `--mock` o environ `AI_MOCK_MODE=1` per output deterministici.
- **Rendering Terminal Fonts**: `vhs` usa font di sistema; configurare `Set FontFamily "JetBrains Mono"` per coerenza. Se non installato → fallback a `Menlo`.
- **Aggiornamenti CLI**: dopo ogni release, rigenerare video con pipeline e confrontare CRC.

## 7. Roadmap Automazione
- [ ] Aggiungere workflow `make media-scenarioA` che esegue sequenza completa.
- [ ] Introdurre test snapshot sugli output (immagini diff via `pixelmatch`).
- [ ] Collegare pipeline a GitHub Actions (nightly) per verificare che gli script restino validi (solo dry-run, senza esport video).
- [ ] Estendere a scenari B-E con modularizzazione tape (inclusione passi comuni: login AI, export pdf XML).

Per ulteriori dettagli, vedere `media/automation/README.md` e gli script nella stessa directory. In caso di modifica della CLI che rompa gli script, aprire task su board Linear `MED-2025` con label `automation`.
