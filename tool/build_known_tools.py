#!/usr/bin/env python3
"""build_known_tools.py - build project-template/Claude/hooks/mcp-known-tools.json from the lab results.

What it is: one line per UEFN MCP tool with what the lab learned (ok / recipe / refused / rejected / no_answer / never),
the area, a short reason, and a flag when the tool is hard to undo (ask the owner first). `mcp_map.py --find` prints it,
so an agent knows before it calls a tool. Nothing here is loaded into a session: only the script reads the file.

    python tool/build_known_tools.py --lab <project>/Content   (reads Claude/logs/explore-ledger.jsonl and
                                                                Claude/docs/mcp/coverage.json + recipes.json)
Refresh after a lab run or after `mcp_map.py` reports a changed tool count.
"""
import argparse, collections, datetime, json, os, re, sys

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True, help="the lab project's Content folder (holds Claude/)")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    c = os.path.join(a.lab, "Claude")
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
