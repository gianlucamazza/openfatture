# Example Hooks

This directory contains example hook scripts demonstrating common use cases for OpenFatture's hook system.

## Available Examples

### 1. `post-invoice-send-slack.sh`
**Trigger:** After invoice sent to SDI
**Purpose:** Send Slack notification with invoice details

**Setup:**
```bash
# 1. Copy to hooks directory
cp post-invoice-send-slack.sh ~/.openfatture/hooks/

# 2. Make executable
chmod +x ~/.openfatture/hooks/post-invoice-send-slack.sh

# 3. Set Slack webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
# Or add to ~/.openfatture/.env:
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 4. Test it
openfatture hooks test post-invoice-send-slack
```

### 2. `post-invoice-create-backup.py`
**Trigger:** After invoice creation
**Purpose:** Automatic database backup with rotation (keeps last 10)

**Setup:**
```bash
# 1. Copy to hooks directory
cp post-invoice-create-backup.py ~/.openfatture/hooks/

# 2. Make executable
chmod +x ~/.openfatture/hooks/post-invoice-create-backup.py

# 3. Test it
openfatture hooks test post-invoice-create-backup
```

**Features:**
- Timestamps each backup
- Includes invoice ID in filename
- Automatically removes old backups (keeps 10 most recent)
- Pure Python (no external dependencies)

## Creating Your Own Hooks

### Hook Naming Convention

Hooks follow this naming pattern:
- `pre-<event>` - Runs before an event
- `post-<event>` - Runs after an event
- `on-<event>` - Runs when an event occurs

Examples:
- `pre-invoice-create.sh` - Before invoice creation
- `post-invoice-send.py` - After invoice sent
- `on-payment-matched.sh` - When payment matched
- `on-sdi-notification.sh` - When SDI notification received

### Available Events

**Invoice Events:**
- `post-invoice-create` - After invoice created
- `post-invoice-send` - After invoice sent to SDI
- `post-invoice-validate` - After XML validation
- `post-invoice-delete` - After invoice deleted

**AI Events:**
- `pre-ai-command` - Before AI command execution
- `post-ai-command` - After AI command completion

**Payment Events:**
- `on-payment-matched` - When transaction matched to invoice
- `on-payment-unmatched` - When match reverted

**SDI Events:**
- `on-sdi-notification` - When SDI notification received

**Batch Events:**
- `pre-batch-import` - Before batch import
- `post-batch-import` - After batch import

### Environment Variables

All hooks receive these variables:
```bash
OPENFATTURE_HOOK_NAME=post-invoice-send
OPENFATTURE_EVENT_TYPE=InvoiceSentEvent
OPENFATTURE_EVENT_ID=uuid-here
OPENFATTURE_EVENT_TIME=2025-01-16T10:30:00Z
OPENFATTURE_EVENT_DATA='{"invoice_id": 123, ...}'  # Full event data as JSON
```

**Event-specific variables:**

For invoice events:
```bash
OPENFATTURE_INVOICE_ID=123
OPENFATTURE_INVOICE_NUMBER=001/2025
OPENFATTURE_CLIENT_ID=45
OPENFATTURE_CLIENT_NAME="Acme Corp"
OPENFATTURE_TOTAL_AMOUNT=1000.00
```

For AI events:
```bash
OPENFATTURE_COMMAND=describe
OPENFATTURE_PROVIDER=openai
OPENFATTURE_MODEL=gpt-4
OPENFATTURE_TOKENS_USED=450
OPENFATTURE_COST_USD=0.0045
```

### Template Scripts

Create new hooks easily:

```bash
# Bash hook
openfatture hooks create my-custom-hook --template bash

# Python hook
openfatture hooks create my-custom-hook --template python
```

### Hook Metadata

Add metadata to your hooks for better documentation:

```bash
#!/bin/bash
# DESCRIPTION: What this hook does
# AUTHOR: Your Name
# TIMEOUT: 30
# REQUIRES: curl, jq
```

View hook info:
```bash
openfatture hooks info post-invoice-send
```

## Hook Management Commands

```bash
# List all hooks
openfatture hooks list

# List only enabled hooks
openfatture hooks list --enabled

# Enable/disable hooks
openfatture hooks enable post-invoice-send
openfatture hooks disable post-invoice-send

# Test a hook with sample data
openfatture hooks test post-invoice-send

# Get detailed info about a hook
openfatture hooks info post-invoice-send
```

## Common Use Cases

### 1. Notifications
- Slack/Discord/Teams notifications
- Email alerts to accounting team
- SMS notifications for urgent events

### 2. Backup & Recovery
- Automatic database backups
- XML file archival to S3/external storage
- Incremental backup on critical operations

### 3. External System Integration
- Update CRM when invoice sent
- Sync to accounting software
- Update inventory management system

### 4. Compliance & Auditing
- Log all invoice operations to audit trail
- Generate compliance reports
- Archive signed XMLs to immutable storage

### 5. Automation
- Auto-generate PDF attachments
- Send invoices to client automatically
- Trigger payment reminder workflows

## Security Considerations

1. **Never commit secrets** to hooks
   - Use environment variables
   - Store in `~/.openfatture/.env`
   - Use secret management tools

2. **Validate inputs** in your hooks
   - Check environment variables exist
   - Validate data before processing

3. **Set appropriate timeouts**
   - Default: 30 seconds
   - Adjust via `# TIMEOUT: N` metadata

4. **Handle failures gracefully**
   - Exit with code 0 for success
   - Exit with non-zero for failures
   - Use `fail_on_error` carefully

## Troubleshooting

### Hook not executing?

1. Check if hook is enabled:
   ```bash
   openfatture hooks list
   ```

2. Check hook script permissions:
   ```bash
   ls -l ~/.openfatture/hooks/
   # Should show -rwxr-xr-x (executable)
   ```

3. Test hook manually:
   ```bash
   openfatture hooks test your-hook-name
   ```

4. Check logs:
   ```bash
   tail -f ~/.openfatture/logs/debug.log
   ```

### Hook timing out?

Increase timeout in hook metadata:
```bash
# TIMEOUT: 60
```

Or modify hook config programmatically.

### Need help?

- See full documentation: `docs/HOOKS.md`
- View hook system architecture: `CLAUDE.md`
- File issues: https://github.com/venerelabs/openfatture/issues

## Contributing

Have a useful hook? Submit a PR to add it to the examples!

1. Add your hook to `examples/hooks/`
2. Document it in this README
3. Test it with `openfatture hooks test`
4. Submit PR with description of use case
