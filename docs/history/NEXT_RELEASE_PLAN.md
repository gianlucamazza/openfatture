# Next Release Planning (v1.0.2)

## Focus & Objectives
- **Payment CLI parity:** ✅ core commands (accounts, transactions, reminders) delivered; complete advanced UX and audit trail.
- **AI forecasting UX:** consolidate the Prophet + XGBoost pipeline now installed by default (metrics, safe retraining).
- **Quality guardrails:** raise coverage targets and pave the way to 85%.

## Payment CLI Backlog
1. **Account Management**
   - [x] `openfatture payment create-account`
   - [x] `openfatture payment list-accounts`
   - [x] `openfatture payment update-account`
   - [x] `openfatture payment delete-account`
   - [ ] Persist advanced validation (unique constraints, audit log).
2. **Transaction Utilities**
   - [x] `list-transactions` with filters (account, status, date).
   - [x] `show-transaction <uuid>` with details and suggested matches.
3. **Reconciliation Flow**
   - [x] `reconcile` with `auto` / `preview` modes wrapping `MatchingService`.
   - [x] `match-transaction` / `unmatch-transaction` for targeted actions.
   - [ ] Guided workflow to ignore transactions and capture operational notes.
4. **Reminder Management**
   - [x] `list-reminders --status` and `cancel-reminder`.
   - [ ] Handle auto-rescheduling and multi-channel reminders.
5. **CLI UX**
   - Update autocompletion (`cli/completion/`).
   - Refresh TUI dashboard to link the new commands.

## Documentation & Tooling
- Align `docs/PAYMENT_TRACKING.md` with the newly shipped commands (see “CLI Command Reference” section).
- Update `docs/CLI_REFERENCE.md` with a dedicated “Payments” chapter.
- Expand examples in `examples/payment_examples.py` to cover the new CLI entry points.

## Quality & Coverage Roadmap
1. **Short-term (v1.0.2)**
   - Raise average coverage to ≥60% with new tests on payment services.
   - Increase `--cov-fail-under` to 60% in `.github/workflows/test.yml`.
2. **Mid-term**
   - Push AI and payment modules toward 75% coverage.
   - Improve demo fixtures to produce realistic datasets.
3. **Long-term (85% goal)**
   - Track differential coverage on PRs.
  - Publish automatic reports in `docs/reports/`.

## Tracking
- Maintain status in `docs/history/ROADMAP.md` (add a “Next Release” section).
- Update `CHANGELOG.md` with significant intermediate progress.
