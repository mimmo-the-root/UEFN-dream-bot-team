#!/usr/bin/env python3
"""mcp_lessons.py - recurring MCP errors from the explore ledger, as lesson candidates.

Reads the ledger (JSON lines), groups non-ok calls by a normalized error signature and
lists the recurring ones, marking those already written in the docs. Read-only except
for --json/--md. Standard library only (Python 3.10+).
"""
import argparse
import json
import os
import re
import sys

MAX_SIG = 120
GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
RE_GUID_PATH = re.compile(r"/" + GUID + r"(?:/[^\s\"',;)\]]*)?")
RE_GAME_PATH = re.compile(r"/Game(?:/[^\s\"',;)\]]*)?")
# project-root paths such as /root_ai_lab/UI_T001 or /ArmASR/ (a lone slash-word-slash prefix)
RE_ROOT_PATH = re.compile(r"(?<![\w<])/[A-Za-z_][\w.]*(?:/[^\s\"',;)\]]*)+")
RE_WIN_PATH = re.compile(r"[A-Za-z]:[\/][^\s\"',;)\]]*")
RE_GUID = re.compile(GUID)
RE_ASSET_N = re.compile(r"\b([A-Za-z][A-Za-z_]*?)[_-]?\d+\b")
RE_LONGNUM = re.compile(r"\b\d{4,}\b")
RE_SPACES = re.compile(r"\s+")


INCLUDE_BATTERY = False


def normalize(msg):
    s = str(msg or "")
    s = RE_GUID_PATH.sub("<path>", s)
    s = RE_GAME_PATH.sub("<path>", s)
    s = RE_WIN_PATH.sub("<path>", s)
    s = RE_ROOT_PATH.sub("<path>", s)
    s = RE_GUID.sub("<guid>", s)
    s = RE_LONGNUM.sub("N", s)
    s = RE_ASSET_N.sub(lambda m: m.group(1) + "_N", s)
    s = RE_SPACES.sub(" ", s).strip()
    return s[:MAX_SIG]


def load_known(path):
    """Return (names, areas): tool-name set and optional {tool: area}."""
    if not path or not os.path.isfile(path):
        return set(), {}
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return set(), {}
    tools = d.get("tools", d) if isinstance(d, dict) else d
    if isinstance(tools, dict):
        # mcp-known-tools.json: {"toolset/tool": {"s": state, "a": area, ...}}
        return set(tools), {k: str(v.get("a")) for k, v in tools.items() if isinstance(v, dict) and v.get("a")}
    if isinstance(tools, list):
        return {str(t) for t in tools}, {}
    return set(), {}


def area_of(toolset, tool, names, areas):
    key = "%s/%s" % (toolset, tool)
    if key in areas:
        return areas[key]
    if tool in areas:
        return areas[tool]
    if key in names or tool in names:
        return (toolset or "other").split(".")[-1] or "other"
    return "other"


def is_battery(row):
    """Rows made by the test batteries (coverage, soak, session) are not lessons: they probe tools with invented arguments.
    New rows carry src=battery; older rows are recognised by the batteries' own folder (/Cover)."""
    if row.get("src") == "battery":
        return True
    if "src" in row:
        return False
    return "/Cover" in str(row.get("args") or "")


def is_noise(row):
    """Guardian refusals that are not lessons (path outside the lab, lab mode not set)."""
    if row.get("r") != "refused":
        return False
    why = str(row.get("why") or row.get("peek") or "").lower()
    return any(k in why for k in ("lab_root", "laborator", "outside", "sandbox"))


def read_ledger(path):
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("toolset") and d.get("tool"):
                yield d


def collect(ledger, names, areas, min_count):
    groups = {}
    for row in read_ledger(ledger):
        r = row.get("r")
        if not r or r == "ok" or is_noise(row) or (not INCLUDE_BATTERY and is_battery(row)):
            continue
        msg = row.get("peek") or row.get("why") or r
        sig = normalize(msg)
        key = "%s/%s | %s" % (row["toolset"], row["tool"], sig)
        g = groups.setdefault(key, {
            "key": key, "area": area_of(row["toolset"], row["tool"], names, areas),
            "count": 0, "r": r, "signature": sig, "first_seen": None, "last_seen": None,
            "example_args": "", "covered": False, "_calls": set(), "_msg": sig})
        g["count"] += 1
        t = str(row.get("t") or "")
        g["_calls"].add((str(row.get("args") or ""), t))
        if t:
            if g["first_seen"] is None or t < g["first_seen"]:
                g["first_seen"] = t
            if g["last_seen"] is None or t > g["last_seen"]:
                g["last_seen"] = t
        if not g["example_args"]:
            g["example_args"] = str(row.get("args") or "")[:160]
    out = [g for g in groups.values() if g["count"] >= min_count and len(g["_calls"]) >= 2]
    return out


def docs_text(dirs):
    parts = []
    for d in dirs:
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if fn.lower().endswith(".md"):
                    try:
                        with open(os.path.join(root, fn), encoding="utf-8", errors="replace") as f:
                            parts.append(f.read())
                    except OSError:
                        pass
    return parts


def mark_covered(items, dirs):
    texts = docs_text(dirs)
    low = [t.lower() for t in texts]
    norm = [normalize(t).lower() for t in texts]
    for g in items:
        sig = g["signature"].lower()
        tool = g["key"].split(" | ")[0].lower()
        probes = [p for p in (sig, g["_msg"].lower()) if len(p) >= 12]
        g["covered"] = any(p in blob for p in probes for blob in low + norm) if probes else False
        g["_tool"] = tool
    return items


def render_md(items):
    unc = [g for g in items if not g["covered"]]
    lines = []
    for g in unc[:38]:
        lines.append("- x%d [%s] %s - %s" % (g["count"], g["r"], g["key"].split(" | ")[0], g["signature"]))
    if len(unc) > 38:
        lines.append("- ... altri %d non coperti nel JSON" % (len(unc) - 38))
    lines.append("%d candidates, %d already covered" % (len(items), len(items) - len(unc)))
    return "\n".join(lines[:40]) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recurring MCP errors as lesson candidates")
    ap.add_argument("--ledger", default=os.path.join("Claude", "logs", "explore-ledger.jsonl"))
    ap.add_argument("--known", default=None)
    ap.add_argument("--docs", nargs="*", default=None)
    ap.add_argument("--min", type=int, default=2)
    ap.add_argument("--include-battery", action="store_true", help="also count rows made by the test batteries")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--md", dest="md_out")
    a = ap.parse_args(argv)
    global INCLUDE_BATTERY
    INCLUDE_BATTERY = a.include_battery
    known = a.known
    if known is None:
        for c in ("mcp-known-tools.json", os.path.join("Claude", "reference", "mcp-known-tools.json")):
            if os.path.isfile(c):
                known = c
                break
    names, areas = load_known(known)
    dirs = a.docs if a.docs else [os.path.join("Claude", "docs", "mcp")]
    items = collect(a.ledger, names, areas, a.min)
    mark_covered(items, [d for d in dirs if os.path.isdir(d)])
    items.sort(key=lambda g: (g["covered"], -g["count"], g["key"]))
    out = [{k: v for k, v in g.items() if not k.startswith("_")} for g in items]
    md = render_md(items)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    if a.md_out:
        with open(a.md_out, "w", encoding="utf-8") as f:
            f.write(md)
    if not a.json_out and not a.md_out:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
