#!/usr/bin/env python3
"""Map every tool UEFN's MCP server offers, once, and notice what changes later.

The agent (which has the MCP tools) lists the toolsets and their tools and pipes them in as JSON; this
script only compares, remembers and writes the map. It never talks to UEFN and sends nothing anywhere.
The MCP server belongs to UEFN, not to a project, so ONE map serves all projects, kept on your computer:
  ~/.claude/skills/mcp-tool-contracts/references/map/   (override: UEFN_KIT_MCP_DIR or --dir)
    latest.json    the current snapshot (tool -> description hash, first sentence, read/write guess)
    MAP.md         the readable catalog, grouped by toolset, with how much of it the kit already uses
    changes.jsonl  one line per change: date, UEFN version, added / removed / changed tools
    history/       the previous snapshot, kept when something changed
The descriptions are Epic's text: they stay in this private folder and are never copied into the kit.

Input on stdin, either form (always prefix the tool with its toolset, names like diff collide otherwise):
  {"tools": {"Toolset/ToolName": "description text", ...}}
  {"toolsets": [{"name": "set", "tools": [{"name": "ToolName", "description": "..."}]}]}

States: first_snapshot (exit 0), unchanged (0), changed (1), bad_input (2).

Usage: toolset_diff.py [--uefn-version 42.40] [--dir DIR] [--no-save] < tools.json
"""
import argparse, hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
READ = ("get", "list", "find", "read", "describe", "query", "search", "is", "has", "capture", "preview", "validate", "diff", "count", "check", "inspect", "resolve", "fetch", "show")
WRITE = ("set", "add", "create", "delete", "remove", "replace", "save", "build", "start", "push", "place", "duplicate", "import", "rename", "move", "apply", "spawn", "destroy", "update", "clear", "compile", "export", "write", "open", "close", "stop", "run", "execute", "load", "unload", "copy", "paste", "attach", "detach", "bind", "unbind", "reparent", "insert", "register", "reload", "restart", "cook", "sync", "submit", "revert", "checkout")


def default_dir():
    return os.environ.get("UEFN_KIT_MCP_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills", "mcp-tool-contracts", "references", "map")


def normalize(data):
    out = {}
    if isinstance(data, dict) and isinstance(data.get("tools"), dict):
        for k, v in data["tools"].items():
            out[str(k)] = str(v)
    elif isinstance(data, dict) and isinstance(data.get("toolsets"), list):
        for ts in data["toolsets"]:
            for t in (ts.get("tools") or []):
                out["%s/%s" % (ts.get("name", "?"), t.get("name", "?"))] = str(t.get("description", ""))
    else:
        raise ValueError("unknown shape")
    return out


def short(name):
    return re.split(r"[/.]", name)[-1]


def access(name):
    first = re.split(r"[_\s]|(?<=[a-z0-9])(?=[A-Z])", short(name).strip("_"))[0].lower()
    return "read" if first in READ else "write" if first in WRITE else "?"


def first_sentence(text):
    t = " ".join(text.split())
    t2 = re.sub(r"\b(i\.e|e\.g|etc|vs)\.", lambda m: m.group(0).replace(".", "\u2024"), t)
    m = re.match(r"(.{20,}?[.!?])(\s|$)", t2)
    return (m.group(1) if m else t2)[:140].replace("\u2024", ".")


def entry(name, desc):
    return {"h": hashlib.sha1(desc.encode("utf-8")).hexdigest()[:10], "d": first_sentence(desc), "a": access(name)}


def today():
    return time.strftime("%Y-%m-%d")


def is_known(k, known):
    """True when the kit documents tool k (full name from the lab map, or short name from the reference list)."""
    return k in known or short(k) in known


