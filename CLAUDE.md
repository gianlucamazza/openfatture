# OpenFatture contributor guide

OpenFatture is a Python 3.12+ CLI-first application for Italian electronic
invoicing. The public interface is intentionally agentic and small:

- `openfatture init`
- `openfatture` (starts the interactive assistant; `-m MESSAGE` sends one
  request)
- `openfatture config ...`
- `openfatture status`
- `openfatture fattura ...` (only the SDI journal and the resolutions that
  need a person's evidence, which must never come from the model)

Domain operations belong in the application and domain layers. Business
operations are assistant tools; the CLI never duplicates them. Do not add a
CLI command, or a command group, for anything the assistant can do through a
tool. The remaining commands are thin adapters over application services and
never query ORM models directly.

## Local workflow

```bash
uv sync --all-extras
uv run openfatture --help
uv run python -m pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy openfatture/ tests/
```

Use `uv run python -m pytest`, not an unrelated global pytest executable.

## Design rules

- Prefer explicit, typed interfaces and small modules.
- Startup only reads the setup. When it is missing, the assistant runs `init`
  in a terminal and otherwise refuses with exit code 3; nothing else creates
  the database or the configuration.
- Configuration precedence is environment > secrets (OS keychain or
  `credentials.toml`) > `config.toml` > defaults. Never read `.env` implicitly
  and never write secrets to `config.toml`.
- Keep `status` read-only and machine-readable with `--json`.
- Route business actions through the assistant and domain tools.
- Respect the package import rules in `docs/ARCHITECTURE.md`; they are
  enforced by `tests/test_import_rules.py`.
- Preserve confirmation and validation boundaries for mutating tools.
- Do not add aliases, deprecated command paths, compatibility shims, or
  duplicate implementations.
- Update the CLI reference and tests when the public surface changes.

## Documentation

The canonical user-facing references are:

- `QUICKSTART.md`
- `docs/CLI_REFERENCE.md`
- `docs/CONFIGURATION.md`
- `docs/STATUS.md`

Historical material belongs under `docs/history/` and must not be presented as
current CLI behavior.
