# Technical Debt Inventory

Honest inventory of remaining debt **after** modernization **2.0** and the
**2.1.0** LangGraph default flip.

**Last updated:** 2026-08-08  
Related: [STATUS.md](STATUS.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md),
[ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md),
[releases/v2.1.0.md](releases/v2.1.0.md), [releases/v2.0.0.md](releases/v2.0.0.md).

---

## Verdict

Structural modernization and AI product backend flip are **done**. Remaining
debt is **oversized modules** and **experimental multi-agent workflows**, not
packaging chaos. Experimental Lightning Network support was **removed** (see
`docs/history/lightning/`).

| Area | Debt level | Notes |
|------|------------|--------|
| Public CLI surface | Low | Small agentic surface; status/extras clean |
| Core billing / SDI / payment | Low | Tools → application; billing re-exports use-cases |
| Package layout | Low | Bounded packages; no empty placeholders |
| AI runtime | Low | Default `langgraph_tool_loop`; single tool-loop; ChatAgent slimmed (structured + rollback) |
| Lightning | **Removed** | Incomplete LND gRPC; archived docs under `docs/history/lightning/` |
| RAG auto-update | Low | Callback required; default auto-update off |
| Tooling / types | Low | No in-code suppressions; only E501 formatter ignore |
| Tests | Low | Skips mostly for external services / interactive |

---

## Modernization status

| Phase | Status |
|-------|--------|
| Repo hygiene + docs | done |
| Ruff-only tooling | done |
| Optional extras | done |
| D0–D3 (layout, tools, runtime) | done |
| Honesty gates (Lightning mock, RAG queue) | done |
| 2.0.0–2.0.2 releases | done |
| LangGraph opt-in product backend | done (2.0.x) |
| LangGraph **default** + ChatAgent slim | done (**2.1.0**) |

---

## High priority (real product risk)

### 1. AI product path — resolved for 2.1.0

- **Default:** `AssistantRuntime` → `GraphAssistantBackend` (`langgraph_tool_loop`).
- **Rollback:** `ASSISTANT_BACKEND=chat` → slim `ChatAgent` (structured output +
  same graph for tool/plain/ReAct turns).
- **Workflows:** `ai.orchestration.workflows.*` remain internal/experimental;
  not on the public CLI.

### 2. AI tools → application services — done

- Thin adapters under `openfatture/ai/tools`.
- Follow-up: split large `*_ops.py` / command modules where complexity grows.

### 3. RAG auto-update queue honesty — resolved

- Requires a real `reindex_callback`; default auto-update remains disabled.

### 4. Lightning Network — removed

- Incomplete experimental module removed from the product tree.
- Historical docs: `docs/history/lightning/`.

---

## Medium priority

### Oversized modules

| Module | ~LOC | Note |
|--------|------|------|
| `ai/agents/cash_flow_predictor.py` | ~1091 | P1 split candidate |
| `ai/orchestration/workflows/invoice_creation.py` | ~921 | experimental |
| `ai/providers/openai.py` | ~855 | provider adapter |
| `ai/tools/registry/core.py` | ~718 | package already split |
| `billing/application/invoice_commands.py` | ~714 | P2 |
| `storage/database/models.py` | ~672 | split by bounded context |
| `billing/application/preventivo_ops.py` | ~550 | P2 |

`chat_agent.py` is slimmed (structured + graph delegation). Registry is a package.

### Experimental workflow human interrupt

- Confidence auto-gates or honest `awaiting_approval`; no invented human decisions.
- Real CLI interrupt is not on the product path.

### Type-safety / lint

- **Resolved:** zero in-code `noqa` / `type: ignore` / `pragma: no cover`.
- Ruff global ignore is only `E501` (formatter-owned).
- `mypy` still ignores entire `tests.*` (optional incremental typing later).
- Third-party packages without stubs use `ignore_missing_imports` in
  `pyproject.toml` (external, not project debt).

### Bulkhead / registry TODOs

- Queue length tracking for bulkhead not implemented (observability).

### ML accuracy drift

- Signal explicitly unavailable (`status: not_implemented`); no silent success claim.

### `async_bridge` nested loops

- `nest_asyncio` optional, else worker thread; primary path `asyncio.run`.

---

## Low priority / acceptable

| Item | Why acceptable |
|------|----------------|
| `except Exception` in hooks/events/email | Intentional isolation |
| External-service test skips | Correct for CI |
| Ruff `E501` ignore | Line length owned by `ruff format` |
| `tests/**` E402 per-file | Fixture/path setup before SUT import |
| `__init__.py` F401 per-file | Public re-export barrels |
| Global coverage floor ~49% in CI | Baseline; payment suite has higher floor (75%) |

---

## Recommended burn-down order

1. Split oversized modules (`cash_flow_predictor`, invoice commands, models)
2. Honest experimental workflow approval nodes (if ever productized)
3. Optional: mypy on selected tests; import-linter boundaries
4. Optional: Textual TUI (product decision)
