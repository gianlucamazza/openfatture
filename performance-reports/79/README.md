# OpenFatture

OpenFatture is an agentic, CLI-first workspace for Italian electronic
invoicing. Describe the work you need; the assistant coordinates the domain
tools and returns an auditable result.

## Start

```bash
uv sync --all-extras
uv run openfatture init
uv run openfatture status
uv run openfatture assistant "Help me prepare an invoice for a software project"
```

For a terminal conversation:

```bash
uv run openfatture interactive start
```

## Public CLI

The supported surface is intentionally small:

- `init` creates local state and guides setup.
- `assistant` handles business requests in natural language.
- `interactive start` opens a conversational session.
- `config` reads or updates configuration.
- `status` reports local readiness without mutation.

See [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md).

## Documentation

- [Quick start](QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [Architecture](docs/AI_ARCHITECTURE.md)
- [Current status](docs/STATUS.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
uv sync --all-extras
uv run python -m pytest -q
uv run ruff check .
uv run black --check .
uv run mypy openfatture/
```

OpenFatture is released under the MIT License.
