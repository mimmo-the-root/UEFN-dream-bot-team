#!/usr/bin/env python3
"""token_budget.py - keep the text the kit loads into every session from growing unnoticed.

Measures (characters; ~4 chars = 1 token): project CLAUDE.md template, user-level CLAUDE.md,
all agent files, all skill entry points (SKILL.md). Compares with tests/token-budget.json.
Fails when a group is more than 10% above its baseline. After a deliberate, justified growth run:
    python tool/token_budget.py --update      (and say why in the CHANGELOG)
"""
import glob, json, os, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = os.path.join(root, "tests", "token-budget.json")
TOL = 1.10

def size(pattern):
    return sum(len(open(f, encoding="utf-8", errors="replace").read()) for f in glob.glob(os.path.join(root, pattern), recursive=True))

def measure():
    return {
        "project CLAUDE.md": size("project-template/CLAUDE.md"),
        "user CLAUDE.md": size("user-level-memory/CLAUDE.md"),
        "agents": size("user-level-agents/*.md"),
        "skill entry points": size("user-level-skills/**/SKILL.md"),
    }

def main():
    m = measure()
    if "--update" in sys.argv:
        json.dump(m, open(BASE, "w"), indent=2); print("baseline updated:", m); return 0
    if not os.path.isfile(BASE):
        json.dump(m, open(BASE, "w"), indent=2); print("baseline created:", m); return 0
    b = json.load(open(BASE)); bad = 0
    for k, v in m.items():
        base = b.get(k, v)
        over = v > base * TOL
        bad += over
        print("%s %-20s %7d chars (~%d tokens), baseline %d" % ("OVER" if over else "ok  ", k, v, v // 4, base))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
