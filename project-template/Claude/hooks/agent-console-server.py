#!/usr/bin/env python3
"""Claude/hooks/agent-console-server.py

Cross-platform equivalent of agent-console-server.ps1 (use this on macOS/Linux, or on Windows if
you'd rather use Python than PowerShell) — see that file's header comment for the full
explanation. Same six endpoints (/, /log, /tokens, /mcp, /session, /active-task), same default port, no
third-party dependencies (standard library only).

Run it from a terminal and leave it running while you work:

    python3 Claude/hooks/agent-console-server.py
    python3 Claude/hooks/agent-console-server.py 9000   # custom port

Then open http://127.0.0.1:8765/ (or your custom port) in your browser.

Also serves "/whoami" -> {"project": "<absolute path to this project's folder>", "started_at":
"<ISO timestamp this server process actually started>"}. "project" is what
session-start-reminder.py/.sh use to tell "this port is already serving THIS project" apart from
"a different/stale project's server is still bound here" when a new session starts. "started_at"
is what the console page itself uses for its "Session running for" stat (v1.44 fix — that stat
used to be computed from the OLDEST line in agent-console.jsonl, which persists across restarts
by design, so it kept showing hours/days of history even seconds after a genuine restart; the
server's own real start time fixes that without touching the history file).
"""
import http.server
import json
import os
import sys
from datetime import datetime, timezone

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(ROOT, "agent-console.html")
PROJECT_DIR = os.path.dirname(os.path.dirname(ROOT))
SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
LOGS_DIR = os.path.join(os.path.dirname(ROOT), "logs")
LOG_FILE = os.path.join(LOGS_DIR, "agent-console.jsonl")
TOKENS_FILE = os.path.join(LOGS_DIR, "agent-console-tokens.json")
MCP_FILE = os.path.join(LOGS_DIR, "agent-console-mcp.jsonl")
SESSION_FILE = os.path.join(LOGS_DIR, "agent-console-session.json")
DOCS_DIR = os.path.join(os.path.dirname(ROOT), "docs")
ACTIVE_TASK_FILE = os.path.join(DOCS_DIR, ".active-task")


def _read_jsonl(path):
    entries = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _read_json_object(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    return default


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # keep the terminal quiet — the browser polls this every second

    def _send_json_bytes(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/log"):
            self._send_json_bytes(json.dumps(_read_jsonl(LOG_FILE)).encode("utf-8"))
        elif self.path.startswith("/tokens"):
            self._send_json_bytes(_read_json_object(TOKENS_FILE, "{}").encode("utf-8"))
        elif self.path.startswith("/mcp"):
            self._send_json_bytes(json.dumps(_read_jsonl(MCP_FILE)).encode("utf-8"))
        elif self.path.startswith("/session"):
            self._send_json_bytes(_read_json_object(SESSION_FILE, '{"active":false}').encode("utf-8"))
        elif self.path.startswith("/active-task"):
            text = ""
            if os.path.exists(ACTIVE_TASK_FILE):
                with open(ACTIVE_TASK_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/whoami"):
            self._send_json_bytes(json.dumps({"project": PROJECT_DIR, "started_at": SERVER_STARTED_AT}).encode("utf-8"))
        else:
            if not os.path.exists(HTML_PATH):
                self.send_response(404)
                self.end_headers()
                return
            with open(HTML_PATH, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Agent Console running at http://127.0.0.1:{PORT}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
