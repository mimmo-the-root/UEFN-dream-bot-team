#!/usr/bin/env python3
"""Tests for T-097: config-changes.log, history(), undo(key), risky keys need confirm."""
import os, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kit_config as kc  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as gdir:
    os.environ["KIT_GLOBAL_SETTINGS"] = os.path.join(gdir, "g.json")
    kc.set("debug.max_lines", 500, proj)
    kc.set("debug.max_lines", 700, proj)
    h = kc.history(5, proj)
    check(len(h) == 2 and h[-1]["old"] == 500 and h[-1]["new"] == 700 and h[-1]["scope"] == "project", "history entries")
    check(os.path.isfile(kc.log_path(proj)), "log file written")
    check(kc.undo("debug.max_lines", proj) is not None and kc.get("debug.max_lines", proj) == 500, "undo restores old value")
    # first change of a key that was unset: undo removes it
    kc.set("debug.exchange_log", "errors", proj)
    kc.reset("debug.exchange_log", proj)
    check(kc.get("debug.exchange_log", proj) is True, "reset still works")
    kc.undo("debug.exchange_log", proj)  # undoes the reset
    check(kc.level("exchange_log", proj) == "errors", "undo of a reset")
    kc.undo("debug.exchange_log", proj)
    kc.undo("debug.exchange_log", proj)
    check(kc.source("debug.exchange_log", proj) in ("project", "default"), "source still works")
    check(kc.undo("no.such", proj) is None, "undo without history")
    # global scope
    kc.set("debug.max_lines", 9, proj, scope="global")
    check(kc.history(1, proj)[0]["scope"] == "global", "global scope logged")
    # risky
    check(kc.is_risky("permissions.allow_bash") and kc.is_risky("safety_check") and not kc.is_risky("debug.max_lines"), "is_risky")
    try:
        kc.set("permissions.allow_bash", True, proj)
        check(False, "risky set must refuse")
    except PermissionError:
        pass
    check(kc.get("permissions.allow_bash", proj) is None, "refused set wrote nothing")
    kc.set("safety_check", False, proj, confirm=True)
    kc.set("safety_check", True, proj, confirm=True)
    try:
        kc.undo("safety_check", proj)
        check(False, "risky undo must refuse")
    except PermissionError:
        pass
    kc.undo("safety_check", proj, confirm=True)
    check(kc.get("safety_check", proj) is False, "risky undo with confirm")
    check(kc.main(["set", "safety_check", "true", "--project", proj]) == 3, "CLI refuses risky")
    check(kc.main(["set", "safety_check", "true", "--confirm", "--project", proj]) == 0 and kc.get("safety_check", proj) is True, "CLI --confirm")
    check(kc.main(["history", "3", "--project", proj]) == 0 and kc.main(["undo", "debug.max_lines", "--project", proj]) == 0, "CLI history/undo")
    # existing behaviours
    kc.set("debug.all_off", True, proj)
    check(kc.level("problems_log", proj) == "off", "all_off still works")

if fails:
    print("FAIL:\n" + "\n".join(fails))
    sys.exit(1)
print("test_kit_config_history OK")
