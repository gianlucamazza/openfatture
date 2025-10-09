# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- **AI-Powered Workflows**:
  - Smart invoice description generation
  - Tax rate and deduction suggestions
  - Cash flow forecasting with ML
  - Compliance checking before SDI submission
  - Multi-agent system with LangGraph orchestration

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

[Unreleased]: https://github.com/gianlucamazza/openfatture/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gianlucamazza/openfatture/releases/tag/v0.1.0
