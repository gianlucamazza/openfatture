# OpenFatture Media Automation

## Complete Setup

### 1. Install Tools
Use the Makefile to install everything automatically:
```bash
make media-install
```

Manual installation:
```bash
# VHS for terminal recording
brew install charmbracelet/tap/vhs

# ffmpeg for video post-processing
brew install ffmpeg

# Ollama for local AI (optional, recommended for Scenario C)
brew install ollama
ollama pull llama3.2
```

### 2. Configure Ollama (Local AI)
For deterministic demos without API costs, run **Ollama locally**:

```bash
# Check installation and start the service
ollama serve  # Default port 11434

# Pull the model in a separate terminal
ollama pull llama3.2

# Health check script
./scripts/check_ollama.sh llama3.2
```

✅ **Why Ollama**
- 🆓 Zero API costs (vs Anthropic/OpenAI)
- 🔒 Privacy-first: no data leaves your machine
- 📦 Deterministic responses for demos
- ⚡ Fast on Apple Silicon M1/M2/M3

### 3. Environment Configuration
`.env.demo` is preconfigured for Ollama:

```bash
# Copy demo configuration
cp .env.demo .env

# Verify AI variables
grep AI_ .env
# Output:
# AI_PROVIDER=ollama
# AI_MODEL=llama3.2
# OPENFATTURE_AI_OLLAMA_BASE_URL=http://localhost:11434
```

---

## Automation Workflow

### Quick Start – Single Scenario
```bash
# Scenario A: Onboarding & Setup
make media-scenarioA

# Output: media/output/scenario_a_onboarding.mp4
```

### Generate All Scenarios
```bash
make media-all

# Generates all five scenarios:
# - Scenario A: Onboarding (2'30")
# - Scenario B: Invoice Creation (3'30")
# - Scenario C: AI Assistant with Ollama (2'45")
# - Scenario D: Batch Operations (2'15")
# - Scenario E: PEC & SDI (3'00")
```

### Capture Screenshots
```bash
# All scenarios
make media-screenshots

# Specific scenario
uv run python scripts/capture_screenshots.py --scenario A

# Output: media/screenshots/v2025/*.png + *.json
```

---

## Available Scenarios

| Tape | Duration | Description | Storyboard |
|------|----------|-------------|------------|
| `scenario_a_onboarding.tape` | 2'30" | Setup, configuration, initialisation | [SCENARIO_A](../../docs/storyboards/SCENARIO_A_ONBOARDING.md) |
| `scenario_b_invoice.tape` | 3'30" | Full invoice creation | [SCENARIO_B](../../docs/storyboards/SCENARIO_B_INVOICE.md) |
| `scenario_c_ai.tape` | 2'45" | AI Assistant with local Ollama | [SCENARIO_C](../../docs/storyboards/SCENARIO_C_AI.md) |
| `scenario_d_batch.tape` | 2'15" | Batch import/export operations | [SCENARIO_D](../../docs/storyboards/SCENARIO_D_BATCH.md) |
| `scenario_e_pec.tape` | 3'00" | PEC delivery and SDI notifications | [SCENARIO_E](../../docs/storyboards/SCENARIO_E_PEC.md) |

---

## Directory Layout

```
media/
├── automation/
│   ├── README.md                     # This file
│   ├── templates/
│   │   └── common.tapeinc            # Reusable snippets
│   ├── scenario_a_onboarding.tape
│   ├── scenario_b_invoice.tape
│   ├── scenario_c_ai.tape
│   ├── scenario_d_batch.tape
│   └── scenario_e_pec.tape
├── output/                            # Generated MP4 videos
│   ├── scenario_a_onboarding.mp4
│   └── ...
├── screenshots/
│   └── v2025/                         # Screenshots + JSON metadata
└── presets/                           # OBS, Resolve, ffmpeg presets
```

---

## Makefile Commands

```bash
make media-install      # Install tools (VHS, ffmpeg)
make media-check        # Verify Ollama and prerequisites
make media-reset        # Reset demo DB with Ollama config
make media-scenarioA    # Generate Scenario A video
make media-scenarioB    # Generate Scenario B video
make media-scenarioC    # Generate Scenario C (AI) video
make media-scenarioD    # Generate Scenario D (Batch) video
make media-scenarioE    # Generate Scenario E (PEC) video
make media-all          # Generate all videos
make media-screenshots  # Capture screenshots
make media-clean        # Clean generated media
```

---

## Troubleshooting

### VHS: Theme Not Found
**Error:** `invalid Set Theme "Solarized Dark": theme does not exist`

**Fix:** use a supported theme:
```
Set Theme "Dracula"  # ✅ Supported
```

### Ollama: Service Not Responding
**Error:** `Ollama service is not responding`

**Fixes:**
- Ensure `ollama serve` is running.
- Confirm the model has been pulled (`ollama pull llama3.2`).
- Check firewall/network settings for port 11434.
- Re-run `./scripts/check_ollama.sh llama3.2`.
