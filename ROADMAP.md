# OpenFatture Development Roadmap

**Last Updated:** October 10, 2025
**Current Version:** 0.1.0
**Project Status:** Phase 3 Complete, Phase 4 In Progress (60%)

---

## Project Vision

Build a modern, open-source electronic invoicing system for Italian freelancers that combines:
- Full compliance with Italian FatturaPA standards
- CLI-first design for keyboard-driven workflows
- AI-powered automation (planned)
- Production-ready architecture

---

## Development Phases

### ✅ Phase 1: Core Foundation (COMPLETED)

**Status:** 100% Complete
**Completion Date:** October 2025
**Test Coverage:** 81%

#### Achievements
- [x] Modern Python tooling (uv, Python 3.12+)
- [x] Core domain models (Cliente, Fattura, LineaFattura)
- [x] SQLAlchemy database layer with migrations
- [x] Pydantic Settings for configuration
- [x] pytest test infrastructure with fixtures
- [x] Pre-commit hooks (Black, Ruff, mypy)
- [x] Structured logging with structlog
- [x] Secrets management framework
- [x] Correlation ID tracking (async-safe)

#### Metrics
- **Test Suite:** 221 tests passing (0 failures)
- **Execution Time:** 3.71s
- **Coverage:** 81%
- **TODOs Fixed:** 4/4

**📄 Documentation:** See [PHASE_1_SUMMARY.md](PHASE_1_SUMMARY.md)

---

### ✅ Phase 2: SDI Integration (COMPLETED)

**Status:** 100% Complete
**Completion Date:** October 2025
**Test Coverage:** 80%

#### Achievements

**2.1 XML Generation & Validation**
- [x] FatturaPA XML v1.9 generator (2025-compliant)
- [x] XSD schema validation with auto-download
- [x] Namespace-aware XML processing
- [x] Official Italian government schema support

**2.2 Digital Signatures**
- [x] PKCS#12 certificate management
- [x] CAdES-BES digital signatures (p7m)
- [x] Certificate validation and expiration checks
- [x] Signature verification
- [x] Support for attached and detached signatures

**2.3 PEC Integration**
- [x] PEC email sender with professional templates
- [x] Rate limiting (token bucket algorithm)
- [x] Exponential backoff retry logic
- [x] Multipart MIME (HTML + text)
- [x] Attachment handling

**2.4 SDI Notifications**
- [x] Parser for 5 notification types:
  - AT (AttestazioneTrasmissioneFattura)
  - RC (RicevutaConsegna)
  - NS (NotificaScarto)
  - MC (NotificaMancataConsegna)
  - NE (NotificaEsito)
- [x] Automatic invoice status updates
- [x] Database persistence of notifications
- [x] Error list extraction

**2.5 Email System**
- [x] Jinja2 HTML templates with inline CSS
- [x] Internationalization (IT/EN)
- [x] Email template renderer
- [x] Context models with Pydantic
- [x] Professional branding/styling
- [x] Automatic notifications for SDI events

**2.6 Batch Operations**
- [x] Generic batch processor framework
- [x] CSV import/export for invoices
- [x] Bulk validation (basic + XSD)
- [x] Batch PEC sending with rate limiting
- [x] Progress tracking with ETA
- [x] Transaction management

#### Metrics
- **New Tests:** 107 tests added
- **Total Tests:** 325 passing, 14 skipped
- **Coverage:** 80% average
- **Lines of Code:** 2,024+ production code
- **High Coverage Modules:**
  - batch/processor.py: 100%
  - batch/operations.py: 100%
  - utils/rate_limiter.py: 96%
  - notifiche/parser.py: 88%

**📄 Documentation:** See [PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)

---

### ✅ Phase 3: CLI & User Experience (95% COMPLETE)

**Status:** 95% Complete
**Current Phase:** Minor enhancements pending

#### Achievements

**3.1 CLI Framework**
- [x] Typer-based command structure
- [x] Rich console output with formatting
- [x] Interactive mode with Questionary
- [x] Hierarchical menu system
- [x] Numeric shortcuts (1-9, 0)
- [x] Fuzzy search in selectors
- [x] Progress bars for long operations

