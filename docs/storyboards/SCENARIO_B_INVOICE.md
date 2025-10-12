# Scenario B · CLI Invoice Creation (Storyboard)

**Version:** v2025.02.03
**Owner:** Backend Guild (lead: Davide Ricci)
**Target duration:** 3'30" ± 10s

## Shot Sequence
| # | Length | Video | Audio/VO | Overlay/Notes |
|---|--------|-------|----------|---------------|
| 1 | 0:04 | Animated logo + title “Electronic Invoicing” | Short intro SFX | Brand palette |
| 2 | 0:15 | Speaker on camera | “Let’s create a complete electronic invoice from the CLI” | CTA “Step 1/5” |
| 3 | 0:20 | Terminal: `openfatture cliente list` | “Check available customers” | Highlight customer rows |
| 4 | 0:25 | Terminal: `openfatture fattura crea --interactive` | “Use the guided wizard to fill the invoice” | Zoom on validation prompts |
| 5 | 0:30 | Filling invoice data (customer, date, notes) | “Select the customer and set the main parameters” | Callout mandatory fields |
| 6 | 0:35 | Adding invoice lines (services, quantity, VAT) | “Add services/products with automatic VAT calculation” | Lower-third showing VAT calc |
| 7 | 0:20 | Summary screen | “Review totals: taxable, VAT, grand total” | Validation badge |
| 8 | 0:25 | Terminal: `openfatture fattura xml 1` | “Generate SDI-compliant FatturaPA XML” | Preview XML structure |
| 9 | 0:25 | Terminal: `openfatture fattura pdf 1 --template professional` | “Produce the PDF for the client” | Zoom on rendered PDF |
|10 | 0:11 | Outro + CTA | “Next: AI Assistant and automations” | Link to Scenario C |

## Production Notes
- **Dataset:** use demo customer “ACME Innovazione S.r.l.” preloaded.
- **Products:** “GDPR Consulting” + “Backend API Development”.
- **Output:** invoice 2025-004 (avoid conflicts with demo seed).
- **Screen capture:** OBS standard preset, full-screen terminal.
- **Callouts:** highlight field validation (VAT number, SDI code).

## Required Assets
- Demo database (`./scripts/reset_demo.sh`).
- “Professional” PDF template validated.
- Sample XML snippet to display in editor (VS Code with syntax highlight).
- Lower-third callout “VAT 22% Calculation”.

## Pre-Shoot Checklist
- [ ] Run `./scripts/reset_demo.sh` and ensure three customers exist.
- [ ] Test wizard `openfatture fattura crea --interactive` manually.
- [ ] Validate XML output with FatturaPA validator.
- [ ] Test PDF generation with the “professional” template.
- [ ] Prepare Resolve markers: Intro, Customer list, Wizard, Lines, XML, PDF, Outro.

## Post-Production
- Timeline markers: Intro (0:00), Customers (0:20), Wizard (0:55), Lines (1:30), XML (2:30), PDF (2:55), Outro (3:20).
- Add Italian subtitles (auto + manual review) and English localisation.
- Exports: Master ProRes + H.264 1080p + vertical 60s highlight (Steps 4-7).
