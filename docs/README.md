# OpenFatture documentation

This is the current documentation index for the CLI-first, agentic product.

## Start here

- [Quick start](../QUICKSTART.md)
- [CLI reference](CLI_REFERENCE.md)
- [Configuration](CONFIGURATION.md)
- [Project status](STATUS.md)
- [Release notes v2.3.0](releases/v2.3.0.md)
- [Release notes v2.2.0](releases/v2.2.0.md)
- [Release notes v2.1.0](releases/v2.1.0.md)
- [Release notes v2.0.2](releases/v2.0.2.md)
- [Release notes v2.0.1](releases/v2.0.1.md)
- [Release notes v2.0.0](releases/v2.0.0.md)
- [Architecture](ARCHITECTURE.md)
- [Core vs extras vs extensions](CORE_VS_EXTENSIONS.md)
- [AI-era redesign](history/ARCHITECTURE_REDESIGN.md)
- [AI architecture](AI_ARCHITECTURE.md)
- [Technical debt](TECHNICAL_DEBT.md)
- [Security](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)

## Core capabilities

- [PDF generation](PDF_GENERATION.md)
- [Architecture diagrams](history/ARCHITECTURE_DIAGRAMS.md)
- [Internationalization](history/I18N_CLI_IMPLEMENTATION.md)

The assistant is the public entry point for business workflows. Only the
`cliente`, `fattura` and `pagamento` data commands are exposed as
deterministic CLI groups, as thin adapters over the same application services
(see [CLI reference](CLI_REFERENCE.md)).

## Operations

- [Development](DEVELOPMENT.md)
- [Security](../SECURITY.md)
- [Changelog](../CHANGELOG.md)

## Historical material

Design notes, old plans, and release-specific reports live under
`docs/history/`, `docs/releases/`, and `docs/reports/`. They describe prior
states and are not current CLI contracts.
