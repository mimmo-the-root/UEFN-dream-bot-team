#!/usr/bin/env python3
"""Phase times and cost of a game build (v1.114). Appends to Claude/logs/phase-times.jsonl; prints a report.

  python Claude/hooks/run_log.py start "1 spec"        # open a phase
  python Claude/hooks/run_log.py stop  "1 spec" [--note "text"] [--tokens N]
  python Claude/hooks/run_log.py report                # table: phase, minutes, tokens, notes, total

Tokens come from the sub-agent counts of agent_cost.py when you pass them with --tokens (counts only: the kit never invents a price).
A phase that was started and never stopped is shown as open."""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def log_path(base=None):
    base = base or os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(os.path.join(HERE, "..", ".."))
    d = os.path.join(base, "Claude", "logs") if os.path.isdir(os.path.join(base, "Claude")) else os.path.join(base, "logs")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "phase-times.jsonl")


def add(ev, phase, note="", tokens=0, now=None, base=None):
    with open(log_path(base), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now or time.time(), "ev": ev, "phase": phase, "note": note, "tokens": int(tokens or 0)}) + "\n")


def rows(base=None):
    p, ph, order = log_path(base), {}, []
    try:
        lines = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    except OSError:
        lines = []
    for e in lines:
        k = e["phase"]
        if k not in ph:
            ph[k] = {"phase": k, "start": None, "stop": None, "note": "", "tokens": 0}
            order.append(k)
        if e["ev"] == "start":
            ph[k]["start"] = e["ts"]
        else:
            ph[k]["stop"] = e["ts"]
            ph[k]["note"] = e.get("note", "") or ph[k]["note"]
            ph[k]["tokens"] += e.get("tokens", 0)
    return [ph[k] for k in order]


def report(base=None):
    rs, tot, tk = rows(base), 0.0, 0
    out = ["| Phase | Minutes | Tokens | Note |", "|---|---|---|---|"]
    for r in rs:
        if r["start"] and r["stop"]:
            m = (r["stop"] - r["start"]) / 60.0
            tot += m
            out.append("| %s | %.1f | %s | %s |" % (r["phase"], m, r["tokens"] or "n/a", r["note"]))
        else:
            out.append("| %s | open | n/a | %s |" % (r["phase"], r["note"]))
        tk += r["tokens"]
    out.append("| **Total** | **%.1f** | **%s** | |" % (tot, tk or "n/a"))
    return "\n".join(out)


def main(argv):
    if not argv or argv[0] not in ("start", "stop", "report"):
        print(__doc__)
        return 2
    if argv[0] == "report":
        print(report())
        return 0
    if len(argv) < 2:
        print("Say the phase name.")
        return 2
    note = argv[argv.index("--note") + 1] if "--note" in argv else ""
    tokens = argv[argv.index("--tokens") + 1] if "--tokens" in argv else 0
    add(argv[0], argv[1], note, tokens)
    print("%s: %s" % (argv[0], argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
