#!/usr/bin/env python3
"""Tests for tools/debug_log.py and the task_status.py log flag: on writes, off does not, default on."""
import json, os, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import debug_log as dl  # noqa: E402
import kit_config as kc  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def setflag(proj, flag, val):
    p = kc.path(proj)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"debug": {flag: val}}, f)


def rd(p):
    try:
        return open(p, encoding="utf-8").read()
    except OSError:
        return None


KIND_FLAG = {"task_status": "task_status_log", "problems": "problems_log", "pending_tests": "pending_tests"}
for kind, flag in KIND_FLAG.items():
    with tempfile.TemporaryDirectory() as d:
        rel = dl.KINDS[kind][1]
        f = os.path.join(d, rel)
        check(dl.debug_line(kind, "a", d) is True and rd(f) == "a\n", kind + ": default (no file) writes")
        setflag(d, flag, True)
        dl.debug_line(kind, "b", d)
        check(rd(f) == "a\nb\n", kind + ": flag on appends")
        setflag(d, flag, False)
        check(dl.debug_line(kind, "c", d) is False and rd(f) == "a\nb\n", kind + ": flag off writes nothing")

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "x", "errors.log")
    check(dl.debug_line("router_error", "e1", d, path=p) and rd(p) == "e1\n", "router_error default on writes")
    setflag(d, "router_error_log", False)
    check(not dl.debug_line("router_error", "e2", d, path=p) and rd(p) == "e1\n", "router_error off skips")
    check(dl.debug_line("router_error", "e3", d) is False, "router_error without path does nothing")
    check(dl.debug_line("nope", "x", d) is False, "unknown kind does nothing")

# task_status.py: copy the script into a temp project so the real repo is untouched
src = os.path.join(ROOT, "project-template", "Claude", "hooks", "task_status.py")
for val, expect in ((None, True), (True, True), (False, False)):
    with tempfile.TemporaryDirectory() as d:
        hooks = os.path.join(d, "Claude", "hooks")
        os.makedirs(hooks)
        os.makedirs(os.path.join(d, "Claude", "docs"))
        with open(src, encoding="utf-8") as a, open(os.path.join(hooks, "task_status.py"), "w", encoding="utf-8", newline="\n") as b:
            b.write(a.read())
        with open(os.path.join(d, "Claude", "docs", "ROADMAP.md"), "w", encoding="utf-8") as f:
            f.write("| ID | Task | Status |\n|---|---|---|\n| T-001 | x | To do |\n")
        if val is not None:
            setflag(d, "task_status_log", val)
        subprocess.run([sys.executable, os.path.join(hooks, "task_status.py"), "T-001", "Blocked", "n"], capture_output=True, text=True, cwd=d)
        log = rd(os.path.join(d, "Claude", "logs", "task-status.log"))
        check((log is not None and "T-001" in log) == expect, "task_status.py log flag=%s expected written=%s got %r" % (val, expect, log))

if fails:
    print("FAIL:\n" + "\n".join(fails))
    sys.exit(1)
print("OK: test_debug_flags")
