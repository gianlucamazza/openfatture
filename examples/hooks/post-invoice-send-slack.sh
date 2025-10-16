#!/bin/bash
# DESCRIPTION: Send Slack notification when invoice is sent to SDI
# AUTHOR: OpenFatture Team
# TIMEOUT: 15
# REQUIRES: curl, jq

# This hook is triggered after an invoice is successfully sent via PEC to SDI.
# It sends a notification to Slack with invoice details.

# Configuration - Set your Slack webhook URL
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"

if [ -z "$SLACK_WEBHOOK" ]; then
    echo "⚠️  SLACK_WEBHOOK_URL not set. Skipping notification."
    echo "Set it in your environment or ~/.openfatture/.env"
    exit 0
fi

# Extract invoice data from environment variables
INVOICE_NUMBER="${OPENFATTURE_INVOICE_NUMBER:-N/A}"
INVOICE_ID="${OPENFATTURE_INVOICE_ID:-N/A}"
CLIENT_NAME="${OPENFATTURE_CLIENT_NAME:-N/A}"
TOTAL_AMOUNT="${OPENFATTURE_TOTAL_AMOUNT:-0.00}"

# Send Slack notification
curl -X POST "$SLACK_WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "{
    \"text\": \"📄 Invoice Sent to SDI\",
    \"blocks\": [
      {
        \"type\": \"header\",
        \"text\": {
          \"type\": \"plain_text\",
          \"text\": \"📄 Invoice Sent Successfully\"
        }
      },
      {
        \"type\": \"section\",
        \"fields\": [
          {
            \"type\": \"mrkdwn\",
            \"text\": \"*Invoice:*\\n${INVOICE_NUMBER}\"
          },
          {
            \"type\": \"mrkdwn\",
            \"text\": \"*Amount:*\\n€${TOTAL_AMOUNT}\"
          },
          {
            \"type\": \"mrkdwn\",
            \"text\": \"*Client:*\\n${CLIENT_NAME}\"
          },
          {
            \"type\": \"mrkdwn\",
            \"text\": \"*Status:*\\nSent to SDI ✅\"
          }
        ]
      },
      {
        \"type\": \"context\",
        \"elements\": [
          {
            \"type\": \"mrkdwn\",
            \"text\": \"Sent at: $(date +'%Y-%m-%d %H:%M:%S') | ID: ${INVOICE_ID}\"
          }
        ]
      }
    ]
  }" \
  --silent --show-error

if [ $? -eq 0 ]; then
    echo "✅ Slack notification sent successfully"
else
    echo "❌ Failed to send Slack notification"
    exit 1
fi