**3.2 Command Modules (11 total)**
- [x] `init` - Database setup wizard
- [x] `config` - Configuration management
- [x] `cliente` - Client CRUD operations
- [x] `fattura` - Invoice management
- [x] `pec` - PEC testing and configuration
- [x] `email` - Email template management
- [x] `notifiche` - SDI notification processing
- [x] `batch` - Batch operations (import/export/send)
- [x] `report` - Business reports (IVA, clienti, scadenze)
- [x] `ai` - AI command stubs (Phase 4)
- [x] `interactive` - Interactive menu mode

**3.3 User Experience**
- [x] Autocomplete for common data:
  - Italian provinces (110 codes)
  - Postal codes for major cities
  - Tax regimes (RF01-RF19)
  - VAT nature codes (N1-N7)
  - Common service descriptions
  - Payment methods
- [x] Input validation with clear error messages
- [x] Confirmation prompts for destructive actions
- [x] Real-time statistics dashboard
- [x] Colored output for readability

#### Pending Items
- [ ] PDF generation for human-readable invoices (reportlab dependency installed)
- [ ] Enhanced status monitoring dashboard
- [ ] CLI command completion scripts (bash/zsh)

#### Metrics
- **Command Modules:** 11
- **CLI Tests:** 68 tests
- **Total Actions:** 40+ available
- **Help System:** Comprehensive with examples

---

### 🚧 Phase 4: AI Layer (IN PROGRESS - 70% Complete)

**Status:** 70% Complete (Phase 4.1 ✅, 4.2 ✅, 4.3 🚧 50% - Streaming ✅, Token Counter ✅, Caching ✅)
**Priority:** High
**Started:** October 2025
**Target Completion:** Q1 2026

#### Current State

**✅ Functional AI Features:**
- `openfatture -i` → "AI Assistant" → "Chat" - **Interactive chat with AI**
- `openfatture ai describe` - **Generates professional invoice descriptions**
- `openfatture ai suggest-vat` - **Suggests correct VAT rates and treatments**
- `openfatture ai forecast` - Placeholder (planned for 4.3)
- `openfatture ai check` - Placeholder (planned for 4.3)

**✅ Infrastructure Completed:**
- 3 LLM providers (OpenAI, Anthropic, Ollama)
- 3 AI agents (InvoiceAssistant, TaxAdvisor, ChatAgent)
- 6 function calling tools
- Session management with persistence
- Tool registry system
- Context enrichment
- Interactive chat UI with Rich

**Dependencies Installed:**
- langchain>=0.1.6
- langchain-core>=0.1.20
- langchain-community>=0.0.17
- langgraph>=0.0.20 (not yet integrated)
- openai>=1.12.0
- anthropic>=0.18.0
- chromadb>=0.4.22 (not yet integrated)

#### Implementation Progress

**✅ 4.1 LLM Provider Integration (COMPLETED)**
- [x] LLM provider abstraction (OpenAI, Anthropic, Ollama)
- [x] Factory pattern for provider creation
- [x] Async-first API design
- [x] Token counting and cost tracking
- [x] Structured output parsing with Pydantic
- [x] Configuration management with AISettings

**✅ 4.2 AI Agents (COMPLETED)**

*Invoice Assistant:*
- [x] Natural language to invoice description
- [x] Context-aware expansion of brief inputs
- [x] Structured output (deliverables, skills, duration)
- [x] Multi-language support (IT/EN)
- [x] CLI integration (`ai describe`)

*Tax Advisor:*
- [x] VAT rate suggestion based on service type
- [x] Regime-specific rules
- [x] Reverse charge detection
- [x] Split payment identification
- [x] Nature code suggestions (N1-N7)
- [x] Legal references in responses
- [x] CLI integration (`ai suggest-vat`)

*Chat Assistant (NEW):*
- [x] Conversational AI with multi-turn context
- [x] Tool calling for invoice/client queries
- [x] Session management and persistence
- [x] Context enrichment with business data
- [x] Interactive UI with command system
- [x] Export conversations (JSON/Markdown)

