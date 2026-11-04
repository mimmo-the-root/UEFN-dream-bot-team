#!/usr/bin/env python3
"""build_known_tools.py - build project-template/Claude/hooks/mcp-known-tools.json from the lab results.

What it is: one line per UEFN MCP tool with what the lab learned (ok / recipe / refused / rejected / no_answer / never),
the area, a short reason, and a flag when the tool is hard to undo (ask the owner first). `mcp_map.py --find` prints it,
so an agent knows before it calls a tool. Nothing here is loaded into a session: only the script reads the file.

    python tool/build_known_tools.py --lab <project>/Content   (reads Claude/logs/explore-ledger.jsonl and
                                                                Claude/docs/mcp/coverage.json + recipes.json)
    python tool/build_known_tools.py --lab <project>/Content --map <latest.json>
        UEFN 43.00: one entry per tool of the saved map (the keys are the new flat names), from the ledger, the validation rows in
        Claude/_spike/validation/*.json, the recipes and the avoid list
Refresh after a lab run or after `mcp_map.py` reports a changed tool count.
"""
import argparse, collections, datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "project-template", "Claude", "hooks", "mcp-known-tools.json")

AREAS = [
    ("physics-mesh", ("StaticMesh", "SkeletalMesh", "PhysicsAsset", "PrimitiveTools", "TextureTools", "static_mesh", "skeletal_mesh", "texture", "primitive")),
    ("ui-widgets", ("UMGToolSet", "MVVMToolset", "WidgetAnimationToolset", "VerseFieldsToolset")),
    ("assets", ("asset.AssetTools", "DataTable", "CurveTable", "GameplayTags", "ObjectTools", "data_table", "curve_table", "object.")),
    ("editor-logs", ("EditorAppToolset", "LogsToolset")),
    ("level-devices", ("ActorTools", "SceneTools", "EntityToolset", "DeviceToolset")),
    ("verse-build", ("VerseToolset",)),
    ("session-regression", ("SessionToolset",)),
    ("scripting-batch", ("Programmatic", "ValkyriePython", "Python")),
    ("materials", ("MaterialTools", "MaterialInstanceTools", "material")),
    ("vfx-niagara", ("Niagara",)),
]
CONFIRM = re.compile(r"^(delete|remove|rename|move|replace|push|stop|clear|reset|destroy|merge)", re.I)


def area_of(toolset):
    for name, keys in AREAS:
        if any(k in toolset for k in keys):
            return name
    return "other"


