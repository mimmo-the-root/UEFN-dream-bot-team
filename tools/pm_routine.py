#!/usr/bin/env python3
"""Product Manager routine, one pass: QUEUE.json + relay state -> report (JSON on stdout).

Usage: pm_routine.py LAB [--queue PATH] [--history PATH] [--apply] [--max-parallel 3] [--idle-gap 120] [--loop-at 3]

Reads LAB/relay/{inbox,running,done,later} and LAB/logs/orchestrator.log, LAB/logs/cod-activity.jsonl. Read-only unless --apply;
with --apply it only MOVES files from relay/later to relay/inbox (never deletes, never overwrites). No memory outside the given files.
  - parallel cap: inbox + running count against max_parallel (default 3); only the free slots may be filled.
  - loops: a package id started --loop-at (3) or more times in orchestrator.log (lines with "start") or in the --history JSON
    (list of ids / {"id": ..} / {"id":.., "event":"start"} rows, or {id: count}) is reported LOOP and never requeued.
  - idle: per worker (the "pkg" field of cod-activity.jsonl rows) gaps between events longer than --idle-gap seconds count as idle;
    the report has idle seconds, gap count and the mean idle per gap per worker, and the mean over workers.
"""
import argparse
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def md_files(d):
    try:
        return sorted(n for n in os.listdir(d) if n.lower().endswith(".md") and os.path.isfile(os.path.join(d, n)))
    except OSError:
        return []


def has_id(text, pid):
    p = re.escape(str(pid).lower())
    return re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % p, str(text).lower()) is not None


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def start_counts(ids, log_path, history_path):
    counts = dict((i, 0) for i in ids)
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                if "start" not in ln.lower():
                    continue
                for i in ids:
                    if has_id(ln, i):
                        counts[i] += 1
    except OSError:
        pass
    h = read_json(history_path, None) if history_path else None
    if isinstance(h, dict):
        h = h.get("history", h.get("runs", h))
    if isinstance(h, dict):
        for k, v in h.items():
            for i in ids:
                if str(k).lower() == i.lower() and isinstance(v, int):
                    counts[i] += v
    elif isinstance(h, list):
        for r in h:
            pid, ev = (r, "start") if isinstance(r, str) else (r.get("id", ""), str(r.get("event", "start")))
            if "start" in ev.lower():
                for i in ids:
                    if str(pid).lower() == i.lower():
                        counts[i] += 1
    return counts


def idle_report(path, idle_gap):
    rows = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                    rows.append((str(r.get("pkg") or "(none)"), float(r["ts"])))
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
    except OSError:
        return {"present": False, "workers": {}, "mean_idle_s": None}
    by = {}
    for pkg, ts in rows:
        by.setdefault(pkg, []).append(ts)
    workers = {}
    for pkg, ts in sorted(by.items()):
        ts.sort()
        gaps = [b - a for a, b in zip(ts, ts[1:]) if b - a > idle_gap]
        workers[pkg] = {"events": len(ts), "idle_gaps": len(gaps), "idle_s": round(sum(gaps), 1),
                        "mean_idle_s": round(sum(gaps) / len(gaps), 1) if gaps else 0.0}
    means = [w["mean_idle_s"] for w in workers.values()]
    return {"present": True, "workers": workers, "mean_idle_s": round(sum(means) / len(means), 1) if means else None}


def routine(lab, queue_path, history_path="", apply=False, max_parallel=3, idle_gap=120.0, loop_at=3):
    relay = os.path.join(lab, "relay")
    inbox, running, done, later = [md_files(os.path.join(relay, d)) for d in ("inbox", "running", "done", "later")]
    queue = read_json(queue_path, {}).get("queue", [])
    ids = [q["id"] for q in queue if isinstance(q, dict) and q.get("id")]
    counts = start_counts(ids, os.path.join(lab, "logs", "orchestrator.log"), history_path)
    busy = len(inbox) + len(running)
    free = max(0, max_parallel - busy)
    loops, requeue, skipped = [], [], []
    for i in ids:
        if counts[i] >= loop_at:
            loops.append({"id": i, "starts": counts[i]})
            continue
        if any(has_id(n, i) for n in inbox + running + done):
            continue
        cands = [n for n in later if has_id(n, i)]
        if not cands:
            continue
        if len(requeue) < free:
            requeue.append({"id": i, "file": cands[0]})
        else:
            skipped.append({"id": i, "reason": "parallel cap %d reached" % max_parallel})
    moved = []
    if apply:
        os.makedirs(os.path.join(relay, "inbox"), exist_ok=True)
        for r in requeue:
            dst = os.path.join(relay, "inbox", r["file"])
            if os.path.exists(dst):
                continue
            shutil.move(os.path.join(relay, "later", r["file"]), dst)
            moved.append(r["file"])
    return {"tool": "pm_routine", "applied": bool(apply), "max_parallel": max_parallel,
            "inbox": len(inbox), "running": len(running), "done": len(done), "free_slots": free,
            "LOOP": loops, "requeue": requeue, "moved": moved, "skipped": skipped,
            "idle": idle_report(os.path.join(lab, "logs", "cod-activity.jsonl"), idle_gap)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("lab")
    ap.add_argument("--queue", default=os.path.join(ROOT, "QUEUE.json"))
    ap.add_argument("--history", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-parallel", type=int, default=3)
    ap.add_argument("--idle-gap", type=float, default=120.0)
    ap.add_argument("--loop-at", type=int, default=3)
    a = ap.parse_args(argv)
    rep = routine(os.path.abspath(a.lab), a.queue, a.history, a.apply, a.max_parallel, a.idle_gap, a.loop_at)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    for l in rep["LOOP"]:
        print("LOOP %s started %d times: not requeued" % (l["id"], l["starts"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
