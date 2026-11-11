# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.14.0] - 2026-11-12

The outstanding amount includes invoices without installments, and the
assistant can record receipts with the default configuration.

### Fixed

- `get_due_dates` and `get_payment_stats` counted only payment installments,
  so an issued invoice without installments (for example one issued
  elsewhere) disappeared from what is still owed. The assistant reported only
  the residual of the installments as the whole exposure. The part of each
  invoice that no installment covers is now listed in `without_due_date`
  (`source: "invoice"`) and counted in `total_outstanding`, matching the
  invoice summary. `get_payment_stats` adds `outstanding_without_installments`
  and `invoices_outstanding`.
- The assistant could not resolve "ieri" or "fine mese": the system prompt
  now states today's date.

### Changed (default)

- `ai_tool_access` defaults to `full`. Changes are gated by a confirmation
  that shows their parameters, rather than hidden: the assistant can record a
  receipt or create an invoice without extra configuration, and every change
  still needs your yes in the terminal. SDI/PEC sending stays off. To keep a
  consultation-only assistant: `openfatture config set ai_tool_access standard`.
- A capability hidden by a lower access level is described by what it does
  (for example "registrazione di incassi, anche manuali"), and the assistant
  says so before consulting other data, instead of guessing a procedure.

## [2.13.0] - 2026-11-12

The assistant's instructions are reorganized for current models, and every
tool states its contract.

### Changed

- **One system prompt for every provider.** The ReAct prompt (providers
  without native tool calling) used to replace it, dropping every rule about
  invoices issued elsewhere, uncertain PEC submissions and the collection
  ledger; it now appends only its text protocol and tool catalogue, without
  invented example data or shouted rules.
- The system prompt is organized in sections (product context, how to read the
  data, actions, tools) written as prose with the reasons. Rules about one tool
  appear only while that tool is enabled. The assistant answers in the user's
  language.
- Removed the prompt rule "ask for confirmation before destructive actions":
  the registry already asks, and the rule produced a second question in text.
- Tool descriptions and parameter descriptions are rewritten as contracts:
  what each tool returns, its limits, failure modes and the neighbouring tool
  to use instead. No "CRITICAL" prefixes.
- `ai_temperature` defaults to 0.3 (it was 0.7).
- `search_invoices` filters by every invoice status.
- `get_invoice_details` returns each line's `id`, `numero_riga` and `natura`,
  so the assistant can edit or delete lines of existing invoices.

### Fixed

- Searching invoices or clients for text containing `_` or `%` found nothing.
- The VAT report and the client report added credit notes (TD04) instead of
  subtracting them.

### Added

- `tests/ai/test_system_prompt.py`: invariants of the prompt and of the tool
  descriptions.
- `tests/evals/`: behaviour scenarios against the configured model (marker
  `llm_eval`, opt-in with `OPENFATTURE_EVAL=1`; they call the provider).

### Removed

- The never-populated `ChatContext.current_year_stats`, `relevant_documents`
  and `knowledge_snippets`, and the prompt sections that read them.

## [2.12.0] - 2026-11-12

Generated documents can be opened from the chat.

### Added

- The path of a document a tool writes (PDF, FatturaPA XML, signed `.p7m`, CSV) is printed as
  a terminal link under the tool line: Ctrl+click opens it.
- `/open [N]` in the chat opens the latest generated document, or the N-th most
  recent, with the default application.
- Assistant tool `open_document` (risk class `local_artifact`, so enabled with
  the default access) for requests such as "aprilo".
- `openfatture.platform.opener`: only `.pdf`, `.xml`, `.p7m` and `.csv` files,
  or folders, in the exports or archive directory are opened, after resolving
  symbolic links; the application starts detached; a launcher that reports no
  handler for the file type is an error; without a person at the terminal or a
  graphical session the path is returned instead.

### Changed

- The tool registry's outcome callback also receives the result data of a
  successful tool.

## [2.11.0] - 2026-11-11

The CLI keeps only what the assistant must not do: the SDI journal and the
resolutions backed by a person's evidence. `openfatture` itself is the
assistant, and it runs `init` when the setup is missing.

### Removed (Breaking)

- `openfatture assistant`. Use `openfatture` for the chat and
  `openfatture -m "..."` for one request; `--session` and `--no-stream` are
  root options. Its `--json` is replaced by the root `--format json`.
- `openfatture pagamento migrate` and the `pagamento` group. `openfatture init`
  already applies the same collection ledger migration, after backing up the
  SQLite file, and every collection operation prepares any balances not yet
  migrated.
- `openfatture fattura generate-xml`. It wrote the XML without XSD validation,
  and with `--output` it recorded on the invoice the archive path instead of the
  file it had written. Ask the assistant for the XML file instead.

### Changed

- Assistant tool `validate_invoice_xml` is now `generate_invoice_xml`, with risk
  class `local_artifact` (it writes the archive file; it used to be `read`, and
  so stayed enabled with `ai_tool_access = "read"`). An XSD error is reported as
  `valid: false` with the validator's message.