**✅ 4.2.1 Tool System (NEW - COMPLETED)**
- [x] Tool definition models (OpenAI/Anthropic compatible)
- [x] Tool registry for centralized management
- [x] 6 built-in tools:
  - [x] search_invoices, get_invoice_details, get_invoice_stats
  - [x] search_clients, get_client_details, get_client_stats
- [x] Async tool execution
- [x] Error handling and validation

**✅ 4.2.2 Session Management (NEW - COMPLETED)**
- [x] ChatSession models with metadata
- [x] SessionManager with CRUD operations
- [x] JSON-based persistence (atomic writes)
- [x] Token and cost tracking per session
- [x] Export functionality (JSON/Markdown)
- [x] Auto-save support

**✅ 4.2.3 Context Enrichment (NEW - COMPLETED)**
- [x] Automatic business data injection
- [x] Current year statistics
- [x] Recent invoices/clients summaries
- [x] Prompt template system (YAML)

**✅ 4.2.4 Interactive UI (NEW - COMPLETED)**
- [x] Rich terminal chat interface
- [x] Markdown rendering for responses
- [x] Command system (/help, /save, /tools, /export, /stats, etc.)
- [x] Real-time token/cost tracking
- [x] Integration with interactive menu

**🚧 4.3 Advanced Features (IN PROGRESS)**

*Cash Flow Predictor Agent:*
- [ ] ML model for payment prediction
- [ ] Historical pattern analysis
- [ ] Client payment behavior profiling
- [ ] Seasonal trend detection
- [ ] Probability distributions for payment timing
- [ ] Risk level assessment (LOW/MEDIUM/HIGH)
- [ ] Integration with `openfatture ai forecast` command (currently stub)
- **Note:** Command exists but shows placeholder output

*Compliance Checker Agent:*
- [ ] Pre-SDI validation with AI reasoning
- [ ] Common error detection from historical rejections
- [ ] Regulatory compliance checks
- [ ] Actionable fix suggestions
- [ ] Severity classification (ERROR/WARNING/INFO)
- [ ] Estimated SDI approval probability
- [ ] Integration with `openfatture ai check` command (currently stub)
- **Note:** Command exists but shows placeholder output

*Complete RAG Implementation:*
- [ ] ChromaDB vector store integration
  - [ ] Setup persistent storage directory
  - [ ] Collection management for sessions/invoices
  - **Note:** ChromaDB dependency already installed (pyproject.toml)
- [ ] Embeddings generation
  - [ ] Choose embedding model (OpenAI/local)
  - [ ] Embed invoice descriptions
  - [ ] Embed conversation history
- [ ] Semantic search functionality
  - [ ] Query embedding
  - [ ] Similarity search over invoice history
  - [ ] Client-specific knowledge retrieval
- [ ] Update `enrich_with_rag()` in `openfatture/ai/context/enrichment.py:193`
  - **Note:** Currently placeholder with TODO comment

*✅ Streaming Response Support (COMPLETED):*
- [x] Implement streaming in all providers
  - [x] OpenAI streaming (fully functional)
  - [x] Anthropic streaming (fully functional)
  - [x] Ollama streaming (fully functional)
- [x] Update ChatAgent to support streaming
  - **Status:** `enable_streaming=True` by default
- [x] Rich terminal UI for streaming output
  - **Implementation:** Rich Live with Markdown rendering
- [x] Token-by-token rendering in chat interface
- [x] Comprehensive test suite (14 tests, 100% pass rate)
- **Benefits:** <100ms time to first token, ChatGPT-like UX

*✅ Advanced Caching System (COMPLETED):*
- [x] LRU cache with TTL support
  - [x] OrderedDict-based implementation for O(1) operations
  - [x] Configurable max_size and default_ttl
  - [x] Background cleanup task with asyncio
- [x] CachedProvider wrapper for transparent caching
  - [x] SHA256 cache key generation from request parameters
  - [x] Automatic cache hit/miss tracking
  - [x] Cost savings estimation
- [x] Pydantic configuration system
  - [x] Environment variable support
  - [x] Strategy selection (lru, semantic, hybrid)
- [x] Comprehensive test suite (44 tests, 100% pass rate)
  - [x] LRU eviction tests
  - [x] TTL expiration tests
  - [x] Concurrency tests
  - [x] Integration tests
