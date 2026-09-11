# Architecture redesign: AI-era product shape

**Status:** design analysis (2026-08)  
**Scope:** what should be redesigned given modern agentic products and LangGraph, and what is non-core enough to remove or deprecate.  
**Constraint:** public surface stays small (`init`, `assistant`, `interactive`, `config`, `status`). No long-lived import shims.

Related: [ARCHITECTURE.md](ARCHITECTURE.md), [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md), [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md).

---

## 1. Product thesis (target)

OpenFatture is **local-first Italian electronic invoicing** with an **optional agentic assistant**. The model does not own business rules: FatturaPA, SDI, validation, and mutations stay deterministic.

| Layer | Responsibility |
|-------|----------------|
| **Domain core** | Billing, SDI, payment, PDF, storage, events, hooks |
| **Assistant runtime** | One multi-turn agent that calls domain tools |
| **Optional satellites** | RAG, forecasting, Lightning, scraper, voice — only if product-proven |

Today the tree mixes those layers and runs **two incomplete AI runtimes** in parallel.

---

## 2. Critical redesign areas

### 2.1 Dual AI runtimes (highest priority)

**What exists**

| Runtime | Location | Used by product? |
|---------|----------|------------------|
| **A. Chat + tools** | `ChatAgent` → `NativeToolOrchestrator` / `ReActOrchestrator` → `ToolRegistry` | **Yes** — `openfatture assistant` |
| **B. LangGraph workflows** | `orchestration/workflows/*` (`InvoiceCreationWorkflow`, `ComplianceCheckWorkflow`, `CashFlowAnalysisWorkflow`) | **No** — tests and internal wiring only |
| **C. Specialized `BaseAgent`s** | `invoice_assistant`, `tax_advisor`, compliance, payment insight, orphan analytics agents | Partly — only inside LangGraph (B) or payment insight service |

**Why it’s wrong now**

Modern agentic products converge on **one graph-shaped runtime**:

- one (or few) entry graphs,
- tools / sub-agents as nodes,
- checkpointed multi-turn state,
- interrupts for human approval on mutations.

We have reinvented tool loops (A) **and** adopted LangGraph (B) without connecting them to the CLI. LangGraph is paid for as a dependency and maintained in tests, but the user-facing path never enters a `StateGraph`.

**Target**

```
CLI assistant / interactive
        │
        ▼
┌───────────────────────────────┐
│  LangGraph assistant graph    │  ← single runtime
│  - model node                 │
│  - tool node(s)               │
│  - optional subgraphs         │  (invoice draft, compliance)
│  - interrupt on write tools   │
│  - checkpointer (session)     │
└───────────────────────────────┘
        │
        ▼
 domain application services (billing, sdi, payment, …)
```

- **Delete or absorb** hand-rolled `ReActOrchestrator` once providers with native tools cover the matrix (OpenAI, Anthropic, current Ollama all support tools; keep a thin fallback only if measured).
- **Delete or absorb** `NativeToolOrchestrator` into LangGraph `ToolNode` / prebuilt agent patterns.
- **Promote** the useful multi-step flows (invoice creation with tax + compliance) to **subgraphs or tool-invoked graphs**, not a second product path.
- **Wire** checkpointing to interactive sessions (today `ai/session` is largely disconnected from the CLI chat loop, which keeps a raw `list[dict]` in memory).

---

### 2.2 Agent zoo vs tools-first assistant

**What exists**

Many “agents” are really **prompt + structured output** wrappers:

- `InvoiceAssistantAgent`, `TaxAdvisorAgent`, `PaymentInsightAgent`
- Orphans (no production callers outside their modules):  
  `ClientIntelligenceAgent`, `InvoiceAnalysisAgent`, `PerformanceAnalyticsAgent`

Plus a full custom hierarchy: `AgentProtocol` / `BaseAgent` / per-agent `*Context` types (~context.py bloat).

**Why it’s wrong now**

2024–2026 product pattern:

1. **Default:** one assistant + **tools** (CRUD, reports, “suggest VAT”, “expand description”).
2. **When needed:** specialist behavior as **tools** or **subgraph** with a fixed system prompt — not a parallel class hierarchy.
3. Analytics-style agents without a user journey are research code, not product.

**Target**

- Keep **capabilities**, drop **agent classes** where a tool + schema suffices.
- Map:
  - description expansion → tool `expand_invoice_description` (or subgraph step)
  - tax advice → tool `suggest_vat_treatment`
  - compliance → pure domain service + optional LLM explanation tool
  - payment insight → keep as application service called by payment tools
- **Deprecate/remove** orphan agents and their contexts/models if unused by tools or graphs.

---

