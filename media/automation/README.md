# Automazione Media OpenFatture

## Setup Completo

### 1. Installazione Tools
Usa il Makefile per installare automaticamente tutti i tools necessari:
```bash
make media-install
```

Oppure installazione manuale:
```bash
# VHS per registrazione terminale
brew install charmbracelet/tap/vhs

# ffmpeg per post-processing video
brew install ffmpeg

# Ollama per AI locale (opzionale ma raccomandato per Scenario C)
brew install ollama
ollama pull llama3.2
```

### 2. Configurazione Ollama (AI Locale)
Per demo deterministiche senza costi API, usiamo **Ollama locale**:

```bash
# Verifica installazione e avvio servizio
ollama serve  # Avvia server (porta 11434)

# In altro terminale: pull modello
ollama pull llama3.2

# Test health check
./scripts/check_ollama.sh llama3.2
```

✅ **Vantaggi Ollama**:
- 🆓 Zero costi API (vs Anthropic/OpenAI)
- 🔒 Privacy-first: dati mai condivisi con cloud
- 📦 Deterministico: risposte consistenti per demo
- ⚡ Veloce su Apple Silicon M1/M2/M3

### 3. Configurazione Environment
Il file `.env.demo` è già configurato per Ollama:

```bash
# Copia configurazione demo
cp .env.demo .env

# Verifica variabili AI
grep AI_ .env
# Output:
# AI_PROVIDER=ollama
# AI_MODEL=llama3.2
# OPENFATTURE_AI_OLLAMA_BASE_URL=http://localhost:11434
```

---

## Workflow Automazione

### Quick Start - Genera Scenario Singolo
```bash
# Scenario A: Onboarding & Setup
make media-scenarioA

# Output: media/output/scenario_a_onboarding.mp4
```

### Genera Tutti gli Scenari
```bash
make media-all

# Genera tutti i 5 scenari:
# - Scenario A: Onboarding (2'30")
# - Scenario B: Invoice Creation (3'30")
# - Scenario C: AI Assistant con Ollama (2'45")
# - Scenario D: Batch Operations (2'15")
# - Scenario E: PEC & SDI (3'00")
```

### Cattura Screenshot
```bash
# Tutti gli scenari
make media-screenshots

# Scenario specifico
uv run python scripts/capture_screenshots.py --scenario A

# Output: media/screenshots/v2025/*.txt + *.json
```

---

## Scenari Disponibili

| Tape | Durata | Descrizione | Storyboard |
|------|--------|-------------|------------|
| `scenario_a_onboarding.tape` | 2'30" | Setup, config, inizializzazione | [SCENARIO_A](../../docs/storyboards/SCENARIO_A_ONBOARDING.md) |
| `scenario_b_invoice.tape` | 3'30" | Creazione fattura completa | [SCENARIO_B](../../docs/storyboards/SCENARIO_B_INVOICE.md) |
| `scenario_c_ai.tape` | 2'45" | AI Assistant con Ollama locale | [SCENARIO_C](../../docs/storyboards/SCENARIO_C_AI.md) |
| `scenario_d_batch.tape` | 2'15" | Operazioni batch import/export | [SCENARIO_D](../../docs/storyboards/SCENARIO_D_BATCH.md) |
| `scenario_e_pec.tape` | 3'00" | Invio PEC e notifiche SDI | [SCENARIO_E](../../docs/storyboards/SCENARIO_E_PEC.md) |

---

## Struttura File

```
media/
├── automation/
│   ├── README.md                     # Questo file
│   ├── templates/
│   │   └── common.tapeinc            # Snippet riutilizzabili
│   ├── scenario_a_onboarding.tape
│   ├── scenario_b_invoice.tape
│   ├── scenario_c_ai.tape
│   ├── scenario_d_batch.tape
│   └── scenario_e_pec.tape
├── output/                            # Video MP4 generati
│   ├── scenario_a_onboarding.mp4
│   └── ...
├── screenshots/
│   └── v2025/                         # Screenshot + metadata JSON
└── presets/                           # Preset OBS, Resolve, ffmpeg
```

---

## Comandi Makefile Disponibili

```bash
make media-install      # Installa tools (VHS, ffmpeg)
make media-check        # Verifica Ollama e prerequisites
make media-reset        # Reset DB demo con Ollama config
make media-scenarioA    # Genera video Scenario A
make media-scenarioB    # Genera video Scenario B
make media-scenarioC    # Genera video Scenario C (AI)
make media-scenarioD    # Genera video Scenario D (Batch)
make media-scenarioE    # Genera video Scenario E (PEC)
make media-all          # Genera TUTTI i video
make media-screenshots  # Cattura screenshot testuali
make media-clean        # Pulisce output video/screenshot
```

---

## Troubleshooting

### VHS: Theme non trovato
**Errore**: `invalid Set Theme "Solarized Dark": theme does not exist`

**Fix**: Usa tema supportato da VHS:
```
Set Theme "Dracula"  # ✅ Supportato
```

### Ollama: Servizio non risponde
**Errore**: `Ollama service is not responding`

**Fix**:
```bash
# Avvia servizio Ollama
ollama serve

# In background (macOS)
brew services start ollama
```

### Ollama: Modello non trovato
**Errore**: `Model 'llama3.2' not found`

**Fix**:
```bash
ollama pull llama3.2
# Oppure usa un modello già scaricato
ollama list
```

### Comandi CLI mancanti
**Errore**: `uv run openfatture status: command not found`

**Fix**: Usa comandi esistenti (vedi `openfatture --help`)
```bash
# ❌ openfatture status (non esiste)
# ✅ openfatture config show
```

---

## Best Practices

1. **Reset DB prima di ogni registrazione**:
   ```bash
   ./scripts/reset_demo.sh
   ```

2. **Usa Ollama per Scenario C**:
   - Deterministico per demo ripetibili
   - Privacy-first (no cloud API)
   - Zero costi

3. **Verifica output video**:
   ```bash
   ls -lh media/output/*.mp4
   file media/output/scenario_a_onboarding.mp4
   ```

4. **Timing VHS**:
   - Comandi veloci: `Sleep 800ms - 1.5s`
   - AI inference: `Sleep 3s - 5s`
   - Reset demo: `Sleep 8s`

---

## Contatti & Support

- **Owner Automation**: Marco Greco (`@marco.greco`)
- **Board Linear**: `MED-2025` ([Link](https://linear.app/openfatture/team/med))
- **Slack Channel**: `#openfatture-media`
- **Docs Completi**: [MEDIA_AUTOMATION.md](../../docs/MEDIA_AUTOMATION.md)

---

## Roadmap Future

- [ ] Playwright rendering HTML per screenshot visuali
- [ ] Template ffmpeg per overlay lower-third automatici
- [ ] CI/CD: nightly run per validare tape sempre aggiornati
- [ ] Support multi-lingua (IT/EN) con variabili LOCALE

Per feature request: aprire issue su GitHub con label `media-automation`.
