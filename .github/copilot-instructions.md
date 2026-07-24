# OpenFatture contribution notes

OpenFatture is a Python 3.12+ CLI-first application. The public CLI is:

```text
openfatture init
openfatture assistant [MESSAGE]
openfatture interactive start
openfatture config ...
openfatture status
```

Keep domain capabilities in their core modules and keep optional integrations
behind their existing extension boundaries. Do not reintroduce one public
command group per domain workflow.

Before submitting changes:

```bash
uv sync --all-extras
uv run python -m pytest -q
uv run ruff check .
uv run black --check .
uv run openfatture --help
make demo
```

The deterministic demo is in `scripts/demo.sh`; the terminal recording
contract is `media/automation/quickstart.tape`.
