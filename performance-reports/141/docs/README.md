# OpenFatture documentation

This is the current documentation index for the CLI-first, agentic product.

## Start here

- [Quick start](../QUICKSTART.md)
- [CLI reference](CLI_REFERENCE.md)
- [Configuration](CONFIGURATION.md)
- [Project status](STATUS.md)
- [Release notes v2.0.2](releases/v2.0.2.md)
- [Release notes v2.0.1](releases/v2.0.1.md)
- [Release notes v2.0.0](releases/v2.0.0.md)
- [Architecture](ARCHITECTURE.md)
- [Core vs extras vs extensions](CORE_VS_EXTENSIONS.md)
- [AI-era redesign](ARCHITECTURE_REDESIGN.md)
- [AI architecture](AI_ARCHITECTURE.md)
- [Technical debt](TECHNICAL_DEBT.md)
- [Security](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)

## Core capabilities

- [PDF generation](PDF_GENERATION.md)
- [Architecture diagrams](ARCHITECTURE_DIAGRAMS.md)
- [Internationalization](I18N_CLI_IMPLEMENTATION.md)

The assistant is the public entry point for business workflows. The
underlying domain and integration modules remain available to the assistant
and to extension code, but they are not duplicated as top-level CLI command
groups.

## Operations

- [Development](DEVELOPMENT.md)
- [CI/CD](operations/SETUP_CI_CD.md)
- [Security](../SECURITY.md)
- [Changelog](../CHANGELOG.md)

## Historical material

Design notes, old plans, and release-specific reports live under
`docs/history/`, `docs/releases/`, and `docs/reports/`. They describe prior
states and are not current CLI contracts.
