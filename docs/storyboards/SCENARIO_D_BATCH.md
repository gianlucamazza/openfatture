# Scenario D · Batch Operations (Storyboard)

**Version:** v2025.02.03
**Owner:** Operations Team (lead: Marco Greco)
**Target duration:** 2'15" ± 10s

## Shot Sequence
| # | Length | Video | Audio/VO | Overlay/Notes |
|---|--------|-------|----------|---------------|
| 1 | 0:04 | Animated logo + title “Batch Import & Export” | Intro SFX | Brand palette |
| 2 | 0:12 | Speaker on camera | “Automate CSV imports and exports with the OpenFatture CLI” | CTA “Step 1/4” |
| 3 | 0:18 | Spreadsheet view of CSV files | “Prepare customer and invoice CSV templates” | Zoom on mandatory columns |
| 4 | 0:20 | Terminal: `openfatture batch import ... --dry-run` | “Run a dry-run to validate the file” | Highlight dry-run summary |
| 5 | 0:25 | Terminal: `openfatture batch import ...` | “Apply the import and review the results” | Display success/failure counters |
| 6 | 0:18 | Terminal: `openfatture batch export export_2025.csv --anno 2025` | “Export invoices for BI/Excel analysis” | Show output path |
| 7 | 0:18 | TUI dashboard (report section) | “Visualise KPIs in the interactive dashboard” | Focus on charts/metrics |
| 8 | 0:12 | Summary slide | “Dry-run → import → verify → export” | Reminder to keep CSV backup |
| 9 | 0:08 | Outro | “Scenario E: PEC & SDI notifications” | Link to Scenario E |

## Production Notes
- **CSV assets:** `examples/batch/clients.csv`, `products.csv`, `invoices.csv`.
- **Demo data:** run `scripts/reset_demo.sh` to reset state.
- **Screen capture:** split-screen for spreadsheet + terminal segments.
- **Validation:** emphasise error handling and email summary option.

## Required Assets
- CSV templates with realistic values.
- CLI output showing dry-run vs applied import.
- Exported CSV opened in spreadsheet app.
- Dashboard screenshot from interactive mode.

## Pre-Shoot Checklist
- [ ] Update CSV samples to reflect latest schema.
- [ ] Run dry-run/import commands and capture outputs.
- [ ] Verify exported file opens correctly (UTF-8, comma-separated).
- [ ] Prep TUI dashboard with relevant metrics.
- [ ] Set OBS scenes for spreadsheet and terminal capture.

## Post-Production
- Insert callouts for command syntax and optional flags.
- Add note about email summaries (requires `NOTIFICATION_EMAIL`).
- Export master + H.264 + vertical snippet focusing on dry-run vs import.
