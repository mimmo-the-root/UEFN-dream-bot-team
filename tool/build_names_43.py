#!/usr/bin/env python3
"""build_names_43.py - translate the tool names the kit knows (UEFN before 43.00) into the names of the 43.00 map.

  python tool/build_names_43.py MAP_LATEST_JSON      writes project-template/Claude/hooks/mcp-names-43.json

Old key "editor_toolset.toolsets.scene.SceneTools/get_current_level" -> new key "EditorToolset/GetCurrentLevel" (the keys of mcp_map latest.json).
Match = same tool name without case or underscores; when several new tools share it, the one whose toolset equals a part of the old toolset wins (most specific part first).
Tools with no match are listed under "gone" (renamed or removed): a person or the map must look at them. Nothing here touches the editor."""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.join(HERE, "..", "project-template", "Claude", "hooks")
norm = lambda s: re.sub(r"[_\W]", "", s).lower()


def build(known, new_tools):
    idx = collections.defaultdict(list)
    for n in new_tools:
        idx[norm(n.split("/", 1)[1])].append(n)
    out, gone, ambiguous = {}, [], []
    for old in sorted(known):
        ts, tool = old.split("/", 1)
        cand = idx.get(norm(tool), [])
        if len(cand) > 1:
            parts = [norm(x) for x in ts.split(".")]
            pick = []
            for part in reversed(parts):   # the most specific part first (ValkyrieToolset.VerseToolset -> VerseToolset)
                pick = [c for c in cand if norm(c.split("/")[0]) == part]
                if pick:
                    break
            if len(pick) == 1:
                cand = pick
        if len(cand) == 1:
            out[old] = cand[0]
        elif cand:
            ambiguous.append({"old": old, "candidates": cand})
        else:
            gone.append(old)
    return {"note": "old key -> key in the 43.00 map; see tool/build_names_43.py", "count": len(out), "names": out, "ambiguous": ambiguous, "gone": gone}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    new = json.load(open(sys.argv[1], encoding="utf-8"))["tools"]
    known = json.load(open(os.path.join(HOOKS, "mcp-known-tools.json"), encoding="utf-8"))["tools"]
    res = build(known, new)
    json.dump(res, open(os.path.join(HOOKS, "mcp-names-43.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    print("translated %d of %d, ambiguous %d, gone %d" % (res["count"], len(known), len(res["ambiguous"]), len(res["gone"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
