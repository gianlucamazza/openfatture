# Invoice lifecycle and SDI evidence (2.5)

Manual changes and bulk operations share the same policy. Native invoices may move only between `bozza` and `da_inviare`; readiness includes in-memory XML validation. Historical invoices cannot be manually queued or resent. An unchanged status is a no-op. Bulk operations validate every invoice before writing and roll back the entire group on failure. Conditional updates detect stale state, SDI identity and update timestamps.

## Imported notifications

Receipts match an exact recorded SDI identifier or archived/transmitted filename, never a substring of invoice number/year. Ambiguous or contradictory references remain in the journal without changing an invoice. Receipt identity is unique: repeats do not duplicate log entries, state changes, events or email. Semantic identity excludes import timestamps; original XML and its digest are retained when imported from a file. Unsupported files are archived without a transition.

RC maps to `consegnata`, NS to `scartata`, NE/EC01 to `accettata`, NE/EC02 to `rifiutata`; MC and AT map to `errore` (delivery unavailable), not rejection or permission to resend. AT means transmission with impossibility of delivery: see the [official Finance Ministry explanation](https://def.finanze.it/DocTribFrontend/getPrassiDetail.do?id=%7B38B72BAA-1A08-4258-BD3E-F1CBCA487E8B%7D). The complete original receipt remains available to distinguish temporary MC from final AT. Transport submission alone is `inviata`, never delivery/acceptance.

Terminal outcomes cannot be replaced by contradictory terminal outcomes for the same transmission. Earlier-stage receipts do not regress a later outcome. Contradictions and out-of-order messages are retained with their processing outcome. Event dates are populated only when explicitly present in the source; import time is not a delivery date.

Receipts imported manually are marked `manual_import`, not cryptographically authenticated. An exact association proves which local invoice the receipt refers to; it does not certify the authenticity of the XML. Historical documents with associated receipts remain blocked from new emission/submission. Without receipts, their SDI status remains unverified.

## Submission journal and human recovery

Both PEC senders persist a unique invoice claim before attempting network I/O. Claims preserve filename and XML digest. Submission does not automatically retry a network failure: an interrupted connection can occur after the server accepted a message. Pending/uncertain claims block a second send, including after restart. Successful submission and invoice state are committed together; a later event/email failure does not reverse that outcome.

Use `openfatture fattura sdi-journal` to inspect claims and receipts. `associate-receipt RECEIPT_ID INVOICE_ID --evidence "reference checked"` requires a human confirmation and cannot override an existing contradictory identity. `resolve-submission ATTEMPT_ID --sent|--not-sent --evidence "provider reference"` requires verification and confirmation. `--not-sent` releases a claim only when no recorded SDI evidence contradicts that conclusion. It does not send anything. A confirmed sent claim remains protected against duplicate submission.

## Migration and rollback

The migration adds only `sdi_notification_records`, `sdi_submission_attempts`, and `sdi_invoice_identities`; invoice and payment rows are untouched. New installations create these tables with the normal schema. Existing databases created without Alembic history can use the packaged `upgrade_status_schema(engine)` helper: it validates the invoice baseline, adds missing journals idempotently, and does not fabricate an Alembic revision history. A tracked Alembic merge revision supports the two existing tracked migration heads.

Back up SQLite through its backup API, test the migration on the copy, and compare all pre-existing table contents before updating a live database. Downgrade refuses to discard non-empty journals. For rollback after use, restore a pre-upgrade database backup with the previous executable; retain the newer journal backup separately for investigation. Do not silently delete transport evidence.

This release does not change collection balances or implement the separate receipt-of-payment ledger, bank allocation splits or payment reversals.
