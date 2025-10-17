#!/usr/bin/env python3
"""
Media Dashboard API Server

Simple HTTP server to serve metrics data for the media dashboard.
Run with: python media/dashboard_api.py
"""

import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

METRICS_DIR = os.path.join(os.path.dirname(__file__), "metrics")


class MediaDashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for media dashboard API."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Set CORS headers
        self.send_cors_headers()

        try:
            if path == "/":
                self.serve_dashboard_html()
            elif path == "/api/metrics/costs":
                self.serve_json_file("costs.json")
            elif path == "/api/metrics/performance":
                self.serve_json_file("performance.json")
            elif path == "/api/metrics/runs":
                self.serve_json_file("runs.json")
            elif path == "/api/metrics/alerts":
                self.serve_json_file("alerts.json")
            elif path == "/api/metrics/all":
                self.serve_all_metrics()
            elif path == "/api/health":
                self.serve_health_check()
            else:
                self.send_error_response(404, "Endpoint not found")

        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")

    def send_cors_headers(self):
        """Send CORS headers for all responses."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def send_error_response(self, code, message):
        """Send an error response."""
        error_data = {"error": message, "timestamp": datetime.now().isoformat(), "status": "error"}
        response = json.dumps(error_data, indent=2, ensure_ascii=False)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def serve_dashboard_html(self):
        """Serve the dashboard HTML page."""
        try:
            html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
            with open(html_path, encoding="utf-8") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

        except FileNotFoundError:
            self.send_error_response(404, "Dashboard HTML file not found")
        except Exception as e:
            self.send_error_response(500, f"Error serving dashboard: {str(e)}")

    def serve_json_file(self, filename):
        """Serve a JSON file from the metrics directory."""
        try:
            file_path = os.path.join(METRICS_DIR, filename)
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            response = json.dumps(data, indent=2, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

        except FileNotFoundError:
            self.send_error_response(404, f"Metrics file not found: {filename}")
        except json.JSONDecodeError as e:
            self.send_error_response(500, f"Invalid JSON in {filename}: {str(e)}")

    def serve_all_metrics(self):
        """Serve all metrics data in a single response."""
        try:
            costs = self.load_json_file("costs.json")
            performance = self.load_json_file("performance.json")
            runs = self.load_json_file("runs.json")

            data = {
                "costs": costs,
                "performance": performance,
                "runs": runs,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            }

            response = json.dumps(data, indent=2, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

        except Exception as e:
            error_data = {
                "error": f"Failed to load metrics data: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
            }
            response = json.dumps(error_data, indent=2, ensure_ascii=False)
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

    def serve_health_check(self):
        """Serve health check information."""
        try:
            metrics_files = []
            if os.path.exists(METRICS_DIR):
                metrics_files = [f for f in os.listdir(METRICS_DIR) if f.endswith(".json")]

            data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "metrics_dir_exists": os.path.exists(METRICS_DIR),
                "metrics_files": metrics_files,
                "server_info": {
                    "python_version": sys.version,
                    "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            }

            response = json.dumps(data, indent=2, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

        except Exception as e:
            self.send_error_response(500, f"Health check failed: {str(e)}")

    def load_json_file(self, filename):
        """Load a JSON file and return the data, or empty dict if not found."""
        try:
            file_path = os.path.join(METRICS_DIR, filename)
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        print(f"[Dashboard API] {format % args}")


def run_server(port=8000, host="localhost"):
    """Run the HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MediaDashboardHandler)

    print("🚀 Starting Media Dashboard API Server...")
    print(f"📊 Serving metrics from: {METRICS_DIR}")
    print(f"🌐 Dashboard available at: http://{host}:{port}")
    print("📡 API endpoints:")
    print(f"  - GET http://{host}:{port}/ (dashboard)")
    print(f"  - GET http://{host}:{port}/api/metrics/costs")
    print(f"  - GET http://{host}:{port}/api/metrics/performance")
    print(f"  - GET http://{host}:{port}/api/metrics/runs")
    print(f"  - GET http://{host}:{port}/api/metrics/all")
    print(f"  - GET http://{host}:{port}/api/health")
    print("\nPress Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Media Dashboard API Server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to run server on (default: 8000)"
    )
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")

    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
