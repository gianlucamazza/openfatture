# Next Release Planning (v1.0.2)

## Focus & Objectives
- **Payment CLI parity**: portare in produzione tutti i comandi documentati (account management, listing, reconciliation granular).
- **AI forecasting UX**: consolidare pipeline Prophet + XGBoost ora installata di default (metriche, retraining sicuro).
- **Quality guardrails**: rialzare gli standard di coverage e preparare il salto verso l’85%.

## Payment CLI Backlog
1. **Account Management**
   - `openfatture payment create-account`
   - `openfatture payment list-accounts`
   - `openfatture payment update-account`
   - `openfatture payment delete-account`
   - Persistenza e validazioni tramite `BankAccountRepository`.
2. **Transaction Utilities**
   - `list-transactions` con filtri (account, stato, data).
   - `show-transaction <uuid>` con dettagli e match suggeriti.
3. **Reconciliation Flow**
   - `reconcile --auto` e `reconcile --review` come wrapper ad alto livello per `MatchingService`.
   - `match-transaction` / `unmatch-transaction` per operazioni mirate.
4. **Reminder Management**
   - `list-reminders --status` e `cancel-reminder` per completare il ciclo operativo.
5. **CLI UX**
   - Aggiornare l’autocompletione (`cli/completion/`).
   - Aggiornare la dashboard TUI per linkare i nuovi comandi.

## Documentation & Tooling
- Allineare `docs/PAYMENT_TRACKING.md` con ogni comando appena introdotto (section “CLI Command Reference”).
- Aggiornare `docs/CLI_REFERENCE.md` aggiungendo il capitolo “Payment”.
- Rafforzare esempi in `examples/payment_examples.py` includendo i nuovi entry point CLI.

## Quality & Coverage Roadmap
1. **Short-term (v1.0.2)**
   - Portare coverage medio ≥60% con nuovi test sui servizi di pagamento.
   - Alzare `--cov-fail-under` a 60% in `.github/workflows/test.yml`.
2. **Mid-term**
   - Incrementare coverage sui moduli AI e payment fino a 75%.
   - Rifinire fixture demo per generare dataset realistici.
3. **Long-term (85% goal)**
   - Misurare coverage differenziale su PR.
   - Integrare report automatici in `docs/reports/`.

## Tracking
- Tenere traccia dello stato in `docs/history/ROADMAP.md` (nuova sezione “Next Release”).
- Aggiornare `CHANGELOG.md` con progressi intermedi quando significativi.
