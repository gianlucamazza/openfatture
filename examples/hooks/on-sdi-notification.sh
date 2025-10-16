#!/bin/bash
# DESCRIPTION: Monitor SDI notifications and send alerts
# TIMEOUT: 10

# This hook is triggered when an SDI notification is received
# Environment variables available:
#   - OPENFATTURE_NOTIFICATION_TYPE: RC, NS, MC, DT, NE
#   - OPENFATTURE_INVOICE_ID: Invoice database ID
#   - OPENFATTURE_INVOICE_NUMBER: Invoice number (e.g., "001/2025")
#   - OPENFATTURE_MESSAGE: Notification message
#   - OPENFATTURE_SDI_IDENTIFIER: SDI identifier

echo "📬 SDI Notification Received"
echo "================================"
echo "Type: ${OPENFATTURE_NOTIFICATION_TYPE}"
echo "Invoice: ${OPENFATTURE_INVOICE_NUMBER} (ID: ${OPENFATTURE_INVOICE_ID})"
echo "Message: ${OPENFATTURE_MESSAGE}"
echo "SDI ID: ${OPENFATTURE_SDI_IDENTIFIER}"
echo "================================"

# Decode notification type
case "${OPENFATTURE_NOTIFICATION_TYPE}" in
    "RC")
        echo "✅ Ricevuta Consegna - Invoice delivered successfully"
        ;;
    "NS")
        echo "❌ Notifica Scarto - Invoice rejected by SDI"
        echo "⚠️  ACTION REQUIRED: Review and fix issues"
        ;;
    "MC")
        echo "⚠️  Mancata Consegna - Delivery failed"
        echo "ACTION REQUIRED: Check recipient data"
        ;;
    "DT")
        echo "📧 Decorrenza Termini - Terms expired (5 days)"
        ;;
    "NE")
        esito=$(echo "${OPENFATTURE_MESSAGE}" | grep -o "EC[0-9]*" || echo "unknown")
        if [[ "$esito" == "EC01" ]]; then
            echo "✅ Notifica Esito - Invoice ACCEPTED by recipient"
        elif [[ "$esito" == "EC02" ]]; then
            echo "❌ Notifica Esito - Invoice REJECTED by recipient"
        else
            echo "ℹ️  Notifica Esito - Outcome notification received"
        fi
        ;;
    *)
        echo "ℹ️  Unknown notification type"
        ;;
esac

# Log to file
log_file="${HOME}/.openfatture/logs/sdi-notifications.log"
mkdir -p "$(dirname "$log_file")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${OPENFATTURE_NOTIFICATION_TYPE} - Invoice ${OPENFATTURE_INVOICE_NUMBER}: ${OPENFATTURE_MESSAGE}" >> "$log_file"

# Send alerts for critical notifications (NS, MC, NE with EC02)
if [[ "${OPENFATTURE_NOTIFICATION_TYPE}" == "NS" ]] || [[ "${OPENFATTURE_NOTIFICATION_TYPE}" == "MC" ]]; then
    echo ""
    echo "🚨 CRITICAL: Sending alert for failed notification"

    # Example: Send email alert
    # echo "SDI ${OPENFATTURE_NOTIFICATION_TYPE} for invoice ${OPENFATTURE_INVOICE_NUMBER}: ${OPENFATTURE_MESSAGE}" | \
    #     mail -s "OpenFatture: SDI Notification Alert" your-email@example.com

    # Example: Send to Slack
    # curl -X POST "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
    #     -H "Content-Type: application/json" \
    #     -d "{
    #         \"text\": \"🚨 SDI Notification Alert\",
    #         \"attachments\": [{
    #             \"color\": \"danger\",
    #             \"fields\": [
    #                 {\"title\": \"Type\", \"value\": \"${OPENFATTURE_NOTIFICATION_TYPE}\", \"short\": true},
    #                 {\"title\": \"Invoice\", \"value\": \"${OPENFATTURE_INVOICE_NUMBER}\", \"short\": true},
    #                 {\"title\": \"Message\", \"value\": \"${OPENFATTURE_MESSAGE}\", \"short\": false}
    #             ]
    #         }]
    #     }"

    # Example: Create ticket in issue tracker
    # curl -X POST "https://your-issuetracker.com/api/issues" \
    #     -H "Content-Type: application/json" \
    #     -d "{
    #         \"title\": \"SDI ${OPENFATTURE_NOTIFICATION_TYPE} - Invoice ${OPENFATTURE_INVOICE_NUMBER}\",
    #         \"description\": \"${OPENFATTURE_MESSAGE}\",
    #         \"priority\": \"high\",
    #         \"labels\": [\"sdi\", \"notification\", \"${OPENFATTURE_NOTIFICATION_TYPE}\"]
    #     }"
fi

echo ""
echo "✅ Notification processed and logged"
echo "📝 Log: ${log_file}"
