# Knowledge Base Integration Blueprint

## 1. Obiettivi e Contesto
- Fornire ai nuovi agent un contesto legale, fiscale e operativo aggiornato per risposte affidabili in italiano.
- Supportare casi d'uso core (chat assistant, tax advisor, invoice assistant) con citazioni e riferimenti normativi verificabili.
- Abilitare l'espansione verso orchestrazioni multi-agent (LangGraph) e future funzionalità Phase 4.4+.

## 2. Casi d'Uso Prioritari
- **Assistenza Conversazionale (ChatAgent)**: risposte a domande transazionali (es. stato fatture), procedurali (workflow PEC/SDI), normative (obblighi IVA).
- **Tax Advisor**: conferma trattamenti IVA, reverse charge, split payment, con riferimento puntuale a DPR 633/72 e circolari.
- **Invoice Assistant**: arricchimento descrizioni con esempi reali e best practice di settore.
- **Future agent (Compliance, Cash Flow)**: spiegazione controlli SDI, pattern anomali, politiche di pagamento.

## 3. Requisiti di Compliance
- Conservare versioni e data di validità delle fonti (campo `effective_date`, `source_version`).
- Annotare giurisdizione e riferimento normativo (`jurisdiction=IT`, `law_reference`).
- Evitare archiviazione di dati personali oltre quelli già presenti in fatture (rispetto GDPR); separare KB normativa da dati clienti.
- Channel per aggiornamenti: revisione trimestrale con consulente fiscale, log delle modifiche.

## 4. Inventario Fonti & Formati

| Fonte | Percorso/Tipo | Formato | Contenuto | Note |
| - | - | - | - | - |
| Database fatture/Clienti | `openfatture/storage/database/models.py` | SQL (PostgreSQL/SQLite) | Dati strutturati fatture, clienti, stati | Già indicizzati in RAG (solo fatture) |
| Prompt Tax Advisor | `openfatture/ai/prompts/tax_advisor.yaml` | YAML | Norme IVA sintetizzate, few-shot | Fonte primaria per knowledge normativa attuale |
| Documentazione configurazione | `docs/CONFIGURATION.md` | Markdown | Tabelle aliquote, codici IVA, configurazioni PEC | Estrarre sezioni rilevanti (chunking) |
| AI Architecture & Roadmap | `docs/AI_ARCHITECTURE.md`, `ROADMAP.md` | Markdown | Visione orchestrazione, TODO RAG | Informazioni operative per agent |
| Summaries Fase 4.x | `PHASE_4_*.md` | Markdown | Decisioni implementative, knowledge AI | Fonte storica, definire se indicizzare |
| Manuale PEC/SDI (esterno) | TODO | PDF/HTML | Specifiche ufficiali Agenzia Entrate | Richiede conversione e licenza |
| FAQ supporto clienti | TODO | Markdown/Notion | Procedure, edge case | Da raccogliere con team supporto |

## 5. Gap Identificati
- Nessun ingestion pipeline per YAML/Markdown esterni; `InvoiceIndexer` indicizza solo fatture.
- Nessun metadato `source`/`law_reference` nel vector store (serve estensione schema).
- Mancano tool CLI per gestire la KB (index, status, wipe).
- Mancano test/metriche per valutare accuratezza RAG vs prompt-only.

## 6. Stakeholder & Responsabilità
- **AI/Engineering**: implementazione pipeline, integrazione con agent e tool.
- **Consulente fiscale**: validazione contenuto normativo, gestione aggiornamenti.
- **Support/Operations**: raccolta FAQ, procedure interne.
- **DevOps**: storage, backup KB, monitoring jobs indicizzazione.

## 7. Deliverable Iniziali
- Schema metadati KB e naming convenzioni.
- Procedura ingest per Markdown/YAML con chunking/normalizzazione.
- Script CLI `openfatture ai rag index|stats|reindex`.
- Estensioni agent per consumare `context.relevant_documents` con citazioni.
- Dashboard logging: `rag_hit`, `rag_miss`, `source`.

## 8. Prossime Azioni
1. Validare con stakeholder lista fonti, priorità normative, frequenza aggiornamenti.
2. Definire policy versionamento e naming (es. `iva_guidelines_2025-01.md`).
3. Progettare `KnowledgeIndexer` + adapter per Markdown/YAML.
4. Aggiornare `RAGSystem` per multi-collezione e filtri per `source`.
5. Abilitare `enrich_with_rag()` nel ChatAgent con fallback e logging citazioni.
6. Preparare suite test retrieval + benchmark qualitativi.

## 9. Schema KB Proposto
- **Metadata obbligatori**
  - `document_id`: stringa stabile (slug + versione).
  - `source`: enum (`INVOICE`, `TAX_GUIDE`, `CONFIG`, `FAQ`, `SDI_MANUAL`...).
  - `law_reference`: stringa (es. `DPR 633/72 art.17 c.6`), opzionale per documenti non normativi.
  - `effective_date`: ISO date; usare range (`valid_to`) per normative superate.
  - `jurisdiction`: default `IT`, supporto multi-country futuro.
  - `tags`: lista parole chiave (es. `reverse_charge`, `split_payment`).
  - `chunk_index`: intero per mantenere ordine originale.
  - `summary`: breve descrizione (generata in fase ingest per ranking).
  - `source_path`: riferimento file originale (es. `docs/CONFIGURATION.md#iva`).
