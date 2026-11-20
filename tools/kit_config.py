#!/usr/bin/env python3
"""kit_config.py - read and write the kit settings file Claude/config/kit-settings.json.

API: defaults(), load(project), get(key, project, default), set(key, value, project), is_on(flag, project), level(flag, project), validate(data).
Debug levels (T-095): each debug.<flag> is "off", "errors" (errors only) or "full". Old booleans still work: true = "full", false = "off".
Global switch: debug.all_off = true turns every debug function off whatever its own level (default false).
Keys are dotted paths such as "debug.exchange_log"; is_on("exchange_log") means "debug.exchange_log".
Rules: unknown keys are kept, missing keys fall back to defaults, a broken file falls back to defaults and says so
(load returns the note; the file is never overwritten by a read). Stdlib only.
Layers (T-096): defaults < global file < project file. The global file is ~/.dream-bot-team/kit-settings.json (override with env
KIT_GLOBAL_SETTINGS); a key in the project file wins over the same key in the global file. source(key) says "project", "global" or "default";
reset(key) removes the key from the project file (scope="global" for the global one) so the next layer shows through; set(..., scope="global") writes the global file.
History and safety (T-097): every set/reset/undo appends one JSON line (time, key, old, new, scope) to Claude/logs/config-changes.log;
history(n) lists the last n changes (newest last); undo(key) restores the previous value of that key. RISKY_KEYS (permissions, safety_check
and everything under them) make set/reset/undo raise PermissionError unless confirm=True (CLI --confirm).
CLI: python tools/kit_config.py [get KEY | set KEY VALUE [--global] [--confirm] | source KEY | reset KEY [--global] [--confirm] | history [N] | undo KEY [--confirm] | validate] [--project DIR]
"""
import copy, json, os, sys, time

REL = os.path.join("Claude", "config", "kit-settings.json")
LOG_REL = os.path.join("Claude", "logs", "config-changes.log")
RISKY_KEYS = ("permissions", "safety_check")
LEVELS = ("off", "errors", "full")
TIERS = ("T0", "T1", "T2", "T3")
BUDGET_PCT_KEYS = ("warn_pct", "throttle_pct", "block_pct")
DEBUG_FLAGS = ["exchange_log", "problems_log", "pending_tests", "task_status_log", "router_error_log", "safety_samples"]
_DEFAULTS = {
    "debug": {
        "description": "Which debug files the agent writes (see docs/DEBUG-EXCHANGE.md). Each flag: off | errors | full (true = full, false = skip). all_off = true silences all.",
        "exchange_log": True,
        "problems_log": True,
        "pending_tests": True,
        "task_status_log": True,
        "router_error_log": True,
        "safety_samples": False,
        "all_off": False,
        "max_lines": 2000,
    },
    "routing": {"description": "Placeholder: model routing settings."},
    "budget": {
        "description": "Token budget. weekly_used_pct is OWNER-ONLY data (null = unknown): the kit never writes it. The three *_pct thresholds say at which weekly_used_pct the governor warns, throttles (free tiers only) and blocks paid work. release_token_budget = tokens one release may spend (0 = no limit).",
        "weekly_used_pct": None,
        "warn_pct": 70,
        "throttle_pct": 85,
        "block_pct": 95,
        "release_token_budget": 0,
    },
    "agents": {
        "description": "Agent limits. max_parallel = agents the relay planner runs at once (1-6, default 3). tier_by_task_kind = model tier per kind of task (T0 free local, T1 free cloud, T2 cheap paid, T3 strong paid). lab_permission_block = true keeps the Lab permission block (T-085) on.",
        "max_parallel": 3,
        "tier_by_task_kind": {"default": "T2", "plan": "T3", "code": "T2", "test": "T1", "docs": "T1", "review": "T2", "research": "T1"},
        "lab_permission_block": True,
    },
    "console": {"description": "Placeholder: Agent Console settings."},
    "skills": {"description": "Placeholder: skill loading settings."},
}


def defaults():
    return copy.deepcopy(_DEFAULTS)


def project_dir(project=None):
    return project or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def path(project=None):
    return os.path.join(project_dir(project), REL)


