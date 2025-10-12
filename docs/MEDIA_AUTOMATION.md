# Media Automation (2025)

> Goal: minimise manual capture for demo scenarios while keeping quality aligned with the media plan.

## 1. Overview
- **Terminal/CLI** → scriptable via input scripts + headless recorders (e.g. `vhs`, `terminalizer`, `agg`).
- **Screenshots (GUI/docs)** → generated with browser automation (Playwright) and Figma API templates.
- **Voice-over / human touch** → kept manual (or curated TTS) to preserve tone.
- **Post-production** → scripted pipeline (`ffmpeg`, `whisperx`) followed by final QA.

## 2. Recommended Stack
| Area | Tool | Notes |
|------|------|-------|
| Terminal recording | [`vhs`](https://github.com/charmbracelet/vhs) | Generates mp4/gif from `.tape` scripts; handles theme, font, size. |
| CLI storyboard | `media/automation/*.tape` | Scenario-driven scripts with comments; include `Sleep`, `Type`, `Enter`. |
| Browser screenshots | [Playwright](https://playwright.dev/python/) (`scripts/capture_screenshots.py`) | Renders docs/CLI HTML (e.g. static pages) at 2× resolution. |
| Video post | `ffmpeg`, `ffmpeg-normalize`, `python -m whisperx` | Composition, audio normalisation, subtitle generation. |
| Asset orchestration | `make media-*` targets | Resets demo environment → capture → export in sequence.

## 3. Automated CLI Scenario Pipeline
1. `./scripts/reset_demo.sh` → deterministic dataset.
2. `vhs media/automation/scenario_a_onboarding.tape` → `media/output/scenario_a.mp4`.
3. `ffmpeg` overlays for callouts/lower-thirds (presets in `media/overlays/`).
4. `whisperx --model medium.it` for draft subtitles (if voice-over recorded).
5. QA: compare with storyboard and checklist, re-record missing segments manually if needed.

## 4. Screenshot Pipeline
1. `uv run playwright install chromium` (one-time).
2. `uv run python scripts/capture_screenshots.py --scenario A`:
   - Runs CLI commands and stores raw output.
   - Renders HTML with syntax highlighting and captures 2560×1440 PNGs.
   - For GUI/docs: opens local URL (`mkdocs serve` or static files) and snaps selected sections.
3. Output stored under `media/screenshots/v2025/*.png` with JSON metadata (timestamp, command, source file).

## 5. Script Examples
- `media/automation/scenario_a_onboarding.tape` → fully scripted onboarding scenario.
- `media/automation/templates/common.tapeinc` → reusable snippets (clear, prompt, helpers).
- `scripts/capture_screenshots.py` → defines CLI screenshot scenarios + manual fallback.

> ⚠️ Run automation in a clean workspace (`git status` clean, demo DB). Every CLI change must be reflected in the storyboard and automated tests (`tests/services/test_media_automation.py`, planned).

## 6. Limitations & Mitigations
- **Latency/prompts:** certain commands (e.g. AI) need manual input or real API keys → use `--mock` or `AI_MOCK_MODE=1` for deterministic output.
- **Terminal font rendering:** `vhs` uses system fonts; configure `Set FontFamily "JetBrains Mono"` for consistency. If missing → fall back to `Menlo`.
- **CLI updates:** regenerate videos after each release and compare checksums.

## 7. Automation Roadmap
- [ ] Add workflow `make media-scenarioA` chaining the full pipeline.
- [ ] Introduce snapshot tests for outputs (image diffs via `pixelmatch`).
- [ ] Wire a GitHub Actions workflow (nightly dry-run) to ensure scripts remain valid.
- [ ] Extend coverage to scenarios B–E with modular tape inclusions (shared steps: AI login, PDF/XML export).

For more detail, consult `media/automation/README.md` and the scripts in the same directory. When CLI changes break scripts, open a task on the Linear board `MED-2025` with the label `automation`.
