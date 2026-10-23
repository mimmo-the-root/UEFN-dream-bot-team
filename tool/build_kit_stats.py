#!/usr/bin/env python3
"""build_kit_stats.py - writes docs/kit-stats.json, the numbers the README badges read (agents, skills, MCP tools, proven recipes).

    python tool/build_kit_stats.py            write the file
    python tool/build_kit_stats.py --check    exit 1 if the committed file is out of date (the tests run this)
"""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "kit-stats.json")


def stats():
    agents = [f for f in os.listdir(os.path.join(ROOT, "user-level-agents")) if f.endswith(".md")]
    skills = [d for d in os.listdir(os.path.join(ROOT, "user-level-skills")) if os.path.isfile(os.path.join(ROOT, "user-level-skills", d, "SKILL.md"))]
    known = json.load(open(os.path.join(ROOT, "project-template/Claude/hooks/mcp-known-tools.json"), encoding="utf-8"))["tools"]
    rec = json.load(open(os.path.join(ROOT, "user-level-skills/mcp-tool-contracts/references/areas/recipes.json"), encoding="utf-8"))
    return {"agents": len(agents), "mcp_subagents": len([a for a in agents if a.startswith("mcp-")]),
            "skills": len(skills), "mcp_tools": len(known), "recipes_proven": sum(1 for v in rec.values() if v.get("status") == "proven"),
            "version": open(os.path.join(ROOT, "project-template/Claude/KIT-VERSION"), encoding="utf-8").read().strip()}


def text():
    return json.dumps(stats(), indent=2) + "\n"


if __name__ == "__main__":
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        same = cur == text()
        print("kit stats are up to date" if same else "kit stats are OUT OF DATE: run python tool/build_kit_stats.py")
        sys.exit(0 if same else 1)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text())
    print(text(), end="")
