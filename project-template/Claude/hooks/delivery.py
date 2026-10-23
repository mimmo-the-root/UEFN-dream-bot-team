#!/usr/bin/env python3
"""Delivery document for a map (v1.109): what you hand to a client, a teammate or the jam judges.

Writes Claude/docs/DELIVERY.md. The part between <!-- auto:start --> and <!-- auto:end --> is rebuilt from the
project's own documents (finished tasks by release, open bugs, release verdict, Verse file count); everything you
write outside the markers is kept. Re-running is safe.

  python Claude/hooks/delivery.py [project dir]            # write the file
  python Claude/hooks/delivery.py [project dir] --print    # only print
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score

START, END = "<!-- auto:start -->", "<!-- auto:end -->"
FREE = """# Delivery

## What this is (fill in)

- Name and one-sentence pitch:
- Island code / where to find it:
- Genre and how long a round lasts:

## How to play (fill in)

- Controls and goal:
- Players: minimum and maximum:

## Credits and third-party content (fill in)

- Assets you did not make, with their source and licence:
- AI use: see `devlog.md`

"""


def build(project):
    ts = score.tasks(project)
    done = {}
    for t in ts:
        if t["done"]:
            done.setdefault(t["rel"], []).append(t)
    openb = score.bugs(project)
    val, txt = score.verdict(project)
    content = os.path.join(project, "Content") if os.path.isdir(os.path.join(project, "Content")) else project
    verse = 0
    for base, dirs, files in os.walk(content):
        dirs[:] = [d for d in dirs if d != "Claude"]
        verse += sum(1 for f in files if f.endswith(".verse"))
    out = [START, "## State", "",
           "- Tasks finished: %d of %d planned" % (sum(len(v) for v in done.values()), len(ts)),
           "- Open bugs: %d" % len(openb),
           "- Release verdict: %s" % (txt or "none written yet (RELEASE-READINESS.md)"),
           "- Verse files: %d" % verse, "", "## What is finished, by release", ""]
    if not done:
        out.append("(no finished task in ROADMAP.md yet)")
    for rel in sorted(done):
        out.append("### %s" % rel)
        out += ["- %s: %s" % (t["id"], t["title"]) for t in done[rel]]
        out.append("")
    out += ["## Known problems", ""]
    out += ["- %s" % b["title"] for b in openb] or ["- none open"]
    out += ["", END]
    return "\n".join(out) + "\n"


def write(project):
    p = os.path.join(project, "Claude", "docs", "DELIVERY.md")
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
