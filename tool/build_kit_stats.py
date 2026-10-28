#!/usr/bin/env python3
"""build_kit_stats.py - writes docs/kit-stats.json, the numbers the README badges read (agents, skills, lessons, MCP tools, proven recipes).

    python tool/build_kit_stats.py            write the file
    python tool/build_kit_stats.py --check    exit 1 if the committed file is out of date (the tests run this)
"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "kit-stats.json")
OUT_CONSOLE = os.path.join(ROOT, "project-template", "Claude", "community", "kit-stats.json")   # the Console reads this copy (offline)


def stats():
    agents = [f for f in os.listdir(os.path.join(ROOT, "user-level-agents")) if f.endswith(".md")]
    skills = [d for d in os.listdir(os.path.join(ROOT, "user-level-skills")) if os.path.isfile(os.path.join(ROOT, "user-level-skills", d, "SKILL.md"))]
    known = json.load(open(os.path.join(ROOT, "project-template/Claude/hooks/mcp-known-tools.json"), encoding="utf-8"))["tools"]
    rec = json.load(open(os.path.join(ROOT, "user-level-skills/mcp-tool-contracts/references/areas/recipes.json"), encoding="utf-8"))
    ids = set()
    for f in glob.glob(os.path.join(ROOT, "user-level-skills", "genre", "*", "community", "*.json")) + glob.glob(os.path.join(ROOT, "user-level-skills", "genre", "*", "official", "*.json")):
        try:
            obj = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for x in (obj.get("patterns") if isinstance(obj, dict) else None) or []:
            if isinstance(x, dict) and x.get("id"):
                ids.add(x["id"])
    return {"agents": len(agents), "mcp_subagents": len([a for a in agents if a.startswith("mcp-")]),
            "skills": len(skills), "lessons": len(ids), "mcp_tools": len(known), "recipes_proven": sum(1 for v in rec.values() if v.get("status") == "proven"),
            "version": open(os.path.join(ROOT, "project-template/Claude/KIT-VERSION"), encoding="utf-8").read().strip()}


def text():
    return json.dumps(stats(), indent=2) + "\n"


if __name__ == "__main__":
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        cur2 = open(OUT_CONSOLE, encoding="utf-8").read() if os.path.isfile(OUT_CONSOLE) else ""
        same = cur == text() and cur2 == text()
        print("kit stats are up to date" if same else "kit stats are OUT OF DATE: run python tool/build_kit_stats.py")
        sys.exit(0 if same else 1)
    for _p in (OUT, OUT_CONSOLE):
        open(_p, "w", encoding="utf-8", newline="\n").write(text())
    print(text(), end="")
