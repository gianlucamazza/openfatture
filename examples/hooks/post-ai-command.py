#!/usr/bin/env python3
"""Monitor AI command usage and track costs.

DESCRIPTION: Track AI command usage and costs for analytics
TIMEOUT: 10

This hook is triggered after AI command execution completes.
Environment variables available:
    - OPENFATTURE_COMMAND: AI command name (describe, suggest-vat, chat, etc.)
    - OPENFATTURE_SUCCESS: "True" or "False"
    - OPENFATTURE_TOKENS_USED: Number of tokens consumed
    - OPENFATTURE_COST_USD: Cost in USD
    - OPENFATTURE_LATENCY_MS: Execution time in milliseconds
"""

import json
import os
from datetime import datetime


def main():
    """Process AI command completion event."""
    # Extract event data
    command = os.environ.get("OPENFATTURE_COMMAND")
    success = os.environ.get("OPENFATTURE_SUCCESS") == "True"
    tokens_used = int(os.environ.get("OPENFATTURE_TOKENS_USED", "0"))
    cost_usd = float(os.environ.get("OPENFATTURE_COST_USD", "0.0"))
    latency_ms = float(os.environ.get("OPENFATTURE_LATENCY_MS", "0.0"))

    print("🤖 AI Command Completed")
    print("=" * 50)
    print(f"Command: {command}")
    print(f"Status: {'✅ Success' if success else '❌ Failed'}")
    print(f"Tokens: {tokens_used:,}")
    print(f"Cost: ${cost_usd:.6f}")
    print(f"Latency: {latency_ms:.2f}ms")
    print("=" * 50)

    # Calculate cost per 1K tokens
    if tokens_used > 0:
        cost_per_1k = (cost_usd / tokens_used) * 1000
        print(f"Cost per 1K tokens: ${cost_per_1k:.6f}")

    # Track usage for analytics
    usage_log = os.path.expanduser("~/.openfatture/logs/ai-usage.jsonl")
    os.makedirs(os.path.dirname(usage_log), exist_ok=True)

    usage_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "success": success,
        "tokens_used": tokens_used,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
    }

    with open(usage_log, "a") as f:
        f.write(json.dumps(usage_entry) + "\n")

    # Check for high costs and send alerts
    if cost_usd > 0.10:  # Alert if single command costs > $0.10
        print(f"\n⚠️  WARNING: High cost detected: ${cost_usd:.6f}")
        print("Consider reviewing AI provider settings or usage patterns.")

        # Example: Send alert to monitoring system
        # import requests
        # requests.post(
        #     "https://your-monitoring.com/api/alerts",
        #     json={
        #         "event": "high_ai_cost",
        #         "command": command,
        #         "cost": cost_usd,
        #         "threshold": 0.10
        #     }
        # )

    # Generate daily summary if needed
    generate_daily_summary(usage_log)

    print(f"\n✅ Usage tracked to: {usage_log}")


def generate_daily_summary(usage_log):
    """Generate a daily usage summary."""
    try:
        # Read all entries for today
        today = datetime.now().date()
        total_tokens = 0
        total_cost = 0.0
        command_counts = {}

        with open(usage_log) as f:
            for line in f:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry["timestamp"]).date()

                if entry_date == today:
                    total_tokens += entry["tokens_used"]
                    total_cost += entry["cost_usd"]
                    command = entry["command"]
                    command_counts[command] = command_counts.get(command, 0) + 1

        if total_tokens > 0:
            print("\n📊 Today's Summary:")
            print(f"Total Commands: {sum(command_counts.values())}")
            print(f"Total Tokens: {total_tokens:,}")
            print(f"Total Cost: ${total_cost:.4f}")
            print("Commands:")
            for cmd, count in sorted(command_counts.items(), key=lambda x: -x[1]):
                print(f"  • {cmd}: {count}x")

    except FileNotFoundError:
        pass  # First run, no historical data yet


if __name__ == "__main__":
    main()
