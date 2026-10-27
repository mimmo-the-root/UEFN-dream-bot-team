#!/usr/bin/env python3
"""Stopwatch for the demo (for the promo video). Writes Claude/docs/DEMO-TIMER.md, which the Docs page reads.
  python demo_timer.py start [--mode auto|interactive]   # starts at the beginning of the demo
  python demo_timer.py phase "label"                     # a new phase starts (the one before is closed as a lap)
  python demo_timer.py mark "label"                      # a lap: the running phase is finished
  python demo_timer.py stop                              # everything is ready: stops the clock
  python demo_timer.py status | report
Exit 1 on a misuse (stop without start, start while running)."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")
P = os.path.join(DOCS, "DEMO-TIMER.md")

def load():
    try:
        t = open(P, encoding="utf-8").read()
        a = t.index("<!-- data:") + 10
        return json.loads(t[a:t.index(" -->", a)])
    except Exception:
        return None

def fmt(s):
    s = int(round(s)); return "%d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60)

def save(d):
    os.makedirs(DOCS, exist_ok=True)
    end = d.get("end") or time.time()
    out = ["# Demo timer", "", "<!-- data:%s -->" % json.dumps(d), "",
           "- Mode: %s" % d["mode"], "- State: %s" % ("stopped" if d.get("end") else "running"),
           "- Total: %s" % fmt(end - d["start"]), "- Phase: %s" % (d.get("phase") or {}).get("label", "-"), "", "| Step | At | Lap |", "|---|---|---|"]
    prev = d["start"]
    for m in d["marks"]:
        out.append("| %s | %s | %s |" % (m["label"].replace("|", "/"), fmt(m["ts"] - d["start"]), fmt(m["ts"] - prev)))
        prev = m["ts"]
    open(P, "w", encoding="utf-8").write("\n".join(out) + "\n")

def main(a):
    cmd = a[0] if a else "status"; d = load()
    if cmd == "start":
        if d and not d.get("end"):
            print("Refused: the demo timer is already running (stop it first)"); return 1
        mode = a[a.index("--mode") + 1] if "--mode" in a and a.index("--mode") + 1 < len(a) else "interactive"
        save({"mode": mode, "start": time.time(), "end": None, "marks": [], "phase": None}); print("demo timer started (%s)" % mode); return 0
    if cmd == "phase":
        if not d or d.get("end"):
            print("Refused: the demo timer is not running"); return 1
        now = time.time()
        if d.get("phase"):
            d["marks"].append({"label": d["phase"]["label"], "ts": now})
        d["phase"] = {"label": " ".join(a[1:]) or "phase", "start": now}
        save(d); print("phase: %s" % d["phase"]["label"]); return 0
    if cmd in ("mark", "stop"):
        if not d or d.get("end"):
            print("Refused: the demo timer is not running"); return 1
        now = time.time()
        if cmd == "mark":
            d["marks"].append({"label": " ".join(a[1:]) or (d.get("phase") or {}).get("label", "step"), "ts": now}); d["phase"] = None
        else:
            if d.get("phase"):
                d["marks"].append({"label": d["phase"]["label"], "ts": now}); d["phase"] = None
            d["end"] = now
        save(d); print("%s: %s" % (cmd, fmt(now - d["start"]))); return 0
    if not d:
        print("no demo timer yet"); return 0
    end = d.get("end") or time.time()
    print("%s %s (%s), %d steps" % ("stopped" if d.get("end") else "running", fmt(end - d["start"]), d["mode"], len(d["marks"])))
    if cmd == "report": print(open(P, encoding="utf-8").read())
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
