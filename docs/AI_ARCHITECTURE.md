# AI Architecture

OpenFatture exposes one agentic business entry point: the assistant. All
CLI and interactive traffic goes through **`openfatture.ai.runtime`**.

## Product path (only supported entry)

```
CLI assistant / interactive
        │
        v
openfatture.ai.runtime.AssistantRuntime
        │
        v
ChatAgent tool loop          ← product backend (status: chat_agent_tool_loop)
  ├── NativeToolOrchestrator  (providers with native tools)
  └── ReActOrchestrator       (fallback)
        │
        v
ToolRegistry → application services (billing.*) → storage
```

```python
# Preferred API for embedders / tests
from openfatture.ai.runtime import create_assistant_runtime, run_assistant

runtime = create_assistant_runtime()
response = await runtime.run("Elenca le fatture non pagate")
```

Interactive sessions can persist to the file session store
(`persist_session=True`) and be resumed with `session_id=...` /
`openfatture assistant --session <id>`. When persistence is on, history is
loaded from the store (do not also pass a parallel in-memory history that
duplicates turns).

## Optional LangGraph multi-node helper (not the product path)

`build_tool_loop_graph` / `build_assistant_graph` compile a model↔tools
StateGraph for tests, observability, or a future product switch. **2.0.0 does
not route CLI traffic through this graph** (policy B1-β). Promoting it to the
product path requires explicit parity tests.

```python
from openfatture.ai.runtime.graph import build_assistant_graph

graph = build_assistant_graph(runtime)
await graph.ainvoke({"user_input": "..."})
```

## Boundaries

- Provider selection and credentials come from configuration.
- Domain validation stays deterministic outside the model.
- Mutating tools keep confirmation boundaries.
- AI tools call **application services** (billing/payment/sdi/pdf), not raw
  SQLAlchemy sessions.
- Multi-agent workflows under `ai/orchestration/workflows/` are **internal /
  experimental** and are **not** registered on the public CLI.

## Tooling

Tools are registered in `openfatture/ai/tools/registry.py`. Prefer application
services under `openfatture.billing.application` (and payment/sdi services) for
new tool logic.

## Observability

AI command lifecycle events record success, latency, token usage, and cost when
available.

See [CLI_REFERENCE.md](CLI_REFERENCE.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md),
[ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md).
