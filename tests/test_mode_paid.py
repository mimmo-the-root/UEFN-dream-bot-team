#!/usr/bin/env python3
"""Mode "paid" of the Dream Router (T-059): the router stays in the path and forwards ONLY to the paid plan with the session's own login.
Never a free model; no login = a clear error, not a blind pass. Fake Claude behind the plan, no network."""
import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")
import dream_router as dr  # noqa: E402

dr.check_all = lambda: []
dr.PORT = 1
SEEN = []
PLAN_CODE = [200]


class FakePlan(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        SEEN.append(self.headers.get("Authorization"))
        out = json.dumps({"id": "m", "type": "message", "role": "assistant", "model": "claude", "stop_reason": "end_turn",
                          "content": [{"type": "text", "text": "from the plan"}], "usage": {"input_tokens": 5, "output_tokens": 3}}).encode()
        self.send_response(PLAN_CODE[0])
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


plan = ThreadingHTTPServer(("127.0.0.1", 0), FakePlan)
threading.Thread(target=plan.serve_forever, daemon=True).start()
dr.UPSTREAM = "http://127.0.0.1:%d" % plan.server_port
router = ThreadingHTTPServer(("127.0.0.1", 0), dr.Handler)
threading.Thread(target=router.serve_forever, daemon=True).start()
R = "http://127.0.0.1:%d" % router.server_port
WORK = {"model": "claude-x", "max_tokens": 64, "messages": [{"role": "user", "content": "hello"}]}
FREE_CALLS = []


def fake_route(req):
    FREE_CALLS.append(req.get("model"))
    return {"id": "m", "type": "message", "role": "assistant", "model": "free", "stop_reason": "end_turn", "stop_sequence": None,
            "content": [{"type": "text", "text": "from the free model"}], "usage": {"input_tokens": 1, "output_tokens": 1}}, "fake-free", None


dr.route_patiently = fake_route


def setmode(mode):
    with open(os.path.join(home, "routing.json"), "w") as f:
        json.dump({"mode": mode, "chain": ["ok"]}, f)
    dr.STATE["plan_until"] = 0
    del SEEN[:]
    del FREE_CALLS[:]
    PLAN_CODE[0] = 200


def post(obj, token="login-abc", path="/v1/messages"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    rq = urllib.request.Request(R + path, json.dumps(obj).encode(), headers=h)
    try:
        with urllib.request.urlopen(rq, timeout=15) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_mode_and_env():
    assert "paid" in dr.MODES
    env = dr.router_env("paid")
    assert "ANTHROPIC_AUTH_TOKEN" not in env and env["ANTHROPIC_BASE_URL"].startswith("http://127.0.0.1:")
    assert dr.router_env("paid") == dr.router_env("auto")   # same session env: no restart to switch modes


def test_paid_goes_only_to_plan_with_session_login():
    setmode("paid")
    code, body = post(WORK)
    assert code == 200 and "from the plan" in body, (code, body)
    assert SEEN == ["Bearer login-abc"] and not FREE_CALLS, (SEEN, FREE_CALLS)


def test_paid_without_login_is_a_clear_error_not_a_pass():
    setmode("paid")
    for tok in (None, dr.FREE_TOKEN):
        code, body = post(WORK, token=tok)
        assert code == 401 and "login" in body, (code, body)
    assert not SEEN and not FREE_CALLS, (SEEN, FREE_CALLS)


def test_paid_never_falls_back_to_free_when_plan_limited():
    setmode("paid")
    PLAN_CODE[0] = 429
    code, body = post(WORK)
    assert code == 503 and "Paid" in body, (code, body)
    assert not FREE_CALLS, FREE_CALLS


def test_auto_and_free_unchanged():
    setmode("auto")
    code, body = post(WORK)
    assert code == 200 and "from the plan" in body and not FREE_CALLS, (code, body)
    setmode("free")
    code, body = post(WORK, token=dr.FREE_TOKEN)
    assert code == 200 and "from the free model" in body and FREE_CALLS and not SEEN, (code, body, SEEN)


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception as e:  # noqa: BLE001
            failed.append(name)
            print("FAIL %s: %r" % (name, e))
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS mode_paid: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
