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
        ├── assistant_backend=langgraph (default)
        │     GraphAssistantBackend (status id: langgraph_tool_loop)
        │       ├── StateGraph call_model ↔ call_tools
        │       ├── ReAct when provider lacks native tools
        │       └── typed tool/token StreamEvent streaming
        │
        └── assistant_backend=chat (rollback)
              ChatAgent (status id: chat_agent_tool_loop)
                ├── structured output (output_schema)
                └── tool/plain turns → same GraphAssistantBackend
        │
        v
ToolRegistry → application services (billing.*) → storage
```

```python
# Preferred API for embedders / tests
from openfatture.ai.runtime import create_assistant_runtime, run_assistant

runtime = create_assistant_runtime()  # default: langgraph
response = await runtime.run("Elenca le fatture non pagate")

# Explicit rollback
runtime = create_assistant_runtime(backend="chat")
```

Interactive sessions can persist to the file session store
(`persist_session=True`) and be resumed with `session_id=...` /
`openfatture assistant --session <id>`. When persistence is on, history is
loaded from the store (do not also pass a parallel in-memory history that
duplicates turns).

## LangGraph product backend (default)

`GraphAssistantBackend` is the product tool-loop. There is a **single**
implementation for model↔tools / ReAct / plain turns; `ChatAgent` no longer
maintains a parallel native orchestrator. Parity tests live in
`tests/ai/test_assistant_backend_parity.py`.

```python
from openfatture.ai.runtime.graph import build_assistant_graph

graph = build_assistant_graph(runtime)  # helper / tests; CLI uses runtime.backend
await graph.ainvoke({"user_input": "..."})
```

Rollback: `ASSISTANT_BACKEND=chat`. Inspect with `openfatture status --json`
(`assistant_backend`, `assistant_backend_id`).

## Boundaries

- Provider selection and credentials come from configuration.
- Domain validation stays deterministic outside the model.
- Mutating tools keep confirmation boundaries. Transmit tools
  (`send_invoice_to_sdi`) are off unless named in `ai_enabled_tools`, and
  the registry refuses to send without an explicit human yes when
  `ai_tools_require_confirmation` is true (the default). An interactive TTY
  may prompt; `source="human"` with `confirmed=True` is an API for
  human-facing callers. No built-in UI uses that path yet (there is no TUI).
- AI tools call **application services** (billing/payment/sdi/pdf), not raw
  SQLAlchemy sessions.
- The tool loop in `ai/runtime/graph.py` is the only orchestration path; the
  experimental multi-agent workflows were removed in 2.8.0.
- `search_knowledge_base` searches the tax knowledge packaged in
  `ai/rag/knowledge/`, indexed into `data_dir/vector_store` on first use.

## Tooling

Tools are registered under `openfatture/ai/tools/registry/`. Prefer application
services under `openfatture.billing.application` (and payment/sdi services) for
new tool logic.

## Observability

AI command lifecycle events record success, latency, token usage, and cost when
available.

See [CLI_REFERENCE.md](CLI_REFERENCE.md), [CORE_VS_EXTENSIONS.md](CORE_VS_EXTENSIONS.md),
[ARCHITECTURE_REDESIGN.md](history/ARCHITECTURE_REDESIGN.md).


## Durable local execution

The default LangGraph backend stores checkpoints for persistent assistant
sessions in `data_dir/ai/runtime/checkpoints.sqlite`. Execution receipts and
human reconciliation evidence live alongside them in `executions.sqlite`.
These files are created on the first persistent turn, never by help or status.
Connections close at the end of every invocation, including cancellation.
Back up the runtime directory together with the chat session files. The chat
session store remains the source of conversation history; checkpoints belong
to individual turns, identified by `session_id:turn_id`.

A pending turn is saved before execution. Reopening `assistant --session ID`
resumes it before accepting a new request. Inside an interactive session use
`/resume`. A pending turn cannot be cleared or replaced by another message.
Suspensions and interrupted attempts do not append completed conversation
messages. A completed checkpoint is replayed without another model/tool call
if saving the conversation previously failed. Locks cover the entire turn,
including history writes; another process using the same session fails fast.
Different sessions have independent locks.

Approval uses `interrupt()` before a tool receipt is reserved. The existing
human interaction callback answers the exact tool name and parameter payload;
`Command(resume=...)` records the decision. Without an interaction callback,
the graph remains suspended, and no tool is run. The registry still applies
its allowlist, enablement and confirmation rules. Model arguments cannot grant
human approval. ReAct providers use the same model/tool graph and receipts;
they retain their text prompt/parser protocol.

A durable receipt is reserved before invoking a tool. Completed receipts are
reused. If the process stops after reservation but before its result is saved,
the outcome is uncertain: it is never automatically retried. This includes
cancellation and transport failures after an operation may have started.
Receipts are separate from domain transactions; an uncertain local write also
requires verification. This is conservative recovery, not a claim of exactly
once execution across independent databases or external services.

### Reconciling an uncertain operation

1. Run `/pending` in the resumed interactive session to obtain the receipt ID
   and tool name. Inspect the domain record or external delivery receipt to
   determine the actual outcome before continuing.
2. Submit the verified outcome, including evidence, using:

   ```text
   /reconcile {"call_id":"SESSION:TURN:1:CALL","evidence":"Verified delivery receipt 123","result":{"tool_name":"send_invoice_to_sdi","success":true,"data":{"receipt":"123"}}}
   ```

3. Run `/resume`. The verified result is supplied to the model without
   repeating the original tool invocation. If verification proves no operation
   occurred, record a failed ToolResult with the evidence; a subsequent new
   operation still follows ordinary confirmation policy.

Only receipts belonging to the session's pending turn may be reconciled.
Reconciliation is a human runtime/CLI operation, never an LLM tool. Existing
completed receipts cannot be overwritten.

## Model budgets and streaming

`AI_MODEL_TIMEOUT_SECONDS` defaults to 120; `AI_TOOL_TIMEOUT_SECONDS` defaults
to 60. Both must be positive. Tool timeouts surround execution after human
confirmation, so time spent deciding is not charged to that timeout. A running
synchronous domain function cannot be forcibly interrupted by an asyncio
timeout; its completion is still journaled. Transient model failures get at
most three attempts with exponential jitter. When an SDK already manages
retries, the runtime does not add another retry loop. Invalid requests and
partial output streams are not retried automatically. Mutating tools are not
retried automatically; tool read retries require explicit `retry_safe` metadata.

Generation temperature and output-token limits propagate to model nodes.
The graph also has a recursion bound derived from the iteration budget.
Budget exhaustion returns PARTIAL with `max_iterations_reached`.

Tool start/result/error events are emitted during execution, with call IDs.
The adapter uses typed v2 LangGraph stream envelopes. The v3 projection API
is experimental in the installed version and is not required by the public
StreamEvent contract.
OpenAI and Anthropic structured streams emit content progressively and carry
final usage; other providers with structured streams use the same adapter.
Providers without that capability return buffered content. ReAct responses are
buffered for parsing. Metrics precede the single terminal `done` event.
Interrupted streams are marked incomplete and do not become completed history.
Logs correlate graph nodes and tools through thread ID, iteration and call ID;
existing registry redaction applies to sensitive parameters.

