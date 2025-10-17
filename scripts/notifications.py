#!/usr/bin/env python3
"""
Notification system for OpenFatture media alerts.

Supports console, email, and Slack notifications.
"""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests


class NotificationManager:
    """Manages sending notifications through various channels."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def send_alerts(self, alerts: list[dict[str, Any]]) -> None:
        """Send notifications for the given alerts."""
        for alert in alerts:
            self._send_single_alert(alert)

    def _send_single_alert(self, alert: dict[str, Any]) -> None:
        """Send a single alert through all configured channels."""
        # Console notifications
        if self.config.get("notifications", {}).get("console", {}).get("enabled", True):
            self._send_console_notification(alert)

        # Email notifications
        if self.config.get("notifications", {}).get("email", {}).get("enabled", False):
            try:
                self._send_email_notification(alert)
            except Exception as e:
                print(f"Failed to send email notification: {e}")

        # Slack notifications
        if self.config.get("notifications", {}).get("slack", {}).get("enabled", False):
            try:
                self._send_slack_notification(alert)
            except Exception as e:
                print(f"Failed to send Slack notification: {e}")

    def _send_console_notification(self, alert: dict[str, Any]) -> None:
        """Send notification to console."""
        level_icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}

        icon = level_icons.get(alert.get("level", "info"), "ℹ️")
        level = alert.get("level", "info").upper()
        title = alert.get("title", "Alert")
        message = alert.get("message", "")

        print(f"{icon} [{level}] {title}: {message}")

        if self.config.get("notifications", {}).get("console", {}).get("verbose", False):
            # Print full alert details in verbose mode
            print(f"  Details: {json.dumps(alert, indent=2, default=str)}")

    def _send_email_notification(self, alert: dict[str, Any]) -> None:
        """Send notification via email."""
        email_config = self.config.get("notifications", {}).get("email", {})

        smtp_server = email_config.get("smtp_server")
        smtp_port = email_config.get("smtp_port", 587)
        sender = email_config.get("sender")
        recipients = email_config.get("recipients", [])

        if not all([smtp_server, sender, recipients]):
            raise ValueError("Email configuration incomplete")

        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = f"OpenFatture Media Alert: {alert.get('title', 'Alert')}"

        # Create HTML body
        html_body = self._create_email_html(alert)
        msg.attach(MIMEText(html_body, "html"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            # Note: In production, use proper authentication
            server.send_message(msg)

        print(f"Email notification sent to {len(recipients)} recipients")

    def _send_slack_notification(self, alert: dict[str, Any]) -> None:
        """Send notification via Slack webhook."""
        slack_config = self.config.get("notifications", {}).get("slack", {})

        webhook_url = slack_config.get("webhook_url")
        channel = slack_config.get("channel", "#alerts")
        username = slack_config.get("username", "OpenFatture Media Monitor")

        if not webhook_url:
            raise ValueError("Slack webhook URL not configured")

        # Create Slack message
        color = self._get_slack_color(alert.get("level", "info"))
        message = {
            "channel": channel,
            "username": username,
            "attachments": [
                {
                    "color": color,
                    "title": alert.get("title", "Alert"),
                    "text": alert.get("message", ""),
                    "fields": [
                        {
                            "title": "Level",
                            "value": alert.get("level", "info").upper(),
                            "short": True,
                        },
                        {"title": "Type", "value": alert.get("type", "unknown"), "short": True},
                    ],
                    "footer": "OpenFatture Media Monitor",
                    "ts": self._timestamp_to_unix(alert.get("timestamp")),
                }
            ],
        }

        # Add scenario and run ID if available
        if alert.get("scenario"):
            message["attachments"][0]["fields"].append(
                {"title": "Scenario", "value": alert.get("scenario"), "short": True}
            )

        if alert.get("run_id"):
            message["attachments"][0]["fields"].append(
                {"title": "Run ID", "value": alert.get("run_id"), "short": True}
            )

        # Send to Slack
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()

        print("Slack notification sent")

    def _create_email_html(self, alert: dict[str, Any]) -> str:
        """Create HTML email body for alert."""
        level_colors = {
            "info": "#3498db",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "critical": "#c0392b",
        }

        color = level_colors.get(alert.get("level", "info"), "#3498db")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px 5px 0 0; }}
                .content {{ border: 1px solid #ddd; border-top: none; padding: 20px; border-radius: 0 0 5px 5px; }}
                .field {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>OpenFatture Media Alert</h2>
                <h3>{alert.get("title", "Alert")}</h3>
            </div>
            <div class="content">
                <div class="field">
                    <span class="label">Message:</span>
                    <span class="value">{alert.get("message", "")}</span>
                </div>
                <div class="field">
                    <span class="label">Level:</span>
                    <span class="value">{alert.get("level", "info").upper()}</span>
                </div>
                <div class="field">
                    <span class="label">Type:</span>
                    <span class="value">{alert.get("type", "unknown")}</span>
                </div>
        """

        if alert.get("scenario"):
            html += f"""
                <div class="field">
                    <span class="label">Scenario:</span>
                    <span class="value">{alert.get("scenario")}</span>
                </div>
            """

        if alert.get("run_id"):
            html += f"""
                <div class="field">
                    <span class="label">Run ID:</span>
                    <span class="value">{alert.get("run_id")}</span>
                </div>
            """

        if alert.get("threshold") is not None and alert.get("actual") is not None:
            html += f"""
                <div class="field">
                    <span class="label">Threshold:</span>
                    <span class="value">{alert.get("threshold")}</span>
                </div>
                <div class="field">
                    <span class="label">Actual:</span>
                    <span class="value">{alert.get("actual")}</span>
                </div>
            """

        html += f"""
                <div class="field">
                    <span class="label">Time:</span>
                    <span class="value">{alert.get("timestamp", "Unknown")}</span>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _get_slack_color(self, level: str) -> str:
        """Get Slack color for alert level."""
        colors = {"info": "good", "warning": "warning", "error": "danger", "critical": "danger"}
        return colors.get(level, "good")

    def _timestamp_to_unix(self, timestamp: str | None) -> float | None:
        """Convert ISO timestamp to Unix timestamp."""
        if not timestamp:
            return None

        try:
            from datetime import datetime

            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None


def load_config(config_path: str = "media/alerts_config.json") -> dict[str, Any]:
    """Load notification configuration."""
    config_file = Path(config_path)

    if not config_file.exists():
        # Return default config
        return {
            "notifications": {
                "console": {"enabled": True, "verbose": False},
                "email": {"enabled": False},
                "slack": {"enabled": False},
            }
        }

    try:
        with open(config_file, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return load_config()  # Return defaults


def send_test_notification(config_path: str = "media/alerts_config.json") -> None:
    """Send a test notification to verify configuration."""
    config = load_config(config_path)

    test_alert = {
        "type": "test",
        "level": "info",
        "title": "Test Notification",
        "message": "This is a test notification to verify your alert configuration.",
        "timestamp": "2024-01-01T12:00:00Z",
        "run_id": "test-run-123",
    }

    manager = NotificationManager(config)
    manager.send_alerts([test_alert])
    print("Test notification sent!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send test notifications")
    parser.add_argument("--test", action="store_true", help="Send test notification")
    parser.add_argument("--config", default="media/alerts_config.json", help="Config file path")

    args = parser.parse_args()

    if args.test:
        send_test_notification(args.config)
    else:
        print("Use --test to send a test notification")