- `--help` groups the `fattura` commands under "Verifiche SDI" (it was "Strumenti").
- Starting the assistant with the setup missing: in a terminal it runs
  `openfatture init` (the wizard when the company profile is missing, only the
  database upgrade otherwise); elsewhere it explains what to run and exits with
  code 3 (`setup_required`, `newer_database`, `ai_key_missing` with
  `--format json`). A missing AI key is reported up front instead of failing
  the first request.
- The `next_steps` of `openfatture status` are in the configured language.
- `ai_model` defaults to empty, meaning the provider's default model; it used to
  be `gpt-4-turbo-preview`, which replaced the OpenAI default `gpt-5`.

### Fixed

- An invalid FatturaPA XML is no longer written to the archive: the file is
  saved only after XSD validation passes, so `sign_invoice_xml` cannot sign it.
- Starting the assistant no longer creates an empty database silently.

## [2.10.1] - 2026-11-11

### Fixed

- `--help` of every command describes itself in the configured locale also with
  Typer releases that vendor Click (as installed from PyPI), which hardcode that
  line in English.

## [2.10.0] - 2026-11-11

The assistant is the only path for business operations: tool access by risk class,
PDFs and a yearly summary out of the box, and no CLI duplicates of assistant tools.

### Added

- The assistant tool `generate_invoice_summary_pdf` renders a PDF summary of a year's
  invoices (invoiced, collected, outstanding and overdue totals, per-document status, clients)
  into `data_dir/exports/riepiloghi/`. The figures come from one application query, not from the
  model. Before, the assistant answered that no summary PDF could be produced.

### Removed

- **Breaking:** CLI commands that duplicated assistant tools are removed: the whole
  `cliente` group, `fattura list|show|create|add-line|generate-pdf|set-status|create-credit-note`
  and `pagamento list|show|record|allocate|allocate-batch|reverse|declare-status|bank-receipt`.
  Ask the assistant instead; changes to data need `ai_tool_access = "full"` and are confirmed
  by a person. The CLI keeps only operations without a tool: `fattura generate-xml`,
  `sdi-journal`, `associate-receipt`, `resolve-submission` and `pagamento migrate`.

### Changed

- **Assistant tool access is decided by risk class.** Every tool declares a `ToolRisk`
  (`read`, `local_artifact`, `mutate`, `transmit`). The new `ai_tool_access` setting picks the
  level: `read`, `standard` (default: adds invoice/quote PDFs and CSV exports) or `full` (adds
  record changes, each confirmed by a person). The assistant can now generate PDFs out of the
  box; before, it answered that no export existed.
- **Breaking:** `ai_enabled_tools` now *adds* tools on top of `ai_tool_access` and defaults to
  empty; `all` is no longer special. Replace `ai_enabled_tools = "all"` with
  `ai_tool_access = "full"`. Transmit tools still need their explicit name.
- The system prompt lists capabilities hidden by the current level with the command that
  enables them, instead of a fixed description of the tools.
- Bulkhead and circuit-breaker limits follow the risk class; ten tools (collections, cassa,
  credit notes) that were missing from the per-name lists now get write limits.
- `openfatture init` no longer writes a tool allowlist to `config.toml`.

### Fixed

- The CLI speaks the configured locale throughout. Command help comes from Fluent
  (`cli-help-*`) in five languages instead of hard-coded text, and describes every command
  and parameter. Click and Typer's own text (panel titles, `--help`, usage errors, prompts)
  comes from bundled gettext catalogs (`openfatture/i18n/gettext`). Refusals of
  `generate-xml`, `associate-receipt` and `resolve-submission` carry an `error_code` and are
  shown localized; the English text stays for the assistant and the JSON envelope.
- `fattura <command> --help` no longer opens the database: it failed without an
  accessible database.
- Resolving an unknown submission attempt reports "not found" instead of a SQLAlchemy error.
- `fattura sdi-journal` says when the journal is empty; refusing XML for an invoice issued
  elsewhere no longer prints a warning log line.
- PDFs generated without an output path are written to `data_dir/exports/fatture/` (or
  `preventivi/`) instead of the current working directory, also when the assistant omits the
  path.
- The invoice PDF footer states it is a courtesy copy without fiscal value (the original is
  the FatturaPA XML sent through SDI), replacing the misleading digital-preservation note.
- CLI and assistant share one default PDF template (`professional`).
- `docs/PDF_GENERATION.md` documented a non-existent `openfatture pdf` command group; it now
  shows how to ask the assistant for PDFs.

## [2.9.0] - 2026-11-10

Consistency of invoice amounts across totals, XML and PDF, and burn-down of all open
technical debt ([ledger](docs/TECHNICAL_DEBT.md)).

### Fixed

- **XML, PDF and stored totals now agree** on every amount (`billing.application.totals`):
  - social security contributions (`DatiCassaPrevidenziale`, e.g. INPS TC22 4%) are part of
    `DatiRiepilogo` and of the totals; editing a line no longer drops them, and SDI no longer
    receives a summary that excludes them;
  - the PDF riepilogo uses the same per-rate VAT as the XML instead of summing line VAT;
  - the PDF totals box ends with the amount due (net of withholding tax) and no longer lists
    the stamp duty as an extra amount; the SEPA QR requests the amount due;
  - `ImportoTotaleDocumento` is emitted; empty `UnitaMisura` is omitted (it failed XSD).
