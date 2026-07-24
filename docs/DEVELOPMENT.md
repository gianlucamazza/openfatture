# Development

## Setup

Requirements:

- Python 3.12 or newer
- `uv`
- `make`
- Docker, only for container checks
- `actionlint` and `act`, only for local workflow validation

Install the locked development environment:

```bash
uv sync --all-extras
uv run pre-commit install
```

Copy `.env.example` to `.env` only when local provider or email credentials are
needed. The deterministic CLI demo does not require credentials.

## Daily checks

```bash
make demo
make lint-check
make test-fast
```

The public CLI is intentionally small:

```bash
uv run openfatture --help
uv run openfatture assistant --help
uv run openfatture interactive --help
uv run openfatture status --json
```

Use `make format` for an intentional rewrite and `make pre-commit` before
opening a pull request.

## Tests

The default pytest configuration excludes performance, benchmark, slow, e2e,
and external-service tests. Run focused suites directly when changing a core
module:

```bash
make test-unit
make test-integration
make test-payment
```

Payment, Lightning, SDI, storage, and AI remain core/domain modules. Their
implementation and tests are independent from the public CLI adapters.

## GitHub Actions

Validate workflow syntax and the deterministic demo plan without containers:

```bash
./scripts/validate-actions.sh
./scripts/test-actions.sh dry-run
```

Run the demo job with Docker when the local daemon and network are available:

```bash
./scripts/test-actions.sh demo
```

`act` does not receive repository secrets automatically. If a workflow needs a
secret, pass an explicit local secret file with `act --secret-file`; never
commit that file or generate it from shell history.

## Database

Use Alembic for schema changes:

```bash
make db-migrate
```

Create a migration only when the domain model change is intentional, and run
the relevant storage tests before committing it.

## Docker

Use the Docker Compose v2 command:

```bash
docker compose up -d
docker compose down
make docker-test
```

The payment image packages the payment core for isolated checks; it does not
restore a payment CLI command.
