# Technical debt analysis — November 2026 (v2.8.1 → v2.8.2)

Tracker: [#36](https://github.com/gianlucamazza/openfatture/issues/36).
Scope: measure the code base after the 2.6–2.8 cleanup, fix what is wrong,
turn regressions into CI checks, and rank what is left.

## Measurements (v2.8.1)

| Signal | Value | Tool |
|---|---|---|
| Product code | ~51k lines in `openfatture/` | `wc` |
| Complexity | 90 blocks at rank C or worse; 17 at D/E (max 40, `_run_assistant`) | `radon cc` |
| Duplication | no duplicated block of 12+ lines | `pylint duplicate-code` |
| Dependencies | 1 undeclared (`prompt_toolkit`), 4 unused (`pyyaml`, `xmlschema`, `asn1crypto`, `langgraph-sdk`) | `deptry` |
| Vulnerabilities | 5 advisories, all chromadb **server** API; not reachable (embedded `PersistentClient` only) | `pip-audit` |
| SAST | 2 High (false positive B701), 2 Medium (B314, B310) | `bandit -ll` |
| Coverage | 81% lines, 76% branches; `billing/application` 35%, `sdi/application` 36% | `coverage` |
| Broad `except` | 207: 113 return an error, 38 re-raise, 54 log only, 4 pass | AST scan |
| Error leaks | 35 sites returned `str(exception)` (SQL included) to the assistant/CLI | grep |
| Hard-coded CLI text | 127 strings outside i18n (69 in `fattura.py`) | AST scan |

## Defects found and fixed

| Severity | Defect | Fix |
|---|---|---|
| High | **Rounding**: line VAT was never rounded and totals were accumulated incrementally; a draft could store `imponibile 110.59 + iva 24.33 = totale 134.93`, and the XML asked the customer for 134.93. XML amounts used banker's rounding. | `billing.application.totals`: half-up cents per line, VAT per rate/natura as in `DatiRiepilogo`, `totale = imponibile + iva`; used by invoice lines, credit notes, quotes, quote conversion and the XML builder. |
| High | **SDI send**: XML was validated only if none existed yet; `fattura generate-xml` writes unvalidated XML, so a later send transmitted unvalidated and possibly stale content. | Unsigned sends always regenerate and validate. |
| High | **Signed send**: the signed `.p7m` path was never stored and the send attached the unsigned XML with a PKCS#7 MIME type. | Signing stores `xml_firmato_path`; a signed send uses the `.p7m` only if the signed XML still validates and matches the current invoice. |
| High | **Signing without a path** always failed (`numero:05d` on a string) and searched invented file names in the working directory. | Defaults to the invoice's archived XML. |
| High | **CSV invoice import**: one duplicate number broke the session; the import reported success while nothing was saved. | Savepoint per row, explicit duplicate check, readable errors (same for client import). |
| Medium | Duplicate explicit invoice number returned a raw SQL error. | Clear message with the next free number. |
| Medium | Untrusted SDI notification XML parsed with `xml.etree` (B314); XSD validation used lxml's default parser. | `sdi.safe_xml`: no entities, DTDs or network. |
| Medium | Raw exceptions (SQL, parameters) returned to the assistant at 35 sites. | `platform.errors.describe_error`. |
| Medium | Test suite wrote into the developer's real data dir (archive XML, assistant checkpoints). | conftest isolates data, archive, certificates, vector store and sessions. |
| Low | Assistant recovery messages hard-coded in Italian for every locale. | Localized in all five locales. |

Also removed: unused dependencies, `download_xsd_schema` (bundled schema; B310),
27 unused exception classes (two shadowed `FileNotFoundError` and `TimeoutError`).
The 7 XSD validation tests were always skipped by a stale check; they now run.

## Guardrails added

- `deptry` in the lint job; accepted exceptions documented in `[tool.deptry]`.
- `pip-audit` on the locked set, blocking; only the documented chromadb server advisories are ignored.
- `bandit -ll`, blocking; `B701` skipped with rationale in `[tool.bandit]`.
- Coverage floor 49% → 78% (`pyproject.toml` and `test.yml`).
- Behaviour tests for invoices, credit notes, quotes, products, clients and SDI transmission on a real database.

## Remaining debt (ranked)

| ID | Item | Impact | Effort | Priority |
|---|---|---|---|---|
| D-SIZE (#37) | Oversized modules; complexity hotspots `_run_assistant` (40), `GraphAssistantBackend.stream` (36), `NotificationProcessor.process_notification` (35), `_readiness` (33), `update_client` (31) | Review cost, bug risk when touched | M | P2 when touched |
| D-CLI-I18N | 120 hard-coded CLI strings (mostly `fattura`, `init`, `cliente`), mixed languages | UX in non-Italian locales | M | P3 |
| D-ERRORS | Error dicts vs exceptions vs `ToolResult` are three contracts; 54 log-only broad `except` blocks (mostly isolation of post-commit side effects, reviewed) | Consistency | L | P3 |
| D-XML-TOTAL | `ImportoTotaleDocumento` is not emitted (optional in FatturaPA) | Customer tooling expectations | S | P3 |
| D-TYPES-TESTS (#42), D-OBS (#40), D-ASYNC (#43), D-PDF-PAGOPA (#41) | unchanged | — | — | as before |
