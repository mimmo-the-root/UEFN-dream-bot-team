#!/usr/bin/env python3
"""Deterministic status flip for ROADMAP.md rows (no model needed).
Usage: python Claude/hooks/task_status.py T-015 "In progress" ["short note"] [--pct 40]
(--pct writes "40% - note" in front of the note; the console shows it as a progress bar on the task)
Allowed: "To do", "In progress", "Blocked", "Done" (Done only with --gate-pass, set by the gate/planner-docs).
Keeps the row, only rewrites the Status cell (3rd column), keeps rows ordered In progress, Blocked, To do, Done
inside the tasks table, then runs docs_lint. Logs one line in Claude/logs/task-status.log."""
import os, re, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROAD = os.path.join(HERE, "..", "docs", "ROADMAP.md")
LOG = os.path.join(HERE, "..", "logs", "task-status.log")
OK = ("To do", "In progress", "Blocked", "Done")
RANK = {"In progress": 0, "Blocked": 1, "To do": 2, "Done": 3}

def bucket(cell):
    for k in OK:
        if cell.strip().lower().startswith(k.lower()):
            return k
    return "To do"

def _lock():
    lk = ROAD + ".lock"
    for _ in range(100):
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd); return lk
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lk) > 30: os.remove(lk)  # stale lock
            except OSError: pass
            time.sleep(0.1)
    return None

def main(a):
    lk = _lock()
    try:
        return _main(a)
    finally:
        if lk:
            try: os.remove(lk)
            except OSError: pass

def _main(a):
    if len(a) < 2:
        print(__doc__); return 2
    tid, st = a[0], a[1]
    rest = list(a[2:]); pct = None
    if "--pct" in rest:
        k = rest.index("--pct")
        try: pct = max(0, min(100, int(rest[k + 1])))
        except (IndexError, ValueError): print("--pct needs a number 0-100"); return 2
        del rest[k:k + 2]
    note = " ".join(x for x in rest if x != "--gate-pass")
    if pct is not None: note = ("%d%%" % pct) + ((" - " + note) if note else "")
    if st not in OK:
        print("status must be one of", OK); return 2
    if st == "Done" and "--gate-pass" not in a:
        print("Done needs --gate-pass (only the gate / planner-docs)"); return 2
    L = open(ROAD, encoding="utf8").read().split("\n")
    hit = False
    for i, l in enumerate(L):
        if l.startswith("| %s |" % tid):
            c = l.split("|")
            c[3] = " %s%s " % (st, (" - " + note) if note else "")
            L[i] = "|".join(c); hit = True
    if not hit:
        print("task not found:", tid); return 1
    # keep the T-rows ordered by status then id
    idx = [i for i, l in enumerate(L) if re.match(r"\| T-\d+ \|", l)]
    if idx and idx == list(range(idx[0], idx[-1] + 1)):
        rows = [L[i] for i in idx]
        rows.sort(key=lambda r: (RANK[bucket(r.split("|")[3])], int(re.search(r"T-(\d+)", r).group(1))))
        L[idx[0]:idx[-1] + 1] = rows
    open(ROAD, "w", encoding="utf8").write("\n".join(L))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "a", encoding="utf8").write("%s %s -> %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), tid, st, note))
    r = subprocess.run([sys.executable, os.path.join(HERE, "docs_lint.py")], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    return 0 if r.returncode == 0 else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
