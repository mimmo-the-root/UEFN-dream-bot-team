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


def test_real_shape_and_golden():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        tel = base / "plan" / "telemetry"
        tel.mkdir(parents=True)
        rt = base / "router"
        rt.mkdir()
        wj(tel / "t-023-pinning.json", {"packages_tested": 20, "packages_with_single_model": 16,
                                        "spread_enabled": True, "calls": 100, "failures": 20})
        wj(rt / "usage-72h.json", {
            "zen/qwen": {"provider": "zen", "model": "qwen", "hours": {"h1": [100, 50, 20, 4]}},
            "claude-plan/x": {"provider": "claude-plan", "model": "x", "hours": {"h1": [300, 100, 10, 0]}},
        })
        golden = base / "golden.json"
        wj(golden, {"total": 20, "models": {"free/good": {"passed": 20, "total": 20},
                                            "free/drop": {"passed": 16, "total": 20}},
                    "comparison": {"degradation": [{"model": "free/drop", "previous": 20,
                                                     "current": 16, "drop": 4}],
                                   "deltas": {"free/drop": 4}, "degraded_models": ["free/drop"]}})
        cfg = base / "cfg.json"
        wj(cfg, {"router": {"disabled_models": []}})
        cfg_before, golden_before = cfg.read_text(), golden.read_text()
        pipe = base / "pipe.json"
        rc, out, err = run("real", "--telemetry-dir", str(tel), "--usage-72h", str(rt / "usage-72h.json"),
                           "--golden", str(golden), "--config", str(cfg), "--pipeline", str(pipe))
        assert rc == 0, out + err
        d = json.loads(pipe.read_text(encoding="utf-8"))
        assert d["metrics"]["pinning_ratio"] == 0.8
        assert abs(d["metrics"]["failure_rate"] - 4 / 30) < 1e-9
        assert abs(d["metrics"]["paid_share"] - 400 / 550) < 1e-9
        assert abs(d["metrics"]["golden_pass_rate"] - 36 / 40) < 1e-9
        assert d["metrics"]["golden_degraded_count"] == 1
        assert d["golden"]["degraded"] == ["free/drop"]
        props = d["proposals"]
        assert 1 <= len(props) <= 3
        gp = [p for p in props if p["key"] == "router.disabled_models"][0]
        assert gp["value"] == ["free/drop"] and gp["rollback_value"] == []
        assert gp["baseline"] == 1 and gp["direction"] == "down" and gp["status"] == "proposed"
        assert cfg.read_text() == cfg_before and golden.read_text() == golden_before
        assert b"\r" not in pipe.read_bytes()

        wj(golden, {"total": 20, "models": {"free/good": {"passed": 20, "total": 20},
                                            "free/drop": {"passed": 16, "total": 20},
                                            "free/worse": {"passed": 17, "total": 20}},
                    "comparison": {"degradation": [{"model": "free/drop", "previous": 20,
                                                     "current": 16, "drop": 4},
                                                    {"model": "free/worse", "previous": 20,
                                                     "current": 17, "drop": 3}],
                                   "degraded_models": ["free/drop", "free/worse"]}})
        rc, out, err = run("check", "--telemetry-dir", str(tel), "--golden", str(golden),
                           "--pipeline", str(pipe))
        assert rc == 0, out + err
        st = {p["key"]: p["status"] for p in json.loads(pipe.read_text())["proposals"]}
        assert st["router.disabled_models"] == "rolled_back", st
        assert golden.read_text() != golden_before


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
