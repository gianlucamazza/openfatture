# Knowledge Base Integration Blueprint

## 1. Objectives & Context
- Provide AI agents with up-to-date legal, fiscal, and operational knowledge so that answers remain trustworthy in Italian.
- Support core use cases (chat assistant, tax advisor, invoice assistant) with citations and verifiable references.
- Lay the groundwork for multi-agent orchestration (LangGraph) and Phase 4.4+ capabilities.

## 2. Priority Use Cases
- **Conversational Assistance (ChatAgent):** transactional questions (invoice status), procedural guidance (PEC/SDI workflows), regulatory FAQs (VAT obligations).
- **Tax Advisor:** confirm VAT treatments, reverse charge, split payment with references to DPR 633/72 and official circulars.
- **Invoice Assistant:** enrich descriptions with real-world examples and industry best practices.
- **Future agents (Compliance, Cash Flow):** explain SDI checks, detect anomalous payment patterns, outline payment policies.

## 3. Compliance Requirements
- Track source versions and validity dates (`effective_date`, `source_version`).
- Store jurisdiction and legal references (`jurisdiction=IT`, `law_reference`).
- Avoid personal data beyond what invoices already include (GDPR compliant); keep the normative KB separate from customer data.
- Define an update channel: quarterly review with a tax consultant + change log.

## 4. Source Inventory & Formats

| Source | Path/Type | Format | Content | Notes |
|--------|-----------|--------|---------|-------|
| Invoice/Customer database | `openfatture/storage/database/models.py` | SQL (PostgreSQL/SQLite) | Structured invoice/customer data, statuses | Already indexed in RAG (invoices only) |
| Tax Advisor prompt | `openfatture/ai/prompts/tax_advisor.yaml` | YAML | VAT rules and few-shot examples | Primary source for current tax knowledge |
| Configuration docs | `docs/CONFIGURATION.md` | Markdown | VAT tables, VAT codes, PEC settings | Extract relevant sections (chunking) |
| AI Architecture & Roadmap | `docs/AI_ARCHITECTURE.md`, `history/ROADMAP.md` | Markdown | Orchestration overview, RAG TODOs | Operational guidance for agents |
| Phase 4.x summaries | `PHASE_4_*.md` | Markdown | Implementation decisions, AI knowledge | Historical resource — decide whether to index |
| PEC/SDI manuals (external) | TODO | PDF/HTML | Official Agenzia delle Entrate specs | Requires conversion and licensing |
| Customer support FAQ | TODO | Markdown/Notion | Procedures, edge cases | Capture with support team |

## 5. Identified Gaps
- No ingestion pipeline for external YAML/Markdown files; `InvoiceIndexer` handles invoices only.
- No `source` / `law_reference` metadata in the vector store (schema needs extension).
- Missing CLI tooling for KB management (index, status, wipe).
- No tests/metrics to measure RAG accuracy versus prompt-only baselines.

## 6. Stakeholders & Ownership
- **AI/Engineering:** implement pipelines, integrate with agents and tools.
- **Tax Consultant:** validate normative content, manage updates.
- **Support/Operations:** collect FAQs and internal procedures.
- **DevOps:** handle storage, KB backups, ingestion job monitoring.

## 7. Initial Deliverables
- Metadata schema and naming convention for KB entries.
- Markdown/YAML ingestion pipeline with chunking/normalisation.
- CLI script `openfatture ai rag index|stats|reindex`.
- Agent extensions to consume `context.relevant_documents` with citations.
- Logging dashboard: `rag_hit`, `rag_miss`, `source`.

## 8. Next Actions
1. Align with stakeholders on source list, normative priorities, update cadence.
2. Define versioning and naming policy (e.g. `iva_guidelines_2025-01.md`).
3. Design `KnowledgeIndexer` + adapter for Markdown/YAML sources.
4. Extend `RAGSystem` for multi-collection support and `source` filters.
5. Enable `enrich_with_rag()` on ChatAgent with fallback and citation logging.
6. Build retrieval test suite + qualitative benchmarks.

## 9. Proposed KB Schema
- **Mandatory metadata**
  - `document_id`: stable string (slug + version).
  - `source`: enum (`INVOICE`, `TAX_GUIDE`, `CONFIG`, `FAQ`, `SDI_MANUAL`, ...).
  - `law_reference`: string (e.g. `DPR 633/72 art.17 c.6`), optional for non-regulatory docs.
  - `effective_date`: ISO date; use `valid_to` for deprecated content.
  - `jurisdiction`: default `IT`, plan for multi-country later.
  - `tags`: keyword list (e.g. `reverse_charge`, `split_payment`).
  - `chunk_index`: integer preserving original order.
  - `summary`: short description (generated during ingestion for ranking).
  - `source_path`: pointer to the original file (e.g. `docs/CONFIGURATION.md#iva`).
