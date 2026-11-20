#!/usr/bin/env python3
"""
T-093: Tests for new console endpoints:
- GET /problems
- POST /problems/handled
- POST /debug-bundle
- GET /config/history?n=
- GET /config/source?key=
- POST /config/undo
- POST /config/reset

Follows the established test pattern from test_config_endpoints.py:
ephemeral port, temp dirs, asserts each endpoint works, POST without X-Router-Action is refused.
"""
import importlib.util
import json
import os
import sys
import tempfile
import threading
import http.server
import socketserver
import urllib.request
import urllib.error

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hooks = os.path.join(root, "project-template", "Claude", "hooks")
tools = os.path.join(root, "tools")
sys.path.insert(0, tools)

tmp = tempfile.mkdtemp(prefix="consoleep2_")
os.environ["KIT_GLOBAL_SETTINGS"] = os.path.join(tmp, "global.json")
os.environ["CLAUDE_PROJECT_DIR"] = tmp

spec = importlib.util.spec_from_file_location("console_server", os.path.join(hooks, "agent-console-server.py"))
srv = importlib.util.module_from_spec(spec)
saved_argv = sys.argv
sys.argv = ["x", "0"]
spec.loader.exec_module(srv)
sys.argv = saved_argv
srv.PROJECT_DIR = tmp

# Create needed directories and seed files
os.makedirs(os.path.join(tmp, "plan"), exist_ok=True)
os.makedirs(os.path.join(tmp, "Claude", "logs"), exist_ok=True)
os.makedirs(os.path.join(tmp, "Claude", "docs"), exist_ok=True)

# seed PROBLEMS-FROM-COD.md
probs = os.path.join(tmp, "plan", "PROBLEMS-FROM-COD.md")
with open(probs, "w", encoding="utf-8") as f:
    # HANDLED format must be without seconds: [HANDLED YYYY-MM-DD HH:MM]
    f.write("2026-01-01|Test ref|First problem\n")
    f.write("2026-01-02|Another ref|Second problem [HANDLED 2026-01-03 12:00]\n")

# seed config
os.makedirs(os.path.join(tmp, "Claude", "config"), exist_ok=True)
settings = os.path.join(tmp, "Claude", "config", "kit-settings.json")
with open(settings, "w", encoding="utf-8") as f:
    json.dump({"budget": {"tokens": {"daily": 100}}}, f)

# seed config-changes.log
changes_log = os.path.join(tmp, "Claude", "logs", "config-changes.log")
with open(changes_log, "w", encoding="utf-8") as f:
    f.write('{"key":"budget.tokens.daily","old":50,"new":100,"scope":"project","when":"2026-01-01T12:00:00"}\n')
    f.write('{"key":"budget.tokens.daily","old":100,"new":200,"scope":"project","when":"2026-01-02T12:00:00"}\n')

class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

httpd = S(("127.0.0.1", 0), srv.Handler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port

fails = []

def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)

def call(method, path, body=None, headers=None):
    h = {"Content-Type": "application/json", "X-Router-Action": "1", "Origin": base}
    if headers:
        h.update(headers)
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

def call_no_auth(method, path, body=None, headers=None):
    """Call without X-Router-Action header or with different Origin"""
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

OK = {"X-Router-Action": "1", "Origin": base}