def kit_known():
    """Tools the kit documents: the short list in reference/ plus every tool the lab map marks as answered
    (ok) or with a recipe, from hooks/mcp-known-tools.json (the file that also feeds `mcp_map.py --find`)."""
    out = set()
    p = os.path.join(HERE, "..", "reference", "mcp-known-tools.json")
    try:
        out |= set(json.load(open(p, encoding="utf-8-sig")).get("tools", []))
    except (OSError, ValueError, AttributeError):
        pass
    try:
        t = json.load(open(os.path.join(HERE, "mcp-known-tools.json"), encoding="utf-8-sig")).get("tools", {})
        out |= {k for k, e in t.items() if isinstance(e, dict) and e.get("s") in ("ok", "recipe")}
    except (OSError, ValueError, AttributeError):
        pass
    try:   # the tool names of UEFN 43.00 and later: the same tools under their new keys (tool/build_names_43.py)
        out |= {v for k, v in names_43().items() if k in out}
    except Exception:
        pass
    return out


def names_43():
    """{old key: key in the 43.00 map} from hooks/mcp-names-43.json; {} when absent."""
    try:
        return json.load(open(os.path.join(HERE, "mcp-names-43.json"), encoding="utf-8-sig")).get("names", {})
    except (OSError, ValueError, AttributeError):
        return {}


def norm_name(name):
    return re.sub(r"[_\W]", "", short(name)).lower()


def fingerprint(raw):
    """One short hash of the whole catalog (every key with the hash of its description). It changes when Epic adds, removes, renames or rewords a tool,
    whether or not the UEFN version number changes (the 43.00 server reports no version at all)."""
    h = hashlib.sha1()
    for k in sorted(raw):
        h.update(k.encode("utf-8") + b"\0" + hashlib.sha1(raw[k].encode("utf-8")).hexdigest()[:10].encode("ascii") + b"\n")
    return h.hexdigest()[:16]


def find_renames(prev, now, added, removed):
    """Pairs (old key, new key) among the removed and added tools: the same tool under another name. Matches: the shipped 43.00 table;
    the same description hash; or the same name (case and underscores ignored) when exactly one tool on each side has it."""
    table, pairs, used = names_43(), [], set()
    for old in removed:
        new = table.get(old)
        if new in added and new not in used:
            pairs.append((old, new)); used.add(new)
    left = [r for r in removed if r not in {p[0] for p in pairs}]
    free = [a for a in added if a not in used]
    by_hash = {}
    for a in free:
        by_hash.setdefault(now[a]["h"], []).append(a)
    for old in left[:]:
        c = [a for a in by_hash.get(prev[old].get("h"), []) if a not in used]
        if len(c) == 1:
            pairs.append((old, c[0])); used.add(c[0]); left.remove(old)
    by_name_new, by_name_old = {}, {}
    for a in [a for a in free if a not in used]:
        by_name_new.setdefault(norm_name(a), []).append(a)
    for r in left:
        by_name_old.setdefault(norm_name(r), []).append(r)
    for n, olds in by_name_old.items():
        news = by_name_new.get(n, [])
        if len(olds) == 1 and len(news) == 1:
            pairs.append((olds[0], news[0]))
    return pairs


