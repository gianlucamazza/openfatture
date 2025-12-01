# Technical Debt Inventory

This document tracks known technical debt, TODOs, and planned improvements in the OpenFatture codebase.

**Last Updated**: 2025-12-01 (Phase 1.5 completion)

---

## Critical (RESOLVED ✅)

### ~~Missing prodotto_id Field~~
- **Status**: ✅ **RESOLVED in Phase 1.5**
- **Files**: `openfatture/storage/database/models.py`, `openfatture/ai/tools/prodotto_tools.py`
- **Resolution**: Added `RigaFattura.prodotto_id` field via Alembic migration `692d8837`
- **Impact**: Product analytics and AI suggestions now functional

---

## High Priority (Integration Stubs)

### LND Client gRPC Integration
- **Files**: `openfatture/lightning/infrastructure/lnd_client.py:137,204,250,278,295`
- **Issue**: Lightning Network integration uses mock stubs instead of real gRPC
- **Impact**: Lightning payments are non-functional in production
- **Effort**: High (8-12 hours)
- **Dependencies**: Requires `lnd-grpc` package, LND node access
- **Notes**: Intentional stub for future implementation
- **TODOs**: 6 locations with `# TODO: Implement real LND gRPC calls`

---

## Medium Priority (Service Improvements)

### Web Service Features

#### Hooks Execution Tracking
- **Files**: `openfatture/web/services/hooks_service.py:50,51`
- **TODOs**:
  - Line 50: Add execution history tracking
  - Line 51: Add success rate metrics
- **Effort**: Medium (3-4 hours)
- **Impact**: Better observability for automation workflows

#### Payment Transaction Lookup
- **Files**: `openfatture/web/services/payment_service.py:294,312`
- **TODOs**:
  - Line 294: Resolve UUID transaction lookup
  - Line 312: Improve amount/date matching
- **Effort**: Medium (2-3 hours)
- **Impact**: Better payment reconciliation accuracy

#### Health Check API
- **File**: `openfatture/web/utils/health.py:103`
- **TODO**: Implement comprehensive health check endpoint
- **Effort**: Low (1-2 hours)
- **Impact**: Production monitoring readiness

### RAG Auto-Update Queue

#### Service Integration Stubs
- **Files**: `openfatture/ai/rag/auto_update/queue.py:231,246`
- **TODOs**:
  - Line 231: Call actual reindexing service
  - Line 246: Call actual deletion service
- **Effort**: Medium (2-3 hours)
- **Dependencies**: RAG indexing service must be initialized
- **Impact**: Automated knowledge base updates

---

## Low Priority (Future Enhancements)

### Plugin System
- **File**: `openfatture/cli/main.py:69`
- **TODO**: Implement plugin-specific configuration loading
- **Effort**: Low (2-3 hours)
- **Impact**: Better plugin ecosystem

### Voice Features
- **File**: `openfatture/cli/commands/ai.py:2545`
- **TODO**: Implement MP3 decoding for in-memory playback
- **Effort**: Low (1-2 hours)
- **Impact**: Better voice chat experience (currently saves to temp file)

### Bulkhead Pattern
- **Files**: `openfatture/ai/tools/registry.py:589,638`
- **TODOs**:
  - Track queue length for bulkhead pattern
- **Effort**: Low (1 hour)
- **Impact**: Better circuit breaker observability

### Media Module
- **File**: `openfatture/cli/commands/media.py:25`
- **TODO**: Clean up optional import dependencies
- **Effort**: Trivial (15 minutes)
- **Impact**: Code cleanliness

### ML Retraining
- **File**: `openfatture/ai/ml/retraining/triggers.py:215`
- **TODO**: Implement accuracy drift detection
- **Effort**: Medium (3-4 hours)
- **Impact**: Automated model quality monitoring

---

## Resolved Issues (History)

### Phase 1.1 ✅
- Retry logic utility implementation

### Phase 1.2 ✅
- Async bridge utility for sync/async interop

### Phase 1.3 ✅
- Database session management migration (CLI + AI/ML + workflows)

### Phase 1.4 ✅
- Logging standardization (Lightning modules)
- Removed all production `print()` statements

### Phase 1.5 ✅
- Database migration system (Alembic)
- Added `prodotto_id` field to `RigaFattura`
- Fixed OFX importer logging

---

## Next Phases (Planned)

### Phase 1.6: Code Modularization
- **Target**: Split large files (cli/commands/ai.py: 2606 lines)
- **Effort**: 12-16 hours
- **Priority**: Medium

### Phase 1.7: Type Safety Enhancement
- **Target**: Enable strict MyPy, remove remaining `type: ignore`
- **Effort**: 8-12 hours
- **Priority**: Medium-High

### Phase 1.8: Coverage Improvement
- **Target**: Raise coverage from 55% to 60%+
- **Effort**: 16-24 hours (ongoing)
- **Priority**: High

### Phase 6: Production Hardening
- **Prerequisites**: Phases 1.5, 1.7, 1.8 complete
- **Effort**: 40+ hours
- **Priority**: Critical for production deployment

---

## Priority Guidelines

- **Critical**: Blocking features or causing bugs → Immediate action
- **High**: Important integrations or major features → Next 2-4 weeks
- **Medium**: Nice-to-have improvements → Next 1-2 months
- **Low**: Polish and optimizations → Backlog

---

## Contributing

When adding new TODOs:
1. Add `# TODO: <description>` comment in code
2. Update this document with file:line reference
3. Categorize by priority
4. Estimate effort and impact
5. Note any dependencies

For questions: See `docs/DEVELOPMENT.md`
