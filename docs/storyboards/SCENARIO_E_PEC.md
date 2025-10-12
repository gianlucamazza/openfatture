# Scenario E · PEC & SDI Notifications (Storyboard)

**Version:** v2025.02.03
**Owner:** Compliance & PEC Team (lead: Chiara Lombardi)
**Target duration:** 3'00" ± 10s

## Shot Sequence
| # | Length | Video | Audio/VO | Overlay/Notes |
|---|--------|-------|----------|---------------|
| 1 | 0:04 | Animated logo + title “PEC & SDI Workflow” | Intro SFX | Brand palette |
| 2 | 0:14 | Speaker on camera | “Send invoices via PEC and track SDI notifications automatically” | CTA “Step 1/5” |
| 3 | 0:20 | Terminal: `openfatture pec test` | “Validate PEC credentials before delivery” | Show success output |
| 4 | 0:22 | Terminal: `openfatture fattura invia 1 --pec` | “Send the invoice with branded HTML template” | Highlight signed/unsigned toggle |
| 5 | 0:26 | Email preview (browser) | “Preview the email template and attachments” | Zoom on branding elements |
| 6 | 0:25 | Terminal: `openfatture notifiche process ...RC_*.xml` | “Process SDI notifications and update invoice status” | Show status change |
| 7 | 0:20 | Inbox view | “Demonstrate automatic notification to NOTIFICATION_EMAIL” | Emphasise audit trail |
| 8 | 0:18 | Terminal: `openfatture fattura show 1` | “Verify status and timeline in the CLI” | Highlight history section |
| 9 | 0:11 | Summary slide | “PEC test → send → process notifications → audit” | Reminder to archive XML/PEC receipts |
|10 | 0:10 | Outro | “Explore more automations in the docs” | Link to documentation hub |

## Production Notes
- **Certificates:** use demo `.p12` certificate for signature step.
- **PEC mailbox:** configure test inbox; ensure sample notifications exist in `/examples/sdi`.
- **Email template:** update colours/logo to match brand guidelines before capture.
- **Security:** mask sensitive fields (passwords, PEC addresses).

## Required Assets
- `.env.demo` with PEC and signature configuration.
- Demo certificate and password stored securely.
- Sample notification XML files (AT, RC, NS, MC, NE).
- Email preview rendered with TemplateRenderer or via CLI.

## Pre-Shoot Checklist
- [ ] Run `openfatture pec test` and capture successful output.
- [ ] Ensure invoice `1` exists and is ready to send.
- [ ] Generate email preview (`openfatture email preview ...`) and open in browser.
- [ ] Test notification processing for each type; confirm status transitions.
- [ ] Prepare inbox screenshots highlighting automated emails.
- [ ] Configure OBS scenes for terminal, browser, inbox.

## Post-Production
- Add callouts for compliance reminders (archive XML, 10-year retention).
- Mention that notifications trigger email summaries when `NOTIFICATION_EMAIL` is set.
- Export master + H.264 + vertical clip (PEC send + notification processing).
