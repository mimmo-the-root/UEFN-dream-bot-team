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

# T-099: budget and agents settings
with tempfile.TemporaryDirectory() as d:
    b, a = kc.defaults()["budget"], kc.defaults()["agents"]
    check(b["weekly_used_pct"] is None and (b["warn_pct"], b["throttle_pct"], b["block_pct"]) == (70, 85, 95), "budget defaults")
    check(a["max_parallel"] == 3 and a["lab_permission_block"] is True and kc.tier_for("code", d) == "T2", "agents defaults")
    check(kc.tier_for("nope", d) == "T2" and kc.tier_for("plan", d) == "T3", "tier_for falls back to default")
    check(not kc.validate(kc.defaults()), "defaults valid")
    for bad in ({"agents": {"max_parallel": 0}}, {"agents": {"max_parallel": 7}}, {"agents": {"max_parallel": True}},
                {"agents": {"max_parallel": "3"}}, {"agents": {"tier_by_task_kind": {"code": "T9"}}},
                {"agents": {"lab_permission_block": "on"}}, {"budget": {"weekly_used_pct": 120}},
                {"budget": {"warn_pct": 90}}, {"budget": {"release_token_budget": -1}}):
        check(kc.validate(bad), "validate rejects %r" % (bad,))
    for ok in ({"agents": {"max_parallel": 1}}, {"agents": {"max_parallel": 6}}, {"budget": {"weekly_used_pct": 42.5}}):
        check(not kc.validate(ok), "validate accepts %r" % (ok,))
    write(d, json.dumps({"agents": {"max_parallel": 9, "lab_permission_block": False}, "budget": {"warn_pct": 50}}))
    cfg, note = kc.load(d)
    check(cfg["agents"]["max_parallel"] == 3 and cfg["agents"]["lab_permission_block"] is False and note, "bad max_parallel -> default, good key kept")
    check(cfg["budget"]["warn_pct"] == 50 and not kc.validate(cfg), "valid override kept")
    kc.reset("agents.max_parallel", d)
    kc.set("agents.max_parallel", 5, d)
    check(kc.get("agents.max_parallel", d) == 5 and kc.history(1, d)[0]["key"] == "agents.max_parallel", "set + history work")
    check(kc.undo("agents.max_parallel", d) and kc.get("agents.max_parallel", d) == 3, "undo works")
    check(kc.get("budget.weekly_used_pct", d, "x") is None and "weekly_used_pct" not in json.load(open(kc.path(d))).get("budget", {}),
          "weekly_used_pct never written by the kit")
    check(not kc.is_risky("agents.max_parallel") and not kc.is_risky("budget.warn_pct"), "budget/agents not risky")

# T-100: console and skills settings
with tempfile.TemporaryDirectory() as d:
    c, k = kc.defaults()["console"], kc.defaults()["skills"]
    check((c["language"], c["palette"], c["page_size"]) == ("en", "dark", 20), "console defaults")
    check(k["enabled"] == [] and k["learn_mode"] == "gated" and k["second_brain"] is False, "skills defaults")
    for bad in ({"console": {"language": "fr"}}, {"console": {"palette": "pink"}}, {"console": {"page_size": 4}},
                {"console": {"page_size": 201}}, {"console": {"page_size": True}}, {"skills": {"enabled": "a"}},
                {"skills": {"enabled": ["a", 3]}}, {"skills": {"enabled": [""]}}, {"skills": {"learn_mode": "always"}},
                {"skills": {"second_brain": "on"}}):
        check(kc.validate(bad), "validate rejects %r" % (bad,))
    for ok in ({"console": {"language": "it", "palette": "light", "page_size": 50}},
               {"skills": {"enabled": ["a", "b"], "learn_mode": "every-change", "second_brain": True}}):
        check(not kc.validate(ok), "validate accepts %r" % (ok,))
    write(d, json.dumps({"console": {"language": "it", "palette": "neon", "page_size": 9999},
                         "skills": {"enabled": ["x", "y"], "learn_mode": "nope", "second_brain": True}}))
    cfg, note = kc.load(d)
    check(cfg["console"]["language"] == "it" and cfg["console"]["palette"] == "dark" and cfg["console"]["page_size"] == 20
          and "console.palette" in note and "console.page_size" in note, "bad console values -> default with a note, good kept")
    check(cfg["skills"]["enabled"] == ["x", "y"] and cfg["skills"]["learn_mode"] == "gated" and cfg["skills"]["second_brain"] is True,
          "bad learn_mode -> default, good skills kept")
    kc.set("console.palette", "light", d)
    kc.set("skills.enabled", ["a"], d)
    check(kc.get("console.palette", d) == "light" and kc.get("skills.enabled", d) == ["a"] and kc.source("skills.enabled", d) == "project", "set/get/source")
    check(kc.undo("console.palette", d) and kc.get("console.palette", d) == "dark", "undo console.palette")
    check(kc.reset("skills.enabled", d) and kc.get("skills.enabled", d) == [], "reset skills.enabled")
    check(not kc.is_risky("skills.second_brain") and not kc.is_risky("console.language"), "console/skills not risky")

if fails:
    print("FAIL: " + "\n".join(fails))
    sys.exit(1)
print("kit_config tests OK")