- **VAT natura**: a 0% line requires a natura and a taxed line forbids it (FatturaPA rule,
  checked at creation and before building the XML). Lines, quote lines and contributions
  default to 0% `N2.2` in the forfettario regime; quotes keep the natura when converted.
- **Stamp duty** (`importo_bollo`) is computed automatically: EUR 2.00 when amounts outside VAT
  exceed EUR 77.47. Charging it to the customer is an `N1` line.
- Credit notes copy the social security contribution of the source invoice.
- PDF: sections that do not fit move to a new page instead of running under the footer or off
  the page; the footer shows the real page count.
- Tool results report `bulkhead_queue_length` as the number of callers actually waiting for
  the tool's concurrency slot, instead of a value derived from a private semaphore field (#40).
- **Assistant tool errors**: an application refusal (`{"error": ...}`, e.g. "invoice not found")
  was reported as a successful tool call, so read tools cached it and metrics counted it as a
  success. It is now a failed result that keeps its payload for the model, and it does not open
  the circuit breaker. Tool exceptions no longer expose SQL.
- `fattura list`/`show`: payment statuses `fully_paid`, `partially_paid` and
  `no_payment_record` had no translation and printed the raw message id.
- Logging no longer writes to a closed stream when `sys.stderr` was redirected after start-up.
- Nested event loops: `run_async` uses one strategy (`asyncio.run`, or a worker thread with its
  own loop and the caller's context when a loop is running); `nest_asyncio` is gone (#43).

### Changed

- CLI command output is localized in all five locales (it, en, de, es, fr), and euro amounts are
  formatted for the active locale.
- Payment matchers have one synchronous contract.
- Internal structure: oversized modules split by cohesion (`storage.database.models` package,
  invoice line and quote commands/queries, invoice tool definitions, tool registry resilience
  and metrics, OpenAI payload mapping, PDF template sections); complexity hotspots refactored.
- Tests are type-checked with mypy in CI.

### Added

- `set_cassa_previdenziale` assistant tool and `natura` on line tools; `fattura add-line --natura`.

### Removed

- `create_lump_line` and `create_rate_line` tools (duplicates of `create_riga`).
- `ReActOrchestrator`, a second ReAct loop unused by the assistant: the assistant graph runs
  ReAct turns with the prompt from `orchestration.react.build_react_messages`.
- The unimplemented pagoPA QR option (pagoPA notices are issued by public creditors).
- `fatture.bollo_assolto_virtuale` (electronic invoices always pay the stamp duty virtually)
  and the unused `user_feedback` / `model_prediction_feedback` tables; run `openfatture init`
  to upgrade the database.

## [2.8.2] - 2026-11-10

Findings of the technical debt analysis ([report](docs/reports/technical-debt-analysis-2026-11.md)).

### Fixed

- **Invoice totals**: line VAT is rounded half-up to the cent and VAT is computed per rate and
  natura like `DatiRiepilogo`; `totale` always equals `imponibile + iva` (it could drift by a
  cent and the XML asked for that amount). Applies to invoices, credit notes, quotes and
  conversions; XML amounts use half-up rounding.
- **SDI transmission**: unsigned sends always regenerate and validate the XML; signed sends use
  the stored `.p7m` only if the signed XML still validates and matches the invoice. Signing
  records the `.p7m` path and defaults to the invoice's archived XML (it always failed without an
  explicit path).
- **CSV import**: a rejected row (e.g. duplicate number) no longer discards the whole batch
  while reporting success.
- Duplicate explicit invoice numbers return a clear error instead of SQL.
- SDI notification XML is parsed without entity expansion, DTDs or network access.
- Errors returned to the assistant and CLI no longer include SQL statements.
- Assistant recovery messages are localized.

### Changed

- Coverage floor 78%; `deptry`, `pip-audit` (locked dependencies) and `bandit` are blocking in CI.
- Declared `prompt-toolkit`; removed unused `pyyaml`, `xmlschema`, `asn1crypto`, `langgraph-sdk`.

### Removed

- `download_xsd_schema` (the schema ships with the package) and 27 unused exception classes.

## [2.8.1] - 2026-11-10

### Fixed

- The assistant failed with `PermissionError` when started from a directory without write
  access (for example `/`): AI settings created `./.chromadb` and the RAG auto-update queue
  defaulted to `./.cache/`. The unused `chromadb_*` AI settings are removed and the queue lives
  in `data_dir`. A test asserts that building settings never writes to the working directory.

## [2.8.0] - 2026-11-10

### Changed

- **Database schema is owned by packaged Alembic migrations** (`openfatture/storage/migrations`,
  now shipped in the wheel). New databases are created and stamped at head; a database behind
  the release is refused until `openfatture init` upgrades it (SQLite files are backed up first);
  databases created before 2.8.0 keep working and are adopted by `init` after a column check.
  `status --json` reports `database_schema`.
