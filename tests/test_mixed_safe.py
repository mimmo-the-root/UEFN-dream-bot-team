#!/usr/bin/env python3
"""Mode "safe" of the Dream Router (T-081, T-083): the work goes to free models, only the auto-mode safety check may use the paid plan
(login kept, plan has credit); with no credit or no login the safety check gets a LOCAL fail-closed verdict, never a blind allow.
Fake Claude behind the plan, no network, never the owner's router or settings."""
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


class FakePlan(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        SEEN.append((self.headers.get("Authorization"), bool(body.get("tools"))))
        out = json.dumps({"id": "m", "type": "message", "role": "assistant", "model": "claude", "stop_reason": "end_turn",
                          "content": [{"type": "text", "text": "<block>no</block>"}], "usage": {"input_tokens": 5, "output_tokens": 3}}).encode()
        self.send_response(200)
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
SAFETY = {"model": "claude-x", "max_tokens": 64, "system": "You are a security monitor. <transcript>User: fix it\nBash: git status</transcript>",
          "messages": [{"role": "user", "content": "decide"}]}
WORK = {"model": "claude-x", "max_tokens": 64, "tools": [{"name": "Read", "description": "r", "input_schema": {"type": "object"}}],
        "messages": [{"role": "user", "content": "hello"}]}


def setmode(**kw):
    cfg = {"mode": "safe", "chain": ["ok"]}
    cfg.update(kw)
    with open(os.path.join(home, "routing.json"), "w") as f:
        json.dump(cfg, f)
    dr.STATE["plan_until"] = 0


def post(obj, token="login-abc"):
    rq = urllib.request.Request(R + "/v1/messages", json.dumps(obj).encode(),
                                headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(rq, timeout=15) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_mode_and_env():
    assert "safe" in dr.MODES
    assert "ANTHROPIC_AUTH_TOKEN" not in dr.router_env("safe") and dr.router_env("safe")["CLAUDE_CODE_AUTO_MODE_SERVER"] == "0"
    assert "ANTHROPIC_AUTH_TOKEN" in dr.router_env("free")


def test_credit_safety_check_goes_to_plan():
    setmode()
    del SEEN[:]
    code, body = post(SAFETY)
    assert code == 200 and "<block>no</block>" in body, (code, body)
    assert SEEN and SEEN[0][0] == "Bearer login-abc", SEEN


def test_work_request_never_goes_to_plan():
    setmode()
    del SEEN[:]
    routed = []

    def fake_route(req):   # stands for the free providers: the test never touches the network
        routed.append(req.get("model"))
        return {"id": "m", "type": "message", "role": "assistant", "model": "free", "stop_reason": "end_turn", "stop_sequence": None,
                "content": [{"type": "text", "text": "from the free model"}], "usage": {"input_tokens": 1, "output_tokens": 1}}, "fake-free", None

    real = dr.route_patiently
    dr.route_patiently = fake_route
    try:
        code, body = post(WORK)
    finally:
        dr.route_patiently = real
    assert code == 200 and "from the free model" in body and routed, (code, body, routed)
    assert not SEEN, SEEN   # the plan was never asked for work


def test_no_credit_gets_local_fail_closed_verdict():
    setmode()
    dr._plan_pause(600, "limit")
    del SEEN[:]
    code, body = post(SAFETY)
    assert code == 200 and "<block>yes</block>" in body and "local-check" in body, (code, body)
    assert not SEEN, SEEN


def test_no_login_gets_local_verdict():
    setmode()
    del SEEN[:]
    code, body = post(SAFETY, token=dr.FREE_TOKEN)
    assert code == 200 and "<block>yes</block>" in body and not SEEN, (code, body, SEEN)


def test_samples_flag_off_writes_nothing_on_writes_one_line_secrets_cut():
    path = os.path.join(home, "safety-samples.jsonl")
    setmode()
    post(SAFETY, token=dr.FREE_TOKEN)
    assert not os.path.exists(path)
    setmode(safety_samples=True)
    secret = "sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd"
    post(dict(SAFETY, system="security monitor <transcript>User: x\nBash: echo %s</transcript>" % secret), token=dr.FREE_TOKEN)
    lines = [x for x in open(path, encoding="utf-8").read().split("\n") if x.strip()]
    assert len(lines) == 1 and secret not in lines[0] and "[cut]" in lines[0], lines
    for _ in range(6):
        post(SAFETY, token=dr.FREE_TOKEN)
    assert len([x for x in open(path, encoding="utf-8").read().split("\n") if x.strip()]) == 5


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
    print("\nPASS mixed_safe: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
