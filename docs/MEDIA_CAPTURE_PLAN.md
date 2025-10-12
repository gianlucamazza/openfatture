# OpenFatture Media Capture Plan · 2025 Edition

## 1. Objectives
- Document the key flows (setup, invoicing, AI, batch, PEC) with demo videos and screenshots aligned with the 2025 product state.
- Ensure outputs follow brand, accessibility, and media-production best practices.
- Make production repeatable (scripts, presets, checklists) for future updates.

## 2. Priority Video Scenarios
### Scenario A · Onboarding & Setup
- **Target duration:** 2:30
- **Goal:** show installation, `.env` configuration, database bootstrap.
- **Prerequisites:** clean `main`, demo environment with dummy credentials (`./scripts/reset_demo.sh`).
- **Script outline:**
  1. Intro (on-camera or voice-over, 3s animated logo).
  2. Repo clone, `uv sync`, `uv run openfatture init --no-interactive`.
  3. Copy `.env.example`, highlight mandatory fields.
  4. Run `openfatture config show`.
  5. Call to action: “Ready to create the first invoice”.
- **Screenshots:** `.env` editor, `openfatture config show` output.

### Scenario B · CLI Invoice Creation
- **Target duration:** 3:30
- **Goal:** generate a complete invoice and save it to XML.
- **Prerequisites:** database seeded with sample customer `ACME Srl`, product `Dev Services`.
- **Script outline:**
  1. `openfatture fattura crea --pdf`.
  2. Highlight field validation and tips.
  3. Save and preview XML (show snippet in VS Code).
  4. `openfatture fattura pdf 1 --template professional`.
  5. Reminder about document versioning.
- **Screenshots:** CLI wizard, XML preview, rendered PDF.

### Scenario C · AI Assistant & Automation
- **Target duration:** 2:45
- **Goal:** demo `openfatture -i` interactive mode + AI commands (`ai describe`, `ai suggest-vat`).
- **Prerequisites:** AI provider configured with mock or safe key, invoice dataset 2024/2025.
- **Script outline:**
  1. Launch interactive UI, open “AI Assistant”.
  2. Prompt example: “Create description for GDPR consulting”.
  3. Run `openfatture ai suggest-vat "GDPR consulting" --importo 1500 --categoria Consulting`.
  4. Close with benefits and privacy/dataset note.
- **Screenshots:** chat assistant output, CLI AI results.

### Scenario D · Batch Operations (Import/Export)
- **Target duration:** 2:15
- **Goal:** import customers/products via CSV and generate multiple invoices.
- **Prerequisites:** demo files `examples/batch/clients.csv`, `products.csv`, `invoices.csv`.
- **Script outline:**
  1. Present CSVs (zoom on key columns).
  2. `openfatture batch import examples/batch/invoices.csv --dry-run`.
  3. Full import (without `--dry-run`) showing summaries/errors.
  4. Show interactive dashboard (`openfatture interactive` → “Report & Analytics”).
- **Screenshots:** CSV in spreadsheet, dry-run vs applied output.

### Scenario E · PEC Delivery & SDI Notifications
- **Target duration:** 3:00
- **Goal:** illustrate optional signing, PEC delivery, and notification tracking.
- **Prerequisites:** demo `.p12` certificate, PEC test mailbox, simulated notifications in `/examples/sdi`.
- **Script outline:**
  1. `openfatture fattura invia 1 --pec` (mention digital signing step).
  2. Validate PEC configuration with `openfatture pec test`.
  3. Highlight template customisation (`docs/EMAIL_TEMPLATES.md`).
  4. Process notification `openfatture notifiche process examples/sdi/RC_IT12345678901_00001.xml`.
  5. Display invoice status with `openfatture fattura show 1`.
- **Screenshots:** PEC logs, email template, invoice status dashboard.

## 3. Standalone Screenshot Deliverables
- Format PNG at 2×, 2560 px long edge, sRGB colour profile.
- CLI layout: font size 18 pt, “Solarized Dark” or “One Dark” theme with clean background.
- Light annotations (semi-transparent rectangles) plus raw variant without overlays.
- Naming: `media/screenshots/v2025/<scenario>_<step>.png`.

