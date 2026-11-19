#!/usr/bin/env python3
"""lab_permissions.py - temporary PRUDENT permission block for a Lab project (opt-in).

Usage: python tools/lab_permissions.py PROJECT_DIR [--remove]

Acts only when LAB-PROJECT.txt (project root or Claude/) has the line
'lab-permissions: prudent'. Otherwise it does nothing and says so.
The block only ADDS deny rules (git push, rm -rf, curl|sh, writes to keys.env and ~/.ssh);
it allows nothing new. Other keys of .claude/settings.json are kept. Writes go to a temp
file, then rename. The entries really added are remembered in .claude/lab_permissions.json
so --remove takes out exactly those. Stdlib only; touches nothing outside the project dir.
"""
import json, os, sys, tempfile

MARKER = "lab-permissions: prudent"
DENY = [
    "Bash(git push:*)",
    "Bash(rm -rf:*)",
    "Bash(curl * | sh:*)",
    "Bash(curl * | bash:*)",
    "Bash(wget * | sh:*)",
    "Bash(wget * | bash:*)",
    "Write(**/keys.env)",
    "Edit(**/keys.env)",
    "Write(~/.ssh/**)",
    "Edit(~/.ssh/**)",
]


def _paths(project_dir):
    root = os.path.realpath(project_dir)
    return root, os.path.join(root, ".claude", "settings.json"), os.path.join(root, ".claude", "lab_permissions.json")


def opted_in(project_dir):
    root = os.path.realpath(project_dir)
    for rel in ("LAB-PROJECT.txt", os.path.join("Claude", "LAB-PROJECT.txt")):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    if any(ln.strip().lower() == MARKER for ln in f):
                        return True
            except OSError:
                pass
    return False


def _inside(root, path):
    return os.path.realpath(path).startswith(root + os.sep)


def _load(path):
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("%s is not a JSON object" % path)
    return data


def _write(root, path, data):
    if not _inside(root, os.path.dirname(path)) and os.path.realpath(os.path.dirname(path)) != root:
        raise ValueError("refusing to write outside the project: " + path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _deny_list(settings):
    perms = settings.get("permissions")
    if not isinstance(perms, dict):
        return []
    d = perms.get("deny")
    return d if isinstance(d, list) else []


def check_missing(project_dir):
    """Return a warning string if LAB-PROJECT.txt says prudent but the block is missing, else ''."""
    try:
        if not opted_in(project_dir):
            return ""
        _root, sp, _st = _paths(project_dir)
        have = _deny_list(_load(sp))
        missing = [e for e in DENY if e not in have]
        if missing:
            return ("LAB-PROJECT.txt asks for 'lab-permissions: prudent' but %d deny rule(s) are missing in .claude/settings.json. "
                    "Run: python tools/lab_permissions.py %s" % (len(missing), project_dir))
    except (OSError, ValueError):
        return "lab-permissions: could not read .claude/settings.json (check that it is valid JSON)."
    return ""


def apply(project_dir):
    """Returns (changed, message)."""
    if not opted_in(project_dir):
        return False, "No 'lab-permissions: prudent' line in LAB-PROJECT.txt: nothing done."
    root, sp, st = _paths(project_dir)
    if not _inside(root, sp):
        return False, "settings.json resolves outside the project: nothing done."
    settings = _load(sp)
    perms = settings.get("permissions")
    if perms is None:
        perms = settings["permissions"] = {}
    if not isinstance(perms, dict):
        return False, "permissions is not an object: nothing done."
    deny = perms.get("deny")
    if deny is None:
        deny = perms["deny"] = []
    if not isinstance(deny, list):
        return False, "permissions.deny is not a list: nothing done."
    add = [e for e in DENY if e not in deny]
    if not add:
        return False, "Block already present: no change."
    deny.extend(add)
    _write(root, sp, settings)
    try:
        prev = _load(st).get("added", [])
    except (OSError, ValueError):
        prev = []
    _write(root, st, {"added": prev + [e for e in add if e not in prev]})
    return True, "Added %d deny rule(s) to .claude/settings.json." % len(add)


def remove(project_dir):
    root, sp, st = _paths(project_dir)
    if not os.path.isfile(st):
        return False, "No block recorded: nothing to remove."
    added = _load(st).get("added", [])
    settings = _load(sp)
    deny = _deny_list(settings)
    keep = [e for e in deny if e not in added]
    changed = len(keep) != len(deny)
    if changed:
        if keep:
            settings["permissions"]["deny"] = keep
        else:
            del settings["permissions"]["deny"]
            if not settings["permissions"]:
                del settings["permissions"]
        _write(root, sp, settings)
    os.remove(st)
    return changed, "Removed the lab block." if changed else "Block was already gone."


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or any(a.startswith("--") and a != "--remove" for a in argv):
        print(__doc__.strip().splitlines()[2])
        return 2
    try:
        _c, msg = remove(args[0]) if "--remove" in argv else apply(args[0])
    except (OSError, ValueError) as e:
        print("lab_permissions: " + str(e))
        return 1
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