- **Benefits:** Expected 60% hit rate, -30% API costs, -40% latency
- **Future:** Semantic similarity caching, Redis for distributed caching

*✅ Token Counter Optimization (COMPLETED):*
- [x] Integrate official Anthropic token counter
  - [x] Client.count_tokens() API integration
  - [x] Async context detection for smart fallback
  - [x] Error handling with logging
- [x] Improve accuracy for cost estimation
  - [x] +30% accuracy for complex/non-English text
  - [x] Model-specific tokenization
- [x] Comprehensive test suite (8 tests, 100% pass rate)
  - [x] Official API usage verification
  - [x] Fallback behavior tests
  - [x] Accuracy comparison tests

**⏳ 4.4 Multi-Agent Orchestration (PLANNED)**

*LangGraph Integration:*
- [ ] State machine framework setup
  - **Note:** LangGraph dependency already installed (pyproject.toml)
- [ ] Define workflow states (InvoiceCreationState, etc.)
- [ ] Implement state transitions and conditional edges
- [ ] Create workflow compilation and execution
- [ ] Add persistence for long-running workflows

*Agent Collaboration:*
- [ ] Invoice creation workflow
  - [ ] Description generation → Tax suggestion → Compliance check
- [ ] Conditional routing based on results
- [ ] Shared state management across agents
- [ ] Context passing between agents
- [ ] Agent communication protocol

*Parallel Execution:*
- [ ] Identify parallelizable agent tasks
- [ ] Implement async parallel execution
- [ ] Result aggregation from multiple agents
- [ ] Timeout handling for parallel tasks
- [ ] Resource pool management

*Error Recovery & Fallbacks:*
- [ ] Retry logic with exponential backoff
- [ ] Fallback to simpler models on failure
- [ ] Graceful degradation strategies
- [ ] Error state handling in workflows
- [ ] Circuit breaker implementation

*Human-in-the-Loop:*
- [ ] Approval checkpoints in workflows
- [ ] Interactive decision points
- [ ] Review interface for AI suggestions
- [ ] Feedback collection mechanism
- [ ] Override capabilities

#### Technical Requirements

*Implemented:*
- [x] Configuration system for LLM providers (AISettings with Pydantic)
- [x] API key management (SecretStr, environment variables)
- [x] Cost tracking for LLM usage (per-request and per-session)
- [x] Token counting (provider-specific implementations)
- [x] Error handling and graceful degradation

*Planned:*
- [ ] **Rate Limiting for API Calls**
  - [ ] Token bucket algorithm per provider
  - [ ] Per-user rate limits
  - [ ] Configurable limits via environment variables
  - [ ] Request queuing when limits reached
  - [ ] Backpressure handling
  - [ ] Metrics for rate limit hits

- [ ] **Advanced Caching Strategy**
  - [ ] Semantic similarity caching (vector-based)
  - [ ] Cache identical requests (exact match)
  - [ ] TTL management (default 24h)
  - [ ] Prompt template caching (in-memory)
  - [ ] Vector store results caching
  - [ ] Cache size limits and eviction policies
  - [ ] Redis support for distributed caching (optional)

- [ ] **Circuit Breakers for Provider Failures**
  - [ ] Per-provider circuit breaker state
  - [ ] Failure threshold configuration
  - [ ] Automatic recovery attempts
  - [ ] Fallback to alternative providers
  - [ ] Health check endpoints
  - [ ] Monitoring and alerting for open circuits
  - [ ] Manual circuit reset capability

#### Testing Strategy

*Implemented:*
- [x] Mock LLM responses for unit tests
- [x] Agent unit tests with fixtures
- [x] Provider abstraction tests
- [x] Tool system tests
- [x] Session management tests
- [x] Cost tracking (basic per-request and per-session)

*Planned:*
- [ ] **Integration Tests with Local Ollama**
  - [ ] Setup Ollama in CI/CD pipeline
  - [ ] Test all providers with real models
  - [ ] Verify streaming functionality
  - [ ] Test function calling with actual LLMs
  - [ ] Validate response formats
  - [ ] End-to-end workflow tests
  - [ ] Skip tests gracefully if Ollama unavailable