def short(v, n=90):
    if isinstance(v, list):
        v = "; ".join(str(x) for x in v[:2])
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def build(ledger_path, coverage_path, recipes_path):
    led = collections.defaultdict(list)
    for line in open(ledger_path, encoding="utf-8", errors="replace"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        led[r["toolset"] + "/" + r["tool"]].append(r["r"])
    cov = json.load(open(coverage_path, encoding="utf-8"))
    rec = json.load(open(recipes_path, encoding="utf-8"))
    recbase = {k.split("#")[0] for k in rec}
    tools = {}
    for k, e in cov.items():
        rs = led.get(k, [])
        if "ok" in rs:
            s = "ok"
        elif k in recbase:
            s = "recipe"
        elif rs and all(x == "refused" for x in rs):
            s = "refused"
        elif "rejected" in rs:
            s = "rejected"
        elif "no_answer" in rs:
            s = "no_answer"
        else:
            s = "never"
        row = {"s": s, "a": area_of(k.split("/")[0])}
        why = short(e.get("why")) if isinstance(e, dict) and s not in ("ok", "recipe") else ""
        if why:
            row["why"] = why
        if CONFIRM.match(k.split("/")[-1]):
            row["c"] = 1
        tools[k] = row
    return tools


def key_of(toolset, tool):
    """Ledger and validation rows write Toolset.Sub/Tool or Toolset.Sub.Tool; the 43.00 map keys are flat: Toolset/Tool."""
    toolset, tool = str(toolset or ""), str(tool or "")
    if "/" in tool:
        toolset, tool = tool.split("/", 1)
    elif not toolset and "." in tool:
        toolset, tool = tool.rsplit(".", 1)
    return toolset.split(".")[0] + "/" + tool


def build43(mp_tools, ledger_path, recipes_path, validation_dir, avoid, old_known, table, area_map):
    """{key: {s, a, why?, c?}} over every tool of the 43.00 map. s: ok (answered in the lab, by use or by validation), recipe, refused (the lab guard
    said no), rejected (the editor answered with an error: a fixture or the argument shape was missing), no_answer, never (not tried, or skipped on purpose)."""
    led = collections.defaultdict(list)
    try:
        for line in open(ledger_path, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            led[key_of(r.get("toolset"), r.get("tool"))].append(r.get("r"))
    except OSError:
        pass
    val = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(validation_dir, "*.json"))):
        if os.path.basename(f) in ("ALREADY.json", "TODO.json", "args-fixed.json") or os.path.basename(f).startswith("_"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for r in (d if isinstance(d, list) else d.get("rows") or d.get("results") or []):
            if isinstance(r, dict) and r.get("tool"):
                val[key_of("", r["tool"])].append((r.get("state"), short(r.get("answer"), 90)))
    try:
        rec = json.load(open(recipes_path, encoding="utf-8"))
    except (OSError, ValueError):
        rec = {}
    recipe_keys = set()
    for k in rec:
        b = k.split("#")[0]
        recipe_keys.add(table.get(b, b))
        if "/" in b:
            recipe_keys.add(b.split("/", 1)[0].split(".")[0] + "/" + b.split("/", 1)[1])
    old_area = {}
    for k, e in old_known.items():
        old_area[table.get(k, k)] = e.get("a")
    out = {}
    for k in sorted(mp_tools):
        ts, tl = k.split("/", 1)
        rs, vs = led.get(k, []), val.get(k, [])
        states = {x[0] for x in vs}
        why = ""
        if k in avoid:
            s, why = "never", "avoid: " + short((avoid[k] or {}).get("why"), 80)
        elif "ok" in rs or states & {"answered", "proven"}:
            s = "ok"
        elif k in recipe_keys:
            s = "recipe"
        elif "refused" in states or (rs and all(x == "refused" for x in rs)):
            s, why = "refused", "the lab guard said no"
        elif states & {"needs-fixture", "shape"} or "rejected" in rs:
            s = "rejected"
            why = "needs a fixture" if "needs-fixture" in states else ("argument shape to fix" if "shape" in states else "")
            why = why or next((a for st, a in vs if a), "")
        elif "no_answer" in rs:
            s = "no_answer"
        else:
            s = "never"
            if "skipped" in states:
                why = "skipped on purpose (heavy, destructive or the owner deferred it)"
        row = {"s": s, "a": old_area.get(k) or area_map.get(ts, "other")}
        if why:
            row["why"] = why
        if CONFIRM.match(tl):
            row["c"] = 1
        out[k] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True, help="the lab project's Content folder (holds Claude/)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--map", help="the saved 43.00 tool map (latest.json): one entry per tool of the map")
    a = ap.parse_args()
    c = os.path.join(a.lab, "Claude")
    if a.map:
        sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
        import toolset_diff as td
        import recipes_status as rs
        mp = json.load(open(a.map, encoding="utf-8-sig"))["tools"]
        hooks = os.path.join(HERE, "..", "project-template", "Claude", "hooks")
        try:
            old = json.load(open(OUT, encoding="utf-8-sig")).get("tools", {})
        except (OSError, ValueError):
            old = {}
        avoid = json.load(open(os.path.join(hooks, "mcp-avoid.json"), encoding="utf-8")).get("avoid", {})
        rec_p = os.path.join(HERE, "..", "user-level-skills", "mcp-tool-contracts", "references", "areas", "recipes.json")
        tools = build43(mp, os.path.join(c, "logs", "explore-ledger.jsonl"), rec_p, os.path.join(c, "_spike", "validation"), avoid, old, td.names_43(), rs.TOOLSET_AREA)
        n = collections.Counter(v["s"] for v in tools.values())
        obj = {"generated": datetime.date.today().isoformat(), "count": len(tools), "summary": dict(n), "uefn": "43.00",
               "legend": "s: ok=answered in the lab (by use or by validation), recipe=has a recipe, refused=the lab guard said no, rejected=the editor answered with an error (needs a fixture or other arguments), no_answer, never=not tried or skipped on purpose; c=1: ask the owner before calling",
               "tools": tools}
        json.dump(obj, open(a.out, "w", encoding="utf-8", newline="\n"), indent=0, sort_keys=True)
        print("%d tools -> %s %s" % (len(tools), os.path.normpath(a.out), dict(n)))
        return 0
    tools = build(os.path.join(c, "logs", "explore-ledger.jsonl"), os.path.join(c, "docs", "mcp", "coverage.json"),
                  os.path.join(c, "docs", "mcp", "recipes.json"))
    n = collections.Counter(v["s"] for v in tools.values())
    obj = {"generated": datetime.date.today().isoformat(), "count": len(tools), "summary": dict(n),
           "legend": "s: ok=answered ok in the lab, recipe=has a recipe, refused=lab guard said no, rejected=the editor said no, no_answer, never=not tried; c=1: ask the owner before calling",
           "tools": tools}
    json.dump(obj, open(a.out, "w", encoding="utf-8", newline="\n"), indent=0, sort_keys=True)
    print("%d tools -> %s %s" % (len(tools), os.path.normpath(a.out), dict(n)))


if __name__ == "__main__":
    sys.exit(main())