- One PEC sender: `sdi.email.TemplatePECSender` (formerly `platform.email`). The `platform` layer
  no longer imports domain packages, enforced by `tests/test_import_rules.py`.
- Application services use `db_session()` / `session_scope()` instead of hand-managed sessions.
- The tax knowledge base ships with the package and is indexed on first use; the vector store
  defaults to `data_dir/vector_store` instead of `./.chroma`.
- Every CLI invocation sets a correlation ID for its logs and events.
- Translations: only referenced messages remain, and de/es/fr now include all assistant and
  status messages.

### Removed

- The ML forecasting stack (`ai.ml`, cash-flow predictor, feedback) and the `ml` extra.
- The experimental multi-agent workflows (invoice creation, compliance, cash flow), their
  agents, states and approval layer, `native_tools`, `PromptManager` and its prompts.
- `sdi.pec_sender.PECSender`, `billing.batch.send_batch` / `validate_batch`, re-export shims
  (`billing.clienti`, `billing.fiscale`, `billing.prodotti`), unused i18n formatters and context,
  `common.ftl` / `email.ftl`, and about 60 functions without callers.

### Fixed

- Event repository sessions leaked when a query failed.
- `init_db` no longer defaults to a database in the current directory.

## [2.7.0] - 2026-11-10

### Changed

- **`.env` is no longer read implicitly** from the working directory, so a command
  behaves the same everywhere. Precedence is now: environment variables > secrets >
  `~/.config/openfatture/config.toml` > defaults. Load an env file explicitly with
  `uv run --env-file .env` or `docker compose` `env_file:`; import an old one with
  `openfatture config migrate --env-file .env`.
- Secrets (`ai_api_key`, `pec_password`, `signature_certificate_password`) are stored
  in the OS keychain through `keyring`, or in `credentials.toml` (0600) when no keychain
  is available. `OPENFATTURE_SECRET_BACKEND=keyring|file` forces the backend.
- `config show` reports where each value comes from; `status --json` adds a
  `configuration` block (config file, secret backend, plaintext secrets, ignored `.env`).
- `init` stores secrets in the keychain and proposes the default model of each provider
  (`qwen3:8b` for Ollama).
- `docker-compose.yml` passes `.env` via `env_file:` instead of mounting it.

### Added

- `openfatture config unset KEY` and `openfatture config migrate [--env-file PATH]`.
- `OPENFATTURE_CONFIG_DIR` selects another configuration directory.

### Fixed

- `config set` wrote every effective setting to `config.toml`, including values from the
  environment or `.env` (secrets too) and all defaults, and dropped comments. It now
  validates the value and writes only the given key, atomically and with 0600 permissions.
- Test runs could read the developer's real `config.toml`; they are now isolated.
- Release assets no longer include `dist/.gitignore`.

### Removed

- Unused `platform.security` secrets helpers (`SecretsManager`, `SecureConfig`,
  `DataEncryption`, `validate_env_vars`, `mask_sensitive_value`, `check_secrets_in_code`).
- `docs/QUICKSTART.md` (superseded by `QUICKSTART.md`; archived in `docs/history/`).

## [2.6.0] - 2026-11-10

### Added

- Append-only collection receipts and allocations, partial reversals, request replay
  protection, atomic splits and unallocated incoming funds.
- `pagamento` CLI commands and assistant tools share the same transaction services.
- Provenance-backed owner declarations, separate from recorded cash movements.
- Structured output for public business CLI commands in JSON, Markdown, HTML and JSONL.
- Packaged migration of historical cumulative balances without changing invoice totals.
- Durable assistant turns: per-turn LangGraph checkpoints, tool receipts reserved
  before execution, resumable pending turns (`/resume`, `/pending`, `/reconcile`);
  uncertain tool outcomes are never retried automatically.
- `tests/test_import_rules.py` enforces the package import rules.

### Changed

- `openfatture` without a subcommand starts the interactive assistant.
- `cliente`, `fattura` and `pagamento` are documented deterministic commands and
  call application services only (PDF, XML, SDI journal, collection upgrade).
- A model-chosen `output_path` for PDF/CSV export tools is confined to
  `data_dir/exports`.
- Payment reconciliation events are global domain events (audit log, EventLog,
  hooks, `EVENT_LISTENERS`).
- ML retraining is no longer started by the CLI lifespan.
- Historical design and implementation reports moved to `docs/history/`.

### Removed

- `openfatture interactive start` (use `openfatture`).
- `PAYMENT_EVENT_LISTENERS` setting and the payment-only event bus.
- Unused payment AI insight agent/service, `ai.context` enrichment and
  `InvoiceBatchProcessor`.

### Fixed

- Invoice and quote numbers were derived from a text sort, reissuing "10" after
  ten invoices. Numbering is numeric per year, and `(numero, anno)` is unique;
  the migration refuses to run while duplicates exist.
- Alembic had two heads; `alembic upgrade head` works again.
- Payment events failed on publish (`event_id` missing) and were only logged.
- A broken tool module started the assistant with no tools; it now fails loudly.

- Bank reconciliation accepts incoming EUR funds, preserves partial availability and
  reverses allocations without deleting financial history.
