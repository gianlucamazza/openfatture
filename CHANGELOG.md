# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
