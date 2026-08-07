# OpenFatture contributor guide

OpenFatture is a Python 3.12+ CLI-first application for Italian electronic
invoicing. The public interface is intentionally agentic and small:

- `openfatture init`
- `openfatture assistant [MESSAGE]`
- `openfatture interactive start`
- `openfatture config ...`
- `openfatture status`

Domain operations belong in the application and domain layers. Do not add
another public command for a workflow that the assistant can express through
existing tools.

## Local workflow

```bash
uv sync --all-extras
uv run openfatture --help
uv run python -m pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy openfatture/
```

Use `uv run python -m pytest`, not an unrelated global pytest executable.

## Design rules

- Prefer explicit, typed interfaces and small modules.
- Keep startup read-only; setup happens only through `init`.
- Keep `status` read-only and machine-readable with `--json`.
- Route business actions through the assistant and domain tools.
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
