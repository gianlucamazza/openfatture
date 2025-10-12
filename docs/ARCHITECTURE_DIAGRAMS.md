# OpenFatture Architecture Diagrams

**Visual reference for system architecture, data flows, and workflows**

This document contains Mermaid diagrams that illustrate the architecture and key workflows of OpenFatture. All diagrams are version-controlled and can be rendered in GitHub, VS Code, and other Markdown viewers that support Mermaid.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [AI Agent Flow](#ai-agent-flow)
- [SDI Workflow](#sdi-workflow)
- [Batch Operations](#batch-operations)
- [Data Model](#data-model)
- [Multi-Agent Orchestration](#multi-agent-orchestration)

---

## System Architecture

High-level overview of OpenFatture's layered architecture:

```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI[CLI Interface<br/>Typer + Rich]
        UI[Interactive UI<br/>Dashboard + Chat]
    end

    subgraph "Application Layer"
        CMD[Commands Layer<br/>fattura, cliente, ai, pec]
        AGENT[AI Agents<br/>Invoice, Tax, Chat, Compliance]
        ORCH[Multi-Agent Orchestrator<br/>LangGraph]
    end

    subgraph "Domain Layer"
        DOM[Domain Models<br/>Fattura, Cliente, Prodotto]
        VAL[Validation Logic<br/>FatturaPA Schema]
        BIZ[Business Rules<br/>Tax, Numbering, Status]
    end

    subgraph "Infrastructure Layer"
        DB[(SQLite/PostgreSQL<br/>SQLAlchemy ORM)]
        XML[XML Generator<br/>FatturaPA XML]
        PDF[PDF Generator<br/>ReportLab]
        PEC[PEC Integration<br/>SMTP + IMAP]
        AI[LLM Providers<br/>OpenAI, Anthropic, Ollama]
        VEC[(Vector Store<br/>ChromaDB)]
    end

    subgraph "External Systems"
        SDI[SDI<br/>Sistema di Interscambio]
        EMAIL[Email<br/>Notifications]
    end

    CLI --> CMD
    UI --> CMD
    CMD --> AGENT
    CMD --> DOM
    AGENT --> ORCH
    AGENT --> AI
    AGENT --> VEC
    DOM --> VAL
    DOM --> BIZ
    DOM --> DB
    VAL --> XML
    BIZ --> PDF
    CMD --> PEC
    XML --> PEC
    PEC --> SDI
    PEC --> EMAIL

    style CLI fill:#001f3f,color:#fff
    style UI fill:#001f3f,color:#fff
    style AGENT fill:#2ECC71,color:#000
    style AI fill:#2ECC71,color:#000
    style SDI fill:#E74C3C,color:#fff
    style DB fill:#3498DB,color:#fff
```

**Key Components:**

- **Presentation:** Typer CLI + Rich UI for terminal interaction
- **Application:** Command handlers + AI agent orchestration
- **Domain:** Core business logic and models
- **Infrastructure:** Database, file generation, external integrations
- **External:** SDI (Italian tax authority), email notifications

---

## AI Agent Flow

How AI agents process requests and interact with the system:

```mermaid
sequenceDiagram
    actor User
    participant CLI
    participant Agent as AI Agent<br/>(Invoice/Tax/Chat)
    participant Context as Context Enrichment
    participant Provider as LLM Provider<br/>(OpenAI/Anthropic/Ollama)
    participant Tools as Tool Registry
    participant DB as Database

    User->>CLI: ai chat "Create invoice for consulting work"
    CLI->>Agent: execute(context)

    Agent->>Context: enrich_context()
    Context->>DB: fetch recent invoices
    Context->>DB: fetch client stats
    DB-->>Context: business data
    Context-->>Agent: enriched context

    Agent->>Provider: generate(messages + tools)

    alt Tool Calling Enabled
        Provider-->>Agent: function_call: search_invoices
        Agent->>Tools: execute_tool(search_invoices)
        Tools->>DB: query
        DB-->>Tools: results
        Tools-->>Agent: tool_result
        Agent->>Provider: continue with tool_result
    end

    Provider-->>Agent: response

    Agent->>DB: save session
    Agent-->>CLI: AgentResponse
    CLI-->>User: formatted output + cost

    Note over User,DB: Token and cost tracking at each step
```

**Flow Details:**

1. **Context Enrichment:** Automatic injection of business data (current stats, recent invoices)
2. **Tool Calling:** Optional function calling for data retrieval (search, stats, details)
3. **Multi-Provider:** Supports OpenAI, Anthropic (Claude), and local Ollama
4. **Session Tracking:** All conversations persisted with token/cost metadata

---

## SDI Workflow

Electronic invoice submission to Italian SDI (Sistema di Interscambio):

```mermaid
stateDiagram-v2
    [*] --> Bozza: Create invoice

    Bozza --> ValidazioneXML: Generate XML

    ValidazioneXML --> ErroreValidazione: Validation fails
    ErroreValidazione --> Bozza: Fix errors

    ValidazioneXML --> ProntaInvio: Validation success

    ProntaInvio --> InvioPEC: Send via PEC

    InvioPEC --> InviataSDI: PEC accepted

    InviataSDI --> AttesaRicevuta: Wait for SDI response

    AttesaRicevuta --> Consegnata: RC (Delivery receipt)
    AttesaRicevuta --> Rifiutata: NS (Notification of rejection)
    AttesaRicevuta --> Scartata: MC (Rejection message)

    Rifiutata --> Bozza: Review and resend
    Scartata --> Bozza: Fix errors and resend

    Consegnata --> [*]

    note right of ValidazioneXML
        FatturaPA XML Schema validation
        - Required fields
        - Tax codes (AliquotaIVA, NaturaIVA)
        - Digital signature (optional)
    end note

    note right of InvioPEC
        PEC email to sdi01@pec.fatturapa.it
        - XML attachment
        - Unique filename (IT+PIVA+Progressive)
        - Sender's PEC address
    end note

    note right of AttesaRicevuta
        SDI response codes:
        - RC: Ricevuta di consegna (success)
        - NS: Notifica di scarto (rejected)
        - MC: Mancata consegna (delivery failed)
        - DT: Decorrenza termini (5-day silence = accepted)
    end note
```

**Status Legend:**

- **Bozza:** Draft invoice, editable
- **InviataSDI:** Submitted to SDI via PEC
- **Consegnata:** Successfully delivered to recipient
- **Rifiutata/Scartata:** Rejected by SDI or recipient, requires fixes

---

## Batch Operations

CSV import/export workflow for bulk operations:

```mermaid
flowchart TD
    Start([User initiates batch operation])

    Start --> Import{Operation type?}

    Import -->|Import| ValidateCSV[Validate CSV format]
    Import -->|Export| FetchData[Fetch data from DB]

    ValidateCSV --> ParseRows[Parse CSV rows]
    ParseRows --> ValidateData{Data valid?}

    ValidateData -->|No| ShowErrors[Show validation errors<br/>Line numbers + messages]
    ShowErrors --> DryRun{Dry-run mode?}
    DryRun -->|Yes| End([Report errors, exit])
    DryRun -->|No| FixData[User fixes CSV]
    FixData --> ValidateCSV

    ValidateData -->|Yes| CheckDuplicates[Check duplicates<br/>PIVA, Invoice numbers]

    CheckDuplicates --> DuplicateFound{Duplicates?}
    DuplicateFound -->|Yes| MergeStrategy{Merge strategy?}
    MergeStrategy -->|Skip| LogSkipped[Log skipped records]
    MergeStrategy -->|Update| UpdateRecords[Update existing]
    MergeStrategy -->|Error| ShowErrors

    DuplicateFound -->|No| TransactionStart[Begin DB transaction]
    LogSkipped --> TransactionStart
    UpdateRecords --> TransactionStart

    TransactionStart --> InsertBatch[Batch insert/update<br/>Chunked for performance]

    InsertBatch --> CommitSuccess{Commit success?}
    CommitSuccess -->|No| Rollback[Rollback transaction]
    Rollback --> ShowErrors

    CommitSuccess -->|Yes| GenerateReport[Generate import report<br/>Success/Skip/Error counts]

    FetchData --> FormatCSV[Format data as CSV]
    FormatCSV --> WriteFile[Write to file]
    WriteFile --> GenerateReport

    GenerateReport --> End

    style Start fill:#001f3f,color:#fff
    style End fill:#2ECC71,color:#000
    style ShowErrors fill:#E74C3C,color:#fff
    style TransactionStart fill:#3498DB,color:#fff
    style CommitSuccess fill:#F39C12,color:#000
```

**Batch Import Features:**

- **Dry-run mode:** Validate without modifying database
- **Duplicate detection:** PIVA, invoice numbers, email addresses
- **Transaction safety:** Atomic operations with rollback on failure
- **Progress reporting:** Real-time progress for large files
- **Error handling:** Line-by-line error messages with suggested fixes

**Supported Entities:**

- Clients (CSV → Cliente table)
- Products (CSV → Prodotto table)
- Invoices (CSV → Fattura + Riga tables)

---

## Data Model

Database schema (SQLAlchemy ORM):

```mermaid
erDiagram
    FATTURA ||--o{ RIGA : contains
    FATTURA }o--|| CLIENTE : "issued to"
    RIGA }o--|| PRODOTTO : references
    FATTURA ||--o{ NOTIFICA_SDI : "has notifications"

    FATTURA {
        int id PK
        string numero UK "Invoice number"
        date data
        string tipo_documento "TD01-TD28"
        string stato "bozza/inviata/consegnata"
        int cliente_id FK
        decimal totale_imponibile
        decimal totale_iva
        decimal totale_documento
        string causale "Payment terms"
        date scadenza
        datetime created_at
        datetime updated_at
    }

    RIGA {
        int id PK
        int fattura_id FK
        int prodotto_id FK "Optional"
        int numero_linea
        string descrizione
        decimal quantita
        string unita_misura
        decimal prezzo_unitario
        decimal aliquota_iva
        string natura_iva "N1-N7 for exempt"
        decimal totale_riga
    }

    CLIENTE {
        int id PK
        string denominazione
        string partita_iva UK
        string codice_fiscale
        string regime_fiscale "RF01-RF19"
        string indirizzo
        string cap
        string comune
        string provincia
        string nazione "IT"
        string email
        string pec
        string codice_destinatario "7-char for PA"
        datetime created_at
    }

    PRODOTTO {
        int id PK
        string codice UK "SKU/Code"
        string descrizione
        string categoria "consulting/license/service"
        decimal prezzo_unitario
        string unita_misura "hours/days/items"
        decimal aliquota_iva_default
        boolean attivo
        datetime created_at
    }

    NOTIFICA_SDI {
        int id PK
        int fattura_id FK
        string tipo "RC/NS/MC/DT"
        string messaggio
        string id_trasmissione UK
        datetime data_ricezione
        string xml_notifica "Raw XML"
    }
```

**Key Relationships:**

- **Fattura → Cliente:** Many-to-one (many invoices per client)
- **Fattura → Riga:** One-to-many (invoice lines)
- **Riga → Prodotto:** Many-to-one (optional product reference)
- **Fattura → Notifica_SDI:** One-to-many (SDI responses)

**Invoice Lifecycle:**

1. **Bozza:** Draft, editable
2. **Inviata:** Submitted to SDI, awaiting response
3. **Consegnata:** Delivered, immutable
4. **Rifiutata/Scartata:** Rejected, can be cloned and resubmitted

---

## Multi-Agent Orchestration

LangGraph workflow for AI-assisted invoice creation (Phase 4.4):

```mermaid
graph TD
    Start([User input:<br/>"3 hours GDPR consulting"]) --> DescriptionAgent

    subgraph "Invoice Assistant Agent"
        DescriptionAgent[Generate detailed description<br/>RAG: previous invoices]
        DescriptionAgent --> DescriptionOut["Professional description<br/>GDPR consulting:<br/>- Regulatory analysis<br/>- Gap assessment<br/>- Action plan<br/>Duration: 3 hours"]
    end

    DescriptionOut --> TaxAgent

    subgraph "Tax Advisor Agent"
    TaxAgent[Suggest VAT treatment<br/>Knowledge base: Italian tax law]
        TaxAgent --> TaxOut["VAT rate: 22%<br/>VAT nature: null<br/>ReverseCharge: false<br/>Notes: Standard consulting"]
    end

    TaxOut --> ComplianceAgent

    subgraph "Compliance Checker Agent"
        ComplianceAgent[Validate FatturaPA compliance<br/>Rule-based + LLM heuristics]
        ComplianceAgent --> ComplianceOut{Compliant?}
    end

    ComplianceOut -->|No| ShowIssues[Show validation issues<br/>Severity: ERROR/WARNING<br/>Suggested fixes]
    ShowIssues --> HumanReview

    ComplianceOut -->|Yes| HumanReview[Human approval checkpoint<br/>Review + edit if needed]

    HumanReview --> Decision{Approved?}
    Decision -->|No| End([Cancel])
    Decision -->|Yes| CreateInvoice[Create Fattura<br/>Save to database]

    CreateInvoice --> GenerateXML[Generate FatturaPA XML]
    GenerateXML --> GeneratePDF[Generate PDF]
    GeneratePDF --> Success([Invoice created<br/>Ready to send])

    style Start fill:#001f3f,color:#fff
    style Success fill:#2ECC71,color:#000
    style ShowIssues fill:#E74C3C,color:#fff
    style HumanReview fill:#F39C12,color:#000
```

**Orchestration Benefits:**

- **Sequential agents:** Each agent focuses on one task
- **Human-in-the-loop:** Final approval before invoice creation
- **Stateful workflow:** LangGraph manages state across agents
- **Error recovery:** Validation failures loop back for fixes
- **Traceability:** Full audit trail of AI decisions

---

## Export Options

All diagrams can be exported as:

1. **PNG images** (for presentations):
   ```bash
   # Using mermaid-cli (mmdc)
   npm install -g @mermaid-js/mermaid-cli
   mmdc -i docs/ARCHITECTURE_DIAGRAMS.md -o media/diagrams/
   ```

2. **SVG** (for web, scalable):
   ```bash
   mmdc -i docs/ARCHITECTURE_DIAGRAMS.md -o media/diagrams/ -t default -b transparent -e svg
   ```

3. **Interactive HTML** (GitHub Pages):
   - Diagrams auto-render in GitHub Markdown viewer
   - Can be embedded in Sphinx/MkDocs documentation

---

## Diagram Maintenance

**When to update:**

- Architecture changes (new layers, components)
- New workflows added (e.g., payment reconciliation)
- SDI process updates (AgID spec changes)
- Data model migrations (schema changes)

**Best Practices:**

- Keep diagrams simple (max 15-20 nodes)
- Use consistent color scheme (#001f3f primary, #2ECC71 success, #E74C3C error)
- Add descriptive notes for complex steps
- Version diagrams alongside code (same PR)
- Generate PNG exports for social/presentations

---

## Related Documentation

- [AI Architecture](AI_ARCHITECTURE.md) - Detailed AI module documentation
- [CLI Reference](CLI_REFERENCE.md) - All command syntax and examples
- [Quickstart Guide](QUICKSTART.md) - 5-minute setup tutorial
- [README](../README.md) - Project overview and features

---

**Last Updated:** October 10, 2025
**Diagrams Version:** 1.0
**Mermaid Syntax:** v10.x+