### 2.3 Custom tool protocol instead of standard tool contracts

**What exists**

- Homegrown `Tool` / `ToolParameter` OpenAI-shaped models
- `ToolRegistry` (~700+ lines) with circuit breaker, bulkhead, rate limit, confirmation
- Tools often talk to **SQLAlchemy/session** directly instead of application services
- No MCP; no shared schema with LangGraph tools

**Why it’s wrong now**

- Resilience belongs at **HTTP/provider** and **domain service** boundaries, not reimplemented per tool registry.
- Application layer should own transactions; tools should be thin adapters (agent-safe API).
- Ecosystem direction: **structured tools** (Pydantic/args schema) + graph execution; optionally **MCP** later for external plugins.

**Target**

- One tool definition style (prefer Pydantic models / `@tool`-like registration).
- `execute` → application service only; ban new raw session access in tools.
- Confirmation → LangGraph **interrupt** (or single CLI confirm hook), not a second policy engine inside the registry.
- Shrink registry to: discover, schema export, dispatch, audit event.

---

### 2.4 Provider stack as mini-framework

**What exists**

Custom `BaseLLMProvider` + OpenAI / Anthropic / Ollama implementations (~2.4k LOC): streaming, tool formats, token accounting, errors — duplicated per vendor.

**Why it’s wrong now**

SDKs and LangGraph model wrappers already cover streaming and tools. Maintaining three full adapters is high cost for a CLI product.

**Target (pick one, prefer thin)**

1. **Thin SDK adapters** (official `openai` / `anthropic` / Ollama HTTP) returning a minimal internal `ModelResponse`, **or**
2. LangGraph-compatible chat models only at the graph edge.

Keep: config selection, cost estimate hooks, redaction. Drop: parallel streaming event systems if the graph already streams.

---

### 2.5 Session, memory, and HITL are fragmented

**What exists**

| Concern | Implementation | Wired to CLI assistant? |
|---------|----------------|-------------------------|
| Multi-turn chat | In-memory `list[dict]` in `assistant.py` | Yes |
| File session store | `ai/session` | Largely **no** |
| LangGraph checkpoint | Optional in workflows | Only workflows |
| HITL workflows | `human_loop.py` + state reviews | Workflows only |
| Tool confirmation | `requires_confirmation` on tools | Registry path |

Docs claim sessions go through `get_session_store`; the public assistant does not use it.

**Target**

- One session identity for interactive mode → checkpointer + optional file export.
- One mutation gate: interrupt/confirm before write tools.
- Delete or fold `human_loop` into that gate; stop maintaining two approval UX paths.

---

### 2.6 RAG as a second product

**What exists**

ChromaDB, embeddings (OpenAI + sentence-transformers), auto-update queue with stubs, knowledge tools — ~3.5k LOC + heavy deps.

**Why rethink**

For freelancers, RAG over regulations is nice-to-have, not the core job (“issue and send a valid invoice”). Operational cost (models, index drift, stubs) is high.

**Target**

- **Optional extra** only (already planned).
- Ship assistant **without** RAG first; reintroduce as `knowledge.search` when quality is measured.
- Prefer one embedding path; delete auto-update stubs or implement fully — no half systems.

---

### 2.7 Classic ML forecasting inside the monorepo

**What exists**

Prophet + XGBoost ensemble, retraining scheduler, cash_flow_predictor agent, LangGraph cash_flow workflow — ~4.5k+ LOC, heavy native deps.

**Why rethink**

This is a **data-science product**, not required for FatturaPA. It pulls the install and CI matrix (libomp, etc.) and is not on the public CLI.

**Target**

- **Deprecate from core product**; optional `ml` extra or separate package later.
- If retained: pure batch/report tool, no LangGraph ceremony until a user-facing command exists.

---

### 2.8 Domain package shape (non-AI, still wrong)

**What exists**

- `payment` / `lightning`: DDD folders  
- `core`: flat entity bags + empty packages  
- `utils`: grab-bag  
- `services.pdf`: third naming scheme  
- Tools and agents import storage models freely  

**Target** (unchanged from modernization plan)

```
billing/  sdi/  payment/  pdf/
events/  hooks/  storage/  platform/
ai/          # assistant runtime + tools only
```

Import rule: **ai → application services → domain/storage**, never tools → ORM as the long-term pattern.

---

### 2.9 Plugins, voice, scraper, Lightning, media

