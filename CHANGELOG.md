# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
    - Trend indicators (📈 increasing, 📉 decreasing, ➡️ stable)
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

- **Web UI Module** - Modern Streamlit-based interface following 2025 Best Practices:
  - **Dashboard**: Real-time KPI with interactive Plotly charts, business metrics, and payment status
  - **AI Assistant**: Chat interface with streaming, invoice description generation, VAT suggestions
  - **Invoice Management**: List with filtering, XML generation, SDI integration preview
  - **Lightning Payments**: Invoice creation, QR code generation, payment monitoring
  - **Security**: File upload validation, input sanitization, rate limiting, CSRF protection
  - **Health Monitoring**: Component status checks, usage metrics, structured logging
  - **Navigation**: Modern st.Page + st.navigation with conditional feature flags
  - **Components**: Reusable React-style library (cards, tables, alerts) reducing duplication by 50%
  - **Caching**: TTL-based intelligent caching with category invalidation
  - **Testing**: 77% coverage with 17 tests, mock-based isolation from Streamlit dependencies

### Technical (Web UI)
- **Architecture**: Service layer pattern with async/sync bridging, component reusability
- **Security**: OWASP-compliant validation, XSS prevention, path traversal protection
- **Performance**: Selective cache invalidation, lazy loading, pagination
- **Configuration**: Production-ready .streamlit/config.toml with security hardening
- **Testing**: Comprehensive test suite with 17 passing tests (100% pass rate)
- **Dependencies**: Streamlit ecosystem (streamlit-aggrid, streamlit-extras, plotly)
- **Best Practices**: Explicit resource cleanup, async standardization, production config

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
  - `BankTransaction`: Full transaction lifecycle (UNMATCHED → MATCHED → IGNORED)
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

[Unreleased]: https://github.com/gianlucamazza/openfatture/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/gianlucamazza/openfatture/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gianlucamazza/openfatture/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/gianlucamazza/openfatture/releases/tag/v0.1.0
