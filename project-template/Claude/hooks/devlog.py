#!/usr/bin/env python3
"""Dev log for a jam entry (v1.108): what was built, day by day, from the kit's own logs.

Reads Claude/logs/verse-changes.jsonl and verse-errors.jsonl and writes the automatic part of
Claude/docs/devlog.md between the markers <!-- auto:start --> and <!-- auto:end -->. Anything you
(or Claude) write outside the markers is kept. Re-running is safe.

  python Claude/hooks/devlog.py [project dir]            # write the file
  python Claude/hooks/devlog.py [project dir] --print    # only print
"""
import json, os, sys, time

START, END = "<!-- auto:start -->", "<!-- auto:end -->"
FREE = """# Dev log

## How AI was used (fill in: this is the part judges read)

- What the human decided:
- What the agents did:
- What went wrong and how it was fixed:
- Where AI help was NOT used:

"""


def _rows(path):
    out = []
    if os.path.isfile(path):
        for l in open(path, encoding="utf-8", errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def build(project):
    logs = os.path.join(project, "Claude", "logs")
    ch = _rows(os.path.join(logs, "verse-changes.jsonl"))
    er = _rows(os.path.join(logs, "verse-errors.jsonl"))
    days = {}
    for r in ch:
        days.setdefault(str(r.get("ts", ""))[:10] or "unknown", {"c": [], "e": []})["c"].append(r)
    for r in er:
        days.setdefault(str(r.get("ts", ""))[:10] or "unknown", {"c": [], "e": []})["e"].append(r)
    files = sorted({r.get("file", "") for r in ch if r.get("file")})
    bad = sum(1 for r in ch if r.get("result") in ("errors", "reverted"))
    out = [START, "## Numbers", "",
           "- Changes logged: %d, in %d Verse file(s)" % (len(ch), len(files)),
           "- Builds that ended with errors: %d" % len(er),
           "- Changes that hit errors or were reverted: %d" % bad, "", "## Day by day", ""]
    if not days:
        out.append("(nothing logged yet: the coder writes one line per change with `verse_changes.py add`)")
    for d in sorted(days):
        out.append("### %s" % d)
        for r in days[d]["c"]:
            why = (" - " + r["reason"]) if r.get("reason") else ""
            out.append("- `%s`: %s%s [%s]" % (r.get("file", "?"), r.get("summary", ""), why, r.get("result", "ok")))
        if days[d]["e"]:
            out.append("- Build errors: %d build(s), codes: %s" % (len(days[d]["e"]), ", ".join(sorted({str(c) for r in days[d]["e"] for c in (r.get("sigs") or [])})[:8]) or "n/a"))
        out.append("")
    out.append(END)
    return "\n".join(out) + "\n"


def write(project):
    p = os.path.join(project, "Claude", "docs", "devlog.md")
    auto = build(project)
    old = open(p, encoding="utf-8").read() if os.path.isfile(p) else FREE
    if START in old and END in old:
        a, b = old.index(START), old.index(END) + len(END)
        new = old[:a] + auto.rstrip("\n") + old[b:]
    else:
        new = old.rstrip("\n") + "\n\n" + auto
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="\n").write(new)
    return p


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    proj = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--print" in sys.argv:
        print(build(proj))
    else:
        print("written: " + write(proj))
