# Next Release Planning (v1.2.0)

## Focus & Objectives
- **Event System & Audit Trail:** Complete the comprehensive event auditing system with analytics, visualizations, and CLI tools.
- **Hooks & Automation:** Implement post-operation hooks for custom workflows and integrations.
- **Preventivi System:** Add quotation/estimate management with conversion to invoices.
- **Web Scraper Module:** Enable automated data extraction for business intelligence.
- **Quality guardrails:** Raise coverage targets to 60-85% across all modules.

## Event System Backlog
1. **Core Event Infrastructure**
    - [x] `EventLog` database model with UUID, timestamps, entity tracking
    - [x] Automatic event persistence with `EventPersistenceListener`
    - [x] Entity tracking (invoice, client, etc.) for filtering and timeline generation
    - [x] Metadata support for additional context (JSON format)
    - [x] JSON serialization for datetime, Decimal, nested objects
    - [ ] Event retention policies and cleanup jobs
2. **Event Repository & Analytics**
    - [x] Advanced query methods (event_type, entity_type, entity_id, date_range)
    - [x] Full-text search in event data with SQLite LIKE queries
    - [x] Timeline generation for entities with human-readable summaries
    - [x] Statistics aggregation (by type, by entity, total counts)
    - [x] Pagination support (limit, offset)
    - [ ] Performance optimization for large event datasets
    - [ ] Event export functionality (CSV/JSON)
3. **Event Analytics Service**
    - [x] Time-based aggregations: daily, weekly, monthly activity
    - [x] Event type distribution with percentages
    - [x] Entity activity metrics (most active entities)
    - [x] Activity trends comparing recent vs previous periods
    - [x] Event velocity metrics (events per hour)
    - [x] Hourly distribution patterns (0-23h analysis)
    - [ ] Predictive analytics for event patterns
4. **CLI Event Commands**
    - [x] `list` - List events with rich filtering (type, entity, date range, limit)
    - [x] `show <event-id>` - Detailed event view with JSON-formatted data
    - [x] `stats [--last-days N]` - Statistics summary with breakdowns
    - [x] `timeline <entity-type> <entity-id>` - Entity event timeline
    - [x] `search <query> [--limit N]` - Full-text search with snippets
    - [x] `types` - List all event types with counts
    - [x] `dashboard [--days N]` - Comprehensive analytics dashboard
    - [x] `trends [--days N] [--type TYPE]` - Time-based activity trends
    - [ ] Event export commands (CSV/JSON)
5. **Visualizations**
    - [x] ASCII bar charts using Rich (█ blocks scaled to data)
    - [x] Timeline view with tree-style connectors (┌ ├ └)
    - [x] Trend indicators with color coding (green/red/yellow)
    - [x] Formatted tables with proper alignment and styling
    - [ ] Interactive web dashboard (future integration)

## Hooks & Automation
1. **Hook System**
    - [ ] Define hook types (pre/post operations)
    - [ ] Hook registry and execution engine
    - [ ] Error handling and isolation
2. **Built-in Hooks**
    - [ ] Post-invoice-send: Send notifications, update external systems
    - [ ] Post-payment-reconcile: Update accounting software
    - [ ] Post-client-create: Setup default configurations
3. **Custom Hooks**
    - [ ] YAML-based hook definitions
    - [ ] Scripting support (Python/shell scripts)
    - [ ] Hook testing and validation

## Preventivi System
1. **Core Models**
    - [ ] Preventivo model with line items
    - [ ] Status tracking (draft, sent, accepted, rejected, expired)
    - [ ] Conversion workflow to Fattura
2. **Business Logic**
    - [ ] Validity periods and expiration handling
    - [ ] Client approval workflow
    - [ ] Version control for revisions
3. **CLI Integration**
    - [ ] `openfatture preventivo` command group
    - [ ] CRUD operations and status management
    - [ ] Convert to invoice functionality

## Web Scraper Module
1. **Core Architecture**
    - [ ] Agent-based scraping with configurable strategies
    - [ ] Rate limiting and politeness controls
    - [ ] Data extraction and normalization
2. **Business Intelligence**
    - [ ] Company data enrichment (VAT, address, contacts)
    - [ ] Market research and competitor analysis
    - [ ] Automated data validation
3. **Integration**
    - [ ] CLI commands for scraping operations
    - [ ] Batch processing capabilities
    - [ ] Results storage and reporting

## Documentation & Tooling
- Update `docs/README.md` with new module documentation
- Expand `docs/CLI_REFERENCE.md` with event system and new commands
- Add examples for event analytics and visualizations
- Document hook system and custom hook development
- Create preventivi workflow documentation
- Add web scraper usage guides

## Quality & Coverage Roadmap
1. **Short-term (v1.2.0)**
    - Raise average coverage to ≥60% with comprehensive event system tests
    - Increase `--cov-fail-under` to 60% in `.github/workflows/test.yml`
    - Add integration tests for event analytics and CLI commands
2. **Mid-term**
    - Push event system and new modules toward 75% coverage
    - Improve demo fixtures for realistic event data
    - Add performance benchmarks for event queries
3. **Long-term (85% goal)**
    - Track differential coverage on PRs
    - Publish automatic reports in `docs/reports/`
    - Implement coverage gates for new features

## Testing Strategy
- **Event System Tests**: 45+ comprehensive tests (100% persistence, 91% repository, 88% base, 15% analytics)
- **Integration Tests**: Event creation, validation, deletion, timeline generation
- **Performance Tests**: Large dataset handling, query optimization
- **CLI Tests**: All event commands with various scenarios
- **Visualization Tests**: ASCII chart rendering and trend calculations

## Tracking
- Maintain status in `docs/history/ROADMAP.md` (add "Next Release" section)
- Update `CHANGELOG.md` with significant intermediate progress
- Track event system adoption and performance metrics
