# Custom Hooks & Event System

OpenFatture includes a powerful hook system that allows you to execute custom scripts at key lifecycle events (invoice creation, AI commands, SDI notifications, etc.). This enables seamless integration with external systems, automation workflows, and custom business logic.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Available Hook Points](#available-hook-points)
- [Environment Variables](#environment-variables)
- [Hook Management](#hook-management)
- [Writing Hooks](#writing-hooks)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The hook system consists of three main components:

1. **Events**: Domain events published at key lifecycle moments
2. **Hooks**: Shell or Python scripts executed when events occur
3. **Bridge**: Automatic connection between events and hooks

```
Event Published → Event Bus → Hook Bridge → Hook Executor → Your Script
```

**Key Features:**
- ✅ Shell (`.sh`, `.bash`) and Python (`.py`) support
- ✅ Automatic event-to-hook mapping
- ✅ Environment variable injection
- ✅ Timeout enforcement
- ✅ Error isolation (one hook failure doesn't affect others)
- ✅ Priority-based execution
- ✅ Enable/disable without deleting
- ✅ Test hooks with sample data

---

## Quick Start

### 1. Create Your First Hook

```bash
# Create a hook from template
openfatture hooks create post-invoice-send --template bash

# This creates: ~/.openfatture/hooks/post-invoice-send.sh
```

### 2. Edit the Hook

```bash
# Open in your editor
$EDITOR ~/.openfatture/hooks/post-invoice-send.sh
```

Example content:
```bash
#!/bin/bash
# DESCRIPTION: Send Slack notification when invoice is sent
# TIMEOUT: 15

INVOICE_NUMBER="${OPENFATTURE_INVOICE_NUMBER}"
TOTAL_AMOUNT="${OPENFATTURE_TOTAL_AMOUNT}"

curl -X POST "$SLACK_WEBHOOK" \
  -d "{\"text\": \"Invoice ${INVOICE_NUMBER} sent! Amount: €${TOTAL_AMOUNT}\"}"
```

### 3. Test the Hook

```bash
# Test with sample event data
openfatture hooks test post-invoice-send
```

### 4. Use It!

```bash
# Send an invoice - your hook will execute automatically
openfatture fattura invia 123 --pec
# → post-invoice-send.sh executes automatically after successful send
```

---

## Architecture

### Event System

The event system is a global publish/subscribe bus that supports:
- **Synchronous and asynchronous** handlers
- **Priority-based execution** (higher priority = runs first)
- **Event filtering** by type
- **Audit logging** of all events
- **Custom listeners** via configuration

Events are published at key points in the application:

```python
# When invoice is created
event_bus.publish(InvoiceCreatedEvent(
    invoice_id=123,
    invoice_number="001/2025",
    client_id=45,
    total_amount=Decimal("1000.00"),
))
```

### Hook Execution

Hooks are discovered automatically from `~/.openfatture/hooks/` and executed when matching events occur:

1. **Event Published** → `InvoiceSentEvent`
2. **Hook Registry** → Finds matching hooks (`post-invoice-send.*`)
3. **Hook Executor** → Runs each hook with:
   - Environment variables injected
   - Timeout enforcement (default: 30s)
   - Output capture (stdout/stderr)
4. **Result Logging** → Success/failure logged with structured data

---

## Available Hook Points

### Invoice Events

| Hook Name | Trigger | Event Data |
|-----------|---------|------------|
| `post-invoice-create` | After invoice created | invoice_id, invoice_number, client_id, client_name, total_amount |
| `post-invoice-send` | After invoice sent to SDI | invoice_id, invoice_number, recipient, pec_address, xml_path |
| `post-invoice-validate` | After XML validation | invoice_id, invoice_number, validation_status, issues[], xml_path |
| `post-invoice-delete` | After invoice deleted | invoice_id, invoice_number, reason |

### AI Events

| Hook Name | Trigger | Event Data |
|-----------|---------|------------|
| `pre-ai-command` | Before AI command execution | command, user_input, provider, model, parameters |
| `post-ai-command` | After AI command completion | command, success, tokens_used, cost_usd, latency_ms |

### Payment Events

| Hook Name | Trigger | Event Data |
|-----------|---------|------------|
| `on-payment-matched` | When transaction matched to payment | transaction_id, payment_id, matched_amount, match_type |
| `on-payment-unmatched` | When match reverted | transaction_id, payment_id, reverted_amount |

### SDI Events

| Hook Name | Trigger | Event Data |
|-----------|---------|------------|
| `on-sdi-notification` | When SDI notification received | notification_type (RC/NS/MC/DT), invoice_id, invoice_number, message |

### Batch Events

| Hook Name | Trigger | Event Data |
|-----------|---------|------------|
| `pre-batch-import` | Before batch import starts | file_path, operation_type, dry_run |
| `post-batch-import` | After batch import completes | file_path, success, records_processed, records_succeeded, records_failed |

---

## Environment Variables

All hooks receive standard environment variables:

### Standard Variables

```bash
OPENFATTURE_HOOK_NAME=post-invoice-send
OPENFATTURE_EVENT_TYPE=InvoiceSentEvent
OPENFATTURE_EVENT_ID=550e8400-e29b-41d4-a716-446655440000
OPENFATTURE_EVENT_TIME=2025-01-16T10:30:00Z
OPENFATTURE_EVENT_DATA='{"invoice_id": 123, "invoice_number": "001/2025", ...}'
```

### Event-Specific Variables

**Invoice Events:**
```bash
OPENFATTURE_INVOICE_ID=123
OPENFATTURE_INVOICE_NUMBER=001/2025
OPENFATTURE_CLIENT_ID=45
OPENFATTURE_CLIENT_NAME="Acme Corp SRL"
OPENFATTURE_TOTAL_AMOUNT=1000.00
OPENFATTURE_CURRENCY=EUR
```

**AI Events:**
```bash
OPENFATTURE_COMMAND=describe
OPENFATTURE_USER_INPUT="3 hours consulting"
OPENFATTURE_PROVIDER=openai
OPENFATTURE_MODEL=gpt-4
OPENFATTURE_TOKENS_USED=450
OPENFATTURE_COST_USD=0.0045
OPENFATTURE_LATENCY_MS=850.5
```

**Payment Events:**
```bash
OPENFATTURE_TRANSACTION_ID=uuid-here
OPENFATTURE_PAYMENT_ID=123
OPENFATTURE_MATCHED_AMOUNT=1000.00
OPENFATTURE_MATCH_TYPE=exact
```

### Parsing Event Data

**Bash (with jq):**
```bash
INVOICE_NUMBER=$(echo "$OPENFATTURE_EVENT_DATA" | jq -r '.invoice_number')
```

**Python:**
```python
import json, os
event_data = json.loads(os.getenv("OPENFATTURE_EVENT_DATA"))
invoice_number = event_data["invoice_number"]
```

---

## Hook Management

### List Hooks

```bash
# List all hooks
openfatture hooks list

# List only enabled hooks
openfatture hooks list --enabled
```

Output:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                   ┃ Enabled ┃ Timeout ┃ Description            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ post-invoice-send      │    ✓    │    15s  │ Send Slack notification│
│ post-invoice-create    │    ✓    │    30s  │ Backup database        │
└────────────────────────┴─────────┴─────────┴────────────────────────┘
```

### Enable/Disable Hooks

```bash
# Disable a hook (doesn't delete it)
openfatture hooks disable post-invoice-send

# Enable it again
openfatture hooks enable post-invoice-send
```

### Test Hooks

```bash
# Test with sample data
openfatture hooks test post-invoice-send

# Output shows execution result
```

### Get Hook Info

```bash
openfatture hooks info post-invoice-send
```

Shows:
- Script path
- Enabled status
- Timeout
- Metadata (description, author, requirements)
- Script preview

---

## Writing Hooks

### Hook Naming

Hooks must follow the naming convention to be matched with events:

**Pattern:** `{timing}-{event}-{action}.{ext}`

Examples:
- `post-invoice-create.sh`
- `pre-batch-import.py`
- `on-payment-matched.sh`

### Metadata Comments

Add metadata at the top of your script:

```bash
#!/bin/bash
# DESCRIPTION: What this hook does
# AUTHOR: Your Name
# TIMEOUT: 30
# REQUIRES: curl, jq
```

Metadata is used by:
- `openfatture hooks list` (description)
- `openfatture hooks info` (all metadata)
- Hook executor (timeout)

### Exit Codes

- **0**: Success
- **Non-zero**: Failure

Failures are logged but don't halt operations unless `fail_on_error=True` is set.

### Bash Template

```bash
#!/bin/bash
# DESCRIPTION: My custom hook
# TIMEOUT: 30

# Get event data
INVOICE_NUMBER="${OPENFATTURE_INVOICE_NUMBER}"
TOTAL_AMOUNT="${OPENFATTURE_TOTAL_AMOUNT}"

echo "Processing invoice ${INVOICE_NUMBER}"

# Your custom logic here
# Example: Send notification, update external system, etc.

exit 0
```

### Python Template

```python
#!/usr/bin/env python3
"""
DESCRIPTION: My custom hook
TIMEOUT: 30
"""

import json
import os
import sys

def main():
    # Get event data
    event_data_json = os.getenv("OPENFATTURE_EVENT_DATA")
    event_data = json.loads(event_data_json)

    invoice_number = event_data["invoice_number"]
    print(f"Processing invoice {invoice_number}")

    # Your custom logic here

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## Examples

See `examples/hooks/` for complete examples:

### 1. Slack Notification

**File:** `post-invoice-send-slack.sh`

Sends rich Slack notification when invoice is sent:

```bash
curl -X POST "$SLACK_WEBHOOK" \
  -d "{
    \"text\": \"Invoice ${OPENFATTURE_INVOICE_NUMBER} sent!\",
    \"blocks\": [...]
  }"
```

### 2. Automatic Database Backup

**File:** `post-invoice-create-backup.py`

Backs up database after each invoice creation, with automatic rotation:

```python
# Backup with timestamp
backup_filename = f"openfatture_backup_{timestamp}_invoice_{invoice_id}.db"
shutil.copy2(db_path, backup_path)

# Cleanup old backups (keep last 10)
_cleanup_old_backups(backup_dir, keep=10)
```

### 3. External CRM Integration

```bash
#!/bin/bash
# Update CRM when invoice sent

curl -X POST "https://crm.example.com/api/invoices" \
  -H "Authorization: Bearer $CRM_API_KEY" \
  -d "{
    \"invoice_number\": \"${OPENFATTURE_INVOICE_NUMBER}\",
    \"client_name\": \"${OPENFATTURE_CLIENT_NAME}\",
    \"amount\": ${OPENFATTURE_TOTAL_AMOUNT},
    \"status\": \"sent\"
  }"
```

---

## Best Practices

### 1. Security

- **Never commit secrets** to hook scripts
- Use environment variables for credentials
- Store secrets in `~/.openfatture/.env` or secret managers
- Validate inputs before processing

### 2. Performance

- Keep hooks fast (< 5 seconds)
- Use async operations for long-running tasks
- Set appropriate timeouts
- Consider running heavy operations in background

### 3. Error Handling

- Exit with code 0 for success
- Use descriptive error messages
- Log errors to stderr
- Handle missing environment variables gracefully

### 4. Testing

- Always test hooks before enabling:
  ```bash
  openfatture hooks test my-hook
  ```
- Test with various event scenarios
- Verify external integrations work
- Check timeout behavior

### 5. Maintenance

- Document your hooks with metadata comments
- Use version control for hooks
- Review logs regularly
- Keep hooks updated with API changes

### 6. Configuration

Configure hooks via `~/.openfatture/.env`:

```bash
# Slack webhook for notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# CRM API credentials
CRM_API_KEY=your-api-key
CRM_BASE_URL=https://crm.example.com

# Custom hook settings
BACKUP_RETENTION_DAYS=30
NOTIFICATION_ENABLED=true
```

---

## Troubleshooting

### Hook Not Executing

**Check if enabled:**
```bash
openfatture hooks list
```

**Check permissions:**
```bash
ls -l ~/.openfatture/hooks/
# Should show: -rwxr-xr-x (executable)
```

**Fix permissions:**
```bash
chmod +x ~/.openfatture/hooks/my-hook.sh
```

### Hook Failing

**Test manually:**
```bash
openfatture hooks test my-hook
# Shows stdout, stderr, exit code
```

**Check logs:**
```bash
tail -f ~/.openfatture/logs/debug.log | grep hook
```

**Common issues:**
- Missing dependencies (`REQUIRES` not installed)
- Environment variables not set
- Timeout too short
- Permission issues

### Hook Timing Out

**Increase timeout in metadata:**
```bash
# TIMEOUT: 60
```

**Or split into async operation:**
```bash
# Queue background job instead of blocking
./long-running-task.sh &
disown
```

### No Hooks Found

**Check hooks directory:**
```bash
ls -la ~/.openfatture/hooks/
```

**Reload registry:**
```bash
# Hooks are auto-discovered on CLI start
# Or explicitly reload:
openfatture hooks list  # Triggers reload
```

---

## Advanced Topics

### Custom Event Listeners

Beyond hooks, you can create custom Python event listeners:

1. **Create listener:**
   ```python
   # myapp/listeners.py
   from openfatture.core.events import BaseEvent

   def my_listener(event: BaseEvent):
       print(f"Event received: {event.__class__.__name__}")
   ```

2. **Configure in `.env`:**
   ```bash
   OPENFATTURE_EVENT_LISTENERS=myapp.listeners.my_listener
   ```

3. **Listener runs automatically** for all events

### Programmatic Hook Configuration

```python
from openfatture.core.hooks import get_hook_registry, HookConfig
from pathlib import Path

registry = get_hook_registry()

# Create custom hook config
hook = HookConfig(
    name="my-hook",
    script_path=Path("/path/to/script.sh"),
    enabled=True,
    timeout_seconds=60,
    fail_on_error=False,  # Don't halt on failure
)

# Manually execute
from openfatture.core.hooks import HookExecutor
executor = HookExecutor()
result = executor.execute_hook(hook, event)
```

### Async Hooks

For non-blocking execution:

```python
result = await executor.execute_hook_async(hook, event)
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENFATTURE_EVENT_LISTENERS` | Custom event listeners (Python paths) | None |

### Hook Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `DESCRIPTION` | What the hook does | "Send Slack notification" |
| `AUTHOR` | Hook author | "John Doe" |
| `TIMEOUT` | Timeout in seconds | 30 |
| `REQUIRES` | Required dependencies | "curl, jq" |

---

## Resources

- **Examples:** `examples/hooks/`
- **Architecture:** `CLAUDE.md` (Hook System section)
- **CLI Reference:** `docs/CLI_REFERENCE.md` (Hooks section)
- **GitHub Issues:** https://github.com/venerelabs/openfatture/issues

---

## Contributing

Have a useful hook? Share it with the community!

1. Add to `examples/hooks/`
2. Document in `examples/hooks/README.md`
3. Test thoroughly
4. Submit PR with use case description

---

**Happy Hooking!** 🪝

For questions or issues, please file an issue on GitHub or consult the documentation.
