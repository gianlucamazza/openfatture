# Collection ledger (2.6)

Invoices, SDI transmission and collections are separate facts. A historical invoice
with technical status `bozza` is still issued elsewhere. No collection record is
not evidence of non-payment. An owner declaration records its provenance; it does
not create a receipt or assert that the amount received is zero.

## Migration and recovery

Back up the SQLite file while application writers are stopped, then run:

```sh
openfatture pagamento migrate
```

This command upgrades the schema and turns historical cumulative paid amounts into
opening receipts and allocations. Individual receipt dates remain unknown when not
attested. Existing bank allocations retain their transaction provenance. Monetary
mismatches abort the migration. It is idempotent. SQLite schema rebuilding temporarily
disables foreign keys on its own connection and validates them before commit. Do
not run concurrent writers during migration. Restore the backup to downgrade; do
not delete ledger tables to erase history.

## Receiving and allocating money

Amounts use decimal strings with at most two fractional digits, not binary floats.
The receipt represents incoming money. Allocations associate it with one or more
invoices and optionally a specific installment. A receipt without an allocation
is available money, not a paid invoice.

```sh
openfatture pagamento record 2000 --invoice 1 --request-id receipt-example-1
openfatture pagamento record 500 --request-id receipt-example-2
openfatture pagamento allocate 2 3 200 --request-id allocation-example-1
openfatture pagamento allocate-batch 2 --allocations '[{"invoice_id":3,"amount":"100"},{"invoice_id":4,"amount":"200"}]' --request-id split-example-1
openfatture pagamento list
openfatture pagamento show 1
```

Use the same request ID and identical arguments after a timeout or uncertain client
response. A replay returns the stored result; conflicting reuse is rejected. A new
ID means a new operation. Public operation IDs are limited to 64 characters.
Splits commit completely or roll back completely. Concurrent allocations cannot
spend more than receipt, invoice or installment balances allow.

`bank-receipt UUID` registers an already-imported positive EUR movement. Bank
movements have one receipt identity; debits and other currencies are rejected.
A partially allocated bank receipt remains `partially_matched` and reports its
available balance. Resetting reconciliation appends reversals; original allocations
and legacy allocation evidence remain available.

## Corrections and declarations

```sh
openfatture pagamento reverse 1 100 --reason 'Wrong invoice' --request-id correction-example-1
openfatture pagamento declare-status 3 not_settled --source owner --date 2026-11-09 --request-id declaration-example-1
```

A reversal corrects an allocation and releases its money for allocation again. It
is **not a bank refund**. It requires human confirmation in the CLI. Receipts and
allocation history cannot be deleted through legacy payment deletion. Legacy
cumulative balance reductions can reverse manual/opening allocations; bank-backed
collections require an explicit reconciliation correction.

An omitted deadline is unknown. Overdue is derived from an attested deadline and
positive residual, independently of a partial collection. Reminders are withheld
when the deadline is unknown or direct invoice collections still need assignment
to installments. Due-date reports concern scheduled installments; consult invoice
balances for unscheduled amounts.

## Assistant and CLI output

The assistant exposes `get_collections` by default. Enable specific write tools in
`ai_enabled_tools` to use them: `record_collection`, `allocate_collection`,
`allocate_collection_batch`, `reverse_collection`, `declare_collection_status`, and
`record_bank_collection`. Existing explicit allowlists are respected. Write tools
require the configured human confirmation gate; the model cannot approve itself.
SDI transmission remains a separate explicit opt-in.

For business commands, `--format json` emits one envelope with `success`, `data`,
`warnings`, and `error`; errors retain nonzero exit codes. Prompts go to stderr and
confirmations remain active. Markdown and HTML wrap the structured payload;
`stream-json` emits a completion event. Assistant one-shot output retains its
response/stream contract. Interactive setup and chat require `rich`; provide a
single assistant request for machine formats. Secrets are redacted while usage
counts remain numeric.