try:
    # ========================================================================
    # Test GET /problems
    # ========================================================================
    c, d = call("GET", "/problems")
    check("GET /problems returns 200", c == 200)
    check("GET /problems has open/closed/items", c == 200 and "open" in d and "closed" in d and "items" in d)
    check("GET /problems correct counts", c == 200 and d["open"] == 1 and d["closed"] == 1)
    check("GET /problems items have line_id and status", c == 200 and len(d["items"]) == 2 and all("line_id" in i and "status" in i for i in d["items"]))
    check("GET /problems first item open", c == 200 and d["items"][0]["status"] == "open")
    check("GET /problems second item closed", c == 200 and d["items"][1]["status"] == "closed")

    # ========================================================================
    # Test POST /problems/handled
    # ========================================================================
    # Get the line_id of the open problem
    c, d = call("GET", "/problems")
    open_item = next(i for i in d["items"] if i["status"] == "open")
    lid = open_item["line_id"]

    c, d = call("POST", "/problems/handled", {"line_id": lid})
    check("POST /problems/handled marks problem", c == 200 and d["ok"] is True and d["marked"] is True)

    # Verify it's now marked
    c, d = call("GET", "/problems")
    open_count = sum(1 for i in d["items"] if i["status"] == "open")
    check("POST /problems/handled updates counts", c == 200 and open_count == 0)

    # POST without X-Router-Action should be refused
    c, d = call_no_auth("POST", "/problems/handled", {"line_id": lid})
    check("POST /problems/handled without X-Router-Action forbidden", c == 403)

    # POST with foreign origin should be refused
    c, d = call("POST", "/problems/handled", {"line_id": lid}, headers={"Origin": "http://evil.com", "X-Router-Action": "1"})
    check("POST /problems/handled with foreign origin forbidden", c == 403)

    # ========================================================================
    # Test POST /debug-bundle
    # ========================================================================
    c, d = call("POST", "/debug-bundle", {})
    check("POST /debug-bundle returns 200", c == 200)
    check("POST /debug-bundle returns zip path", c == 200 and d["ok"] is True and "zip" in d and d["zip"].endswith(".zip"))
    check("POST /debug-bundle file exists", c == 200 and os.path.exists(d["zip"]))

    # POST without X-Router-Action should be refused
    c, d = call_no_auth("POST", "/debug-bundle", {})
    check("POST /debug-bundle without X-Router-Action forbidden", c == 403)

    # ========================================================================
    # Test GET /config/history?n=
    # ========================================================================
    c, d = call("GET", "/config/history?n=1")
    check("GET /config/history?n=1 returns 200", c == 200)
    check("GET /config/history?n=1 has history", c == 200 and d["ok"] is True and "history" in d and len(d["history"]) == 1)

    c, d = call("GET", "/config/history")
    check("GET /config/history default returns all", c == 200 and len(d["history"]) == 2)

    # ========================================================================
    # Test GET /config/source?key=
    # ========================================================================
    c, d = call("GET", "/config/source?key=budget.tokens.daily")
    check("GET /config/source project key", c == 200 and d["ok"] is True and d["source"] == "project")

    c, d = call("GET", "/config/source?key=nonexistent.key")
    check("GET /config/source unknown key", c == 200 and d["ok"] is True and d["source"] == "default")

    c, d = call("GET", "/config/source?key=")
    check("GET /config/source missing key returns error", c == 200 and d["ok"] is False and "key required" in d.get("error", ""))

    # ========================================================================
    # Test POST /config/undo
    # ========================================================================
    c, d = call("POST", "/config/undo", {"key": "budget.tokens.daily", "confirm": True})
    check("POST /config/undo with confirm works", c == 200 and d["ok"] is True and "undone" in d)

    # POST without confirm for risky key should fail
    # Risky keys are "permissions" and "safety_check"
    c, d = call("POST", "/config/undo", {"key": "permissions"})
    check("POST /config/undo without confirm for risky key refused", c == 409 and "confirm" in d.get("error", "").lower())

    # POST without X-Router-Action should be refused
    c, d = call_no_auth("POST", "/config/undo", {"key": "budget.tokens.daily", "confirm": True})
    check("POST /config/undo without X-Router-Action forbidden", c == 403)

    # POST with foreign origin should be refused
    c, d = call("POST", "/config/undo", {"key": "budget.tokens.daily", "confirm": True}, headers={"Origin": "http://evil.com", "X-Router-Action": "1"})
    check("POST /config/undo with foreign origin forbidden", c == 403)

    # ========================================================================
    # Test POST /config/reset
    # ========================================================================
    c, d = call("POST", "/config/reset", {"key": "budget.tokens.daily", "scope": "project"})
    check("POST /config/reset works", c == 200 and d["ok"] is True and "value" in d and "source" in d)

    c, d = call("POST", "/config/reset", {"key": "budget.tokens.daily", "scope": "invalid"})
    check("POST /config/reset invalid scope refused", c == 400 and "scope must be" in d.get("error", ""))

    c, d = call_no_auth("POST", "/config/reset", {"key": "budget.tokens.daily", "scope": "project"})
    check("POST /config/reset without X-Router-Action forbidden", c == 403)

    c, d = call("POST", "/config/reset", {"key": "budget.tokens.daily", "scope": "project"}, headers={"Origin": "http://evil.com", "X-Router-Action": "1"})
    check("POST /config/reset with foreign origin forbidden", c == 403)

finally:
    httpd.shutdown()

print("\nAll console endpoints2 tests OK" if not fails else "\nFAILURES: " + ", ".join(fails))
sys.exit(1 if fails else 0)