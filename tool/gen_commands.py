#!/usr/bin/env python3
"""gen_commands.py - writes docs/manual/commands.md, the list of every custom command of the kit, from the command files themselves
(user-level-commands/ and project-template/.claude/commands/). The description of each command is the 'description' line of its file,
so the list can never drift from the commands. build_manual.py runs it first; run it alone with: python tool/gen_commands.py"""
import os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIRS = [os.path.join(ROOT, "user-level-commands"), os.path.join(ROOT, "project-template", ".claude", "commands")]
OUT = os.path.join(ROOT, "docs", "manual", "commands.md")
GROUPS = [
    ("From idea to game, in order", ["spec", "game-plan", "task-list", "consistency", "environment", "audit", "delivery"]),
    ("See the kit work", ["demo"]),
    ("Fab and jam", ["fab-check", "concept-card", "jam-check", "devlog", "text-scan", "ui-kit-check"]),
    ("Verse and the editor", ["verse-check", "verse-map", "editor-changes", "mcp-snapshot", "learn-map"]),
    ("Safety and continuity", ["restore-point", "handoff"]),
    ("The kit itself", ["kit-update", "kit-doctor"]),
]
WHEN = {"spec": "You have an idea, or none: start here.", "game-plan": "The spec is approved.", "task-list": "The plan is approved.",
        "consistency": "Before building: do spec, plan and tasks agree?", "environment": "Before building and before the playtest.",
        "audit": "A build is ready: check it against the rules, Fab and island compliance.", "delivery": "Before the private release.",
        "demo": "You want to watch the whole flow on a pilot game, in a new empty test project."}


def meta(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    f = {}
    for l in (m.group(1) if m else "").splitlines():
        if ":" in l:
            k, v = l.split(":", 1)
            f[k.strip()] = v.strip().strip('"').replace('\\"', '"')
    return f


def collect():
    out = {}
    for d in DIRS:
        if os.path.isdir(d):
            for n in sorted(os.listdir(d)):
                if n.endswith(".md"):
                    out[n[:-3]] = meta(os.path.join(d, n))
    return out


def build():
    c = collect()
    L = ["# All the commands", "",
         "Type a command in Claude Code's chat. A command never runs by itself: you type it, and every change still waits for your approval. "
         "This list is written from the command files, so it is always the real one.", ""]
    seen = set()
    for title, names in GROUPS:
        rows = [n for n in names if n in c]
        if not rows:
            continue
        L += ["## " + title, "", "| Command | What it does | When |", "|---|---|---|"]
        for n in rows:
            seen.add(n)
            h = c[n].get("argument-hint", "")
            L.append("| `/%s%s` | %s | %s |" % (n, (" " + h) if h else "", c[n].get("description", "").replace("|", "/"), WHEN.get(n, "")))
        L.append("")
    rest = [n for n in sorted(c) if n not in seen]
    if rest:
        L += ["## Other", "", "| Command | What it does |", "|---|---|"]
        L += ["| `/%s` | %s |" % (n, c[n].get("description", "").replace("|", "/")) for n in rest] + [""]
    L += ["## Two ways to see the flow work", "",
          "- `/demo`: the whole round on a pilot game (idea, spec, plan, tasks, environment, build, audit, delivery), asking you at each approval.",
          "- `/demo --auto`: the same round, no questions: the AI approves for you and writes it down. The Docs page shows the clock.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    open(OUT, "w", encoding="utf-8", newline="\n").write(build())
    print("wrote", OUT)
