#!/usr/bin/env python3
"""Tests for tools/retro.py: temp dirs, fake telemetry, no network."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = str(ROOT / "tools" / "retro.py")


def run(*args):
    r = subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True,
                       timeout=60, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def wj(p, d):
    Path(p).write_text(json.dumps(d), encoding="utf-8")


def setup(tmp, spread=True, single=10, paid=60, free=40, failures=0):
    tel, use = Path(tmp) / "tel", Path(tmp) / "use"
    tel.mkdir(); use.mkdir()
    wj(tel / "a.json", {"packages_tested": 20, "packages_with_single_model": single,
                        "spread_enabled": spread, "calls": 100, "failures": failures})
    (tel / "broken.json").write_text("{nope", encoding="utf-8")
    wj(use / "token-ledger.json", {"total": {"paid": paid, "free": free}})
    return tel, use


def test_propose_and_limits():
    with tempfile.TemporaryDirectory() as tmp:
        tel, use = setup(tmp, failures=50)
        cfg = Path(tmp) / "cfg.json"
        wj(cfg, {"router": {"max_retries": 2}})
        before = cfg.read_text()
        pipe = Path(tmp) / "pipe.json"
        rc, out, _ = run("propose", "--telemetry-dir", str(tel), "--usage-dir", str(use),
                         "--config", str(cfg), "--pipeline", str(pipe))
        assert rc == 0, out
        d = json.loads(pipe.read_text())
        assert 1 <= len(d["proposals"]) <= 3
        for p in d["proposals"]:
            for k in ("metric", "expected_effect", "rollback_value", "key", "value"):
                assert k in p, k
        retries = [p for p in d["proposals"] if p["key"] == "router.max_retries"][0]
        assert retries["rollback_value"] == 2
        assert cfg.read_text() == before
        assert b"\r" not in pipe.read_bytes()


def test_healthy_gives_none():
    with tempfile.TemporaryDirectory() as tmp:
        tel, use = setup(tmp, single=20, paid=1, free=99)
        pipe = Path(tmp) / "pipe.json"
        rc, _, _ = run("propose", "--telemetry-dir", str(tel), "--usage-dir", str(use),
                       "--pipeline", str(pipe))
        assert rc == 0 and json.loads(pipe.read_text())["proposals"] == []


def test_missing_dirs_ok():
    with tempfile.TemporaryDirectory() as tmp:
        pipe = Path(tmp) / "pipe.json"
        rc, _, _ = run("propose", "--telemetry-dir", str(Path(tmp) / "none"), "--pipeline", str(pipe))
        assert rc == 0 and json.loads(pipe.read_text())["proposals"] == []


def test_auto_rollback_when_worse():
    with tempfile.TemporaryDirectory() as tmp:
        tel, use = setup(tmp)
        pipe = Path(tmp) / "pipe.json"
        run("propose", "--telemetry-dir", str(tel), "--usage-dir", str(use), "--pipeline", str(pipe))
        wj(use / "token-ledger.json", {"total": {"paid": 90, "free": 10}})
        rc, _, _ = run("check", "--telemetry-dir", str(tel), "--usage-dir", str(use),
                       "--pipeline", str(pipe))
        assert rc == 0
        st = {p["metric"]: p["status"] for p in json.loads(pipe.read_text())["proposals"]}
        assert st["paid_share"] == "rolled_back"
        wj(use / "token-ledger.json", {"total": {"paid": 10, "free": 90}})
        run("propose", "--telemetry-dir", str(tel), "--usage-dir", str(use), "--pipeline", str(pipe))
        wj(use / "token-ledger.json", {"total": {"paid": 5, "free": 95}})
        run("check", "--telemetry-dir", str(tel), "--usage-dir", str(use), "--pipeline", str(pipe))
        assert all(p["status"] == "proposed" for p in json.loads(pipe.read_text())["proposals"])


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
