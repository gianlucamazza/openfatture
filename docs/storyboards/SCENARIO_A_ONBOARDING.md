# Scenario A · Onboarding & Setup (Storyboard)

**Versione:** v2025.02.03
**Owner:** Product Team (lead: Gianluca Mazza)
**Durata target:** 2'30" ± 10s

## Sequenza Shot
| # | Durata | Video | Audio/VO | Overlay/Note |
|---|--------|-------|----------|--------------|
| 1 | 0:04 | Logo animato + titolo "Setup OpenFatture" | SFX intro breve | Paletta brand, lower third neutro |
| 2 | 0:12 | Speaker on cam (Mezzobusto) | "Benvenuto, oggi configuriamo OpenFatture in meno di 3 minuti" | CTA grafico "Step 1/4" |
| 3 | 0:18 | Terminale: `git clone` + `uv sync` | Spiega prerequisiti e clonazione repo | Highlight CLI + callout scorciatoia |
| 4 | 0:15 | Terminale: `uv run openfatture init --no-interactive` | "Inizializziamo il database con un comando" | Overlay comando in lower third |
| 5 | 0:22 | Editor testo con `.env.demo` | "Copiamo la configurazione demo e aggiorniamo i dati obbligatori" | Zoom campi P.IVA, PEC |
| 6 | 0:18 | Terminale: `./scripts/reset_demo.sh` | "Lo script demo prepara clienti, prodotti e fatture" | Mostrare output ✅ |
| 7 | 0:20 | Terminale: `uv run openfatture config show` | "Verifichiamo che tutto sia operativo" | Badge "All systems go" |
| 8 | 0:12 | Slide riepilogo | "Siamo pronti per creare la prima fattura" | CTA verso scenario B |
| 9 | 0:09 | Outro con logo | "Scopri gli altri capitoli" | Link docs + QR |

## Note Produzione
- **B-roll**: riprese tastiera + mouse (opzionali per versioni social).
- **Screen capture**: usare preset OBS `OpenFatture 1440p60`.
- **Capture audio**: microfono SM7B → loopback; tracce separate.
- **Callout**: utilizzare stile Figma `OF_Callout_2025`.
- **Ritmo**: mantenere 130 wpm, lasciare 0.5s di respiro tra step.

## Asset Necessari
- `.env.demo` (incluso nel repo) + script `scripts/reset_demo.sh`.
- Database demo generato (verifica output script prima della registrazione).
- Lower third "Step 1/4" + CTA slide Figma (link nel board Linear).
- Musica background "OF_CalmBeat_v1.wav" (-22 LUFS, loop 3 min).

## Checklist Pre-shoot
- [ ] Aggiornare repo `main` + eseguire `uv sync`.
- [ ] Confermare versione CLI (`openfatture --version` → 0.2.0-rc1).
- [ ] Lanciare `./scripts/reset_demo.sh` e verificare messaggio ✅.
- [ ] Aprire template lower third in Figma per eventuali modifiche.
- [ ] Test audio (noise gate -55 dB, compressore 3:1, limiter -1 dB).
- [ ] Caricare scena OBS "CLI Capture" e verificare crop terminale.

## Post-produzione
- Marker timeline Resolve: Intro (0:00), Setup (0:20), Env (1:00), Demo script (1:35), Recap (2:10).
- Inserire sottotitoli IT (auto + revisione manuale) e localizzazione EN successiva.
- Export: Master ProRes + H.264 1080p (bitrate 18 Mbps) + verticale 60s highlight Step 3-7.
