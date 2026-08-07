# Core vs feature extras vs extensions

How OpenFatture draws the line between **what ships as product core**,
**optional in-tree features**, and **out-of-process extensions**.

Related: [ARCHITECTURE.md](ARCHITECTURE.md), [CONFIGURATION.md](CONFIGURATION.md),
[ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md).

---

## 1. Three layers (not two)

| Layer | Meaning | How you get it | Examples |
|-------|---------|----------------|----------|
| **Core** | Required for Italian electronic invoicing and the public CLI | `uv sync` / `pip install openfatture` | billing, SDI, payment, PDF, storage, events, hooks, platform, CLI |
| **Feature extras** | In-tree modules with heavy or niche deps; same repo, optional install | `uv sync --extra ai` (etc.) | `ai`, `rag`, `ml`, `lightning` |
| **Extensions** | User or third-party automation **outside** the core package API | hooks scripts; future MCP/tools | `~/.openfatture/hooks/*` |

There is **no in-process plugin product API**. User extensions use **hooks**
(see §4–5).

```
                    ┌─────────────────────────────┐
                    │  Public CLI (always core)   │
                    │  init · config · status     │
                    │  assistant* · interactive*  │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   ┌─────────────┐        ┌──────────────┐        ┌────────────────┐
   │    CORE     │        │ FEATURE      │        │  EXTENSIONS    │
   │  billing    │        │  EXTRAS      │        │  hooks scripts │
   │  sdi        │        │  [ai]        │        │  (~/.openfatture│
   │  payment    │        │  [rag]       │        │   /hooks)      │
   │  pdf        │        │  [ml]        │        │                │
   │  storage    │        │  [lightning] │        │  no in-process │
   │  events     │        │              │        │  plugin API    │
   │  hooks eng. │        │  same monorepo│        │                │
   │  platform   │        │  optional deps│        │                │
   └─────────────┘        └──────────────┘        └────────────────┘

* assistant / interactive require the `ai` extra at runtime
```

---

## 2. What is **core**

Must remain installable and useful **without** AI, RAG, ML, or Lightning.

| Package | Role |
|---------|------|
| `cli` | Public surface: init, config, status; wires assistant when `ai` is present |
| `billing` | Clients, invoices, quotes, products, batch |
| `sdi` | FatturaPA XML, validation, signature, PEC, notifications |
| `payment` | Bank import, matching, reconciliation (freelancer day-to-day) |
| `pdf` | Human-readable invoices |
| `storage` | SQLAlchemy models and sessions |
| `events` | Domain event bus and audit trail |
| `hooks` | **Engine** that runs user scripts (core); scripts themselves are extensions |
| `platform` | Config, logging, email templates, validators, extras helpers |
| `i18n` | Locale strings for CLI |

**Product rule:** domain workflows are not re-exposed as large CLI trees; they
are application services + (with `ai`) assistant tools.

---

## 3. What is a **feature extra** (in-tree, not a “plugin”)

Same repository, optional dependencies, guarded imports. Not third-party
plugins: they are **first-party optional product modules**.

| Extra | Package area | Core without it? |
|-------|--------------|------------------|
| `ai` | `openfatture.ai` (assistant, tools, providers, orchestration) | Yes — use domain code only; no assistant |
| `rag` | `openfatture.ai.rag` (+ embeddings stack) | Yes |
| `ml` | `openfatture.ai.ml`, cash-flow forecasting | Yes |
| `lightning` | `openfatture.lightning` | Yes — gated by config; experimental |

**Criteria for staying as an extra (not core):**

- Heavy or native dependencies (torch, prophet, grpc, chromadb, …)
- Not required to issue/send a valid FatturaPA invoice
- Can fail with `MissingExtraError` / clear install hint
- Must not be imported by `platform` or `storage` at module import time

**Criteria for staying in the monorepo (not a separate plugin repo):**

- Shares domain models and application services tightly
- Released on the same version cadence as OpenFatture
- Tested in this CI matrix (`--all-extras` job)

---

## 4. What is a true **extension** (user/third-party)

### 4.1 Hooks (supported today)

- Location: `~/.openfatture/hooks/` (scripts)
- Trigger: domain events via `hooks` engine in lifespan
- Contract: env vars + exit code; no Python import of private packages required
- **This is the supported way to automate Slack, backup, custom notify, etc.**

See `examples/hooks/` and `openfatture/hooks/`.

### 4.2 Assistant tools (with `ai` extra)

- In-tree tools under `openfatture.ai.tools` are **product tools**, not plugins
- Future third-party tools should not land as new public CLI groups; prefer
  tool registration or MCP once designed (redesign D3+)

### 4.3 Out-of-tree packages (future)

A real plugin would be a **separate distribution** (e.g. `openfatture-plugin-foo`)
that:

- Declares compatibility with OpenFatture version
- Does **not** add top-level CLI command groups that duplicate the assistant
- Integrates via hooks, documented tool APIs, or MCP — not by forking core

Until that contract exists, do not document `BasePlugin` as user-facing.

---

## 5. In-process plugins (removed / unsupported)

The experimental `openfatture.plugins` package (`BasePlugin`, discovery,
registry, Typer `get_cli_app`) has been **removed**. It was never wired into
the public CLI lifespan and conflicted with the agentic small command surface.

**Policy:**

1. Do not reintroduce in-process plugins without a design that preserves the
   small public CLI and does not bypass application services.
2. Supported extension today: **hooks**.
3. Future third-party integration: hooks, documented tool contracts, or MCP —
   not ad-hoc CLI command groups.

---

## 6. Misplacements to avoid

| Temptation | Correct placement |
|------------|-------------------|
| “Put payment in a plugin” | **Core** — reconciliation is freelancing core |
| “Put PDF in a plugin” | **Core** — human-readable invoice is expected offline |
| “Put AI in core deps” | **`ai` extra** — keep install light |
| “Put Lightning in core” | **`lightning` extra** — experimental / node-specific |
| “User Slack notify as Python plugin” | **Hook script** |
| “New `openfatture fattura` CLI group” | **No** — assistant tool + application service |
| “Web scraper / voice as core” | **Removed** — not product core |

---

## 7. Decision checklist

When adding a module, ask:

1. **Can a freelancer issue and send a FatturaPA invoice without it?**  
   - No → core (or hard dependency of core).  
   - Yes → extra or extension.
2. **Does it need the same DB models and release train?**  
   - Yes → in-tree package (+ extra if heavy).  
   - No → out-of-tree extension later.
3. **Is the integration “run my script on event X”?**  
   - Yes → **hook**, not a plugin package.
4. **Would it add a public CLI command group?**  
   - Default **no** — conflicts with the agentic surface.
5. **Does `platform`/`storage` import it at import time?**  
   - Must be **no** for extras.

---

## 8. Summary table

| Capability | Classification | Install / enable |
|------------|----------------|------------------|
| FatturaPA / SDI / PEC | Core | default |
| Clients, invoices, quotes, batch | Core | default |
| Payment reconciliation | Core | default |
| PDF | Core | default |
| Events + hooks engine | Core | default |
| User hook scripts | Extension | drop-in files |
| Assistant + domain tools | Feature extra | `--extra ai` |
| RAG | Feature extra | `--extra rag` |
| Cash-flow ML | Feature extra | `--extra ml` |
| Lightning | Feature extra | `--extra lightning` + config |
| In-process plugins API | Not product | **removed** |
| Voice / web scraper | Removed | — |
