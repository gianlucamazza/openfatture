# Collection behavior audit — 2026-11-09

Release target: 2.6.0. Tests use temporary SQLite databases and synthetic invoices.
No SMTP delivery, real SDI transmission or bank-side operation is part of this audit.

Verified cases include partial receipts, split allocation rollback, immutable
reversal history, replay/conflict IDs, competing allocations on a file-backed
SQLite database, legacy balance preservation, bank debit rejection and transaction
commit/rollback event publication (including savepoints). Public CLI tests cover
structured successes/errors, declared formats and refusal of interactive machine
output. Existing runtime/PTY/confirmation tests remain part of the full suite.

A rehearsal on a copy of the local 2.5 database preserved every existing invoice,
client and payment row. It created two opening receipts and two allocations totaling
EUR 2,960. Foreign-key validation passed. Backup, detailed logs and synthetic
transcripts are stored locally under `openfatture-release-artifacts/v2.6.0`.

Live DeepSeek checks exercised the actual product runtime with both `langgraph`
and `chat`, restricted to local ledger tools on synthetic data: reading history,
unknown payment evidence, denied write and approved write. Eight completed turns
passed database postconditions. The run made 20 HTTP requests, including three
initial requests with an incomplete audit allowlist; those initial attempts are
retained as failed setup evidence, not counted as successful tool-loop checks.

Including the earlier 12-call audit, the conservative usage estimate is USD 0.02057;
the cumulative reserved upper bound is USD 0.10434, below the authorized USD 2
budget. Prices used were USD 0.30/M input and USD 1.20/M output, verified against
[DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/). Account debit
was not independently verified. These checks are a behavioral sample, not a proof
that every possible model response is correct. Real external delivery and
PostgreSQL contention were not exercised locally.