| Area | Reality | Redesign stance |
|------|---------|-----------------|
| **plugins** | Discovery/registry incomplete | **Removed**; hooks + tools until MCP |
| **voice** | ~1.7k LOC, no public CLI command | Deprecate or archive until demand |
| **web_scraper** | Playwright stack, config hooks, not product path | **Removed (D0)** |
| **lightning** | DDD + gRPC stubs; lifespan integration | Keep as **hard optional**; do not block core; finish LND or remove client pretence |
| **media/** | Dashboards, tapes, OBS presets | Not runtime product; keep as ops/marketing only, never import from package |
| **landing-page/** | Separate static site | Keep out of Python package |

---

## 3. Target architecture (concise)

```
                    ┌──────────── public CLI ────────────┐
                    │ init config status                 │
                    │ assistant / interactive ──┐        │
                    └───────────────────────────│────────┘
                                                ▼
                              ┌────────────────────────────────┐
                              │ AssistantGraph (LangGraph)     │
                              │  model ↔ tools ↔ interrupts    │
                              │  checkpointer = session        │
                              └────────────┬───────────────────┘
                                           │ tools only
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
              billing app            sdi app                 payment app
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           ▼
                              storage + events + hooks
```

**Naming**

| Avoid | Prefer |
|-------|--------|
| `core` | `billing` (+ `events` / `hooks`) |
| `utils` | `platform` |
| `services.pdf` | `pdf` |
| `web_scraper` | remove or `scraper` satellite |
| `*Agent` for pure prompts | `tools` / `skills` / graph nodes |
| Dual “orchestrator” types | one graph runtime |

---

## 4. Deprecate / remove (authorized non-core)

Prioritized for deletion or archival under `docs/history/` + git history (no shims).

### Remove or archive soon (low product value, high noise)

1. **Orphan specialized agents**  
   `client_intelligence_agent`, `invoice_analysis_agent`, `performance_analytics_agent` + matching contexts/output models if unused.
2. **Voice package** (`openfatture/ai/voice`) until a real CLI story exists.
3. **Web scraper package** + Playwright from default story (extra or out of tree).
4. **LangGraph workflows as a second product path** — either merge into the assistant graph or delete; stop maintaining three large workflow modules only for tests.
5. **Hand-rolled ReAct path** after native tool coverage is verified for supported providers.
6. **Dead session/doc drift** — either wire `ai/session` to interactive or delete unused store code paths.
7. **Incomplete plugin system** — freeze; document “no public plugin API” until redesigned.
8. **media/** automation — stay non-package; do not grow into runtime.

### Demote to optional / freeze (do not invest)

| Module | Action |
|--------|--------|
| `ai/ml` + cash flow predictor | optional extra only; freeze features |
| `ai/rag` + auto_update stubs | optional; implement or delete stubs |
| `lightning` | optional; real gRPC or honest “experimental” status |
| `ai/feedback` | keep minimal metrics; drop productized feedback UI ambitions |
| `ai/cache` | keep only if measured cost win; else simplify |

### Keep as core

- FatturaPA XML, validation, signature, PEC/SDI notifications  
- Clients, invoices, quotes, products, batch import  
- Payment reconciliation (bank import / matching) — high freelancer value  
- PDF generation  
- Events + hooks  
- Assistant + **domain tools** that exercise the above  
- Config / status / init  

---

## 5. Phased redesign (recommended)

| Phase | Work | Outcome |
|-------|------|---------|
| **D0** | Cut orphans: agents, voice, scraper from default tree; freeze ML/RAG extras | **Done** |
| **D1** | Domain rename (`billing`, `events`, `hooks`, `platform`, `pdf`) | **Done** |
| **D2** | Tools → application services only; slim registry | **Done** |
| **D3** | Single assistant runtime entry; LangGraph helper | **Done** (product path); multi-node graph TBD |
| **D4** | Absorb invoice/tax/compliance as subgraph or tools; delete parallel workflow product | One UX |
| **D5** | Thin providers; delete ReAct if unused | Less framework |
| **D6** | Optional RAG/ML only with measured quality gates | Honest extras |

D0–D1 landed in the 2.0 modernization tree; D2–D5 are the remaining **AI-era** redesign.

---

## 6. Explicit non-goals

- Browser/web app frontend  
- Recreating a large domain CLI (`fattura`, `cliente`, …)  
- Compatibility shims for old import paths  
- Building a general LangChain app platform — stay a **vertical invoicing agent**

---

## 7. Decision checklist (for implementation PRs)

When touching AI code, ask:

1. Does this serve **assistant → tools → domain services**?  
2. Is there already a second path (workflow / agent / orchestrator) that should be deleted instead of extended?  
3. Does it introduce deps that belong in an **extra**?  
4. Can a **tool + schema** replace a new `*Agent` class?  
5. Is HITL/session handled by the **single** graph/session mechanism?

If the answer is “extend the zoo”, stop and redesign.
