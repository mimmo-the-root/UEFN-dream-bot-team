#!/usr/bin/env python3
"""Tests for tools/run_findings.py on temp copies with fake telemetry."""
import json
import subprocess
import sys
import tempfile
import calendar
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "run_findings.py"


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as d:
        tel, rt = Path(d) / "tel", Path(d) / "router"
        tel.mkdir(); rt.mkdir()
        t0 = calendar.timegm((2026, 11, 18, 10, 5, 0))
        hour = str(t0 // 3600)
        (rt / "usage-72h.json").write_text(json.dumps({"zen/qwen": {"provider": "zen", "model": "qwen", "hours": {hour: [10, 5, 3, 0]}}}))
        runs = [
            {"cmd": "1", "model": "general-purpose", "ts_start": "2026-11-18T10:05:00Z", "ts_end": "2026-11-18T10:20:00Z", "outcome": "done"},
            {"cmd": "2", "model": "opencode/big", "outcome": "busy"},
            {"cmd": "3", "model": "haiku", "outcome": "done"},
        ]
        (tel / "runs.jsonl").write_text("\n".join(json.dumps(r) for r in runs) + "\nnot json\n")
        ev = [{"event": "limit_busy", "ts": "2026-11-18T10:10:00Z", "count": 6, "agents_in_flight": 6, "max_parallel": 50}]
        (tel / "events.jsonl").write_text("\n".join(json.dumps(e) for e in ev) + "\n")
        out = Path(d) / "S.md"
        r = run("--telemetry", str(tel), "--router-home", str(rt), "--out", str(out))
        assert r.returncode == 0, r.stderr
        t = out.read_text()
        assert "zen/qwen" in t and "router-log" in t, t
        assert "opencode/big" in t
        assert "| haiku" not in t and "general-purpose |" not in t
        assert "Runs with outcome busy: 1" in t and "counted hits: 6" in t
        assert "Peak agents in flight: 6" in t
        assert "Skipped bad lines: 1" in t
        # missing files: no crash
        r = run("--telemetry", str(Path(d) / "none"), "--router-home", str(Path(d) / "none"))
        assert r.returncode == 0 and "0 runs" in r.stdout
    print("ok")


if __name__ == "__main__":
    main()