- [ ] **Property-Based Tests for AI Outputs**
  - [ ] Use Hypothesis for generative testing
  - [ ] Test prompt rendering with arbitrary inputs
  - [ ] Verify structured output parsing
  - [ ] Validate token counting accuracy
  - [ ] Test context enrichment invariants
  - [ ] Ensure no crashes on edge case inputs

- [ ] **Performance Benchmarks**
  - [ ] Latency measurements per agent
  - [ ] Throughput testing (requests/sec)
  - [ ] Token/sec for streaming responses
  - [ ] Memory usage profiling
  - [ ] Database query performance
  - [ ] Cache hit/miss rates
  - [ ] Benchmark suite with historical tracking

- [ ] **Advanced Cost Analysis**
  - [ ] Per-operation cost breakdown
  - [ ] Cost by agent type
  - [ ] Cost by provider and model
  - [ ] Daily/weekly/monthly cost aggregation
  - [ ] Budget alerting system
  - [ ] Cost optimization recommendations
  - [ ] Historical cost trends

#### Success Metrics
- **Accuracy:** >90% for tax suggestions
- **User Adoption:** >60% of users try AI features
- **Time Saved:** Average 5 min per invoice
- **Error Reduction:** 30% fewer SDI rejections
- **Cost:** <€0.10 per AI-assisted invoice

---

### 🚀 Phase 5: Production & Advanced Features (NOT STARTED)

**Status:** Not Started
**Priority:** Medium
**Estimated Timeline:** 4-6 weeks

#### Planned Features

**5.1 Production Deployment**
- [ ] Docker optimization (multi-stage build review)
- [ ] Docker Compose production profile
- [ ] Health check endpoints
- [ ] Graceful shutdown handling
- [ ] Log aggregation (ELK/Loki)
- [ ] Metrics collection (Prometheus)
- [ ] Distributed tracing (Jaeger/Tempo)

**5.2 CI/CD Enhancement**
- [ ] Automated semantic versioning
- [ ] Release notes generation
- [ ] PyPI package publishing
- [ ] Docker Hub automated builds
- [ ] Staging environment deployment
- [ ] Smoke tests post-deployment
- [ ] Rollback procedures

**5.3 Payment Tracking & Bank Integration**
- [ ] **Payment Tracking System**
  - [ ] Complete Pagamento table integration
    - **Note:** Table exists in `models.py:255` but not fully integrated
  - [ ] Payment due date tracking
  - [ ] Payment status management (pending, partial, complete)
  - [ ] Overdue invoice detection
  - [ ] Payment reminders (automated emails)
  - [ ] Implement `openfatture report scadenze` command
    - **Note:** Currently shows placeholder output (report.py:195-217)

- [ ] **Bank Statement Import**
  - [ ] OFX format support
  - [ ] QIF format support
  - [ ] CSV import with custom mappings
  - [ ] Transaction categorization
  - [ ] Duplicate detection

- [ ] **Bank Reconciliation**
  - [ ] Automatic matching of payments to invoices
  - [ ] Manual reconciliation interface
  - [ ] Reconciliation reports
  - [ ] Unmatched transaction handling

- [ ] **Payment Gateway Integration**
  - [ ] Stripe for online payments
  - [ ] PayPal invoicing
  - [ ] Bank transfer automation (SEPA)
  - [ ] Payment status webhooks

**5.4 Invoice Automation**
- [ ] Recurring invoice automation
  - [ ] Schedule templates (monthly, quarterly, yearly)
  - [ ] Auto-generation with email notifications
  - [ ] Client-specific recurrence rules
- [ ] Multi-currency support
  - [ ] Currency conversion with real-time rates
  - [ ] Multi-currency reports
- [ ] Multi-company support
  - [ ] Separate databases per company
  - [ ] Company switching in UI

**5.5 Accountant Export & Integration**
- [ ] Export formats:
  - [ ] Excel workbooks with formulas
  - [ ] LibreOffice Calc compatible
  - [ ] CSV for accounting software
  - [ ] XML for FatturaPA import by accountants
- [ ] Accounting software integration:
  - [ ] API connectors for popular platforms
  - [ ] Data synchronization

