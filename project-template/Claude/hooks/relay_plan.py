#!/usr/bin/env python3
"""relay_plan.py - what the mailbox worker does at this poll (1.124.47). No AI judgement: a fixed rule.

  python Claude/hooks/relay_plan.py            prints one JSON line: close / start / run_now / waiting / active

- close:   commands in running/ whose result is already in outbox/ -> the worker does the shared steps (tests, version,
           CHANGELOG, commit when the command asks for them), moves them to done/, updates HEARTBEAT.
- start:   commands of inbox/ to start NOW as background agents (parallel: yes), up to MAX_PARALLEL running at once,
           lowest number first, skipping those whose `after:` commands are not in done/ yet.
- run_now: one command without `parallel: yes`, run by the worker itself while the background agents go on; one at a time.
           A command that must wait for others says so with `after: 062, 070` in its header.
- waiting: commands held back and why (after: / slots full / a serial command waits for the others).
The worker starts every `start` command in the SAME message (several Agent calls side by side, run_in_background)."""
import json, os, re, sys

MAX_PARALLEL = 5
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def header(path):
    h = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f.read().splitlines()[:20]:
                m = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
                if m:
                    h[m.group(1)] = m.group(2).strip()
    except OSError:
        pass
    return h


def num(name):
    m = re.match(r"^(\d+)", name)
    return m.group(1) if m else None


def plan(relay):
    def ls(d):
        p = os.path.join(relay, d)
        return sorted(n for n in os.listdir(p) if n.endswith(".md")) if os.path.isdir(p) else []
    outbox = os.path.join(relay, "outbox")
    results = {num(n) for n in (os.listdir(outbox) if os.path.isdir(outbox) else []) if n.endswith(".result.md")}
    done = {num(n) for n in ls("done")}
    running = ls("running")
    close = [n for n in running if num(n) in results]
    active = [n for n in running if num(n) not in results]
    out = {"close": close, "start": [], "run_now": None, "waiting": [], "active": active}
    if os.path.isfile(os.path.join(relay, "STOP")):
        out["waiting"].append("STOP: nothing starts")
        return out
    free = MAX_PARALLEL - len(active)
    serial_active = any(header(os.path.join(relay, "running", n)).get("parallel", "no") != "yes" for n in active)
    for n in ls("inbox"):
        h = header(os.path.join(relay, "inbox", n))
        need = [x for x in re.findall(r"\d{3}", h.get("after", "")) if x not in done]
        if need:
            out["waiting"].append("%s: after %s" % (n, ",".join(need)))
            continue
        if h.get("approved") != "yes" and (h.get("risk") == "high" or h.get("needs_owner", "no").startswith("yes")):
            out["waiting"].append("%s: waits for the owner's approved: yes" % n)
            continue
        if h.get("parallel", "no") == "yes":
            if free > 0:
                out["start"].append(n)
                free -= 1
            else:
                out["waiting"].append("%s: %d running, slots full" % (n, MAX_PARALLEL))
        else:
            if not serial_active and out["run_now"] is None:
                out["run_now"] = n   # the worker runs it itself; the background agents go on meanwhile
            else:
                out["waiting"].append("%s: serial, one at a time" % n)
    return out


if __name__ == "__main__":
    print(json.dumps(plan(os.path.join(sys.argv[1] if len(sys.argv) > 1 else ROOT, "Claude", "relay"))))
