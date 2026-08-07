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
        ├── assistant_backend=chat (default)
        │     ChatAgent tool loop (status id: chat_agent_tool_loop)
        │       ├── NativeToolOrchestrator  (providers with native tools)
        │       └── ReActOrchestrator       (fallback / Ollama)
        │
        └── assistant_backend=langgraph (opt-in)
              GraphAssistantBackend (status id: langgraph_tool_loop)
                ├── StateGraph call_model ↔ call_tools
                ├── ReAct node when provider lacks native tools
                └── node-granularity StreamEvent streaming
        │
        v
ToolRegistry → application services (billing.*) → storage
```

```python
# Preferred API for embedders / tests
from openfatture.ai.runtime import create_assistant_runtime, run_assistant

runtime = create_assistant_runtime()  # default: chat
response = await runtime.run("Elenca le fatture non pagate")

# Opt-in LangGraph product backend (or set ASSISTANT_BACKEND=langgraph)
runtime = create_assistant_runtime(backend="langgraph")
```

Interactive sessions can persist to the file session store
(`persist_session=True`) and be resumed with `session_id=...` /
`openfatture assistant --session <id>`. When persistence is on, history is
loaded from the store (do not also pass a parallel in-memory history that
duplicates turns).

## LangGraph product backend (opt-in)

`GraphAssistantBackend` is a first-class product path behind the same facade.
Default remains **`chat`** until a later release flips the default after soak.
Parity tests (`tests/ai/test_assistant_backend_parity.py`) gate readiness.

```python
from openfatture.ai.runtime.graph import build_assistant_graph

graph = build_assistant_graph(runtime)  # helper / tests; CLI uses runtime.backend
await graph.ainvoke({"user_input": "..."})
```

Set `ASSISTANT_BACKEND=langgraph` or `assistant_backend = "langgraph"` in
config. Check with `openfatture status --json` (`assistant_backend`,
`assistant_backend_id`).

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
