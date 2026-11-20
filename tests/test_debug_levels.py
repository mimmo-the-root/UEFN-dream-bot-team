#!/usr/bin/env python3
"""Tests for T-095 debug levels (off/errors/full), the all_off switch and old boolean flags. Temp dirs only."""
import json, os, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import debug_log as dl  # noqa: E402
import kit_config as kc  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def cfg(proj, debug):
    p = kc.path(proj)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"debug": debug}, f)


def rd(p):
    try:
        return open(p, encoding="utf-8").read()
    except OSError:
        return None


with tempfile.TemporaryDirectory() as d:
    log = os.path.join(d, "Claude", "plan", "PROBLEMS-FROM-COD.md")
    check(kc.level("problems_log", d) == "full", "default level full")
    cfg(d, {"problems_log": "off"})
    check(kc.level("problems_log", d) == "off" and not kc.is_on("problems_log", d), "off level")
    check(dl.debug_line("problems", "x", d) is False and rd(log) is None, "off writes nothing")
    cfg(d, {"problems_log": "errors"})
    check(kc.is_on("problems_log", d), "errors counts as on")
    check(dl.debug_line("problems", "info", d) is False and rd(log) is None, "errors skips non-error")
    check(dl.debug_line("problems", "boom", d, error=True) is True and rd(log) == "boom\n", "errors writes error")
    cfg(d, {"problems_log": "full"})
    check(dl.debug_line("problems", "info", d) is True, "full writes info")
    # old booleans
    cfg(d, {"problems_log": True})
    check(kc.level("problems_log", d) == "full", "true = full")
    cfg(d, {"problems_log": False})
    check(kc.level("problems_log", d) == "off", "false = off")
    # router_error is an error kind
    rp = os.path.join(d, "errors.log")
    cfg(d, {"router_error_log": "errors"})
    check(dl.debug_line("router_error", "e", d, path=rp) is True, "router_error writes at errors")
    # global switch
    cfg(d, {"problems_log": "full", "router_error_log": "full", "all_off": True})
    check(kc.level("problems_log", d) == "off", "all_off forces off")
    check(dl.debug_line("router_error", "e2", d, path=rp) is False, "all_off blocks writes")
    cfg(d, {"all_off": False})
    check(kc.level("problems_log", d) == "full", "all_off false = normal")
    # validation and fallback
    check(kc.validate({"debug": {"problems_log": "errors", "all_off": False}}) == [], "valid levels")
    check(len(kc.validate({"debug": {"problems_log": "loud"}})) == 1, "bad level reported")
    check(len(kc.validate({"debug": {"all_off": "yes"}})) == 1, "bad all_off reported")
    cfg(d, {"problems_log": "loud"})
    check(kc.level("problems_log", d) == "full", "bad level falls back to default")
    kc.set("debug.problems_log", "errors", d)
    check(kc.level("problems_log", d) == "errors", "set level via kit_config.set")

if fails:
    print("FAIL test_debug_levels:\n  " + "\n  ".join(fails))
    sys.exit(1)
print("test_debug_levels OK")
