#!/usr/bin/env python3
"""kit_config.py - read and write the kit settings file Claude/config/kit-settings.json.

API: defaults(), load(project), get(key, project, default), set(key, value, project), is_on(flag, project), validate(data).
Keys are dotted paths such as "debug.exchange_log"; is_on("exchange_log") means "debug.exchange_log".
Rules: unknown keys are kept, missing keys fall back to defaults, a broken file falls back to defaults and says so
(load returns the note; the file is never overwritten by a read). Stdlib only.
CLI: python tools/kit_config.py [get KEY | set KEY VALUE | validate] [--project DIR]
"""
import copy, json, os, sys

REL = os.path.join("Claude", "config", "kit-settings.json")
DEBUG_FLAGS = ["exchange_log", "problems_log", "pending_tests", "task_status_log", "router_error_log", "safety_samples"]
_DEFAULTS = {
    "debug": {
        "description": "Which debug files the agent writes (see docs/DEBUG-EXCHANGE.md). true = write, false = skip.",
        "exchange_log": True,
        "problems_log": True,
        "pending_tests": True,
        "task_status_log": True,
        "router_error_log": True,
        "safety_samples": False,
    },
    "routing": {"description": "Placeholder: model routing settings."},
    "budget": {"description": "Placeholder: token and cost budget settings."},
    "agents": {"description": "Placeholder: agent limits and behaviour."},
    "console": {"description": "Placeholder: Agent Console settings."},
    "skills": {"description": "Placeholder: skill loading settings."},
}


def defaults():
    return copy.deepcopy(_DEFAULTS)


def project_dir(project=None):
    return project or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def path(project=None):
    return os.path.join(project_dir(project), REL)


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
            if f in dbg and not isinstance(dbg[f], bool):
                out.append("debug.%s must be true or false" % f)
    return out


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
    if data is None:
        return defaults(), note
    cfg = _merge(_DEFAULTS, data)
    probs = validate(cfg)
    if probs:
        d = defaults()
        for f in DEBUG_FLAGS:
            if not isinstance(cfg.get("debug", {}).get(f), bool):
                cfg.setdefault("debug", {})[f] = d["debug"][f]
        for sec in _DEFAULTS:
            if not isinstance(cfg.get(sec), dict):
                cfg[sec] = d[sec]
        note = "settings problem(s), defaults used for them: " + "; ".join(probs)
    return cfg, note


def get(key, project=None, default=None):
    cur = load(project)[0]
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def is_on(flag, project=None):
    key = flag if "." in flag else "debug." + flag
    return get(key, project, False) is True


def set(key, value, project=None):  # noqa: A001  public API name asked by the package
    """Write one key, keeping every other key (unknown ones too). A broken file is saved as .broken first."""
    p = path(project)
    data, note = _read(project)
    if data is None:
        if os.path.isfile(p):
            os.replace(p, p + ".broken")
        data = defaults()
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
    cmd = argv[0] if argv else "validate"
    if cmd == "get" and len(argv) == 2:
        print(json.dumps(get(argv[1], project)))
    elif cmd == "set" and len(argv) == 3:
        set(argv[1], _parse(argv[2]), project)
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
