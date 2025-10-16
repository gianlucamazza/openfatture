#!/bin/bash
# DESCRIPTION: Monitor batch import operations and send notifications
# TIMEOUT: 10

# This hook is triggered after batch import operations complete
# Environment variables available:
#   - OPENFATTURE_FILE_PATH: Path to the imported CSV file
#   - OPENFATTURE_OPERATION_TYPE: "import" or "export"
#   - OPENFATTURE_SUCCESS: "True" or "False"
#   - OPENFATTURE_RECORDS_PROCESSED: Number of records processed
#   - OPENFATTURE_RECORDS_SUCCEEDED: Number of successful records
#   - OPENFATTURE_RECORDS_FAILED: Number of failed records

echo "📦 Batch Import Completed"
echo "================================"
echo "File: ${OPENFATTURE_FILE_PATH}"
echo "Operation: ${OPENFATTURE_OPERATION_TYPE}"
echo "Success: ${OPENFATTURE_SUCCESS}"
echo "Processed: ${OPENFATTURE_RECORDS_PROCESSED}"
echo "Succeeded: ${OPENFATTURE_RECORDS_SUCCEEDED}"
echo "Failed: ${OPENFATTURE_RECORDS_FAILED}"
echo "================================"

# Calculate success rate
if [ -n "${OPENFATTURE_RECORDS_PROCESSED}" ] && [ "${OPENFATTURE_RECORDS_PROCESSED}" -gt 0 ]; then
    success_rate=$((OPENFATTURE_RECORDS_SUCCEEDED * 100 / OPENFATTURE_RECORDS_PROCESSED))
    echo "Success Rate: ${success_rate}%"
fi

# Send alert if there are failures
if [ -n "${OPENFATTURE_RECORDS_FAILED}" ] && [ "${OPENFATTURE_RECORDS_FAILED}" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: ${OPENFATTURE_RECORDS_FAILED} records failed to import!"
    echo "Review the error log for details."

    # Example: Send to monitoring system
    # curl -X POST "https://your-monitoring-system.com/api/alerts" \
    #     -H "Content-Type: application/json" \
    #     -d "{
    #         \"event\": \"batch_import_failures\",
    #         \"file\": \"${OPENFATTURE_FILE_PATH}\",
    #         \"failed_count\": ${OPENFATTURE_RECORDS_FAILED}
    #     }"
fi

# Log to file
log_file="${HOME}/.openfatture/logs/batch-imports.log"
mkdir -p "$(dirname "$log_file")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Import completed: ${OPENFATTURE_RECORDS_SUCCEEDED}/${OPENFATTURE_RECORDS_PROCESSED} succeeded" >> "$log_file"

echo ""
echo "✅ Hook executed successfully"