def write_map(d, tools, version, known):
    sets = {}
    for k in sorted(tools):
        sets.setdefault(k.split("/")[0] if "/" in k else "(no toolset)", []).append(k)
    used = [k for k in tools if is_known(k, known)]
    L = ["# UEFN MCP map", "", "Private to this computer (the descriptions are Epic's text). Made %s%s by /mcp-snapshot." % (time.strftime("%Y-%m-%d"), (", UEFN " + version) if version else ""), "",
         "%d toolsets, %d tools. The kit documents and uses %d of them (%.1f%%): marked [kit] below." % (len(sets), len(tools), len(used), 100.0 * len(used) / max(1, len(tools))), "",
         "| Toolset | Tools | Read | Write | Not sure | Kit uses |", "|---|---|---|---|---|---|"]
    for s, ks in sorted(sets.items()):
        c = lambda a: sum(1 for k in ks if tools[k]["a"] == a)
        L.append("| %s | %d | %d | %d | %d | %d |" % (s, len(ks), c("read"), c("write"), c("?"), sum(1 for k in ks if is_known(k, known))))
    for s, ks in sorted(sets.items()):
        L += ["", "## " + s, ""]
        for k in ks:
            e = tools[k]
            L.append("- `%s` (%s)%s %s" % (short(k), e["a"], " [kit]" if is_known(k, known) else "", e["d"]))
    tmp = os.path.join(d, "MAP.md.tmp")
    open(tmp, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    os.replace(tmp, os.path.join(d, "MAP.md"))
    return len(used)


def write_news(d, res, now, version):
    L = ["# UEFN MCP news", "", "%s%s. %d tools in %d toolsets; the kit documents and uses %d (%.1f%%)." % (time.strftime("%Y-%m-%d"), (", UEFN " + version) if version else "", res["count"], res["toolsets"], res["kit_uses"], res["kit_uses_pct"]), ""]
    if res["state"] == "first_snapshot":
        L += ["First map of the MCP. Read MAP.md (overview table at the top), or search it with `mcp_map.py --find <words>`."]
    else:
        L += ["## Added (%d)" % res.get("added_total", 0), ""]
        L += ["- `%s` (%s): %s" % (x["tool"], x["access"], x["does"]) for x in res.get("added", [])] or ["- none"]
        L += ["", "## Renamed (%d)" % res.get("renamed_total", 0), "", "Same tool, new name. Not new."] 
        L += ["", "## Removed (%d)" % res.get("removed_total", 0), ""] + (["- `%s`" % x for x in res.get("removed", [])] or ["- none"])
        L += ["", "## Description changed (%d)" % res.get("changed_total", 0), ""] + (["- `%s`" % x for x in res.get("changed", [])] or ["- none"])
    tmp = os.path.join(d, "NEWS.md.tmp")
    open(tmp, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    os.replace(tmp, os.path.join(d, "NEWS.md"))
    open(os.path.join(d, "NEWS.pending"), "w").write(time.strftime("%Y-%m-%d"))
    nj = {"date": time.strftime("%Y-%m-%d"), "state": res["state"], "added": res.get("added", [])[:30], "added_total": res.get("added_total", 0),
          "removed_total": res.get("removed_total", 0), "changed_total": res.get("changed_total", 0), "renamed_total": res.get("renamed_total", 0), "stopped_working": []}
    json.dump(nj, open(os.path.join(d, "news.json"), "w", encoding="utf-8"))


def apply_map(raw, d, version="", save=True, server="", schemas=None):
    """Compare a {tool: description} catalog with the saved map, save it when new or changed. Returns (result, exit code)."""
    now = {k: entry(k, v) for k, v in raw.items()}
    for k, sch in (schemas or {}).items():   # the signature (arguments) of each tool: a rename with the same signature is the same tool
        if k in now and sch:
            now[k]["sg"] = hashlib.sha1(json.dumps(sch, sort_keys=True).encode("utf-8")).hexdigest()[:10]
            props = sch.get("properties") if isinstance(sch, dict) else None
            if isinstance(props, dict):   # the argument names: lets the kit check a recipe's arguments against the tool without calling it
                now[k]["pn"] = sorted(props)[:40]
                req = sch.get("required")
                if isinstance(req, list) and req:
                    now[k]["rq"] = sorted(str(x) for x in req)[:20]
    path = os.path.join(d, "latest.json")
    prev = None
    try:
        prev = json.load(open(path, encoding="utf-8")).get("tools")
    except (OSError, ValueError, AttributeError):
        pass
    known = kit_known()
    used = sum(1 for k in now if is_known(k, known))
    res = {"count": len(now), "toolsets": len({k.split("/")[0] for k in now if "/" in k}), "kit_uses": used, "kit_uses_pct": round(100.0 * used / len(now), 1)}
    code = 0
    added = removed = changed = renamed = []
    if prev is None:
        for k in now:
            now[k]["fs"] = ""
        res["fingerprint"] = fingerprint(raw)
        res.update(state="first_snapshot", message="First map saved: %d tools in %d toolsets; the kit uses %d (%.1f%%)." % (len(now), res["toolsets"], used, res["kit_uses_pct"]))
    else:
        added = sorted(set(now) - set(prev))
        removed = sorted(set(prev) - set(now))
        renamed = find_renames(prev, now, added, removed)
        r_old, r_new = {p[0] for p in renamed}, {p[1] for p in renamed}
        added = [k for k in added if k not in r_new]
        removed = [k for k in removed if k not in r_old]
        carry = {new: old for old, new in renamed}
        def differs(k, p):
            a, b = now[k], prev[p]
            return a["h"] != b.get("h") or bool(a.get("sg") and b.get("sg") and a["sg"] != b["sg"])
        changed = sorted(k for k in now if (k in prev and differs(k, k)) or (k in carry and differs(k, carry[k])))
        for k in now:   # when each tool was first seen ("" = in the very first map, so not a discovery) and last reworded
            src = prev.get(k) or prev.get(carry.get(k, ""), None)
            if src is not None:
                now[k]["fs"] = src.get("fs", "")
                if src.get("ch"):
                    now[k]["ch"] = src["ch"]
            else:
                now[k]["fs"] = today()
            if k in changed:
                now[k]["ch"] = today()
        res["fingerprint"] = fingerprint(raw)
        if added or removed or changed or renamed:
            code = 1
            res.update(state="changed", added=[{"tool": k, "access": now[k]["a"], "does": now[k]["d"]} for k in added[:60]], added_total=len(added), removed=removed[:60], removed_total=len(removed), changed=changed[:60], changed_total=len(changed),
                       renamed=[{"old": a, "new": b} for a, b in renamed[:60]], renamed_total=len(renamed),
                       message="The MCP tools changed since the last map. Tell the owner what is new and what it could be used for before relying on it. A renamed tool is the same tool under a new name, not a new one.")
        else:
            res.update(state="unchanged", message="Same %d tools as the last map." % len(now))
    bare = [k for k in now if "/" not in k]
    if bare:
        res["warning"] = "%d tool names have no 'Toolset/' prefix; names such as diff or create can collide between toolsets and be lost. Use Toolset/ToolName keys." % len(bare)
    backfill = bool(schemas) and prev is not None and any("pn" not in e for e in prev.values())   # an older map without argument names: save again, no news
    if save and (prev is None or res["state"] == "changed" or backfill):
        try:
            os.makedirs(os.path.join(d, "history"), exist_ok=True)
            if prev is not None and os.path.isfile(path):
                os.replace(path, os.path.join(d, "history", time.strftime("%Y-%m-%d-%H%M%S") + ".json"))
            tmp = path + ".tmp"
            if backfill and res["state"] == "unchanged":
                for k in now:   # same catalog: keep the first-seen dates of the saved map
                    src = prev.get(k) or {}
                    now[k]["fs"] = src.get("fs", "")
                    if src.get("ch"):
                        now[k]["ch"] = src["ch"]
            json.dump({"saved": time.strftime("%Y-%m-%d"), "uefn_version": version, "server": server, "fp": res.get("fingerprint", fingerprint(raw)), "fmt": 2, "tools": now}, open(tmp, "w", encoding="utf-8"), indent=1)
            os.replace(tmp, path)
            write_map(d, now, version, known)
            if res["state"] != "unchanged":
                write_news(d, res, now, version)
            if res["state"] != "unchanged":
                with open(os.path.join(d, "changes.jsonl"), "a", encoding="utf-8", newline="\n") as f:
                    row = {"date": time.strftime("%Y-%m-%d"), "uefn": version, "state": res["state"], "count": len(now), "fp": res.get("fingerprint", "")}
                    if res["state"] == "changed":
                        row.update(added=added, removed=removed, changed=changed, renamed=[list(p) for p in renamed])
                    f.write(json.dumps(row) + "\n")
            res["map"] = os.path.join(d, "MAP.md")
        except OSError:
            res["message"] += " (map could not be saved)"
    return res, code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None)
    ap.add_argument("--uefn-version", default="")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    try:
        raw = normalize(json.loads(sys.stdin.read()))
        if not raw:
            raise ValueError("empty")
    except (ValueError, TypeError, AttributeError):
        print(json.dumps({"state": "bad_input", "message": "Expected JSON with a non-empty tools map or toolsets list on stdin."}))
        return 2
    res, code = apply_map(raw, a.dir or default_dir(), a.uefn_version, not a.no_save)
    print(json.dumps(res, ensure_ascii=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
