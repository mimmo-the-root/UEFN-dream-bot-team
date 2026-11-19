#!/usr/bin/env python3
"""GET/POST /router/mode of the Dream Router (T-060): read and set the mode, reject unknown modes, local origins only. No network."""
import json
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")
import dream_router as dr  # noqa: E402

dr.check_all = lambda: []
dr.PORT = 1
router = ThreadingHTTPServer(("127.0.0.1", 0), dr.Handler)
threading.Thread(target=router.serve_forever, daemon=True).start()
R = "http://127.0.0.1:%d" % router.server_port


def call(method, obj=None, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    rq = urllib.request.Request(R + "/router/mode", json.dumps(obj).encode() if obj is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


ACT = {"X-Router-Action": "1"}


def test_read():
    code, b = call("GET")
    assert code == 200 and b["mode"] in b["modes"] and "paid" in b["modes"], (code, b)


def test_set_and_read_back():
    for m in ("paid", "free", "auto"):
        code, b = call("POST", {"mode": m}, ACT)
        assert code == 200 and b["mode"] == m, (code, b)
        assert call("GET")[1]["mode"] == m
        assert json.load(open(os.path.join(home, "routing.json")))["mode"] == m


def test_reject_unknown_mode():
    call("POST", {"mode": "auto"}, ACT)
    code, b = call("POST", {"mode": "nonsense"}, ACT)
    assert code == 400 and call("GET")[1]["mode"] == "auto", (code, b)


def test_reject_non_local_origin_and_missing_header():
    code, _ = call("POST", {"mode": "paid"}, dict(ACT, Origin="https://evil.example"))
    assert code == 403, code
    code, _ = call("POST", {"mode": "paid"})
    assert code == 403, code
    assert call("GET")[1]["mode"] == "auto"


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
    print("\nPASS mode_endpoint: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
