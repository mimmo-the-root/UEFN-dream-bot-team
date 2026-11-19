#!/usr/bin/env python3
"""Tests for tools/orchestrate.py on a temp LAB with a fake roadmap and fake packages."""
import os, subprocess, sys, tempfile, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "tools", "orchestrate.py")
HEAD = "| ID | Task | Status | Acceptance | Prio | Release | Kind | Source |\n|---|---|---|---|---|---|---|---|\n"


def row(n, status, rel="P0-R1", extra=""):
    return "| T-%03d | task %d %s | %s | acc | P1 | %s | feature | src |\n" % (n, n, extra, status, rel)


def make_lab(rows, later, inbox=(), running=(), done=()):
    lab = tempfile.mkdtemp()
    os.makedirs(os.path.join(lab, "docs"))
    with open(os.path.join(lab, "docs", "ROADMAP.md"), "w", newline="\n") as f:
        f.write(HEAD + "".join(rows))
    for sub, names in (("later", later), ("inbox", inbox), ("running", running), ("done", done)):
        os.makedirs(os.path.join(lab, "relay", sub))
        for n in names:
            name, after, owner = (n if isinstance(n, tuple) else (n, "", "no"))
            with open(os.path.join(lab, "relay", sub, name), "w", newline="\n") as f:
                f.write("id: x\nneeds_owner: %s\nafter: %s\n" % (owner, after))
    os.makedirs(os.path.join(lab, "plan"))
    return lab


def run(lab, *extra):
    return subprocess.run([sys.executable, SCRIPT, "--lab", lab, "--integrate-cmd", "", *extra],
                          capture_output=True, text=True, cwd=ROOT)


def ls(lab, sub):
    return sorted(os.listdir(os.path.join(lab, "relay", sub)))


def snap(lab):
    out = {}
    for d, _, fs in os.walk(lab):
        for f in fs:
            if f == "orchestrator.log":
                continue
            p = os.path.join(d, f)
            out[p] = open(p, "rb").read()
    return out


