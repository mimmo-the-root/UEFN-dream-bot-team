#!/usr/bin/env python3
"""Tokens per agent, from the transcripts Claude Code keeps for each sub-agent run.

Reads (never writes) ~/.claude/projects/<this project>/<session>/subagents/agent-*.jsonl and the
agent-*.meta.json next to each (the agent's name). One model answer can be written on several lines with
partial counts, so each request is counted once, from the line with the most output tokens. The main session
is not included (the console already shows it). Nothing here is a price: counts only, because prices change.

Per-file results are cached in Claude/logs/agent-costs-cache.json, so only new files are read; a call stops
reading after a time budget and says how many files are still pending (the next call continues).
Any problem means "not available", never a guess.

Usage: agent_cost.py [project-dir] [--days 30] [--budget 6]      (prints one JSON object)
"""
import glob, json, os, re, sys, time

CACHE_V = 1


def config_dir():
    return os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")


def transcripts_dir(project):
    enc = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
    return os.path.join(config_dir(), "projects", enc)


def read_file(path):
    """Aggregate one sub-agent transcript: name, model, distinct requests, token sums."""
    best = {}
    model = agent = ""
    first_ts = ""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"usage"' not in line and '"attributionAgent"' not in line:
                continue
            try:
                o = json.loads(line)
            except ValueError:
                continue
            agent = agent or str(o.get("attributionAgent") or "")
            m = o.get("message")
            u = m.get("usage") if isinstance(m, dict) else None
            if not isinstance(u, dict):
                continue
            model = model or str(m.get("model") or o.get("requestedModel") or "")
            first_ts = first_ts or str(o.get("timestamp") or "")
            key = o.get("requestId") or o.get("uuid") or id(o)
            out = u.get("output_tokens") or 0
            if key not in best or out >= (best[key].get("output_tokens") or 0):
                best[key] = u
    n = lambda k: sum(int(u.get(k) or 0) for u in best.values())
    return {"agent": agent, "model": model, "calls": len(best), "input": n("input_tokens"), "output": n("output_tokens"),
            "cache_read": n("cache_read_input_tokens"), "cache_creation": n("cache_creation_input_tokens")}


def meta_name(path):
    mp = path[:-len(".jsonl")] + ".meta.json"
    try:
        with open(mp, encoding="utf-8") as f:
            return str(json.load(f).get("agentType") or "")
    except (OSError, ValueError):
        return ""


def load_cache(p):
    try:
        with open(p, encoding="utf-8") as f:
            c = json.load(f)
        if c.get("v") == CACHE_V and isinstance(c.get("files"), dict):
            return c
    except (OSError, ValueError):
        pass
    return {"v": CACHE_V, "files": {}}


def summary(project, days=30, budget=6.0):
    tdir = transcripts_dir(project)
    if not os.path.isdir(tdir):
        return {"available": False, "reason": "no Claude Code transcripts found for this project on this computer"}
    cutoff = time.time() - days * 86400
    files = []
    for p in glob.glob(os.path.join(tdir, "*", "subagents", "agent-*.jsonl")):
        try:
            st = os.stat(p)
        except OSError:
            continue
        if st.st_mtime >= cutoff:
            files.append((p, st.st_mtime, st.st_size))
    cpath = os.path.join(os.environ.get("UEFN_KIT_CACHE_DIR") or os.path.join(project, "Claude", "logs"), "agent-costs-cache.json")
    cache = load_cache(cpath)
    cf = cache["files"]
    t0 = time.time()
    pending = 0
    dirty = False
    live = {}
    for p, mt, sz in sorted(files, key=lambda x: -x[1]):
        key = os.path.relpath(p, tdir)
        c = cf.get(key)
        if not c or c.get("mtime") != mt or c.get("size") != sz:
            if time.time() - t0 > budget:
                pending += 1
                continue
            try:
                c = read_file(p)
            except OSError:
                continue
            c["agent"] = meta_name(p) or c["agent"] or "unknown"
            c["mtime"], c["size"] = mt, sz
            cf[key] = c
            dirty = True
        live[key] = c
    if dirty or len(live) + pending < len(cf):
        cache["files"] = {k: v for k, v in cf.items() if k in live}
        try:
            os.makedirs(os.path.dirname(cpath), exist_ok=True)
            with open(cpath + ".tmp", "w", encoding="utf-8") as f:
                json.dump(cache, f)
            os.replace(cpath + ".tmp", cpath)
        except OSError:
            pass
    agents = {}
    for c in live.values():
        a = agents.setdefault(c["agent"], {"agent": c["agent"], "runs": 0, "calls": 0, "input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "models": []})
        a["runs"] += 1
        for k in ("calls", "input", "output", "cache_read", "cache_creation"):
            a[k] += c[k]
        if c["model"] and c["model"] not in a["models"]:
            a["models"].append(c["model"])
    rows = sorted(agents.values(), key=lambda a: -(a["input"] + a["output"] + a["cache_read"] + a["cache_creation"]))
    for a in rows:
        a["total"] = a["input"] + a["output"] + a["cache_read"] + a["cache_creation"]
    return {"available": True, "days": days, "complete": pending == 0, "pending": pending, "agents": rows,
            "total": sum(a["total"] for a in rows), "runs": sum(a["runs"] for a in rows)}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    days = 30
    if "--days" in args:
        i = args.index("--days")
        days = int(args[i + 1])
        del args[i:i + 2]
    budget = 6.0
    if "--budget" in args:
        i = args.index("--budget")
        budget = float(args[i + 1])
        del args[i:i + 2]
    project = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        res = summary(project, days, budget)
    except Exception as e:
        res = {"available": False, "reason": "could not read the transcripts (%s)" % e.__class__.__name__}
    sys.stdout.write(json.dumps(res) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