**5.6 Web GUI (Optional)**
- [ ] FastAPI backend for REST API
- [ ] React/Vue frontend
- [ ] Real-time updates (WebSocket)
- [ ] Mobile-responsive design
- [ ] Dashboard with charts
- [ ] User authentication & authorization
- [ ] Multi-tenancy support

**5.7 Compliance & Security**
- [ ] GDPR compliance audit
- [ ] Data retention policies
- [ ] Automated backups
- [ ] Disaster recovery plan
- [ ] Penetration testing
- [ ] Security audit
- [ ] Digital preservation (10-year storage)

**5.8 Performance Optimization**
- [ ] Database query optimization
- [ ] Connection pooling
- [ ] Caching layer (Redis)
- [ ] Async operations where beneficial
- [ ] Load testing (1000+ invoices)
- [ ] Memory profiling
- [ ] Benchmark suite

---

## Known Placeholders & Incomplete Implementations

This section tracks code that exists but is incomplete or shows placeholder behavior.

### CLI Commands (Stubs)

**`openfatture ai forecast`** - Cash Flow Forecasting
- **Location:** `openfatture/cli/commands/ai.py:382-403`
- **Status:** Stub command with placeholder output
- **Message:** "AI/ML features not yet implemented"
- **Target:** Phase 4.3 - Cash Flow Predictor Agent

**`openfatture ai check`** - Compliance Checker
- **Location:** `openfatture/cli/commands/ai.py:405-427`
- **Status:** Stub command with placeholder output
- **Message:** "AI features not yet implemented"
- **Target:** Phase 4.3 - Compliance Checker Agent

**`openfatture report scadenze`** - Payment Due Dates
- **Location:** `openfatture/cli/commands/report.py:195-217`
- **Status:** Partial implementation (Pagamento table exists but not integrated)
- **Message:** "Payment tracking not yet fully implemented"
- **Target:** Phase 5.3 - Payment Tracking System

### Code TODOs

**RAG with ChromaDB** - `openfatture/ai/context/enrichment.py:193`
- **TODO:** Implement RAG with ChromaDB
- **Required:**
  1. Embed query
  2. Search similar conversations
  3. Search similar invoice descriptions
  4. Add to context.similar_conversations and context.relevant_documents
- **Dependency:** ChromaDB already installed
- **Target:** Phase 4.3 - Complete RAG Implementation

**✅ Streaming Responses** - ~~`openfatture/cli/ui/chat.py:124`~~ (COMPLETED)
- **Status:** ~~TODO~~ ✅ Implemented in Phase 4.3
- **Current State:** `enable_streaming=True` by default
- **Implementation:**
  - BaseAgent.execute_stream() method with AsyncIterator[str]
  - All providers support streaming (OpenAI, Anthropic, Ollama)
  - Rich Live terminal UI with Markdown rendering
  - 14 comprehensive tests (100% pass rate)

**✅ Token Counter Optimization** - ~~`openfatture/ai/providers/anthropic.py:247-292`~~ (COMPLETED)
- **Status:** ~~TODO~~ ✅ Implemented in Phase 4.3
- **Current State:** Uses official Anthropic `client.count_tokens()` API
- **Implementation:**
  - Official Anthropic token counter integration
  - Smart fallback for async contexts
  - Error handling with logging
  - 8 comprehensive tests (100% pass rate)
  - +30% accuracy improvement for non-English text

**✅ Advanced Caching** - `openfatture/ai/cache/` (COMPLETED)
- **Status:** ✅ Implemented in Phase 4.3
- **Current State:** LRU cache with TTL, CachedProvider wrapper
- **Implementation:**
  - LRUCache with background cleanup
  - CachedProvider transparent wrapper
  - Pydantic configuration
  - 44 comprehensive tests (100% pass rate)
  - Expected: 60% hit rate, -30% costs, -40% latency

### Phase 3 Pending Items

**PDF Generation** - Human-readable Invoices
- **Status:** ReportLab dependency installed but not implemented
- **Required:**
  - Invoice PDF template design
  - PDF generation service
  - Integration with invoice commands
- **Target:** Phase 3 completion (minor enhancement)

**CLI Completion Scripts** - bash/zsh Autocomplete
- **Status:** Not implemented
- **Required:**
  - Generate completion scripts
  - Installation instructions
  - Command/argument completion