- **Campi opzionali**
  - `confidence`: da assegnare a mano per livello affidabilità (es. FAQ non verificate).
  - `reviewed_by`: email/ID revisore fiscale.
  - `last_reviewed_at`: timestamp ISO.

## 10. Pipeline di Ingestion
- **Stadi**
  1. **Discovery**: scansione cartelle sorgente (`docs/`, `prompts/`, storage esterni) con manifest YAML (es. `kb_sources.yml`) per definire file da includere.
  2. **Parsing**: loader Markdown/YAML → struttura logica (titoli, tabelle, esempi) con normalizzazione (rimozione markup inutile).
  3. **Chunking**: suddivisione 350 token con overlap 50, mantenendo `chunk_index`, generando riassunto breve e parole chiave (LLM o algoritmo classico).
  4. **Metadata Enrichment**: applicazione schema campi obbligatori, aggiunta `law_reference` se pattern riconosciuto (regex DPR, art., comma).
  5. **Embedding**: uso `create_embeddings()` con caching; fallback locale se manca API key.
  6. **Persistenza**: scrittura su nuova collezione Chroma (`openfatture_kb`), oppure namespace `source` per distinguere da fatture.
- **Tooling**
  - Script CLI `openfatture ai rag index --source tax_guides` per ingestion mirata.
  - Job schedulabile (GitHub Actions/cron) per re-index automatico quando cambiano file sorgenti.
  - Log JSON per ogni chunk (`document_id`, bytes, durata embedding).

## 11. Modifiche ai Componenti RAG/VectorStore
- **RAGConfig**
  - Aggiungere campi `collections`, `default_collection`, `enable_knowledge_kb`.
  - Consentire override via env (`OPENFATTURE_RAG_KB_COLLECTION`).
- **VectorStore**
  - Supportare collezioni multiple: metodo `get_collection(name)`; `add_documents` accetta `collection` opzionale.
  - Filtri predefiniti su `source`, `effective_date`.
- **InvoiceIndexer**
  - Rifattorizzare in `BaseIndexer` + `InvoiceIndexer`.
  - Nuovo `KnowledgeIndexer` per Markdown/YAML con pipeline di chunking.
- **RAGSystem**
  - Factory per creare indexer/retriever per tipologia (invoice, knowledge).
  - Metodo `search_knowledge(query, source=None, filters=None)`.
- **Retrieval**
  - Introdurre reranker semplice (es. punteggio combinato similarity + match tag).
  - Funzione di formattazione che produce snippet e citazioni (`source_path`, `law_reference`).

## 12. Integrazione con gli Agent
- **ChatAgent**
  - Toggle `config.rag_enabled=True`.
  - Invocare `enrich_with_rag(context, user_input)` con debounce (evitare chiamate su messaggi troppo corti/di servizio).
  - Aggiornare `_build_system_prompt` per includere elenco citazioni (max 3) con formato `[1] DPR 633/72 art...`.
  - Gestire fallback: se RAG fallisce → log `rag_miss` e proseguire con prompt base.
- **TaxAdvisor**
  - Modalità ibrida: prompt YAML + snippet top-2 della KB (filtrati su tag `iva`).
  - Validare che output citi almeno un riferimento se fornito da snippet.
- **InvoiceAssistant**
  - Recuperare esempi di descrizioni simili (tag `invoice_example`) e aggiungere come few-shot dinamici.
- **LangGraph (future)**
  - Definire nodo dedicato `KnowledgeRetriever` riusabile da più agenti.

## 13. Tooling & CLI
- Nuovi comandi `openfatture ai rag ...`:
  - `status`: mostra document count, collezioni, ultimo update.
  - `index --source <name>`: ingest selettiva.
  - `reindex --since <date>`: rigenera chunk aggiornati.
  - `search "<query>" --source tax_guides --top 5`: debug rapido per team.
- Estendere Chat UI `/tools` per includere `search_knowledge_base`.
- Aggiornare `ToolRegistry` con tool:
  ```python
  Tool(
      name="search_knowledge_base",
      description="Recupera estratti normativi e note operative",
      parameters=[...],
      category="knowledge",
  )
  ```
- Output tool deve restituire snippet + citazioni; ChatAgent formatta con elenco puntato.

## 14. Testing & Quality
- **Unit Test**
  - Test chunking Markdown (lunghezza, preservation headings).
  - Test metadata enrichment (regex normativa).
  - Test VectorStore multi-collezione.
- **Integration Test**
  - Ingestion end-to-end su sample `docs/iva_sample.md`.
  - Retrieval assert su query note (es. "reverse charge edilizia").
  - ChatAgent con RAG mock → verifica citazioni nell'output.
- **Benchmark**
  - Confronto risposte TaxAdvisor con/ senza RAG (precision@3 di citazioni).
  - Monitoring costi embedding vs baseline.

## 15. Osservabilità & Rollout
- Logging strutturato (`rag_event`, `source`, `similarity`, `latency_ms`, `chunks_used`).
- Feature flag `AISettings.rag_enabled` + `AISettings.rag_mode` (`disabled`, `knowledge_only`, `full`).
- Rollout graduale:
  1. **Phase Alpha**: team interno con flag manuale.
  2. **Beta**: subset utenti CLI, tracking feedback.
  3. **GA**: flag on di default, documentazione aggiornata (`docs/AI_ARCHITECTURE.md`, README).
- Procedure di incident response: disabilitare flag via env, flush collezione se necessario.
