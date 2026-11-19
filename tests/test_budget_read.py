#!/usr/bin/env python3
"""Tests for tools/budget_read.py.

Covers: normal case, missing file, broken JSON (both files, one at a time).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_tool(project_dir):
    """Run budget_read.py against project_dir, return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(ROOT / "tools" / "budget_read.py"), str(project_dir)]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=60,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def make_project(tmp, name):
    """Create a fresh project dir with Claude/relay/outbox and return (project_dir, outbox)."""
    project = Path(tmp) / name
    outbox = project / "Claude" / "relay" / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    return project, outbox


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def write_raw(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def test_normal_case(tmp):
    """Normal: both LIMIT.json and budget.json are present and valid."""
    project, outbox = make_project(tmp, "normal")
    write_json(outbox / "LIMIT.json", {
        "state": "session-closed",
        "hit_at": 1795025122.856456,
        "hit_at_text": "2026-11-18 19:05:22",
        "resets_at": 1795026000.0,
        "resets_at_text": "2026-11-18 19:20:00",
        "kind": "limit",
        "session_id": "a93b2dc3-d2b6-4eea-99cf-0c34a292449b",
        "transcript_path": "some/path.jsonl",
        "claude_pid": 1896,
        "wakes": 0,
    })
    write_json(outbox / "budget.json", {"weekly_used_pct": 42.5})

    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"]["state"] == "session-closed"
    assert result["limit"]["resets_at_text"] == "2026-11-18 19:20:00"
    assert result["budget"]["weekly_used_pct"] == 42.5
    print("  PASS normal: both files read")


def test_missing_both(tmp):
    """Missing: neither file exists."""
    project, _ = make_project(tmp, "missing_both")
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    assert result["budget"] == {}
    print("  PASS missing: neither file present")


def test_missing_limit(tmp):
    """Missing: only budget.json exists."""
    project, outbox = make_project(tmp, "missing_limit")
    write_json(outbox / "budget.json", {"weekly_used_pct": 10.0})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    assert result["budget"]["weekly_used_pct"] == 10.0
    print("  PASS missing: only budget.json present")


def test_missing_budget(tmp):
    """Missing: only LIMIT.json exists."""
    project, outbox = make_project(tmp, "missing_budget")
    write_json(outbox / "LIMIT.json", {"state": "limit-hit"})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"]["state"] == "limit-hit"
    assert result["budget"] == {}
    print("  PASS missing: only LIMIT.json present")


def test_broken_limit(tmp):
    """Broken: LIMIT.json is not valid JSON."""
    project, outbox = make_project(tmp, "broken_limit")
    write_raw(outbox / "LIMIT.json", "{ not valid json")
    write_json(outbox / "budget.json", {"weekly_used_pct": 50.0})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    assert result["budget"]["weekly_used_pct"] == 50.0
    print("  PASS broken: LIMIT.json unparseable")


def test_broken_budget(tmp):
    """Broken: budget.json is not valid JSON."""
    project, outbox = make_project(tmp, "broken_budget")
    write_json(outbox / "LIMIT.json", {"state": "limit-hit"})
    write_raw(outbox / "budget.json", "{ not valid json either")
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"]["state"] == "limit-hit"
    assert result["budget"] == {}
    print("  PASS broken: budget.json unparseable")


def test_broken_both(tmp):
    """Broken: both files are not valid JSON."""
    project, outbox = make_project(tmp, "broken_both")
    write_raw(outbox / "LIMIT.json", "]]]")
    write_raw(outbox / "budget.json", "{{{")
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    assert result["budget"] == {}
    print("  PASS broken: both files unparseable")


def test_limit_without_state(tmp):
    """Broken shape: LIMIT.json has no 'state' key -> treated as unusable."""
    project, outbox = make_project(tmp, "no_state")
    write_json(outbox / "LIMIT.json", {"foo": "bar"})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    print("  PASS broken: LIMIT.json without state")


def test_budget_not_a_dict(tmp):
    """Broken shape: budget.json is a JSON array, not an object."""
    project, outbox = make_project(tmp, "not_dict")
    write_json(outbox / "budget.json", [1, 2, 3])
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["budget"] == {}
    print("  PASS broken: budget.json is not an object")


def test_budget_without_weekly_pct(tmp):
    """budget.json exists but has no weekly_used_pct -> key present, value None."""
    project, outbox = make_project(tmp, "no_pct")
    write_json(outbox / "budget.json", {"note": "owner has not set it yet"})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["budget"]["weekly_used_pct"] is None
    print("  PASS: budget.json without weekly_used_pct")


def test_no_outbox_folder(tmp):
    """Project dir has no Claude/relay/outbox at all -> still exits 0."""
    project = Path(tmp) / "no_outbox"
    project.mkdir(parents=True, exist_ok=True)
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    result = json.loads(out)
    assert result["limit"] == {}
    assert result["budget"] == {}
    print("  PASS: no outbox folder")


def test_no_secret_leak(tmp):
    """The reader must never echo a key or token that sits in the files."""
    project, outbox = make_project(tmp, "no_leak")
    write_json(outbox / "LIMIT.json", {"state": "limit-hit", "transcript_path": "C:/x/y.jsonl"})
    write_json(outbox / "budget.json", {"weekly_used_pct": 3.0})
    code, out, err = run_tool(project)
    assert code == 0, "expected exit 0, got %s: %s" % (code, err)
    low = out.lower()
    for forbidden in ("api_key", "apikey", "token", "secret", "password", "authorization", "bearer"):
        assert forbidden not in low, "reader leaked %r in its output" % forbidden
    print("  PASS: no key or token printed")


def main():
    tests = [
        test_normal_case,
        test_missing_both,
        test_missing_limit,
        test_missing_budget,
        test_broken_limit,
        test_broken_budget,
        test_broken_both,
        test_limit_without_state,
        test_budget_not_a_dict,
        test_budget_without_weekly_pct,
        test_no_outbox_folder,
        test_no_secret_leak,
    ]
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        for test in tests:
            try:
                test(tmp)
            except AssertionError as e:
                print("  FAIL %s: %s" % (test.__name__, e))
                failed.append(test.__name__)
            except Exception as e:
                print("  ERROR %s: %s" % (test.__name__, e))
                failed.append(test.__name__)
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS budget_read: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
