#!/usr/bin/env python3
"""Tests for tools/kit_config.py: defaults, set and get, broken file, unknown keys kept."""
import json, os, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kit_config as kc  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def write(proj, text):
    p = kc.path(proj)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


# defaults: no file
with tempfile.TemporaryDirectory() as d:
    cfg, note = kc.load(d)
    check(cfg == kc.defaults() and note, "no file -> defaults and a note")
    check(kc.is_on("exchange_log", d) is True and kc.is_on("safety_samples", d) is False, "default flags")
    for s in ("routing", "budget", "agents", "console", "skills"):
        check(isinstance(cfg[s].get("description"), str), "section %s has a description" % s)
    check(kc.get("debug.nope", d, "x") == "x", "get default for a missing key")
    check(not os.path.exists(kc.path(d)), "reading never creates the file")

# shipped template file is valid and equals the defaults
shipped = json.load(open(os.path.join(ROOT, "project-template", kc.REL), encoding="utf-8"))
check(shipped == kc.defaults() and not kc.validate(shipped), "template file matches defaults")

# set and get, unknown keys kept, missing keys fall back
with tempfile.TemporaryDirectory() as d:
    write(d, json.dumps({"debug": {"exchange_log": False, "custom_flag": 7}, "mine": {"a": 1}}))
    check(kc.is_on("exchange_log", d) is False, "file value wins")
    check(kc.is_on("problems_log", d) is True, "missing key falls back to default")
    kc.set("debug.problems_log", False, d)
    saved = json.load(open(kc.path(d), encoding="utf-8"))
    check(saved["debug"]["custom_flag"] == 7 and saved["mine"] == {"a": 1}, "unknown keys kept after set")
    check(kc.get("debug.problems_log", d) is False and kc.get("debug.custom_flag", d) == 7, "set then get")
    check(kc.get("mine.a", d) == 1, "unknown section readable")

# set creates the file from defaults
with tempfile.TemporaryDirectory() as d:
    kc.set("debug.safety_samples", True, d)
    check(kc.is_on("safety_samples", d) and kc.is_on("exchange_log", d), "set on a new file")

# broken file
with tempfile.TemporaryDirectory() as d:
    p = write(d, "{not json")
    cfg, note = kc.load(d)
    check(cfg == kc.defaults() and "broken" in note, "broken file -> defaults and says so")
    check(open(p).read() == "{not json", "read does not touch a broken file")
    kc.set("debug.exchange_log", False, d)
    check(os.path.isfile(p + ".broken") and kc.is_on("exchange_log", d) is False, "set keeps a .broken copy")

# wrong types
with tempfile.TemporaryDirectory() as d:
    write(d, json.dumps({"debug": {"exchange_log": "yes"}}))
    cfg, note = kc.load(d)
    check(cfg["debug"]["exchange_log"] is True and note, "bad flag type -> default and a note")
    check(kc.validate({"debug": {"exchange_log": 1}}) and kc.validate([]), "validate reports problems")

# T-096: global versus project layers (temp dirs only)
with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as g:
    os.environ["KIT_GLOBAL_SETTINGS"] = os.path.join(g, "global.json")
    check(kc.source("debug.max_lines", d) == "default", "source: default")
    kc.set("debug.max_lines", 500, d, scope="global")
    kc.set("debug.exchange_log", "errors", d, scope="global")
    check(kc.get("debug.max_lines", d) == 500 and kc.source("debug.max_lines", d) == "global", "global value shows, source global")
    check(kc.level("exchange_log", d) == "errors", "global level used")
    kc.set("debug.max_lines", 100, d)
    check(kc.get("debug.max_lines", d) == 100 and kc.source("debug.max_lines", d) == "project", "project overrides global")
    check(kc.source("debug.exchange_log", d) == "global", "other key still global")
    check(kc.load(d)[1] == "", "no note when layers are fine")
    check(kc.reset("debug.max_lines", d) is True and kc.get("debug.max_lines", d) == 500, "reset project -> global value back")
    check(kc.reset("debug.max_lines", d, scope="global") is True and kc.get("debug.max_lines", d) == 2000
          and kc.source("debug.max_lines", d) == "default", "reset global -> default")
    check(kc.reset("debug.max_lines", d) is False, "reset of an absent key is a no-op")
    kc.set("debug.all_off", True, d)
    check(kc.level("exchange_log", d) == "off", "all_off in project still works with a global layer")
    with open(os.environ["KIT_GLOBAL_SETTINGS"], "w") as f:
        f.write("{broken")
    check(kc.get("debug.max_lines", d) == 2000, "broken global file is ignored")
    del os.environ["KIT_GLOBAL_SETTINGS"]

if fails:
    print("FAIL: " + "\n".join(fails))
    sys.exit(1)
print("kit_config tests OK")