## 4. Environment & Toolchain
- **Hardware:** Mac Studio / Linux workstation with 27" 1440p monitor.
- **Software:** OBS Studio 30+, preset `media/presets/OBS_OF-1440p60.json` (NVENC/Apple VT H.264, 18 Mbps; lossless master ProRes). iTerm2 (CLI), VS Code, Figma (annotations), DaVinci Resolve/FCPX (editing with preset `media/presets/resolve_of_timeline.yaml`), ffmpeg (batch export), WhisperX (subtitles).
- **Audio:** XLR mic + interface, high-pass filter at 80 Hz, compression ratio 2:1.
- **Brand assets:** logo SVG `docs/assets/logo.svg`, palette `#001f3f`, `#2ECC71`, `#FF851B`.

## 5. Production Workflow
1. **Pre-production:** approve scripts/storyboards, prep demo environment via `scripts/reset_demo.sh`.
2. **Capture:** record separate tracks (video, mic, system audio, cursor highlight).
3. **Editing:**
   - Import into NLE, sync tracks, create chapter markers for each step.
   - Add lower-thirds for key commands (`openfatture fattura crea`, etc.).
   - Light colour grading, audio denoise, final compression to -1 LUFS short-term.
4. **Accessibility:** generate transcript with WhisperX, review manually, export SRT/WEBVTT.
5. **QA:** checklist (section 7), technical review (dev lead) + brand review (design).
6. **Distribution:** export master ProRes + H.264 1080p, vertical 1080×1920 cut. Upload to CDN/YouTube (unlisted) → embed in docs.
7. **Versioning:** tag folder `media/v2025.1`, update `docs/QUICKSTART.md` and README with new links/screenshots.

## 6. Roles & Responsibilities
- **Producer:** planning, resource coordination.
- **Technical Host:** executes commands, maintains demo data consistency.
- **Narrator:** Italian/English voice-over based on approved script.
- **Editor:** editing, colour correction, multi-format export.
- **Accessibility Reviewer:** subtitles, contrast, narration pacing.
- **QA Lead:** signs off checklist before publication.

## 7. Quality Checklist
- **Content:** commands correct, outputs consistent, CLI/UI versions current (`openfatture --version` visible).
- **Visuals:** legible text, no flicker, tasteful zoom/overlays.
- **Audio:** -16 LUFS integrated, controlled dynamics, noise-free.
- **Accessibility:** synchronised subtitles, published transcript, descriptive callouts.
- **Branding:** intro/outro ≤4s, official logo/palette, scenario titles consistent.
- **Deliverables:** lossless master + compressed versions, 2× screenshots, metadata (title, description, chapters, tags).
- **Distribution:** README/docs links updated, assets stored with correct naming in shared storage.

## 8. Timeline Template (4-week sprint)
- **Week 1:** finalise scripts, OBS presets, environment setup.
- **Week 2:** primary recordings, screenshot capture.
- **Week 3:** editing, subtitles, QA iterations.
- **Week 4:** publishing, documentation updates, retrospective.

## 9. Continuous Maintenance
- Quarterly audit to ensure CLI/UI changes are reflected.
- Update assets on every minor release (`v0.x.y`): refresh affected scenario, regenerate videos/screenshots.
- Store source materials (NLE projects, OBS presets, demo datasets) under versioned `media/` directories.

## 10. Script Validation & Role Assignment (Reference: Feb 2025 Sprint)
- **Script reviews:** validated 3 Feb 2025 with Product, Backend, Content; log major updates in `docs/storyboards/`.
- **Scenario owners:** A → Product; B → Backend Guild; C → AI/ML; D → Operations; E → Compliance & PEC (see storyboard files for leads/backups).
- **Role matrix:** Producer, Technical Host, Narrator, Editor, Accessibility Reviewer, QA Lead (assign primary + backup per sprint).
- **Change control:** storyboard updates >3 modifications require cross-approval (Producer + QA Lead) before capture.
- **Operational channels:** Slack `#openfatture-media` for daily comms; Linear board `MED-2025` for tracking.
- **Scheduling:** detailed calendar maintained in `docs/MEDIA_PRODUCTION_SCHEDULE.md` (updated daily by the Producer).
