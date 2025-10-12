# Scenario A · Onboarding & Setup (Storyboard)

**Version:** v2025.02.03
**Owner:** Product Team (lead: Gianluca Mazza)
**Target duration:** 2'30" ± 10s

## Shot Sequence
| # | Length | Video | Audio/VO | Overlay/Notes |
|---|--------|-------|----------|---------------|
| 1 | 0:04 | Animated logo + title “OpenFatture Setup” | Short intro SFX | Brand palette |
| 2 | 0:12 | Speaker on camera | “Welcome, let's configure OpenFatture in under three minutes” | CTA graphic “Step 1/4” |
| 3 | 0:18 | Terminal: `git clone` + `uv sync` | Explain prerequisites and repo clone | Highlight terminal + shortcut callout |
| 4 | 0:15 | Terminal: `uv run openfatture init --no-interactive` | “Initialise the database in one command” | Command overlay in lower-third |
| 5 | 0:22 | Text editor with `.env.example` | “Copy the demo config and update mandatory fields” | Zoom on VAT, PEC fields |
| 6 | 0:18 | Terminal: `./scripts/reset_demo.sh` | “The demo script prepares customers, products, invoices” | Show ✅ output |
| 7 | 0:20 | Terminal: `uv run openfatture config show` | “Verify everything is ready” | Badge “All systems go” |
| 8 | 0:12 | Recap slide | “We’re ready to create the first invoice” | CTA to Scenario B |
| 9 | 0:09 | Outro with logo | “Explore the next chapters” | Docs link + QR code |

## Production Notes
- **B-roll:** optional keyboard/mouse shots for social edits.
- **Screen capture:** use OBS preset `OpenFatture 1440p60`.
- **Audio capture:** SM7B → Loopback; separate tracks.
- **Callouts:** use Figma style `OF_Callout_2025`.
- **Pacing:** keep 130 wpm, add 0.5 s pause between steps.

## Required Assets
- `.env.example` + script `scripts/reset_demo.sh`.
- Demo database (run script before recording).
- Lower-third “Step 1/4” + CTA slide (Figma board in Linear).
- Background music “OF_CalmBeat_v1.wav” (-22 LUFS, loop 3 min).

## Pre-Shoot Checklist
- [ ] Update repo to `main` + run `uv sync`.
- [ ] Confirm CLI version (`openfatture --version` → 1.0.0).
- [ ] Run `./scripts/reset_demo.sh` and confirm ✅ message.
- [ ] Open lower-third template in Figma for adjustments.
- [ ] Test audio (noise gate -55 dB, compressor 3:1, limiter -1 dB).
- [ ] Load OBS scene “CLI Capture” and verify terminal crop.

## Post-Production
- Resolve markers: Intro (0:00), Setup (0:20), `.env` (1:00), Demo script (1:35), Recap (2:10).
- Generate Italian subtitles (auto + manual review) and prepare English localisation.
- Export: Master ProRes + H.264 1080p (18 Mbps) + vertical 60s highlight (Steps 3-7).
