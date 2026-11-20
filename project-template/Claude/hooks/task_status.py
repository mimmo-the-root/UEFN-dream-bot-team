#!/usr/bin/env python3
"""Deterministic status flip for ROADMAP.md rows (no model needed).
Usage: python Claude/hooks/task_status.py T-015 "In progress" ["short note"] [--pct 40]
(--pct writes "40% - note" in front of the note; the console shows it as a progress bar on the task)
Allowed: "To do", "In progress" (always with --pct), "Blocked", "Done" (Done only with --gate-pass, set by the gate/planner-docs).
Milestones for --pct: 10 started, 30 code written, 60 test written, 80 test passing, 90 gate running, 100 only with Done --gate-pass.
Keeps the row, only rewrites the Status cell (3rd column), keeps rows ordered In progress, Blocked, To do, Done
inside the tasks table, then runs docs_lint. Logs one line in Claude/logs/task-status.log.

Batch mode: python Claude/hooks/task_status.py --batch FILE
FILE contains one update per line: ID|status|note|pct|gate (gate=1 for --gate-pass)
Locks the roadmap once, applies all, runs lint once, logs each line. Bad lines are reported and others still apply."""
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

def _apply_update(L, tid, st, note, pct, gate_pass):
    """Apply a single update to the roadmap lines. Returns (hit, error_msg)."""
    if st not in OK:
        return False, "status must be one of " + str(OK)
    if st == "In progress" and pct is None:
        return False, "In progress needs --pct (milestones: 10 started, 30 code written, 60 test written, 80 test passing, 90 gate running; 100 only with Done --gate-pass)"
    if st == "Done" and not gate_pass:
        return False, "Done needs --gate-pass (only the gate / planner-docs)"
    hit = False
    for i, l in enumerate(L):
        if l.startswith("| %s |" % tid):
            c = l.split("|")
            note_text = ("%d%%" % pct) + ((" - " + note) if note else "") if pct is not None else ((" - " + note) if note else "")
            c[3] = " %s%s " % (st, (" - " + note_text) if note_text else "")
            L[i] = "|".join(c)
            hit = True
    if not hit:
        return False, None  # task not found is not an error for single mode (task may not exist yet)
    return True, None

def _reorder_rows(L):
    """Keep T-rows ordered by status then id."""
    idx = [i for i, l in enumerate(L) if re.match(r"\| T-\d+ \|", l)]
    if idx and idx == list(range(idx[0], idx[-1] + 1)):
        rows = [L[i] for i in idx]
        rows.sort(key=lambda r: (RANK[bucket(r.split("|")[3])], int(re.search(r"T-(\d+)", r).group(1))))
        L[idx[0]:idx[-1] + 1] = rows

def _flag_on(flag="task_status_log"):
    """debug.<flag> in Claude/config/kit-settings.json; default on when the file or key is missing or broken."""
    try:
        import json
        with open(os.path.join(HERE, "..", "config", "kit-settings.json"), encoding="utf-8") as f:
            return json.load(f).get("debug", {}).get(flag, True) is not False
    except Exception:
        return True

def _log_update(tid, st, note, pct):
    """Log a single update (skipped when debug.task_status_log is off)."""
    if not _flag_on():
        return
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    note_text = ("%d%%" % pct) + ((" - " + note) if note else "") if pct is not None else ((" - " + note) if note else "")
    open(LOG, "a", encoding="utf8").write("%s %s -> %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), tid, st, note_text))

def _run_lint():
    """Run docs_lint and return (success, output)."""
    r = subprocess.run([sys.executable, os.path.join(HERE, "docs_lint.py")], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()

def _main_batch(batch_file):
    """Process batch file with multiple updates."""
    if not os.path.exists(batch_file):
        print("batch file not found:", batch_file)
        return 2

    # Read all updates from batch file
    updates = []
    with open(batch_file, encoding="utf8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) != 5:
                print("line %d: bad format (need 5 fields ID|status|note|pct|gate), got: %s" % (line_num, line))
                continue
            tid, st, note, pct_str, gate_str = parts
            tid = tid.strip()
            st = st.strip()
            note = note.strip()
            try:
                pct = int(pct_str) if pct_str.strip() else None
            except ValueError:
                print("line %d: invalid pct '%s'" % (line_num, pct_str))
                continue
            gate_pass = gate_str.strip() == "1"
            updates.append((tid, st, note, pct, gate_pass))

    if not updates:
        print("no valid updates in batch file")
        return 0

    # Acquire lock once
    lk = _lock()
    if not lk:
        print("could not acquire lock")
        return 1

    try:
        L = open(ROAD, encoding="utf8").read().split("\n")
        errors = []
        applied = 0

        for tid, st, note, pct, gate_pass in updates:
            hit, err = _apply_update(L, tid, st, note, pct, gate_pass)
            if hit:
                _log_update(tid, st, note, pct)
                applied += 1
            else:
                errors.append("%s: %s" % (tid, err))

        # Reorder rows once
        _reorder_rows(L)

        # Write roadmap once
        open(ROAD, "w", encoding="utf8").write("\n".join(L))

        # Run lint once
        lint_ok, lint_out = _run_lint()
        if lint_out:
            print(lint_out)

        # Report errors
        if errors:
            print("ERRORS:")
            for e in errors:
                print("  " + e)

        print("Applied %d/%d updates" % (applied, len(updates)))
        return 0 if lint_ok else 1
    finally:
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
    gate_pass = "--gate-pass" in rest
    # Validate status and gate requirements (don't check task existence here)
    if st not in OK:
        print("status must be one of", OK); return 2
    if st == "In progress" and pct is None:
        print("In progress needs --pct (the console shows it). Milestones: 10 started, 30 code written, "
              "60 test written, 80 test passing, 90 gate running; 100 only with Done --gate-pass."); return 2
    if st == "Done" and not gate_pass:
        print("Done needs --gate-pass (only the gate / planner-docs)"); return 2
    L = open(ROAD, encoding="utf8").read().split("\n")
    hit, err = _apply_update(L, tid, st, note, pct, gate_pass)
    if not hit:
        print("task not found:", tid); return 1
    _log_update(tid, st, note, pct)
    _reorder_rows(L)
    open(ROAD, "w", encoding="utf8").write("\n".join(L))
    lint_ok, lint_out = _run_lint()
    if lint_out:
        print(lint_out)
    return 0 if lint_ok else 1


def main(a):
    # Batch mode
    if a and a[0] == "--batch":
        if len(a) != 2:
            print("usage: task_status.py --batch FILE")
            return 2
        return _main_batch(a[1])
    lk = _lock()
    try:
        return _main(a)
    finally:
        if lk:
            try: os.remove(lk)
            except OSError: pass

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
