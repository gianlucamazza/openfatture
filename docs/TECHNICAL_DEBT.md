# Technical Debt Inventory

Honest inventory of remaining debt **after** the 2.0.0 modernization release
(hygiene, Ruff-only tooling, extras, package reorg, core/extension boundaries,
D2 tools, D3 runtime, honesty gates).

**Last updated:** 2026-08-07  
Related: [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md), [ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md),
[releases/v2.0.0.md](releases/v2.0.0.md).

---

## Verdict

Structural modernization for 2.0.0 is **done**. Remaining debt is mostly
**product completeness** (Lightning gRPC, oversized modules, experimental
workflows), not packaging chaos.

| Area | Debt level | Notes |
|------|------------|--------|
| Public CLI surface | Low | Small agentic surface; status/extras clean |
| Core billing / SDI / payment | Low | Tools → application; billing namespaces re-export use-cases |
| Package layout | Low | Bounded packages; no empty placeholders |
| AI runtime | Medium | Product = ChatAgent; LangGraph multi-node is tested helper only |
| Lightning | Medium–High | Fail-closed; simulate_payment gated; real gRPC still missing |
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
| D0 non-core cut | done |
| D1 package reorg | done |
| Core vs extras vs extensions | done (plugins package removed) |
| Honesty gates (Lightning mock, RAG queue) | done |
| D2 tools → application services | done |
| D3 single assistant runtime | done |
| 2.0.0 release notes | done |

---

## High priority (real product risk)

### 1. AI product path vs LangGraph helper

- **Product path:** `AssistantRuntime` → `ChatAgent` (native tools / ReAct).
- **Helper:** `ai.runtime.graph.build_tool_loop_graph` (multi-node model↔tools).
- **Workflows:** `ai.orchestration.workflows.*` remain internal/experimental.
- **Remaining:** promote graph to product only with parity tests; fix simulated
  human approval in experimental workflows or rename nodes honestly.

### 2. Lightning LND real gRPC still missing

- **Files:** `openfatture/lightning/infrastructure/lnd_client.py`
- **Honesty:** Mock is **off by default** (`allow_mock=False` /
  `lightning_allow_mock=false`). Without stubs, operations raise `LNDClientError`.
- **Status:** Silent mock **fixed**; full RPC **still open**. Lightning is
  experimental until real bindings land.

### 3. AI tools → application services — done

- All AI tool modules under `openfatture/ai/tools` are thin adapters.
- Domain use-cases: `billing.application.*`, `payment.application.*`,
  `sdi.application.*`, `pdf.tool_ops`.
- **Follow-up:** split large `*_ops.py` modules where complexity grows.

### 4. RAG auto-update queue honesty — resolved

- Requires a real `reindex_callback` (wired by `AutoIndexingService`).
- Default auto-update remains disabled.

---

## Medium priority

### Oversized modules

- `ai/agents/cash_flow_predictor.py`, `chat_agent.py`
- `ai/tools/registry.py`
- `ai/orchestration/workflows/invoice_creation.py`
- `billing/application/preventivo_ops.py`, `prodotto_ops.py`, `invoice_commands.py`
- `storage/database/models.py`

### Empty billing packages — resolved as re-exports

- `billing/clienti`, `billing/prodotti`, `billing/fiscale` re-export
  application modules (no empty placeholders).

### Experimental workflow human interrupt

- `invoice_creation` / `compliance_check` use **confidence auto-gates** or
  leave `awaiting_approval` without inventing human decisions. Real CLI
  interrupt is not on the product path (internal workflows only).

### Type-safety / lint

- **Resolved:** zero in-code `noqa` / `type: ignore` / `pragma: no cover`.
  Ruff global ignore is only `E501` (formatter-owned).
- Remaining: `mypy` still ignores entire `tests.*`.
- Third-party packages without stubs use `ignore_missing_imports` in
  `pyproject.toml` (external, not project debt).

### Bulkhead / registry TODOs

- `ai/tools/registry.py`: queue length tracking for bulkhead not implemented.

### ML accuracy drift

- Signal **explicitly unavailable** (`status: not_implemented` in
  `get_trigger_summary`); does not silent-trigger and does not claim
  “accuracy is fine”.

### Fuzzy matcher — resolved

- No Mock/MagicMock special-casing in production matcher.

### `async_bridge` nested loops

- Documented nested path: `nest_asyncio` optional, else worker thread.
  Primary path remains `asyncio.run`.

---

## Low priority / acceptable

| Item | Why acceptable |
|------|----------------|
| `except Exception` in hooks/events/email | Intentional isolation |
| Retry / rate-limit `sleep` | Normal control flow |
| External-service test skips | Correct for CI |
| SQLAlchemy `.is_(True)` / `.is_(False)` | Correct ORM boolean comparisons |
| Ruff `E501` ignore | Line length owned by `ruff format` |
| `tests/**` E402 per-file | Fixture/path setup before SUT import |
| `__init__.py` F401 per-file | Public re-export barrels |

---

## Counts (approximate)

| Signal | Count / note |
|--------|----------------|
| Explicit `TODO` in code | ~15 (LND, bulkhead, ML drift, …) |
| `type: ignore` / `noqa` / `pragma: no cover` | **0** |
| AI tools → application layer only | D2 done |
| Skipped tests | mostly external/interactive |

---

## Recommended burn-down order

1. Session resume polish and graph test coverage (product UX)
2. Lightning: real gRPC **or** keep hard experimental posture in docs/CLI
3. Split oversized ops modules
4. Honest experimental workflow approval nodes
5. Optional: mypy on tests; import-linter boundaries