- **Optional metadata**
  - `confidence`: manual confidence level (e.g. unverified FAQs).
  - `reviewed_by`: email/ID of the tax reviewer.
  - `last_reviewed_at`: ISO timestamp.

## 10. Ingestion Pipeline
- **Stages**
  1. **Discovery:** scan source folders (`docs/`, `prompts/`, external storage) using a manifest (`kb_sources.yml`) to define included files.
  2. **Parsing:** load Markdown/YAML → logical structure (headings, tables, examples); normalise markup.
  3. **Chunking:** split into ~350 tokens with 50-token overlap, keep `chunk_index`, generate short summary and keywords (LLM or heuristic).
  4. **Metadata enrichment:** apply schema fields, detect `law_reference` via regex (DPR, art., comma).
  5. **Embedding:** call `create_embeddings()` with caching; fall back to local provider if API key absent.
  6. **Persistence:** write to new Chroma collection (`openfatture_kb`) or dedicate a `source` namespace distinct from invoices.
- **Tooling**
  - CLI `openfatture ai rag index --source tax_guides` for targeted ingestion.
  - Scheduled job (GitHub Actions/cron) to re-index when source files change.
  - JSON logs per chunk (`document_id`, bytes, embedding duration).

## 11. RAG / Vector Store Changes
- **RAGConfig**
  - Add fields `collections`, `default_collection`, `enable_knowledge_kb`.
  - Allow overrides via env (`OPENFATTURE_RAG_KB_COLLECTION`).
- **VectorStore**
  - Support multiple collections: `get_collection(name)`; `add_documents` accepts optional `collection`.
  - Built-in filters for `source`, `effective_date`.
- **InvoiceIndexer**
  - Refactor into `BaseIndexer` + `InvoiceIndexer`.
  - New `KnowledgeIndexer` for Markdown/YAML with chunking pipeline.
- **RAGSystem**
  - Factory to create indexers/retrievers per source type (invoice, knowledge).
  - Method `search_knowledge(query, source=None, filters=None)`.
- **Retrieval**
  - Introduce a simple re-ranker (similarity + tag matches).
  - Formatter returns snippets with citations (`source_path`, `law_reference`).

## 12. Agent Integration
- **ChatAgent**
  - Toggle `config.rag_enabled=True`.
  - Call `enrich_with_rag(context, user_input)` with debouncing (skip very short/system messages).
  - Update `_build_system_prompt` to include up to three citations formatted as `[1] DPR 633/72 art...`.
  - Handle fallback: log `rag_miss` and continue with the base prompt.
- **TaxAdvisor**
  - Hybrid mode: YAML prompt + top-2 KB snippets filtered by tag `iva`.
  - Enforce that outputs cite at least one reference when provided by snippets.
- **InvoiceAssistant**
  - Retrieve similar descriptions (tag `invoice_example`) for dynamic few-shot augmentation.
- **LangGraph (future)**
  - Dedicated `KnowledgeRetriever` node reused across agents.

## 13. Tooling & CLI
- New commands `openfatture ai rag ...`:
  - `status`: show document counts, collections, last update.
  - `index --source <name>`: ingest specific sources.
  - `reindex --since <date>`: rebuild updated chunks.
  - `search "<query>" --source tax_guides --top 5`: quick team debugging.
- Extend Chat UI `/tools` to include `search_knowledge_base`.
- Update `ToolRegistry`:
  ```python
  Tool(
      name="search_knowledge_base",
      description="Retrieve normative extracts and operational notes",
      parameters=[...],
      category="knowledge",
  )
  ```
- Tool output should return snippets + citations; ChatAgent formats them as bullet points.

## 14. Testing & Quality
- **Unit Tests**
  - Markdown chunking (length, heading preservation).
  - Metadata enrichment (legal reference regex).
  - VectorStore multi-collection support.
- **Integration Tests**
  - End-to-end ingestion on sample `docs/iva_sample.md`.
  - Retrieval assertions for key queries (e.g. "reverse charge edilizia").
  - ChatAgent with mocked RAG → assert that responses include citations.
- **Benchmarking**
  - Compare TaxAdvisor answers with/without RAG (precision@3 for citations).
  - Monitor embedding costs versus baseline.

## 15. Observability & Rollout
- Structured logging (`rag_event`, `source`, `similarity`, `latency_ms`, `chunks_used`).
- Feature flag `AISettings.rag_enabled` + `AISettings.rag_mode` (`disabled`, `knowledge_only`, `full`).
- Gradual rollout:
  1. **Phase Alpha:** internal team with manual flag.
  2. **Beta:** subset of CLI users, capture feedback.
  3. **GA:** flag on by default, documentation updated (`docs/AI_ARCHITECTURE.md`, README).
- Incident response: disable flag via env, flush collection if needed.
