# Self-Learning System

OpenFatture includes an advanced self-learning system that automatically improves over time by learning from user interactions, retraining ML models, and keeping the AI knowledge base synchronized with your business data.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
  - [1. Feedback Collection](#1-feedback-collection)
  - [2. ML Model Retraining](#2-ml-model-retraining)
  - [3. RAG Auto-Update](#3-rag-auto-update)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Production Deployment](#production-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)

## Overview

The self-learning system consists of three integrated components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Learning System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │    Feedback      │  │   ML Model       │  │    RAG    │ │
│  │   Collection     │─▶│  Retraining      │  │Auto-Update│ │
│  └──────────────────┘  └──────────────────┘  └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Application Database                     │  │
│  │  • UserFeedback      • AIModels    • Fattura         │  │
│  │  • PredictionFeedback              • Cliente         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Continuous Improvement**: AI responses get better as users provide corrections
2. **Always Up-to-Date**: RAG knowledge base reflects latest invoice/client data
3. **Automated Maintenance**: No manual intervention required once configured
4. **Production-Ready**: Graceful degradation, error handling, and monitoring

## Architecture

### Component Interaction Flow

```
User Interaction
    │
    ▼
AI Response (Cash Flow Prediction, Chat, etc.)
    │
    ▼
Feedback Collection ─────────────────────────┐
    │                                          │
    │                                          ▼
    │                                   Feedback Database
    │                                          │
    ▼                                          │
Data Changes (Invoice Created, Client Updated)│
    │                                          │
    ▼                                          ▼
RAG Auto-Update Queue                  Retraining Triggers
    │                                          │
    ▼                                          ▼
Vector Store Reindex                   ML Model Retrain
    │                                          │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
              Improved AI Responses
```

### Lifecycle Integration

All self-learning components are integrated into the application lifecycle manager (`openfatture/cli/lifespan.py`):

- **Startup**: Event listeners registered, services started if enabled
- **Runtime**: Async processing of changes and feedback
- **Shutdown**: Graceful cleanup, queue persistence, resource release

## Components

### 1. Feedback Collection

Collects user corrections and ratings to improve AI responses.

**Location**: `openfatture/ai/feedback/`

**Key Classes**:
- `FeedbackService`: Main service for collecting/storing feedback
- `FeedbackAnalyzer`: Analyzes feedback patterns and generates insights

**Database Models**:
```python
# Generic AI interaction feedback
class UserFeedback:
    id: int
    agent_type: str          # "cash_flow_predictor", "chat", etc.
    user_input: str
    ai_response: str
    user_correction: str     # What the correct response should be
    rating: int              # 1-5 stars
    created_at: datetime

# ML prediction-specific feedback
class ModelPredictionFeedback:
    id: int
    model_name: str          # "cash_flow", "payment_matcher", etc.
    model_version: str
    prediction: dict         # Original prediction
    actual_outcome: dict     # What actually happened
    was_accurate: bool
    created_at: datetime
```

**CLI Commands**:
```bash
# Submit feedback for a chat interaction
openfatture ai feedback submit \
  --agent-type chat \
  --input "What's my revenue this month?" \
  --response "Your revenue is €10,000" \
  --correction "Revenue is €12,500 including pending" \
  --rating 3

# Submit feedback for ML prediction
openfatture ai feedback submit-prediction \
  --model cash_flow \
  --prediction '{"amount": 5000, "confidence": 0.8}' \
  --actual '{"amount": 5500}' \
  --accurate false

# View feedback statistics
openfatture ai feedback stats

# Export feedback for analysis
openfatture ai feedback export --output feedback.json
```

**Configuration**:
```bash
# Enable feedback collection (default: true)
OPENFATTURE_AI_FEEDBACK_ENABLED=true

# Prompt timeout for feedback after AI responses (seconds)
OPENFATTURE_AI_FEEDBACK_PROMPT_TIMEOUT=3

# Retention period for feedback data (days, 0 = forever)
OPENFATTURE_AI_FEEDBACK_RETENTION_DAYS=365
```

### 2. ML Model Retraining

Automatically retrains ML models when enough feedback accumulates.

**Location**: `openfatture/ai/ml/retraining/`

**Key Classes**:
- `RetrainingScheduler`: APScheduler-based job scheduler
- `TriggerEvaluator`: Evaluates if retraining should occur
- `ModelVersionManager`: Manages model versions and rollback
- `ModelEvaluator`: Evaluates model performance

**Retraining Triggers**:

1. **Feedback Accumulation**: ≥25 feedback entries since last training
2. **Time-Based**: ≥7 days since last training
3. **Performance Degradation**: Accuracy drops >10% from baseline

**Workflow**:

```
Scheduled Check (every 24h)
    │
    ▼
Evaluate Triggers
    │
    ├─▶ Feedback Count ≥ 25? ────┐
    ├─▶ Days Since Training ≥ 7? ─┤
    └─▶ Performance Drop > 10%? ──┤
                                   │
                                   ▼
                              Retrain Model
                                   │
                                   ▼
                           Evaluate New Model
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
            Improvement ≥ 2%?              No Improvement
                    │                             │
                    ▼                             ▼
            Deploy New Model                Keep Old Model
                    │                             │
                    ▼                             ▼
            Save Version                     Log Event
```

**CLI Commands**:
```bash
# Trigger manual retraining
openfatture ai retrain --model cash_flow

# Check retraining status
openfatture ai retrain status

# List model versions
openfatture ai retrain list-versions --model cash_flow

# Rollback to previous version
openfatture ai retrain rollback --model cash_flow --version 1.2.0
```

**Configuration**:
```bash
# Enable automatic retraining (default: false - enable in production)
OPENFATTURE_ML_RETRAINING_ENABLED=false

# Check interval for retraining triggers (hours)
OPENFATTURE_ML_RETRAINING_CHECK_INTERVAL_HOURS=24

# Minimum feedback count before retraining
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=25

# Maximum days since last training before forcing retrain
OPENFATTURE_ML_RETRAINING_MAX_DAYS_SINCE_TRAINING=7

# Performance degradation threshold (10% = retrain if accuracy drops >10%)
OPENFATTURE_ML_RETRAINING_PERFORMANCE_DEGRADATION_THRESHOLD=0.10

# Model versioning
OPENFATTURE_ML_RETRAINING_MAX_VERSIONS=10
OPENFATTURE_ML_RETRAINING_MIN_IMPROVEMENT_PERCENTAGE=0.02

# Dry run mode (test without deploying new models)
OPENFATTURE_ML_RETRAINING_DRY_RUN=false
```

### 3. RAG Auto-Update

Automatically reindexes the vector store when invoice/client data changes.

**Location**: `openfatture/ai/rag/auto_update/`

**Key Classes**:
- `AutoIndexingService`: Main service orchestrating reindexing
- `ChangeTracker`: Tracks data changes for reindexing
- `ReindexQueue`: Async queue with debouncing and batching
- Event listeners: SQLAlchemy hooks for Fattura, Cliente, Prodotto

**How It Works**:

1. **Data Change**: User creates/updates invoice via CLI
2. **Event Listener**: SQLAlchemy `after_insert`/`after_update` event fires
3. **Change Tracker**: Records change with entity type and ID
4. **Debouncing**: Waits 5 seconds for more changes
5. **Batching**: Groups up to 50 changes together
6. **Reindexing**: Updates vector store with new embeddings
7. **Cleanup**: Removes deleted entities from vector store

**Example Flow**:

```python
# User creates invoice
openfatture fattura crea
# → after_insert event fires
# → ChangeTracker records: EntityChange(entity_type="invoice", entity_id=123)
# → ReindexQueue adds to pending queue
# → After 5s debounce, processes batch
# → Fetches invoice 123 from database
# → Generates embeddings
# → Updates ChromaDB collection
# → AI now knows about this invoice
```

**CLI Commands**:
```bash
# Check auto-update status
openfatture ai auto-update status

# View pending changes
openfatture ai auto-update pending

# View reindexing statistics
openfatture ai auto-update stats

# Pause/resume auto-update
openfatture ai auto-update pause
openfatture ai auto-update resume

# Manual reindex (useful after bulk imports)
openfatture ai rag reindex
```

**Configuration**:
```bash
# Enable RAG auto-update (default: false - enable in production)
OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=false

# Batch size for reindexing operations
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=50

# Debounce time (seconds) before processing changes
# Higher values = fewer but larger batches
OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS=5

# Maximum queue size (older changes dropped if exceeded)
OPENFATTURE_RAG_AUTO_UPDATE_MAX_QUEUE_SIZE=1000

# Entity tracking (which changes to monitor)
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_INVOICES=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_CLIENTS=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_PRODUCTS=false

# Update strategy
OPENFATTURE_RAG_AUTO_UPDATE_INCREMENTAL_UPDATES=true
OPENFATTURE_RAG_AUTO_UPDATE_DELETE_ON_REMOVAL=true

# Performance
OPENFATTURE_RAG_AUTO_UPDATE_ASYNC_PROCESSING=true
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=3

# Persistence (persist queue on shutdown for recovery)
OPENFATTURE_RAG_AUTO_UPDATE_PERSIST_QUEUE_ON_SHUTDOWN=true
OPENFATTURE_RAG_AUTO_UPDATE_QUEUE_PERSIST_PATH=.cache/rag_update_queue.json
```

## Configuration

### Quick Start (Development)

For development, you can enable all self-learning features with minimal configuration:

```bash
# .env
OPENFATTURE_AI_FEEDBACK_ENABLED=true
OPENFATTURE_ML_RETRAINING_ENABLED=false  # Disable until you have data
OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true
```

### Production Configuration

For production deployment, use these recommended settings:

```bash
# === Feedback Collection ===
OPENFATTURE_AI_FEEDBACK_ENABLED=true
OPENFATTURE_AI_FEEDBACK_PROMPT_TIMEOUT=3
OPENFATTURE_AI_FEEDBACK_RETENTION_DAYS=365

# === ML Model Retraining ===
OPENFATTURE_ML_RETRAINING_ENABLED=true
OPENFATTURE_ML_RETRAINING_CHECK_INTERVAL_HOURS=24
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=25
OPENFATTURE_ML_RETRAINING_MAX_DAYS_SINCE_TRAINING=7
OPENFATTURE_ML_RETRAINING_PERFORMANCE_DEGRADATION_THRESHOLD=0.10
OPENFATTURE_ML_RETRAINING_MAX_VERSIONS=10
OPENFATTURE_ML_RETRAINING_MIN_IMPROVEMENT_PERCENTAGE=0.02
OPENFATTURE_ML_RETRAINING_DRY_RUN=false

# === RAG Auto-Update ===
OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=50
OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS=5
OPENFATTURE_RAG_AUTO_UPDATE_MAX_QUEUE_SIZE=1000
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_INVOICES=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_CLIENTS=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_PRODUCTS=false
OPENFATTURE_RAG_AUTO_UPDATE_INCREMENTAL_UPDATES=true
OPENFATTURE_RAG_AUTO_UPDATE_DELETE_ON_REMOVAL=true
OPENFATTURE_RAG_AUTO_UPDATE_ASYNC_PROCESSING=true
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=3
OPENFATTURE_RAG_AUTO_UPDATE_PERSIST_QUEUE_ON_SHUTDOWN=true
OPENFATTURE_RAG_AUTO_UPDATE_QUEUE_PERSIST_PATH=.cache/rag_update_queue.json
```

## Usage Guide

### Scenario 1: Enable Self-Learning for Cash Flow Predictions

**Goal**: Improve cash flow prediction accuracy over time.

**Steps**:

1. **Enable Feedback Collection**:
```bash
# .env
OPENFATTURE_AI_FEEDBACK_ENABLED=true
```

2. **Train Initial Model** (requires ≥25 invoices):
```bash
openfatture ai forecast --retrain
```

3. **Use Predictions and Provide Feedback**:
```bash
# Make prediction
openfatture ai forecast --days 30

# When actual payment comes in, record feedback
openfatture ai feedback submit-prediction \
  --model cash_flow \
  --prediction '{"amount": 5000, "date": "2025-02-15"}' \
  --actual '{"amount": 5200, "date": "2025-02-17"}' \
  --accurate false
```

4. **Enable Automatic Retraining**:
```bash
# .env
OPENFATTURE_ML_RETRAINING_ENABLED=true
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=25
```

5. **Monitor Retraining**:
```bash
openfatture ai retrain status
```

**Result**: After 25 feedback entries, model automatically retrains with improved accuracy.

### Scenario 2: Keep AI Chat Context Up-to-Date

**Goal**: AI assistant always knows about latest invoices and clients.

**Steps**:

1. **Enable RAG Auto-Update**:
```bash
# .env
OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_INVOICES=true
OPENFATTURE_RAG_AUTO_UPDATE_TRACK_CLIENTS=true
```

2. **Initial RAG Index** (if not done):
```bash
openfatture ai rag reindex
```

3. **Normal Operations**:
```bash
# Create invoice
openfatture fattura crea

# → Auto-update automatically indexes it within 5 seconds

# Ask AI about it immediately
openfatture ai chat
> "What invoices did I create today?"
# → AI has fresh data!
```

4. **Monitor Auto-Update**:
```bash
openfatture ai auto-update status
openfatture ai auto-update stats
```

**Result**: AI chat always has current invoice/client data without manual reindexing.

### Scenario 3: Improve AI Chat Responses

**Goal**: Train AI to give better answers for your specific business.

**Steps**:

1. **Enable Feedback**:
```bash
# .env
OPENFATTURE_AI_FEEDBACK_ENABLED=true
OPENFATTURE_AI_FEEDBACK_PROMPT_TIMEOUT=3
```

2. **Use Chat and Provide Corrections**:
```bash
openfatture ai chat
> "What's my average invoice amount?"
< AI Response: "Your average invoice is €1,000"

# If incorrect, submit feedback
openfatture ai feedback submit \
  --agent-type chat \
  --input "What's my average invoice amount?" \
  --response "Your average invoice is €1,000" \
  --correction "Average invoice is €1,250 (including pending invoices)" \
  --rating 2
```

3. **Analyze Feedback Patterns**:
```bash
openfatture ai feedback stats

# Shows:
# - Most common corrections
# - Low-rated response patterns
# - Areas for improvement
```

4. **Future Enhancement**: Use feedback to fine-tune prompts or models.

**Result**: You build a database of corrections that can inform future improvements.

## Production Deployment

### Pre-Deployment Checklist

- [ ] **Database Backup**: Ensure regular backups of SQLite/PostgreSQL
- [ ] **Initial Training**: Train ML models with sufficient data (≥25 invoices)
- [ ] **Initial Indexing**: Run `openfatture ai rag reindex` for RAG
- [ ] **Configuration Review**: Verify `.env` settings match production needs
- [ ] **Disk Space**: Ensure adequate space for:
  - `.models/` directory (model versions)
  - `.chroma/` directory (vector store)
  - `.cache/` directory (queue persistence)
- [ ] **Monitoring Setup**: Configure logging and monitoring
- [ ] **Test Graceful Shutdown**: Verify queue persistence works

### Deployment Steps

1. **Copy Production Configuration**:
```bash
cp .env.example .env.production
# Edit .env.production with production values
```

2. **Initialize Database**:
```bash
openfatture --env-file .env.production init-db
```

3. **Train Initial Models** (if using ML features):
```bash
openfatture --env-file .env.production ai forecast --retrain
```

4. **Build Initial RAG Index** (if using RAG):
```bash
openfatture --env-file .env.production ai rag reindex
```

5. **Enable Self-Learning**:
```bash
# Edit .env.production
OPENFATTURE_RAG_AUTO_UPDATE_ENABLED=true
OPENFATTURE_ML_RETRAINING_ENABLED=true
OPENFATTURE_AI_FEEDBACK_ENABLED=true
```

6. **Start Application**:
```bash
openfatture --env-file .env.production ai chat
# Self-learning systems start automatically via lifespan manager
```

7. **Verify Startup**:
```bash
# Check logs for:
# - "RAG auto-update enabled, starting service"
# - "ML retraining enabled, starting scheduler"
# - "Self-learning systems initialized successfully"
```

### Monitoring in Production

**Log Messages to Monitor**:

```
INFO  | Self-learning systems initialized successfully
INFO  | RAG auto-update enabled, starting service
INFO  | Auto-indexing service started
INFO  | ML retraining enabled, starting scheduler
INFO  | Retraining scheduler started

# During operation:
DEBUG | Processing 15 pending changes for reindexing
INFO  | Reindexed 15 entities in 2.3s
INFO  | Evaluating retraining triggers for cash_flow model
INFO  | Retraining triggered: min_feedback_count condition met
INFO  | Model retrained successfully, version: 1.2.0, improvement: 3.5%
```

**Error Messages to Watch**:

```
ERROR | Failed to initialize self-learning systems: <error>
ERROR | Error processing reindex batch: <error>
ERROR | Retraining failed: <error>
WARN  | Queue size limit reached, dropping oldest changes
```

**CLI Monitoring Commands**:

```bash
# RAG Auto-Update
openfatture ai auto-update status
openfatture ai auto-update stats
openfatture ai auto-update pending

# ML Retraining
openfatture ai retrain status
openfatture ai retrain list-versions

# Feedback
openfatture ai feedback stats
```

### Backup and Recovery

**Critical Files to Backup**:

1. **Database**: `openfatture.db` or PostgreSQL dump
2. **Model Files**: `.models/*.json`, `.models/*.pkl`
3. **Vector Store**: `.chroma/` directory
4. **Queue State**: `.cache/rag_update_queue.json` (if persistence enabled)

**Backup Script Example**:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Database
cp openfatture.db "$BACKUP_DIR/" || sqlite3 openfatture.db ".backup $BACKUP_DIR/openfatture.db"

# ML Models
cp -r .models "$BACKUP_DIR/"

# Vector Store
cp -r .chroma "$BACKUP_DIR/"

# Queue State
cp -r .cache "$BACKUP_DIR/"

# Compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup complete: $BACKUP_DIR.tar.gz"
```

**Recovery Steps**:

1. Stop application
2. Restore database: `cp backup/openfatture.db ./`
3. Restore models: `cp -r backup/.models ./`
4. Restore vector store: `cp -r backup/.chroma ./`
5. Restore queue: `cp -r backup/.cache ./`
6. Start application

## Monitoring

### Key Metrics to Track

**RAG Auto-Update**:
- **Pending Changes**: Number of changes waiting to be processed
- **Processed Count**: Total entities reindexed
- **Success Rate**: Percentage of successful reindex operations
- **Processing Time**: Average time per reindex batch
- **Queue Size**: Current queue size vs max limit

**ML Retraining**:
- **Last Training Date**: When model was last retrained
- **Model Version**: Current deployed version
- **Training Trigger**: Why retraining occurred
- **Improvement**: Performance gain from new version
- **Feedback Count**: Number of feedback entries since last training

**Feedback Collection**:
- **Total Feedback**: Count by agent type
- **Average Rating**: User satisfaction score
- **Correction Rate**: Percentage of responses corrected
- **Common Issues**: Most frequently corrected responses

### Metrics Access

**CLI Commands**:
```bash
# View all self-learning metrics
openfatture ai status

# Individual component metrics
openfatture ai auto-update stats
openfatture ai retrain status
openfatture ai feedback stats
```

**Programmatic Access**:
```python
from openfatture.ai.rag.auto_update import get_auto_indexing_service
from openfatture.ai.ml.retraining import get_scheduler
from openfatture.ai.feedback import FeedbackAnalyzer

# RAG metrics
service = get_auto_indexing_service()
stats = await service.get_stats()

# Retraining metrics
scheduler = get_scheduler()
status = scheduler.get_status()

# Feedback metrics
analyzer = FeedbackAnalyzer(session)
stats = analyzer.get_statistics()
```

## Troubleshooting

### RAG Auto-Update Issues

**Problem**: "Queue size limit reached, dropping oldest changes"

**Cause**: Too many changes happening faster than they can be processed.

**Solutions**:
```bash
# Increase queue size
OPENFATTURE_RAG_AUTO_UPDATE_MAX_QUEUE_SIZE=2000

# Reduce debounce time (process more frequently)
OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS=3

# Increase batch size (process more per batch)
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=100

# Increase concurrent updates
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=5
```

---

**Problem**: "Auto-update service not starting"

**Cause**: ChromaDB or embedding provider not available.

**Solutions**:
```bash
# Check RAG configuration
openfatture ai rag status

# Verify embedding provider
OPENFATTURE_RAG_EMBEDDING_PROVIDER=sentence-transformers

# Test manual reindex
openfatture ai rag reindex
```

---

**Problem**: Changes not being tracked

**Cause**: Event listeners not set up.

**Solution**: Event listeners are automatically set up via lifespan manager. Check logs for:
```
DEBUG | Setting up RAG auto-update event listeners
```

If missing, ensure you're using application lifespan:
```python
from openfatture.cli.lifespan import run_sync_with_lifespan

run_sync_with_lifespan(your_command())
```

### ML Retraining Issues

**Problem**: "Model retraining failed: insufficient data"

**Cause**: Not enough training data (requires ≥25 data points).

**Solutions**:
```bash
# Check data availability
openfatture ai feedback stats

# Adjust minimum feedback count
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=50

# Use dry run mode to test without deployment
OPENFATTURE_ML_RETRAINING_DRY_RUN=true
```

---

**Problem**: "New model performance worse than previous"

**Cause**: Model degradation due to outliers or insufficient data.

**Solutions**:
```bash
# Rollback to previous version
openfatture ai retrain rollback --model cash_flow --version 1.1.0

# Adjust minimum improvement threshold
OPENFATTURE_ML_RETRAINING_MIN_IMPROVEMENT_PERCENTAGE=0.05

# Review feedback for outliers
openfatture ai feedback export --output feedback.json
```

---

**Problem**: Retraining running too frequently

**Cause**: Aggressive trigger thresholds.

**Solutions**:
```bash
# Increase check interval
OPENFATTURE_ML_RETRAINING_CHECK_INTERVAL_HOURS=48

# Increase minimum feedback count
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=50

# Relax performance threshold
OPENFATTURE_ML_RETRAINING_PERFORMANCE_DEGRADATION_THRESHOLD=0.15
```

### Feedback Collection Issues

**Problem**: Feedback prompts too intrusive

**Cause**: Long timeout blocking user workflow.

**Solutions**:
```bash
# Reduce prompt timeout
OPENFATTURE_AI_FEEDBACK_PROMPT_TIMEOUT=1

# Or disable interactive prompts
OPENFATTURE_AI_FEEDBACK_ENABLED=false
# Use manual feedback submission instead
```

---

**Problem**: Feedback database growing too large

**Cause**: No retention policy.

**Solutions**:
```bash
# Set retention period
OPENFATTURE_AI_FEEDBACK_RETENTION_DAYS=180

# Or clean up old feedback manually
openfatture ai feedback cleanup --older-than 180
```

### General Issues

**Problem**: High memory usage

**Cause**: Too many concurrent operations or large batches.

**Solutions**:
```bash
# Reduce batch sizes
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=25

# Reduce concurrent updates
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=1

# For embeddings, use smaller model
OPENFATTURE_RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smallest model
```

---

**Problem**: Slow reindexing

**Cause**: Large vector store or slow embedding generation.

**Solutions**:
```bash
# Use local embeddings instead of API
OPENFATTURE_RAG_EMBEDDING_PROVIDER=sentence-transformers

# Enable caching
OPENFATTURE_RAG_ENABLE_CACHING=true

# Increase concurrent updates
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=5
```

## Performance Tuning

### High-Volume Scenarios

**Scenario**: Creating 100+ invoices per day

**Recommended Settings**:
```bash
# RAG Auto-Update: Aggressive batching
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=100
OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS=10
OPENFATTURE_RAG_AUTO_UPDATE_MAX_QUEUE_SIZE=2000
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=5

# ML Retraining: Less frequent
OPENFATTURE_ML_RETRAINING_CHECK_INTERVAL_HOURS=48
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=100
```

### Low-Volume Scenarios

**Scenario**: Creating <10 invoices per day

**Recommended Settings**:
```bash
# RAG Auto-Update: Quick processing
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=10
OPENFATTURE_RAG_AUTO_UPDATE_DEBOUNCE_SECONDS=2
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=2

# ML Retraining: More frequent
OPENFATTURE_ML_RETRAINING_CHECK_INTERVAL_HOURS=24
OPENFATTURE_ML_RETRAINING_MIN_FEEDBACK_COUNT=25
```

### Resource-Constrained Environments

**Scenario**: Limited CPU/memory (e.g., Raspberry Pi, low-cost VPS)

**Recommended Settings**:
```bash
# Use smallest embedding model
OPENFATTURE_RAG_EMBEDDING_PROVIDER=sentence-transformers
OPENFATTURE_RAG_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Conservative processing
OPENFATTURE_RAG_AUTO_UPDATE_BATCH_SIZE=10
OPENFATTURE_RAG_AUTO_UPDATE_MAX_CONCURRENT_UPDATES=1

# Disable retraining (or run manually)
OPENFATTURE_ML_RETRAINING_ENABLED=false
```

## Best Practices

### Development

1. **Start with Feedback Only**: Enable feedback collection first, accumulate data
2. **Test with Dry Run**: Use `OPENFATTURE_ML_RETRAINING_DRY_RUN=true` initially
3. **Monitor Logs**: Check logs during development to understand behavior
4. **Use Manual Commands**: Test manually before enabling automation

### Production

1. **Enable All Components**: Full self-learning system for maximum benefit
2. **Set Up Monitoring**: Track metrics and set up alerts
3. **Regular Backups**: Backup models, vector store, and feedback database
4. **Version Control**: Track model versions for rollback capability
5. **Gradual Rollout**: Enable one component at a time, verify stability

### Optimization

1. **Tune Batch Sizes**: Based on your invoice volume
2. **Adjust Debounce Times**: Balance latency vs efficiency
3. **Right-Size Queue**: Prevent overflow while minimizing memory
4. **Use Local Embeddings**: For cost savings and privacy
5. **Monitor Performance**: Regularly review metrics and adjust

## See Also

- [AI Architecture](AI_ARCHITECTURE.md) - Complete AI system documentation
- [RAG System](RAG_SYSTEM.md) - RAG implementation details
- [Configuration Guide](CONFIGURATION.md) - Complete `.env` reference
- [CLI Reference](CLI_REFERENCE.md) - All CLI commands

---

**Need Help?**

- Check logs: `~/.openfatture/logs/`
- Run diagnostics: `openfatture ai status`
- Report issues: https://github.com/venerelabs/openfatture/issues