def global_path():
    return os.environ.get("KIT_GLOBAL_SETTINGS") or os.path.join(os.path.expanduser("~"), ".dream-bot-team", "kit-settings.json")


def _scope_path(project, scope):
    if scope not in ("project", "global"):
        raise ValueError("scope must be 'project' or 'global'")
    return global_path() if scope == "global" else path(project)


def _read_global():
    """Global file data or None (missing or broken: ignored, never an error)."""
    try:
        with open(global_path(), encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _merge(base, over):
    """Defaults under file values; keys only in the file are kept."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def validate(data):
    """Returns a list of problem strings (empty = fine)."""
    if not isinstance(data, dict):
        return ["the settings file must hold a JSON object"]
    out = []
    for sec, dflt in _DEFAULTS.items():
        if sec in data and not isinstance(data[sec], dict):
            out.append("section '%s' must be an object" % sec)
    dbg = data.get("debug")
    if isinstance(dbg, dict):
        for f in DEBUG_FLAGS:
            if f in dbg and _norm_level(dbg[f]) is None:
                out.append("debug.%s must be true, false, \"off\", \"errors\" or \"full\"" % f)
        if "all_off" in dbg and not isinstance(dbg["all_off"], bool):
            out.append("debug.all_off must be true or false")
        ml = dbg.get("max_lines")
        if "max_lines" in dbg and (isinstance(ml, bool) or not isinstance(ml, int) or ml < 1):
            out.append("debug.max_lines must be a whole number of 1 or more")
    out += _validate_budget_agents(data)
    return out


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _bad_keys(data):
    """Dict {dotted key: problem} for the budget and agents settings that are present but invalid."""
    bad = {}
    b = data.get("budget")
    if isinstance(b, dict):
        if "weekly_used_pct" in b and b["weekly_used_pct"] is not None and not (_is_num(b["weekly_used_pct"]) and 0 <= b["weekly_used_pct"] <= 100):
            bad["budget.weekly_used_pct"] = "budget.weekly_used_pct must be null or a number from 0 to 100"
        for k in BUDGET_PCT_KEYS:
            if k in b and not (_is_num(b[k]) and 0 <= b[k] <= 100):
                bad["budget." + k] = "budget.%s must be a number from 0 to 100" % k
        t = [b.get(k, _DEFAULTS["budget"][k]) for k in BUDGET_PCT_KEYS]
        if all(_is_num(x) for x in t) and not (t[0] <= t[1] <= t[2]) and not any(("budget." + k) in bad for k in BUDGET_PCT_KEYS):
            for k in BUDGET_PCT_KEYS:
                if k in b:
                    bad["budget." + k] = "budget thresholds must satisfy warn_pct <= throttle_pct <= block_pct"
        r = b.get("release_token_budget")
        if "release_token_budget" in b and (not _is_int(r) or r < 0):
            bad["budget.release_token_budget"] = "budget.release_token_budget must be a whole number of 0 or more (0 = no limit)"
    a = data.get("agents")
    if isinstance(a, dict):
        m = a.get("max_parallel")
        if "max_parallel" in a and (not _is_int(m) or not 1 <= m <= 6):
            bad["agents.max_parallel"] = "agents.max_parallel must be a whole number from 1 to 6"
        if "tier_by_task_kind" in a:
            t = a["tier_by_task_kind"]
            if not isinstance(t, dict) or any(not isinstance(k, str) or v not in TIERS for k, v in t.items()):
                bad["agents.tier_by_task_kind"] = "agents.tier_by_task_kind must map task kinds to T0, T1, T2 or T3"
        if "lab_permission_block" in a and not isinstance(a["lab_permission_block"], bool):
            bad["agents.lab_permission_block"] = "agents.lab_permission_block must be true or false"
    return bad


def _validate_budget_agents(data):
    return list(_bad_keys(data).values())


def tier_for(kind, project=None):
    """Tier for a task kind from agents.tier_by_task_kind (falls back to its 'default', then 'T2')."""
    t = get("agents.tier_by_task_kind", project, {})
    t = t if isinstance(t, dict) else {}
    return t.get(kind) or t.get("default") or "T2"


def _read(project):
    """Returns (file_data or None, note). note is '' when fine."""
    p = path(project)
    if not os.path.isfile(p):
        return None, "no settings file, using defaults"
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError) as e:
        return None, "settings file is broken (%s), using defaults" % e
    if not isinstance(data, dict):
        return None, "settings file is not a JSON object, using defaults"
    return data, ""


def load(project=None):
    """Returns (settings, note). Bad values (wrong type for a known flag) fall back to the default for that key."""
    data, note = _read(project)
    g = _read_global()
    if data is None and g is None:
        return defaults(), note
    if data is None and not note.startswith("settings file"):
        note = ""  # no project file but a global one: nothing to complain about
    cfg = _merge(_merge(_DEFAULTS, g or {}), data or {})
    probs = validate(cfg)
    if probs:
        d = defaults()
        for f in DEBUG_FLAGS:
            if _norm_level(cfg.get("debug", {}).get(f)) is None:
                cfg.setdefault("debug", {})[f] = d["debug"][f]
        for sec in _DEFAULTS:
            if not isinstance(cfg.get(sec), dict):
                cfg[sec] = d[sec]
        if not isinstance(cfg.get("debug", {}).get("all_off"), bool):
            cfg.setdefault("debug", {})["all_off"] = False
        ml = cfg.get("debug", {}).get("max_lines")
        if isinstance(ml, bool) or not isinstance(ml, int) or ml < 1:
            cfg.setdefault("debug", {})["max_lines"] = d["debug"]["max_lines"]
        for k in _bad_keys(cfg):
            sec, name = k.split(".")
            cfg[sec][name] = d[sec][name]
        note = "settings problem(s), defaults used for them: " + "; ".join(probs)
    return cfg, note


_MISSING = object()


def _has(data, key):
    cur = data
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


def source(key, project=None):
    """Where the value of a dotted key comes from: 'project', 'global' or 'default'."""
    if _has(_read(project)[0], key):
        return "project"
    if _has(_read_global(), key):
        return "global"
    return "default"


def get(key, project=None, default=None):
    cur = load(project)[0]
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def is_on(flag, project=None):
    """True when the flag writes anything (level errors or full). Non-debug keys keep the plain true/false meaning."""
    key = flag if "." in flag else "debug." + flag
    if key.startswith("debug.") and key[6:] in DEBUG_FLAGS:
        return level(key[6:], project) != "off"
    return get(key, project, False) is True


def _norm_level(v):
    """bool or level string -> 'off'/'errors'/'full', or None when not a valid value."""
    if v is True:
        return "full"
    if v is False:
        return "off"
    if isinstance(v, str) and v.strip().lower() in LEVELS:
        return v.strip().lower()
    return None


def level(flag, project=None):
    """Effective level of one debug function: 'off', 'errors' or 'full'. debug.all_off forces 'off'."""
    flag = flag[6:] if flag.startswith("debug.") else flag
    if get("debug.all_off", project, False) is True:
        return "off"
    lv = _norm_level(get("debug." + flag, project))
    if lv is None:
        lv = _norm_level(_DEFAULTS["debug"].get(flag, False)) or "off"
    return lv


def _set_raw(key, value, project=None, scope="project"):
    """Write one key, keeping every other key (unknown ones too). A broken file is saved as .broken first."""
    p = _scope_path(project, scope)
    if scope == "global":
        data = _read_global()
    else:
        data, note = _read(project)
    if data is None:
        if os.path.isfile(p):
            os.replace(p, p + ".broken")
        data = {} if (scope == "global" or _read_global() is not None) else defaults()
    parts = key.split(".")
    cur = data
    for part in parts[:-1]:
        if not isinstance(cur.get(part), dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)
    return data


def _reset_raw(key, project=None, scope="project"):
    """Reset to default: remove the key from the project file (or the global one), so the next layer shows through.
    Returns True when something was removed. A missing or broken file is left alone."""
    p = _scope_path(project, scope)
    data = _read_global() if scope == "global" else _read(project)[0]
    if data is None:
        return False
    parts = key.split(".")
    chain = [data]
    for part in parts[:-1]:
        nxt = chain[-1].get(part)
        if not isinstance(nxt, dict):
            return False
        chain.append(nxt)
    if parts[-1] not in chain[-1]:
        return False
    del chain[-1][parts[-1]]
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)
    return True


def log_path(project=None):
    return os.path.join(project_dir(project), LOG_REL)


def is_risky(key):
    return any(key == r or key.startswith(r + ".") or key.endswith("." + r) or ("." + r + ".") in key for r in RISKY_KEYS)


def _check_confirm(key, confirm):
    if is_risky(key) and confirm is not True:
        raise PermissionError("'%s' is a risky setting (permissions / safety check): pass confirm=True (CLI --confirm) to change it" % key)


def _value_of(key, project, scope):
    """(is_set, value) of a key inside one scope's file."""
    data = _read_global() if scope == "global" else _read(project)[0]
    cur = data
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, None
        cur = cur[part]
    return True, copy.deepcopy(cur)


def _log(key, old, new, scope, project):
    """Append one change line; logging must never break a settings write."""
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "key": key, "scope": scope,
             "old": old[1] if old[0] else None, "old_set": old[0],
             "new": new[1] if new[0] else None, "new_set": new[0]}
    try:
        lp = log_path(project)
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        with open(lp, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def set(key, value, project=None, scope="project", confirm=False):  # noqa: A001  public API name asked by the package
    """Write one key and log the change. Risky keys need confirm=True (PermissionError otherwise)."""
    _check_confirm(key, confirm)
    old = _value_of(key, project, scope)
    data = _set_raw(key, value, project, scope)
    _log(key, old, (True, value), scope, project)
    return data


def reset(key, project=None, scope="project", confirm=False):
    """Reset to default (see _reset_raw) and log it. Risky keys need confirm=True."""
    _check_confirm(key, confirm)
    old = _value_of(key, project, scope)
    done = _reset_raw(key, project, scope)
    if done:
        _log(key, old, (False, None), scope, project)
    return done


def history(n=20, project=None):
    """The last n logged changes as dicts, oldest first. Broken lines are skipped."""
    out = []
    try:
        with open(log_path(project), encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if isinstance(e, dict) and "key" in e:
                    out.append(e)
    except OSError:
        return []
    return out[-n:] if n > 0 else []


def undo(key, project=None, confirm=False):
    """Restore the value the key had before its last logged change (removes the key when it was not set then).
    Returns the entry that was undone, or None when the key has no history. The undo is logged too."""
    _check_confirm(key, confirm)
    last = None
    for e in history(10 ** 9, project):
        if e.get("key") == key:
            last = e
    if last is None:
        return None
    scope = last.get("scope", "project")
    old = _value_of(key, project, scope)
    if last.get("old_set"):
        _set_raw(key, last.get("old"), project, scope)
        _log(key, old, (True, last.get("old")), scope, project)
    else:
        _reset_raw(key, project, scope)
        _log(key, old, (False, None), scope, project)
    return last


def _parse(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def main(argv):
    project = None
    if "--project" in argv:
        i = argv.index("--project")
        project = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    scope = "project"
    if "--global" in argv:
        argv = [a for a in argv if a != "--global"]
        scope = "global"
    confirm = "--confirm" in argv
    argv = [a for a in argv if a != "--confirm"]
    cmd = argv[0] if argv else "validate"
    try:
        return _run(cmd, argv, project, scope, confirm)
    except PermissionError as e:
        print(str(e))
        return 3


def _run(cmd, argv, project, scope, confirm):
    if cmd == "get" and len(argv) == 2:
        print(json.dumps(get(argv[1], project)))
    elif cmd == "set" and len(argv) == 3:
        set(argv[1], _parse(argv[2]), project, scope, confirm)
    elif cmd == "source" and len(argv) == 2:
        print(source(argv[1], project))
    elif cmd == "reset" and len(argv) == 2:
        print("reset" if reset(argv[1], project, scope, confirm) else "nothing to reset")
    elif cmd == "history" and len(argv) <= 2:
        for e in history(int(argv[1]) if len(argv) == 2 else 20, project):
            print(json.dumps(e, ensure_ascii=False))
    elif cmd == "undo" and len(argv) == 2:
        print("undone" if undo(argv[1], project, confirm) else "nothing to undo")
    elif cmd == "validate":
        cfg, note = load(project)
        print(note or "settings OK")
        return 1 if note and "broken" in note else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