class T(unittest.TestCase):
    def test_refill_in_roadmap_order_and_limit(self):
        rows = [row(2, "To do"), row(1, "To do"), row(3, "To do"), row(4, "To do"), row(5, "To do", "P0-R2")]
        lab = make_lab(rows, ["100-t-001-a.md", "101-t-002-b.md", "102-t-003-c.md", "103-t-004-d.md", "104-t-005-e.md"])
        self.assertEqual(run(lab).returncode, 0)
        self.assertEqual(ls(lab, "inbox"), ["100-t-001-a.md", "101-t-002-b.md", "102-t-003-c.md"])
        # roadmap order: T-002 before T-001, so inbox is the first three rows: T-002, T-001, T-003
        self.assertEqual(ls(lab, "later"), ["103-t-004-d.md", "104-t-005-e.md"])

    def test_order_follows_roadmap_not_filename(self):
        rows = [row(9, "To do"), row(1, "To do")]
        lab = make_lab(rows, ["100-t-001-a.md", "101-t-009-b.md"], inbox=["050-t-050-x.md", "051-t-051-y.md"])
        run(lab)
        self.assertEqual(ls(lab, "inbox"), ["050-t-050-x.md", "051-t-051-y.md", "101-t-009-b.md"])

    def test_finished_moved_to_done(self):
        rows = [row(1, "Done"), row(2, "To do"), row(3, "To do")]
        lab = make_lab(rows, ["102-t-003-c.md"], inbox=["101-t-002-b.md"], running=["100-t-001-a.md"])
        run(lab)
        self.assertEqual(ls(lab, "done"), ["100-t-001-a.md"])
        self.assertEqual(ls(lab, "running"), [])
        self.assertEqual(ls(lab, "inbox"), ["101-t-002-b.md", "102-t-003-c.md"])

    def test_owner_and_frozen_never_moved(self):
        rows = [row(1, "To do", extra="[Owner]"), row(2, "To do"), row(3, "To do"), row(4, "To do"), row(5, "To do")]
        lab = make_lab(rows, ["100-t-001-a.md", ("101-t-002-b.md", "", "yes"), "102-t-003-FROZEN.md",
                              "103-t-004-LATER.md", "104-t-005-owner-stop.md"])
        run(lab)
        self.assertEqual(ls(lab, "inbox"), [])
        self.assertEqual(len(ls(lab, "later")), 5)

    def test_dependency_respected(self):
        rows = [row(1, "To do"), row(2, "To do")]
        lab = make_lab(rows, ["100-t-001-a.md", ("101-t-002-b.md", "100", "no")])
        run(lab)
        self.assertEqual(ls(lab, "inbox"), ["100-t-001-a.md"])
        self.assertEqual(ls(lab, "later"), ["101-t-002-b.md"])
        lab2 = make_lab(rows, [("101-t-002-b.md", "100", "no")], done=["100-t-001-a.md"])
        run(lab2)
        self.assertEqual(ls(lab2, "inbox"), ["101-t-002-b.md"])

    def test_active_release_in_progress_wins(self):
        rows = [row(1, "To do", "P0-R1"), row(2, "In progress", "P0-R2"), row(3, "To do", "P0-R2")]
        lab = make_lab(rows, ["100-t-001-a.md", "101-t-003-c.md"])
        run(lab)
        self.assertEqual(ls(lab, "inbox"), ["101-t-003-c.md"])

    def test_release_ready_line(self):
        rows = [row(1, "Done", "P0-R1"), row(2, "Done", "P0-R1"), row(3, "To do", "P0-R2")]
        lab = make_lab(rows, [])
        run(lab)
        for p in ("STATUS.md", "FEEDBACK-FROM-COD.md"):
            self.assertIn("RELEASE P0-R1 READY", open(os.path.join(lab, "plan", p)).read())
        run(lab)
        self.assertEqual(open(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md")).read().count("READY"), 1)

    def test_idempotent(self):
        rows = [row(1, "Done"), row(2, "To do"), row(3, "To do")]
        lab = make_lab(rows, ["102-t-003-c.md"], inbox=["101-t-002-b.md"], running=["100-t-001-a.md"])
        run(lab)
        before = snap(lab)
        log1 = open(os.path.join(lab, "logs", "orchestrator.log")).read().count("\n")
        self.assertEqual(run(lab).returncode, 0)
        self.assertEqual(snap(lab), before)
        self.assertEqual(open(os.path.join(lab, "logs", "orchestrator.log")).read().count("\n"), log1 + 1)

    def test_dry_run_changes_nothing(self):
        rows = [row(1, "To do")]
        lab = make_lab(rows, ["100-t-001-a.md"])
        before = snap(lab)
        r = run(lab, "--dry-run")
        self.assertEqual(r.returncode, 0)
        self.assertIn("would move", r.stdout)
        self.assertEqual(snap(lab), before)
        self.assertFalse(os.path.exists(os.path.join(lab, "logs")))

    def test_lock_and_bad_roadmap_exit_1(self):
        lab = make_lab([row(1, "To do")], ["100-t-001-a.md"])
        open(os.path.join(lab, "docs", "ROADMAP.md.lock"), "w").close()
        self.assertEqual(run(lab).returncode, 1)
        self.assertEqual(ls(lab, "later"), ["100-t-001-a.md"])
        lab2 = make_lab([], ["100-t-001-a.md"])
        with open(os.path.join(lab2, "docs", "ROADMAP.md"), "w") as f:
            f.write("| T-001 | broken |\n")
        self.assertEqual(run(lab2).returncode, 1)
        self.assertIn("unreadable", open(os.path.join(lab2, "logs", "orchestrator.log")).read())

    def test_integrate_result_logged(self):
        lab = make_lab([row(1, "To do")], [])
        fake = '"%s" -c "pass"' % sys.executable  # never the real integrator: it would run the whole suite
        r = subprocess.run([sys.executable, SCRIPT, "--lab", lab, "--integrate-cmd", fake], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0)
        self.assertIn("integrate: ok", r.stdout)


if __name__ == "__main__":
    unittest.main()