- Unknown deadlines stay unknown in reports, reminders and generated invoice XML.
- Reminder delivery pauses when invoice collections require installment allocation.
- Reconciliation events publish only after commit, including nested rollback handling.
- Historical invoices issued elsewhere participate in revenue reports.


## [2.4.0] - 2026-11-09

### Added

- Localized terminal chat with Markdown previews, slash completion, session history,
  explicit human approval and `--debug` diagnostics.
- Session-scoped interaction contracts, complete turn outcomes and provider usage
  accounting, including interrupted turns and unknown model prices.
- Fresh-process CLI, pseudo-terminal, confirmation, credential-redaction and
  configuration-precedence regression tests.

### Fixed

- `openfatture init` invokes setup directly; invoice and client commands initialize
  their database connection independently; help without arguments exits successfully.
- Setup and configuration use the user profile, respect environment overrides and
  preserve existing credentials. Missing fiscal data is reported explicitly instead
  of assuming RF19; configuration inspection does not create directories.
- Custom OpenAI-compatible endpoints such as DeepSeek are honored.
- AI-only installs no longer import optional ML workflows eagerly.
- Denied confirmations and cache hits no longer consume concurrency slots.

### Security

- Tools default to a single execution attempt; transient read retries require an
  explicit safe-to-repeat declaration.
- Credentials are redacted recursively from diagnostics, configuration output and
  approval summaries; debug tracebacks omit local variables.

### Security

- Fail-closed AI tool policy for SDI/PEC send: `send_invoice_to_sdi` is
  disabled for the chat/AI agent unless named in `ai_enabled_tools` (the
  value `all` does not enable it). The tool registry now requires an
  explicit human yes before transmit — interactive TTY prompt, or
  `confirmed=True` from a human-facing path. The model cannot self-confirm.
  Non-interactive sessions refuse. `ai_enabled_tools` and
  `ai_tools_require_confirmation` (default true) are actually read.

### Changed

- The chat agent now only sees tools listed in `ai_enabled_tools` (default:
  read-only lookups). With `all`, every write tool is visible and asks for
  confirmation before it runs; SDI/PEC send still stays off unless named.
- Drop remaining user-facing Venere Labs / `venerelabs` branding after
  `venerelabs.com` expired (not renewed). Example company data uses
  `Example S.r.l.`; package `__author__` is Gianluca Mazza; landing-page
  copyright is `© 2024–2026 Gianluca Mazza` (`info@gianlucamazza.it`).
  `PlatformDirs` still uses the historical `venerelabs` appauthor so
  Windows data/config paths stay put.

## [2.3.0] - 2026-09-11

### Added

