#!/usr/bin/env python3
"""Tests for tools/golden_nightly.py: fake local router on an ephemeral port, temp dirs only."""
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "golden_nightly.py"
sys.path.insert(0, str(ROOT / "tools"))
import golden_set  # noqa: E402
import golden_nightly  # noqa: E402

ANS = {
    "arith-add": "42", "arith-mul": "144", "arith-div": "18", "capital-it": "Rome.",
    "reverse": "esrev", "upper": "FORTNITE", "count-letters": "6", "sort-nums": "1, 3, 5, 9",
    "max-list": "19", "json-key": '{"ok": true}', "json-sum": '{"sum": 42}',
    "verse-func": "Add(A:int, B:int):int =", "verse-var": "var Score : int = 0",
    "verse-import": "using { /Fortnite.com/Devices }", "verse-log": "Print", "not-contains": "Red",
    "weekday": "Tuesday", "month-days": "28", "bool-logic": "False", "prefix-echo": "READY-7",
}
PACKAGES = golden_set.load_set()
BY_PROMPT = {p["prompt"]: p["id"] for p in PACKAGES}
IDS = [p["id"] for p in PACKAGES]


class Handler(BaseHTTPRequestHandler):
    drops = {}
    bad_models = set()
    count = 0

    def do_POST(self):
        size = int(self.headers.get("Content-Length") or 0)
        req = json.loads(self.rfile.read(size) or b"{}")
        prompt = req.get("messages", [{}])[-1].get("content", "")
        model = req.get("model", "")
        pid = BY_PROMPT.get(prompt, "")
        Handler.count += 1
        answer = ANS.get(pid, "I do not know")
        if model in Handler.bad_models or pid in Handler.drops.get(model, set()):
            answer = "I do not know"
        body = json.dumps({"content": [{"type": "text", "text": answer}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          timeout=180, encoding="utf-8", errors="replace")


def main():
    assert len(PACKAGES) == 20 and len(ANS) == 20
    assert golden_nightly.DEFAULT_URL == "http://127.0.0.1:8787/v1/messages"
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = "http://127.0.0.1:%d/v1/messages" % server.server_port
    try:
        Handler.bad_models = {"free/bad"}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            first, second = root / "run1.json", root / "run2.json"
            models = ["--model", "free/good", "--model", "free/bad",
                      "--model", "free/drop2", "--model", "free/drop3"]
            p = run("--url", url, *models, "--out", str(first))
            assert p.returncode == 0, p.stderr
            r1 = json.loads(first.read_text(encoding="utf-8"))
            assert r1["models"]["free/good"]["passed"] == 20, r1["models"]["free/good"]
            assert r1["models"]["free/bad"]["passed"] == 0
            assert r1["comparison"]["degradation"] == []
            assert r1["url"] == url and not r1["previous"]
            assert b"\r" not in first.read_bytes()

            Handler.drops = {"free/good": set(IDS[:4]), "free/drop2": set(IDS[:2]),
                             "free/drop3": set(IDS[:3])}
            before = Handler.count
            p = run("--url", url, *models, "--previous", str(first), "--out", str(second))
            assert p.returncode == 0, p.stderr
            assert Handler.count - before == 80, Handler.count - before
            r2 = json.loads(second.read_text(encoding="utf-8"))
            assert r2["models"]["free/good"]["passed"] == 16
            assert r2["models"]["free/drop2"]["passed"] == 18
            assert r2["models"]["free/drop3"]["passed"] == 17
            assert r2["comparison"]["deltas"]["free/drop2"] == 2
            assert [a["model"] for a in r2["comparison"]["degradation"]] == ["free/good", "free/drop3"]
            assert r2["comparison"]["degraded_models"] == ["free/good", "free/drop3"]
            assert r2["comparison"]["degradation"][0] == {"model": "free/good", "previous": 20,
                                                            "current": 16, "drop": 4}
            assert "DEGRADED free/good: 20 -> 16 (drop 4)" in p.stdout

            p = run("--url", url, *models, "--out", str(second))
            assert p.returncode == 0, p.stderr
            r3 = json.loads(second.read_text(encoding="utf-8"))
            assert r3["previous"] == str(second) and r3["comparison"]["degradation"] == []

            Handler.drops = {}
            script = root / "answer.py"
            script.write_text(
                "import json, os, sys, urllib.request\n"
                "url = sys.argv[1]\n"
                "assert url == os.environ['GOLDEN_ROUTER_URL']\n"
                "assert os.environ['GOLDEN_MODEL'] == 'free/cmd'\n"
                "prompt = sys.stdin.read()\n"
                "payload = json.dumps({'model': os.environ['GOLDEN_MODEL'], 'max_tokens': 16, "
                "'messages': [{'role': 'user', 'content': prompt}]}).encode('utf-8')\n"
                "req = urllib.request.Request(url, data=payload, "
                "headers={'Content-Type': 'application/json'})\n"
                "obj = json.loads(urllib.request.urlopen(req, timeout=10).read())\n"
                "sys.stdout.write(''.join(b['text'] for b in obj['content']))\n",
                encoding="utf-8")
            cmd = '"%s" "%s" "{url}"' % (sys.executable, script)
            p = run("--url", url, "--model", "free/cmd=" + cmd, "--out", str(root / "cmd.json"))
            assert p.returncode == 0, p.stderr
            rc = json.loads((root / "cmd.json").read_text(encoding="utf-8"))
            assert rc["models"]["free/cmd"]["passed"] == 20, rc["models"]["free/cmd"]

            p = run("--url", url, "--model", "claude-plan/opus", "--out", str(root / "paid.json"))
            assert p.returncode != 0 and "paid model rejected" in p.stderr, p.stderr
            assert not (root / "paid.json").exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("ok")


if __name__ == "__main__":
    main()
