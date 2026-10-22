#!/usr/bin/env python3
"""Generate docs/manual/mcp-tool-reference.md: every UEFN MCP tool the kit knows,
grouped by toolset, with parameter names taken from the shipped recipes.
Epic's tool descriptions are NOT included (they stay on the user's computer)."""
import json, os, re
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN = os.path.join(ROOT, "project-template/Claude/hooks/mcp-known-tools.json")
REC = os.path.join(ROOT, "user-level-skills/mcp-tool-contracts/references/areas/recipes.json")
OUT = os.path.join(ROOT, "docs/manual/mcp-tool-reference.md")

def shape(v):
    if isinstance(v, bool): return "true/false"
    if isinstance(v, (int, float)): return "number"
    if isinstance(v, list): return "list"
    if isinstance(v, dict):
        return "asset ref" if "refPath" in v else "object"
    if v is None: return "optional"
    return "text"

def cell(s): return str(s).replace("|", "/").replace("\n", " ")

def main():
    known = json.load(open(KNOWN, encoding="utf-8"))["tools"]
    rec = json.load(open(REC, encoding="utf-8"))
    by_short = {}
    for k, v in rec.items():
        by_short[k.split("/")[-1] if "/" in k else k] = (k, v)
    sets = defaultdict(list)
    for key, info in known.items():
        ts, _, tool = key.partition("/")
        short = ts.split(".")[-1]
        r = rec.get(key) or rec.get(short + "/" + tool)
        sets[short].append((tool, info, r))
    L = ["# Tool reference", "",
         "Every tool of the UEFN MCP that the kit has met, grouped by toolset, with the parameters its tested recipe uses. "
         "The last column says how far the kit trusts the recipe: proven (used in real work or replayed), tool-ok (answered in a test), unverified, avoid (known trap, do not call). "
         "This page is generated; the full live description of each tool stays on your computer: run `mcp_map.py --find <word>` to see it.", ""]
    n = p = 0
    for ts in sorted(sets):
        L += ["## " + ts, "", "| Tool | Parameters | Writes | Status |", "|---|---|---|---|"]
        for tool, info, r in sorted(sets[ts], key=lambda x: x[0]):
            n += 1
            if r:
                args = r.get("args") or {}
                params = ", ".join(f"{a} ({shape(v)})" for a, v in args.items()) or "none"
                w = "yes" if r.get("writes") else "no"
                st = r.get("status", "unverified")
                if st == "proven": p += 1
            else:
                params, w, st = "see mcp_map.py --find", "yes" if info.get("w") else "?", "no recipe"
            L.append(f"| {cell(tool)} | {cell(params)} | {w} | {st} |")
        L.append("")
    L.insert(2, f"{n} tools, {p} with a proven recipe.\n")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print(n, "tools,", p, "proven ->", OUT)

main()