- **Nota di credito (TD04) support** (PR #57):
  - `create_nota_credito_from_fattura` application command for creating credit notes from invoices
  - CLI command: `openfatture fattura create-credit-note --from-invoice <id>`
  - FatturaPA XML builder support for TD04 document type
  - `DatiFattureCollegate` XML element for linking credit notes to original invoices
  - Alembic migration adding `fattura_originale_id`, `fattura_originale_numero`, `fattura_originale_data` columns for document linkage
  - Comprehensive integration tests for TD04 XML generation and workflow

### Changed

- **Real CLI: `openfatture fattura generate-xml`** command now actually generates FatturaPA XML:
  - Wired to existing `InvoiceService.generate_xml()` and FatturaPA XML builder (no stubs, no mocks)
  - Honors `--output` for custom XML file path
  - Honors `--dry-run` to display XML without writing to disk
  - Full test coverage for normal generation, custom output, dry-run mode, and error handling
- **Slim Alembic migration** (commit 8cf82bd24752):
  - TD04 linkage columns added with minimal schema footprint
  - Migration tested and validated in CI

## [2.2.0] - 2026-09-11

### Added

- **PDF Layout improvements** (PR #51):
  - Text wrapping for long line descriptions using ReportLab Paragraph objects
  - Multi-page table rendering with proper `Table.split()` support
  - Dynamic summary box height with space reservation calculation
  - HTML entity escaping for invoice descriptions (& < > characters)
  - Improved spacing between invoice sections
- **Professional PDF template** (PR #52):
  - Professional template is now the default (was minimalist)
  - Enhanced CEDENTE/PRESTATORE header block with better typography
  - Structured IBAN/payment information block with method mapping
  - Optional logo support via configuration (graceful fallback if missing)
  - Italian terminology throughout (Scadenza, Modalità di pagamento)
- **First-class CLI commands** (PR #52):
  - `openfatture cliente` command group (list, show, create)
  - `openfatture fattura` command group (list, show, create, add-line, generate-pdf, generate-xml, set-status)
  - Rich formatting for terminal output
- **FatturaPA XML improvements** (PR #53):
  - Fixed XML namespace qualification to pass XSD validation
  - Native support for `natura` field on line items (N1-N7 codes for zero-rated, exempt, out-of-scope VAT)
  - `DatiCassaPrevidenziale` model for social security contributions (TC01-TC22 codes)
  - Comprehensive XSD validation tests
  - Documentation: `docs/SDI_TRANSPORT_READINESS.md` (implementation guide, no live SDI emit)

### Removed

- **Experimental Lightning Network module** (`openfatture.lightning`, extra
  `lightning`, config flags, lifespan hook, tests). LND gRPC was never
  product-complete. Docs archived under `docs/history/lightning/`.

### Changed

- Project config hygiene: pytest local runs no longer force coverage (CI still
  does); `Settings.app_version` tracks package `__version__`; bumpversion
  pin aligned; technical debt docs updated for LangGraph default.
- **SSOT:** assistant backend ids live in `platform.assistant_backends`;
  package `__version__` is re-exported by subpackages; `AISettings` hydrates
  credentials from platform `AI_*` (init/docs) with `OPENFATTURE_AI_*`
  override precedence; coverage `fail_under=49` in pyproject.
- Feature extras are now `ai`, `rag`, `ml` only (`all` no longer includes lightning).
- Default PDF template changed from minimalist to professional.

## [2.1.0] - 2026-08-08

### Added

- LangGraph is the **default** product assistant backend (`langgraph_tool_loop`).
- Release notes: `docs/releases/v2.1.0.md`.

### Changed

- Default `assistant_backend` / `ASSISTANT_BACKEND`: `chat` → **`langgraph`**.
- `ChatAgent` slimmed: single tool-loop via `GraphAssistantBackend`; keeps
  structured-output and shared prompt helpers. Rollback path: `ASSISTANT_BACKEND=chat`.
- `AssistantRuntime` constructs only the selected backend (no always-on dual init).

### Notes

- Opt-in backend plumbing and parity tests shipped in 2.0.x unreleased work and
  are now the product default.

## [2.0.2] - 2026-08-07

### Fixed

- Status readiness no longer suggests enabling the AI extra when the extra is
  already installed and only credentials are missing.

## [2.0.1] - 2026-08-07

### Added

- Status readiness: `core_ready`, `assistant_ready`, checks, and `next_steps`
  (human table + `--json`).
- Interactive slash commands: `/help`, `/exit`, `/session`, `/clear`.
- LangGraph tool-loop parity tests (product backend remains `chat_agent_tool_loop`).

### Changed

- `ai.tools.registry` is a package (`core` + `defaults`) with stable public imports.
- Init refuses silent `.env` overwrite; post-setup messaging is honesty-first.

### Fixed

- Clearer onboarding next steps after init (does not claim assistant ready without extra).

## [2.0.0] - 2026-08-07

### Added

- Unified assistant runtime (`openfatture.ai.runtime.AssistantRuntime`) as the
  only product entry for CLI and interactive mode.
- Application-layer use-cases for AI tools under `billing.application`,
  `payment.application`, `sdi.application`, and `pdf.tool_ops`.
- Optional multi-node LangGraph tool-loop helper (`ai.runtime.graph`).
- File-backed interactive session persistence with optional `--session` resume.
- Honesty gates: `lightning_allow_mock` (default false), RAG reindex callback
  required, `MissingExtraError` for optional stacks.
- PEP 621 extras matrix: `ai`, `rag`, `ml`, `lightning`, `all`.
- Architecture docs: `ARCHITECTURE.md`, `CORE_VS_EXTENSIONS.md`, redesign notes.

### Changed

- Package layout: `billing`, `events`, `hooks`, `platform`, `pdf` replace
  `core`, `utils`, and `services.pdf`.
- Tooling is Ruff-only for format and lint (Black/isort removed as drivers).
- Core install no longer pulls AI/ML/RAG/Lightning by default.
- Status JSON reports feature flags and experimental Lightning posture.

### Removed

- Voice assistant package, web scraper, orphan analytics agents.
- In-process experimental plugins package (extensions use hooks only).
- Compatibility import shims for old package paths.

### Fixed

- Lightning client no longer returns mock invoices/node info unless mock is
  explicitly allowed.
- RAG reindex queue no longer simulates work without a callback.
- Lint debt: no in-code `noqa` / `type: ignore` / `pragma: no cover` suppressions.

See [docs/releases/v2.0.0.md](docs/releases/v2.0.0.md) for migration details.

## [1.3.1] - 2026-07-24

### Fixed

- Updated the i18n CLI test contract to validate the current reduced command
  surface instead of removed web and domain command groups.

## [1.3.0] - 2026-07-24

### Removed

- Removed the retired frontend application, its dependencies, tests, locale bundles, configuration, and documentation.
- Removed the in-memory web session backend; AI sessions now use the file-backed CLI store.

### Changed

- OpenFatture is now explicitly CLI-first, with interactive terminal mode as its guided user experience.
- Reduced the public CLI to setup, configuration, status, and the agentic assistant; domain and plugin modules remain internal extension boundaries.
- Updated current documentation, version references, and project status to match the `1.3.0` codebase.

### Tooling

- Added deterministic CLI demo validation and modernized GitHub Actions workflows.
- Added pre-commit checks for Python, TOML, YAML, Ruff, Black, and GitHub Actions.
- Consolidated MyPy configuration in `pyproject.toml` and made type checking blocking in CI.
- Updated Make and Docker Compose targets for the current CLI and Alembic workflow.

### Removed

- Removed obsolete media automation workflows, generated scenario videos, and provider-dependent demo scripts.
- Removed obsolete command adapters while retaining core payment, Lightning, SDI, AI, and plugin modules.

## [1.2.0] - 2025-12-02

### Added

- **Event System & Audit Trail**:

  - `EventLog` database model for complete event audit trail with UUID, timestamps, and entity tracking
  - Automatic event persistence with `EventPersistenceListener` (priority -100, error isolation)
  - Entity tracking (invoice, client, etc.) for filtering and timeline generation
  - Metadata support for additional context (JSON format)
  - JSON serialization for datetime, Decimal, nested objects, and lists
  - Global event bus initialization and shutdown management

- **Event Repository**:

  - Advanced query methods with flexible filtering (event_type, entity_type, entity_id, date_range)
  - Full-text search in event data with SQLite LIKE queries
  - Timeline generation for entities with human-readable summaries
  - Statistics aggregation (by type, by entity, total counts)
  - Pagination support (limit, offset)
  - Session management (internal or external session support)

- **Event Analytics Service**:

  - Time-based aggregations: daily, weekly, monthly activity
  - Event type distribution with percentages
  - Entity activity metrics (most active entities)
  - Activity trends comparing recent vs previous periods
  - Event velocity metrics (events per hour)
  - Hourly distribution patterns (0-23h analysis)
  - Comprehensive dashboard summary with key metrics

- **CLI Event Commands** (`openfatture events`):

  - `list` - List events with rich filtering (type, entity, date range, limit)
  - `show <event-id>` - Detailed event view with JSON-formatted data and metadata
  - `stats [--last-days N]` - Statistics summary with event type and entity breakdowns
  - `timeline <entity-type> <entity-id>` - Entity event timeline with tree-style visualization
  - `search <query> [--limit N]` - Full-text search with result snippets
  - `types` - List all event types with counts
  - `dashboard [--days N]` - Comprehensive analytics dashboard with:
    - Key metrics (total events, event types, velocity, trends)
    - Top event types with ASCII bar charts
    - Entity activity distribution
    - Trend indicators (increasing, decreasing, stable)
  - `trends [--days N] [--type TYPE]` - Time-based activity trends with bar charts

- **Visualizations**:
  - ASCII bar charts using Rich (█ blocks scaled to data)
  - Timeline view with tree-style connectors (┌ ├ └)
  - Trend indicators with color coding (green/red/yellow)
  - Formatted tables with proper alignment and styling
  - Panels for headers and detailed views

### Technical

- **Tests**: 45+ new comprehensive tests for event system
  - 13 tests for event persistence (100% passing)
  - 27 tests for EventRepository (filters, search, stats, pagination)
  - 5 integration tests for fattura events (creation, validation, deletion, sending, timeline)
  - All tests passing with proper timezone handling
- **Test Coverage**:
  - Event persistence: 100%
  - Event repository: 91%
  - Event base (event bus): 88%
  - Event analytics: 15% (new module, will increase with usage)
- **Total Project Tests**: ~170 (increased from 117)
- **Architecture**: Observer pattern for event bus, Repository pattern for data access, error isolation for reliability

## [1.1.0] - 2025-10-12

### Changed

- Localised the CLI, interactive experience, email templates, and PDF outputs to English for consistency across platforms.
- Updated documentation, quickstarts, automation tapes, and examples to reflect global English-first messaging.

### Removed

- Dropped the legacy `openfatture payment import-statement` command alias in favour of `openfatture payment import`.

## [1.0.0] - 2025-10-10

### Added

- **Payment Tracking Module** - Enterprise-grade bank reconciliation system:

  **Domain Models**:

  - `BankAccount`: Multi-account support with IBAN validation
  - `BankTransaction`: Full transaction lifecycle (UNMATCHED MATCHED IGNORED)
  - `PaymentReminder`: Automated payment tracking with configurable strategies
  - Value Objects: `MatchResult`, `ReconciliationResult` for type-safe operations
  - Enums: `TransactionStatus`, `MatchType`, `ReminderStatus`, `ReminderStrategy`

  **Application Services**:

  - `MatchingService`: Intelligent payment matching with pluggable algorithms (Facade pattern)
  - `ReconciliationService`: Saga-based workflow for multi-step reconciliation
  - `ReminderScheduler`: Automated payment reminder system with escalation strategies

  **Matching Strategies** (Strategy pattern):

  - `ExactAmountMatcher`: Amount + date window matching (configurable tolerance)
  - `FuzzyDescriptionMatcher`: NLP-based description matching with Levenshtein distance
  - `IBANMatcher`: Direct IBAN/BIC validation for wire transfers
  - `DateWindowMatcher`: Flexible date range matching
  - `CompositeMatcher`: Weighted combination of multiple strategies

  **Import Infrastructure**:

  - Bank statement importers: CSV (Intesa Sanpaolo, UniCredit, Revolut), OFX, QIF
  - Factory pattern for format detection
  - Bank-specific presets with field mapping
  - Transaction deduplication and validation

  **Notification System** (Strategy + Composite patterns):

  - `EmailNotifier`: SMTP with Jinja2 templates (HTML + text fallback)
  - `ConsoleNotifier`: Development/testing output
  - `CompositeNotifier`: Multi-channel notifications (email + SMS + webhook)
  - Configurable SMTP settings with TLS support

  **Reminder Strategies**:

  - `DEFAULT`: Single reminder at due date
  - `PROGRESSIVE`: Escalating reminders (-7, -3, 0, +3, +7 days)
  - `AGGRESSIVE`: Frequent follow-ups for high-risk clients
  - `CUSTOM`: User-defined reminder schedules

  **CLI Interface** (`openfatture payment`):

  - `import`: Bulk transaction import with progress tracking
  - `list-transactions`: Paginated transaction browser with filters
  - `reconcile`: Interactive matching with confidence scores
  - `review`: Review queue for medium-confidence matches
  - `batch-reconcile`: Automated high-confidence reconciliation
  - `ignore`/`reset`: Transaction state management
  - `reminders`: Schedule and manage payment reminders

  **Testing & Quality**:

  - 74 comprehensive tests (62 deliverable + 12 integration)
  - 100% test pass rate
  - 82-96% code coverage on critical services
  - Property-based testing with Hypothesis
  - Integration tests with real database workflows
  - CI/CD pipeline with GitHub Actions (multi-OS, multi-Python)

  **Architecture**:

  - Hexagonal Architecture (Ports & Adapters)
  - Domain-Driven Design (DDD) with aggregates and entities
  - SOLID principles throughout
  - Design patterns: Strategy, Saga, Facade, Composite, Factory
  - Type-safe with full mypy compliance
  - Structured logging with structlog

### Changed

- Enhanced `Pagamento` model with `stato` tracking and `data_pagamento`
- Improved database models for payment reconciliation workflows

### Technical Metrics

- **Production Code**: 6,742 LOC
- **Test Code**: 6,014 LOC
- **Examples**: 900 LOC
- **Total Project Size**: 13,656 LOC
- **Test Coverage**: 85%+ (enforced in CI)
- **Dependencies**: SQLAlchemy, structlog, rapidfuzz, ofxparse

## [0.1.0] - 2025-01-10

### Added

- **Core Invoicing**:

  - FatturaPA XML v1.9 generation with full compliance
  - SDI integration via PEC (Certified Email)
  - Automatic XSD schema validation
  - Digital signature support (P7M, CAdES, PKCS#12)
  - Client and product management with SQLite database
  - Invoice CRUD operations with SQLAlchemy ORM
  - Payment tracking and due date monitoring

- **Interactive CLI**:

  - Modern TUI with Rich and Questionary
  - Hierarchical menu system (9 sections, 40+ actions)
  - Numeric shortcuts (1-9, 0) for fast navigation
  - Fuzzy search in all selectors
  - Multi-selection for batch operations
  - Progress bars for long-running tasks
  - Interactive dashboard with real-time statistics

- **AI-Powered Workflows** (CLI stubs - implementation planned for Phase 4):

  - CLI commands for AI features (`ai describe`, `ai suggest-vat`, `ai forecast`, `ai check`)
  - Placeholder responses showing planned functionality
  - Full implementation with LangChain/LangGraph planned for Phase 4
  - Dependencies included (langchain, langgraph, openai, anthropic, chromadb)

- **Email System**:

  - Professional HTML email templates with Jinja2
  - Multipart MIME support
  - Automatic notifications for SDI events
  - Template preview and testing

- **Batch Operations**:

  - CSV import/export for invoices
  - Bulk send to SDI with progress tracking
  - Bulk delete with safety confirmations
  - Operation history logging

- **Developer Experience**:

  - Type-safe code with Pydantic and mypy
  - Comprehensive test suite with pytest (>80% coverage)
  - Code formatting with Black and Ruff
  - Pre-commit hooks for quality checks
  - Database migrations with Alembic
  - Dynamic versioning with Hatchling
  - Automated version bumping with bump-my-version

- **Autocomplete & Data**:

  - Italian provinces (110 codes)
  - Postal codes for major cities
  - Tax regimes (RF01-RF19)
  - VAT nature codes (N1-N7)
  - Common service descriptions for freelancers
  - Payment methods

- **Configuration**:
  - TOML-based configuration
  - Environment variable support with .env
  - PEC account setup and testing
  - Database initialization wizard

### Changed

- Migrated from Poetry to uv for faster dependency management
- Changed license from MIT to GPL-3.0-or-later

### Security

- Secure credential storage for PEC accounts
- Encrypted digital signature handling
- Input validation for all user data

[2.2.0]: https://github.com/gianlucamazza/openfatture/compare/v2.1.0...v2.2.0
[1.3.1]: https://github.com/gianlucamazza/openfatture/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/gianlucamazza/openfatture/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/gianlucamazza/openfatture/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/gianlucamazza/openfatture/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gianlucamazza/openfatture/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/gianlucamazza/openfatture/releases/tag/v0.1.0
