#!/usr/bin/env python3
"""import_worker_fixes.py - takes into the kit the fixes the worker (Claude Code next to the editor) made to kit files in a project.

The worker learns the real behaviour of the editor first; the kit learns from the worker, not the other way round. When a kit file blocks a
command, the worker may fix it in its project (owner's standing permission, see Claude/relay/RELAY-README.md, "Kit fixes") and puts a copy of
every file it changed in  <project>/Claude/relay/fixes/files/<path inside the project>  with a note  fixes/NNN-name.md.

  python tool/import_worker_fixes.py PROJECT_CONTENT_DIR            lists what differs from the kit source and shows each diff (nothing is written)
  python tool/import_worker_fixes.py PROJECT_CONTENT_DIR --apply    copies the changed files into project-template/ (never settings.json: merge it by hand)

Mapping: Claude/<x> -> project-template/Claude/<x>; .claude/commands/<x> -> project-template/.claude/commands/<x>. Anything else is listed, not copied.
After --apply run the tests and read the note of each fix before you publish."""
import difflib, os, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def target(rel):
    rel = rel.replace("\\", "/")
    if rel == ".claude/settings.json":
        return None, "merge by hand (hook settings)"
    if rel.startswith("Claude/") or rel.startswith(".claude/commands/"):
        return os.path.join(ROOT, "project-template", *rel.split("/")), ""
    return None, "not a kit file"


def scan(project):
    base = os.path.join(project, "Claude", "relay", "fixes", "files")
    out = []
    if not os.path.isdir(base):
        return out
    for d, _, fs in os.walk(base):
        for f in sorted(fs):
            p = os.path.join(d, f)
            rel = os.path.relpath(p, base).replace("\\", "/")
            t, why = target(rel)
            new = open(p, encoding="utf-8", errors="replace").read()
            old = open(t, encoding="utf-8", errors="replace").read() if t and os.path.isfile(t) else None
            state = "skip: " + why if t is None else ("new file" if old is None else ("same" if old == new else "changed"))
            out.append({"rel": rel, "src": p, "dst": t, "state": state, "old": old, "new": new})
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        print(__doc__)
        return 2
    items = scan(a[0])
    if not items:
        print("No worker fixes in %s" % os.path.join(a[0], "Claude", "relay", "fixes", "files"))
        return 0
    for it in items:
        print("%-12s %s" % (it["state"].split(":")[0], it["rel"]) + ("  (%s)" % it["state"].split(": ", 1)[1] if it["state"].startswith("skip") else ""))
        if it["state"] == "changed":
            for l in list(difflib.unified_diff(it["old"].splitlines(), it["new"].splitlines(), "kit", "worker", lineterm="", n=1))[:60]:
                print("    " + l)
    if "--apply" in sys.argv:
        n = 0
        for it in items:
            if it["state"] in ("changed", "new file"):
                os.makedirs(os.path.dirname(it["dst"]), exist_ok=True)
                shutil.copyfile(it["src"], it["dst"])
                n += 1
        print("copied %d file(s) into project-template/. Run the tests and read the notes in %s" % (n, os.path.join(a[0], "Claude", "relay", "fixes")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
