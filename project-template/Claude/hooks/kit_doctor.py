#!/usr/bin/env python3
"""kit_doctor.py - diagnose (and with --fix repair) the common kit problems of ONE project. Zero AI tokens.

Usage (from the project folder): python Claude/hooks/kit_doctor.py [--fix] [--project DIR]
Prints one line per check: OK / FIXED / PROBLEM, then a one-line summary. Never deletes anything.
Env UEFN_KIT_TEMPLATE and UEFN_HOME (profile dir, default ~/.claude) exist for tests.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_sync  # noqa: E402


def check(project, fix=False):
    out = []  # (status, text)
    add = lambda s, t: out.append((s, t))
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    tpl = kit_sync.template_dir()

    # 1. kit versions
    pv = kit_sync._read_version(project)
    tv = kit_sync._read_version(tpl) if os.path.isdir(tpl) else ""
    if not os.path.isdir(tpl):
        add("PROBLEM", "No kit copy in your profile (%s). Run update-my-profile.cmd from your kit folder." % tpl)
    elif not pv:
        add("PROBLEM", "This project has no kit version file. Run /kit-update.")
    elif kit_sync._newer(tv, pv):
        if fix:
            try:
                kit_sync.run(project)
                add("FIXED", "Project updated from kit %s to %s (reload the console page and open a new session)." % (pv, tv))
            except Exception as e:  # noqa: BLE001
                add("PROBLEM", "Update from %s to %s failed: %s" % (pv, tv, e))
        else:
            add("PROBLEM", "Project is on kit %s, your profile has %s. Run /kit-update (or /kit-doctor --fix)." % (pv, tv))
    elif kit_sync._newer(pv, tv):
        add("PROBLEM", "Project (%s) is newer than your profile kit (%s). Run update-my-profile.cmd from your kit folder." % (pv, tv))
    else:
        add("OK", "Kit version %s, same as your profile." % pv)

    # 2. managed files that differ or are missing (reported only; the update fixes them)
    if os.path.isdir(tpl):
        bad = []
        for rel, full in kit_sync._walk(tpl):
            if any(rel.startswith(m) or rel == m for m in kit_sync.MANAGED):
                mine = os.path.join(project, rel)
                if not os.path.isfile(mine) or kit_sync._norm_hash(mine) != kit_sync._norm_hash(full):
                    bad.append(rel)
        if bad and not (tv and pv and kit_sync._newer(tv, pv)):
            add("PROBLEM", "%d kit file(s) differ from your profile copy (e.g. %s). Run /kit-update." % (len(bad), bad[0]))
        elif not bad:
            add("OK", "Kit files match your profile copy.")

    # 3. .verse backups would break the UEFN build
    stray = []
    for base, _, files in os.walk(os.path.join(project, "Claude", "logs")):
        stray += [os.path.join(base, f) for f in files if f.endswith(".verse")]
    if stray:
        if fix:
            kit_sync.neutralize_backups(project)
            add("FIXED", "%d .verse backup copy(ies) renamed to .verse.bak (UEFN compiles every .verse)." % len(stray))
        else:
            add("PROBLEM", "%d .verse backup copy(ies) under Claude/logs would break the UEFN build. /kit-doctor --fix renames them." % len(stray))
    else:
        add("OK", "No compilable .verse copies in Claude/logs.")

    # 4. settings.json valid + reminder hook
    sp = os.path.join(project, ".claude", "settings.json")
    if not os.path.isfile(sp):
        add("PROBLEM", "No .claude/settings.json: hooks are not active. Run /kit-update.")
    else:
        try:
            json.load(open(sp, encoding="utf-8"))
            if fix:
                notes = kit_sync.repair_settings(project)
                add("FIXED" if notes else "OK", notes[0] if notes else "Hook settings are valid.")
            else:
                add("OK", "Hook settings are valid JSON.")
        except ValueError as e:
            add("PROBLEM", "settings.json is not valid JSON (%s). Hooks are off; restore it or run /kit-update." % e)

    # 5. second brain path
    cm = os.path.join(home, "CLAUDE.md")
    try:
        m = re.search(r"\*\*Second brain path\*\*:\s*`([^`]*)`", open(cm, encoding="utf-8").read())
    except OSError:
        m = None
    if not m:
        add("OK", "Second brain: not configured (feature off).")
    elif m.group(1).strip() == "<SECOND_BRAIN_PATH>":
        add("OK", "Second brain: off (placeholder). Set the path in ~/.claude/CLAUDE.md rule 11 to enable it.")
    elif os.path.isfile(os.path.join(m.group(1), "CLAUDE.md")) and os.path.isdir(os.path.join(m.group(1), "wiki")):
        add("OK", "Second brain vault found.")
    else:
        add("PROBLEM", "Second brain path %s is not a valid vault (needs CLAUDE.md and wiki/). Fix rule 11 in ~/.claude/CLAUDE.md." % m.group(1))

    # 6. docs format
    try:
        import docs_lint
        issues = docs_lint.lint(project)
        if issues:
            add("PROBLEM", "Docs format: %d issue(s), first: %s. Ask planner-docs to fix them." % (len(issues), issues[0]))
        else:
            add("OK", "Docs format is valid.")
    except Exception:  # noqa: BLE001
        add("OK", "Docs format check skipped.")

    # 7. secrets file kept out of git
    if os.path.isfile(os.path.join(project, ".mcp.json")) and os.path.isdir(os.path.join(project, ".git")):
        gi = os.path.join(project, ".gitignore")
        txt = open(gi, encoding="utf-8").read() if os.path.isfile(gi) else ""
        if ".mcp.json" not in txt:
            if fix:
                with open(gi, "a", encoding="utf-8", newline="\n") as f:
                    f.write(("\n" if txt and not txt.endswith("\n") else "") + ".mcp.json\n")
                add("FIXED", ".mcp.json added to .gitignore (it can hold a token).")
            else:
                add("PROBLEM", ".mcp.json may hold a token and is not in .gitignore. /kit-doctor --fix adds it.")
        else:
            add("OK", ".mcp.json is ignored by git.")
    return out


def main():
    fix = "--fix" in sys.argv
    project = os.getcwd()
    if "--project" in sys.argv:
        project = sys.argv[sys.argv.index("--project") + 1]
    res = check(project, fix)
    for s, t in res:
        print("%-7s %s" % (s, t))
    n = sum(1 for s, _ in res if s == "PROBLEM")
    f = sum(1 for s, _ in res if s == "FIXED")
    print("kit-doctor: %d problem(s), %d fixed." % (n, f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
