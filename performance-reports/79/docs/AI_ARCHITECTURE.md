# AI Architecture

OpenFatture exposes one agentic business entry point: the assistant. The
assistant translates a natural-language request into a bounded sequence of
domain-tool calls and presents the result in the terminal.

## Flow

```
CLI request
    |
    v
ChatAgent -> provider -> response
    |
    +-> read tools  -> local repositories and reports
    +-> write tools -> validated domain services
    +-> events      -> audit and metrics
```

The interactive command uses the same assistant session runner and keeps
conversation history in the file-backed session store.

## Boundaries

- Provider selection and credentials come from configuration.
- Domain validation remains deterministic and executes outside the model.
- Mutating tools are responsible for their own confirmation and authorization
  boundaries.
- The CLI never performs setup implicitly at import or startup.
- `status` is read-only and does not contact external services.

## Tooling

Tools are registered in `openfatture/ai/tools/registry.py` and grouped by
domain. Read operations retrieve local data; write operations delegate to
application services. The assistant is not a replacement for validation,
signing, or SDI transport rules.

## Sessions and observability

Conversation sessions are persisted as JSON files through
`openfatture.ai.session.get_session_store`. AI command lifecycle events record
success, latency, token usage, and estimated cost when available.

For the supported user workflow, see [CLI_REFERENCE.md](CLI_REFERENCE.md).