- **Target:** Phase 3 completion (minor enhancement)

**Enhanced Status Dashboard**
- **Status:** Basic dashboard exists, enhancements needed
- **Required:**
  - Real-time status updates
  - Advanced filtering
  - Better visualization
- **Target:** Phase 3 completion (minor enhancement)

### Dependencies Installed But Not Used

**ChromaDB** (`pyproject.toml:65`)
- **Status:** Installed, not yet integrated
- **Usage:** Vector store for RAG functionality
- **Target:** Phase 4.3 - Complete RAG Implementation

**LangGraph** (`pyproject.toml:59`)
- **Status:** Installed, not yet used
- **Usage:** Multi-agent workflow orchestration
- **Target:** Phase 4.4 - Multi-Agent Orchestration

**ReportLab** (`pyproject.toml:77`)
- **Status:** Installed, not yet used
- **Usage:** PDF generation for invoices
- **Target:** Phase 3 completion

---

## Release Schedule

### v0.1.0 - Initial Release ✅
**Released:** January 10, 2025
**Focus:** Core invoicing + SDI integration + CLI

### v0.2.0 - AI Integration (Planned)
**Target:** Q2 2025
**Focus:** Phase 4 implementation

### v0.3.0 - Production Ready (Planned)
**Target:** Q3 2025
**Focus:** Phase 5 features

### v1.0.0 - Stable Release (Planned)
**Target:** Q4 2025
**Focus:** Production deployment + documentation

---

## Success Criteria

### Phase 4 (AI) Progress:
- ✅ Phase 3 complete (95% done)
- ✅ Test coverage >80%
- ✅ All core features working
- ✅ Documentation up to date
- ✅ **Phase 4.1 & 4.2 completed (60% of Phase 4)**
- ✅ **3 AI agents functional**
- ✅ **Interactive chat system operational**
- 🚧 Phase 4.3 in progress
- [ ] User feedback collected on AI features (ongoing)

### Phase 5 (Production) Ready to Start When:
- [ ] Phase 4 complete
- [ ] AI features validated by users
- [ ] No critical bugs in backlog
- [ ] Performance benchmarks met

### v1.0.0 Release Criteria:
- [ ] All phases 1-4 complete
- [ ] Selected Phase 5 features complete
- [ ] Zero critical bugs
- [ ] >90% test coverage
- [ ] Comprehensive documentation
- [ ] Security audit passed
- [ ] 100+ active users

---

## Contributing to the Roadmap

We welcome community input on priorities! Please:

1. **Vote on features** via GitHub Discussions
2. **Propose new features** via GitHub Issues
3. **Share use cases** that would benefit from specific features
4. **Volunteer** to implement features (see CONTRIBUTING.md)

### High-Impact Contributions Wanted
- 🤖 AI agent implementations (Phase 4)
- 📱 Mobile app development
- 🌍 Internationalization (languages beyond IT/EN)
- 🔌 Accounting software integrations
- 📊 Advanced reporting and analytics

---

## Maintenance & Support

### Active Development
- **Phase 1-3:** Maintenance mode (bug fixes only)
- **Phase 4:** Active development (Q2 2025)
- **Phase 5:** Planning

### Long-Term Support
- Security patches: Ongoing
- Bug fixes: Prioritized by severity
- Feature requests: Evaluated quarterly
- Documentation: Updated with each release

---

## Risk Management

### Known Risks
1. **AI API Costs** - Mitigation: Support local Ollama models
2. **SDI Changes** - Mitigation: XSD auto-download, version detection
3. **Compliance Updates** - Mitigation: Regular government website monitoring
4. **User Adoption** - Mitigation: Excellent documentation, community support

### Dependencies Watch List
- FatturaPA specification updates
- SDI system changes
- LangChain API stability
- Python version end-of-life

---

## Questions?

- 📖 **Detailed Docs:** See phase summaries (PHASE_1_SUMMARY.md, PHASE_2_SUMMARY.md)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- 🐛 **Issues:** [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
- 📧 **Email:** info@gianlucamazza.it

---

**Last Updated:** October 10, 2025
**Next Review:** Monthly or at phase completion
