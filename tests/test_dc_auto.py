#!/usr/bin/env python3
"""Tests for tools/dc_auto.py (T-028): temp lab only, audit gate, undo, CRLF."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import dc_auto  # noqa: E402

TABLE = """# T-028 proposal

| Area | Source file | ID | Feature | Acceptance criteria | Priority | Release |
|---|---|---|---|---|---|---|
| a | plan/intake/freellmapi-0*, plan/intake/claude-code-router-09* | T-120 | [Later] Router resilience pack (depends on T-110) | Unit test with injected clock; suite green | P1 | P0-R12 |
| b | plan/intake/claude-code-router-09* | T-121 | [Later] Reply repair and retry pack | Fake-provider tests pass; suite green | P1 | P0-R12 |
| c | plan/intake/token-00* | T-122 | [Later] Retry-after clamp and trace | Each item has a test on fake data | P2 | P0-R13 |
| d | plan/intake/freellmapi-0* | T-123 | [Later] Ranking learning | Fake failures change ranking; suite green | P2 | P0-R13 |
| e | plan/intake/freellmapi-0* | T-124 | [Later] Stated waits and keys | Keys tests pass; suite green | P2 | P0-R13 |
| f | plan/intake/token-00* | T-125 | [Later] Hooks and meter | Each hook has a test; suite green | P2 | P0-R14 |
| g | plan/intake/freellmapi-0* | T-027 | [Owner][Later] Owner pays for the plan | Owner confirms payment | P1 | P0-R12 |
| h | plan/intake/token-00* | T-044 | [Owner][Later] Owner decision | Owner decides scope | P2 | P0-R12 |
| i | plan/intake/token-00* | T-046 | [Later] Publish the kit | Version published by owner | P1 | P0-R12 |
| j | plan/intake/token-00* | T-070 | [Later] Version bump | Bump the version | P1 | P0-R12 |
| k | plan/intake/token-00* | T-071 | [Later] Start the scheduler | Start scheduled task | P1 | P0-R12 |
| l | plan/intake/token-00* | T-117 | [Later] Start the cron | Git push after tests | P1 | P0-R12 |
| m | plan/intake/freellmapi-0* | T-127 | [Owner][Later] Windows logon | The owner runs it once | P2 | P0-R14 |
| n | plan/intake/freellmapi-0* | T-120 | [Later] Router resilience pack (depends on T-110) | Unit test with injected clock; suite green | P1 | P0-R12 |
| o | plan/intake/token-00* | T-001 | [Later] Seed already in roadmap | Already there | P1 | P0-R11 |
| p | plan/intake/token-00* | T-999 | [Later] Reply repair and retry pack | Duplicate feature under a new id | P2 | P0-R11 |
"""

HEAD = ["# Roadmap", "", "## Tasks", "",
        "| ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source |",
        "|---|---|---|---|---|---|---|---|",
        "| T-001 | [Existing] Seed | To do | seed | P1 | P0-R11 | feature | test |"]


def base_roadmap():
    rows = ["| T-%03d | [Existing] R12 filler | To do | filler | P2 | P0-R12 | feature | test |" % n
            for n in range(10, 18)]
    return "\n".join(HEAD + rows + [""])


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text, eol="\n"):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", eol))


def make_lab(root, lint_source=None):
    kb = os.path.join(root, "Claude")
    for d in ("plan", "plan/intake", "scratch", "docs", "hooks", "logs",
              "relay/inbox", "relay/running", "relay/done", "relay/later"):
        os.makedirs(os.path.join(kb, *d.split("/")), exist_ok=True)
    with open(os.path.join(kb, "plan", "analysis-rows.json"), "w", encoding="utf-8") as f:
        json.dump([{"metric": "router.mode", "value": "safe"}], f)
    write(os.path.join(kb, "scratch", "T-028-proposal.md"), TABLE)
    for name in ("freellmapi-01.md", "claude-code-router-09.md", "token-00.md"):
        write(os.path.join(kb, "plan", "intake", name), "# idea\n")
    write(os.path.join(kb, "docs", "ROADMAP.md"), base_roadmap(), "\r\n")
    lint = lint_source or os.path.join(ROOT, "project-template", "Claude", "hooks", "docs_lint.py")
    shutil.copyfile(lint, os.path.join(kb, "hooks", "docs_lint.py"))
    return kb


with tempfile.TemporaryDirectory() as root:
    kb = make_lab(root)
    roadmap = os.path.join(kb, "docs", "ROADMAP.md")
    queue = os.path.join(kb, "plan", "QUEUE.json")
    before = read(roadmap)
    rep = dc_auto.run(root, timestamp="20260101T000000Z")
    assert rep["status"] == "approved", rep
    assert rep["appended"] == ["T-120", "T-121", "T-122", "T-123", "T-124"], rep
    after = read(roadmap)
    assert after != before
    assert after.count("\r\n") == after.count("\n"), "CRLF lost"
    ids = [c[0] for c in dc_auto.task_rows(after)]
    assert ids.count("T-120") == 1, ids
    assert not set(ids) & {"T-027", "T-044", "T-046", "T-070", "T-071", "T-117", "T-127", "T-999", "T-125"}, ids
    assert ("T-120", "duplicate id") in rep["dropped"], rep["dropped"]
    assert ("T-001", "duplicate id") in rep["dropped"], rep["dropped"]
    assert ("T-999", "duplicate feature") in rep["dropped"], rep["dropped"]
    assert any("owner-only" in reason for _id, reason in rep["dropped"]), rep["dropped"]
    assert max(dc_auto.open_releases(after).values()) <= 8, dc_auto.open_releases(after)
    baks = [n for n in os.listdir(os.path.join(kb, "docs")) if n.startswith("ROADMAP.md.bak-DC-")]
    assert baks == ["ROADMAP.md.bak-DC-20260101T000000Z"], baks
    assert read(os.path.join(kb, "docs", baks[0])) == before
    log = read(os.path.join(kb, "plan", "DC-LOG.md"))
    assert "APPROVED" in log and "Undo:" in log and baks[0] in log, log
    assert "Release" in log and "cap 3" in log, log
    q = json.load(open(queue, encoding="utf-8"))
    assert q["max_parallel"] == 3 and "queue" in q and "excluded" in q and q["count"] > 0, q
    lint = subprocess.run([sys.executable, os.path.join(kb, "hooks", "docs_lint.py"), root],
                          capture_output=True, text=True)
    assert lint.returncode == 0 and "docs format OK" in lint.stdout, lint.stdout + lint.stderr

with tempfile.TemporaryDirectory() as root:
    kb = make_lab(root)
    roadmap = os.path.join(kb, "docs", "ROADMAP.md")
    before = read(roadmap)
    saved = dc_auto.audit_batch
    dc_auto.audit_batch = lambda candidates: {"approved": False, "reasons": ["fake audit rejection"]}
    try:
        rep = dc_auto.run(root, timestamp="20260101T010101Z")
    finally:
        dc_auto.audit_batch = saved
    assert rep["status"] == "rejected" and rep["approved"] is False, rep
    assert read(roadmap) == before, "rejected batch changed the roadmap"
    assert not [n for n in os.listdir(os.path.join(kb, "docs")) if n.startswith("ROADMAP.md.bak-DC-")]
    assert not os.path.exists(os.path.join(kb, "plan", "QUEUE.json"))
    log = read(os.path.join(kb, "plan", "DC-LOG.md"))
    assert "fake audit rejection" in log and "No files changed" in log, log

with tempfile.TemporaryDirectory() as root:
    stub = os.path.join(root, "bad_lint.py")
    write(stub, "def lint(project):\n    return ['fake lint problem']\n")
    kb = make_lab(root, lint_source=stub)
    roadmap = os.path.join(kb, "docs", "ROADMAP.md")
    before = read(roadmap)
    rep = dc_auto.run(root, timestamp="20260101T020202Z")
    assert rep["status"] == "rollback", rep
    assert read(roadmap) == before, "lint failure did not roll back"
    assert "docs_lint FAILED" in read(os.path.join(kb, "plan", "DC-LOG.md"))

print("ok test_dc_auto")
