#!/usr/bin/env python3
"""debug_log.py - one place that writes the kit's debug lines, only when the matching flag is on.

API: debug_line(kind, text, project=None, path=None) -> True if a line was written, False if the flag is off or the write failed.
kinds: "task_status"   (flag task_status_log,  Claude/logs/task-status.log)
       "router_error"  (flag router_error_log, needs path=, the router's errors.log)
       "problems"      (flag problems_log,     Claude/plan/PROBLEMS-FROM-COD.md)
       "pending_tests" (flag pending_tests,    Claude/plan/PENDING-TESTS.md)
Every flag defaults to on (kit_config.is_on), so nothing changes until the owner turns one off. Never raises. Stdlib only.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_config  # noqa: E402

KINDS = {
    "task_status": ("task_status_log", os.path.join("Claude", "logs", "task-status.log")),
    "router_error": ("router_error_log", None),
    "problems": ("problems_log", os.path.join("Claude", "plan", "PROBLEMS-FROM-COD.md")),
    "pending_tests": ("pending_tests", os.path.join("Claude", "plan", "PENDING-TESTS.md")),
}


def debug_line(kind, text, project=None, path=None):
    try:
        if kind not in KINDS:
            return False
        flag, rel = KINDS[kind]
        if not kit_config.is_on(flag, project):
            return False
        target = path or (os.path.join(kit_config.project_dir(project), rel) if rel else None)
        if not target:
            return False
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "a", encoding="utf-8", newline="\n") as f:
            f.write(text.rstrip("\n") + "\n")
        return True
    except Exception:
        return False
