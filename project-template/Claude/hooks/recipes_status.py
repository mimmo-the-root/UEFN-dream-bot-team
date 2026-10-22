#!/usr/bin/env python3
"""recipes_status.py - which MCP recipes have been proven by real work.

The recipes shipped with the kit (user-level-skills/mcp-tool-contracts/references/areas/recipes.json) carry a status:
  tool-ok    the tool answered ok in the lab (arguments not re-checked)
  proven     an agent called the tool with the same call FORM and it worked (this script finds those in the ledger)
  unverified not proven
"Same form" = same tool, same argument names (nested too), same true/false values. Text and number values are ignored, because
a recipe is a template ({lab_mount}, {widget_bp}). Only rows with src "work" (real work) or "replay" (a deliberate replay of the recipe) count; exploration rows of the batteries (src=battery, or the /Cover folder) never do.

  python recipes_status.py --report                    local evidence from this project's ledger, merged with the shipped recipes
  python recipes_status.py --todo [--area NAME]        what a validation battery still has to replay (proven recipes are skipped)
  python recipes_status.py --gap [--area NAME]         tools that answered in the lab but have no recipe yet (with the last good call)
  python recipes_status.py --export OUT.json           the same evidence as counts per recipe, with NO arguments and NO paths (shareable)
  python recipes_status.py --apply EVIDENCE.json [--write]   the maintainer: raise recipes to proven from an evidence/export file
The evidence stays in Claude/logs/recipes-evidence.json; the shipped recipes.json is never edited by a normal run.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcp_lessons as ML  # noqa: E402

RECIPES = os.path.join(HERE, "..", "..", "..", "user-level-skills", "mcp-tool-contracts", "references", "areas", "recipes.json")
DEFAULT_RECIPES = [RECIPES, os.path.join(os.path.expanduser("~"), ".claude", "skills", "mcp-tool-contracts", "references", "areas", "recipes.json")]


def shape(v):
    """The call form: names and booleans, not values."""
    if isinstance(v, dict):
        return {k: shape(x) for k, x in sorted(v.items())}
    if isinstance(v, bool):
        return v
    if isinstance(v, list):
        return ["list"]
    if v is None:
        return None
    return "v"


def form(args):
    return json.dumps(shape(args), sort_keys=True)


def parse_args(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None  # the ledger keeps only the first 400 characters: a cut call cannot be compared


def evidence_from_ledger(path):
    ev = {}  # "toolset/tool" -> {form: [ok_n, fail_n, last_fail]}
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return ev
    for line in f:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if "tool" not in r or r.get("src") not in ("work", "replay") or r.get("r") not in ("ok", "rejected"):  # only real work and the deliberate replay of a recipe (src work / replay, both from mcp_work_log.py) count
            continue
        a = parse_args(r.get("args"))
        if a is None:
            continue
        slot = ev.setdefault("%s/%s" % (r["toolset"], r["tool"]), {}).setdefault(form(a), [0, 0, ""])
        if r["r"] == "ok":
            slot[0] += 1
        else:
            slot[1] += 1
            slot[2] = ML.normalize(r.get("why") or r.get("peek") or "")[:120]
    return ev


def is_note(key):
    """A multi-step note ("recipe/...", a title with spaces) is documentation, not one tool call: it cannot be proven by the ledger."""
    base = key.split("#")[0]
    return "/" not in base or " " in base or base.startswith("recipe/")


def _slot(ev, tool, f):
    """Evidence of one call form. A short toolset name (MaterialInstanceTools/set_parent) matches the full class name in the ledger."""
    if tool in ev:
        return ev[tool].get(f)
    for k, forms in ev.items():
        if k.endswith("." + tool) and f in forms:
            return forms[f]
    return None


def merge(recipes, ev):
    out = {}
    for key, rec in recipes.items():
        tool = key.split("#")[0]
        if is_note(key):
            out[key] = {"status": "note", "ok": 0, "failed": 0, "last_failure": ""}
            continue
        slot = _slot(ev, tool, form(rec.get("args", {})))
        base = rec.get("status", "unverified")
        base = "tool-ok" if base == "verified" else base
        ok_n, fail_n, last = slot or (0, 0, "")
        out[key] = {"status": "proven" if ok_n else base, "ok": ok_n, "failed": fail_n, "last_failure": last}
    return out


def load_recipes(path=None):
    for p in ([path] if path else DEFAULT_RECIPES):
        if p and os.path.isfile(p):
            return json.load(open(p, encoding="utf-8"))
    return {}


def report(merged):
    n = {}
    for v in merged.values():
        n[v["status"]] = n.get(v["status"], 0) + 1
    lines = ["recipes: %d (%s)" % (len(merged), ", ".join("%s %d" % kv for kv in sorted(n.items())))]
    for k, v in sorted(merged.items()):
        if v["failed"]:
            lines.append("FAILED x%d (ok x%d) %s | %s" % (v["failed"], v["ok"], k, v["last_failure"]))
    return "\n".join(lines)


def todo(merged, area=None):
    """The recipes a validation battery still has to replay: everything that is not `proven` (proven ones worked in real work
    and are skipped). Returns [(area, key, status)] sorted by area, optionally for one area."""
    try:
        tools = json.load(open(os.path.join(HERE, "mcp-known-tools.json"), encoding="utf-8")).get("tools", {})
    except (OSError, ValueError):
        tools = {}
    out = []
    for key, v in merged.items():
        if v["status"] in ("proven", "note"):
            continue
        ar = (tools.get(key.split("#")[0]) or {}).get("a") or "other"
        if area is None or ar == area:
            out.append((ar, key, v["status"]))
    return sorted(out)


def tool_coverage(merged, names):
    """How many of the server's tools have at least one recipe, and how many a proven one. `names` = full tool names (Toolset/Tool).
    A recipe with a short toolset name matches the full class name. Notes (multi-step) cover nothing."""
    names = list(names)
    have, proven = set(), set()
    for key, v in merged.items():
        if v["status"] == "note":
            continue
        base = key.split("#")[0]
        for n in names:
            if n == base or n.endswith("." + base):
                have.add(n)
                if v["status"] == "proven":
                    proven.add(n)
    return len(have), len(proven)


def gap(merged, tools, ledger, area=None):
    """Tools that answered in the lab (s == "ok" in mcp-known-tools.json) and have NO recipe yet, with the last good call from the ledger as
    a starting point (args may hold lab-only paths: turn them into placeholders in the recipe). [(area, tool, sample args)]."""
    have = set()
    for key, v in merged.items():
        if v["status"] != "note":
            have.add(key.split("#")[0])
    last = {}
    try:
        for line in open(ledger, encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("r") == "ok" and "tool" in r:
                last["%s/%s" % (r.get("toolset", ""), r["tool"])] = r.get("args") or "{}"
    except OSError:
        pass
    out = []
    for name, e in tools.items():
        if not isinstance(e, dict) or e.get("s") != "ok":
            continue
        if name in have or any(h and name.endswith("." + h) for h in have):
            continue
        ar = e.get("a") or "other"
        if area is None or ar == area:
            out.append((ar, name, last.get(name, "")[:300]))
    return sorted(out)


def _areas(merged):
    """Recipes per area (the area of the tool in mcp-known-tools.json); tools not in the file count as "other"."""
    try:
        tools = json.load(open(os.path.join(HERE, "mcp-known-tools.json"), encoding="utf-8")).get("tools", {})
    except (OSError, ValueError):
        tools = {}
    out = {}
    for key, v in merged.items():
        if v["status"] == "note":
            continue
        area = (tools.get(key.split("#")[0]) or {}).get("a") or "other"
        slot = out.setdefault(area, {"area": area, "total": 0, "proven": 0, "tool_ok": 0})
        slot["total"] += 1
        if v["status"] == "proven":
            slot["proven"] += 1
        elif v["status"] == "tool-ok":
            slot["tool_ok"] += 1
    return sorted(out.values(), key=lambda x: (-x["total"], x["area"]))


def _history(path, proven, tool_ok):
    """One line per ISO week in Claude/logs/recipes-history.json, so the Console can draw the growth. Never raises."""
    import datetime
    wk = "%d-W%02d" % datetime.date.today().isocalendar()[:2]
    try:
        h = json.load(open(path, encoding="utf-8"))
        if not isinstance(h, list):
            h = []
    except (OSError, ValueError):
        h = []
    if not h or h[-1].get("week") != wk:
        h.append({"week": wk, "proven": proven, "tool_ok": tool_ok})
    else:
        h[-1].update(proven=proven, tool_ok=tool_ok)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(h[-60:], open(path, "w", encoding="utf-8", newline="\n"))
    except OSError:
        pass
    return h[-7:]


def progress(ledger=None, recipes_path=None, history=None, tools=None):
    """Counts for the Console (UEFN MCP map): recipes per status, per area, and the weekly history. Never raises; {} when there is no recipes file."""
    try:
        recipes = load_recipes(recipes_path)
        if not recipes:
            return {}
        led = ledger or os.path.join("Claude", "logs", "explore-ledger.jsonl")
        merged = merge(recipes, evidence_from_ledger(led))
        n = {"proven": 0, "tool-ok": 0, "unverified": 0}
        for v in merged.values():
            n[v["status"]] = n.get(v["status"], 0) + 1
        total = len(merged) - n.get("note", 0)
        out = {"total": total, "notes": n.get("note", 0), "proven": n["proven"], "tool_ok": n["tool-ok"], "unverified": n["unverified"],
               "failed": sum(1 for v in merged.values() if v["failed"] and v["status"] != "proven"),  # a recipe that failed once and later worked is not "failed"
                "proven_pct": round(100.0 * n["proven"] / max(1, total), 1),
               "areas": _areas(merged)}
        if tools:
            out["tools_covered"], out["tools_proven"] = tool_coverage(merged, tools)
        hp = history or os.path.join(os.path.dirname(led), "recipes-history.json")
        out["history"] = _history(hp, n["proven"], n["tool-ok"])
        return out
    except Exception:
        return {}


def export(merged):
    """Counts per recipe key, nothing else: no arguments, no paths, no project names."""
    return {"kind": "mcp-recipes-evidence", "recipes": {k: {"ok": v["ok"], "failed": v["failed"], "last_failure": v["last_failure"]}
                                                       for k, v in merged.items() if v["ok"] or v["failed"]}}


def apply(recipes, evidence, min_ok=1):
    changed = 0
    for k, v in (evidence.get("recipes") or {}).items():
        if k in recipes and v.get("ok", 0) >= min_ok and recipes[k].get("status") != "proven":
            recipes[k]["status"] = "proven"
            changed += 1
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ledger", default=os.path.join("Claude", "logs", "explore-ledger.jsonl"))
    ap.add_argument("--recipes", default=None)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--export", metavar="OUT")
    ap.add_argument("--apply", metavar="EVIDENCE")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--gap", action="store_true")
    ap.add_argument("--area", default=None)
    ap.add_argument("--write", action="store_true", help="with --apply: write the recipes file (else just count)")
    ap.add_argument("--min-ok", type=int, default=1)
    a = ap.parse_args(argv)
    recipes = load_recipes(a.recipes)
    if a.apply:
        n = apply(recipes, json.load(open(a.apply, encoding="utf-8")), a.min_ok)
        if a.write:
            json.dump(recipes, open(a.recipes or RECIPES, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
        print("%d recipe(s) %s proven" % (n, "set to" if a.write else "would become"))
        return 0
    merged = merge(recipes, evidence_from_ledger(a.ledger))
    if a.gap:
        try:
            kt = json.load(open(os.path.join(HERE, "mcp-known-tools.json"), encoding="utf-8-sig")).get("tools", {})
        except (OSError, ValueError):
            kt = {}
        rows = gap(merged, kt, a.ledger, a.area)
        print("tools that answered but have no recipe: %d" % len(rows))
        for ar, name, args in rows:
            print("%s | %s | %s" % (ar, name, args))
        return 0
    if a.todo:
        rows = todo(merged, a.area)
        skipped = sum(1 for v in merged.values() if v["status"] == "proven")
        print("to replay: %d (skipping %d proven)" % (len(rows), skipped))
        for ar, key, st in rows:
            print("%s | %s | %s" % (ar, key, st))
        return 0
    if a.export:
        json.dump(export(merged), open(a.export, "w", encoding="utf-8", newline="\n"), indent=1)
    out = os.path.join(os.path.dirname(os.path.abspath(a.ledger)), "recipes-evidence.json")
    try:
        json.dump(merged, open(out, "w", encoding="utf-8", newline="\n"), indent=0)
    except OSError:
        pass
    print(report(merged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
