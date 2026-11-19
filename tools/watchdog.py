#!/usr/bin/env python3
"""Watchdog for Cod (T-111). Called by a schedule every 5 minutes. It reads FILES only, never the terminal of Cod.

Looks at: LAB/relay/inbox, LAB/relay/running, LAB/logs/cod-activity.jsonl (written by hooks/cod_activity.py) and the mtime of
LAB/plan/FEEDBACK-FROM-COD.md.
  - inbox empty                                  -> logs IDLE
  - something in running, or Cod active < --idle-min minutes ago -> busy, does nothing
  - inbox has packages, running empty, no activity for --idle-min minutes -> starts ONE non-interactive run for the oldest package
    (--run-cmd; {do} = the package "do:" text, {id} = package id, {file} = package path) and logs 'time | started pkg-N'
It never starts a second run within --idle-min minutes of its own last start. No answer from an owner is ever waited for.
Also: counts classifier blocks (last hour) and idle minutes in LAB/logs/watchdog.log; after 3 blocks in one hour it appends one
line to LAB/plan/PROBLEMS-FROM-COD.md (at most once per hour); writes LAB/plan/STATUS.md (max 15 lines).

Usage: watchdog.py [--lab DIR] [--run-cmd "claude -p {do} --permission-mode acceptEdits"] [--idle-min 10] [--dry-run]
LAB defaults to $UEFN_LAB, else $CLAUDE_PROJECT_DIR/Claude, else ./Claude. Exit code is always 0 unless the arguments are wrong.
Stdlib only.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time

DEFAULT_RUN_CMD = "claude -p {do} --permission-mode acceptEdits"


def now_str(t=None):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() if t is None else t))


def list_pkgs(d):
    try:
        return sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n)) and n.lower().endswith(".md") and not n.startswith("."))
    except OSError:
        return []


def read_text(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def package_do(path):
    """The text of the 'do:' field of a package (front matter style), up to the next 'key:' line. Falls back to a pointer to the file."""
    lines = read_text(path).splitlines()
    out, on = [], False
    for ln in lines:
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", ln)
        if on and m and m.group(1).lower() != "do":
            break
        if m and m.group(1).lower() == "do":
            on = True
            out.append(m.group(2))
        elif on:
            out.append(ln)
    text = "\n".join(out).strip()
    return text or "Read and carry out the relay package %s" % path


def read_activity(path):
    rows = []
    for ln in read_text(path).splitlines()[-2000:]:
        try:
            r = json.loads(ln)
            if isinstance(r, dict):
                rows.append(r)
        except ValueError:
            pass
    return rows


def mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0.0


def load_state(p):
    try:
        with open(p, encoding="utf-8") as f:
            s = json.load(f)
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def append(path, line):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line.rstrip("\n") + "\n")


def last_committed(lab):
    for ln in reversed(read_text(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md")).splitlines()):
        if "COMMITTED" in ln:
            return " ".join(ln.split())[:200]
    return "none"


def router_mode(lab):
    for n in ("routing.json", "router-mode.json", "router-state.json"):
        try:
            with open(os.path.join(lab, "logs", n), encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and d.get("mode"):
                return str(d["mode"])
        except (OSError, ValueError):
            pass
    t = read_text(os.path.join(lab, "logs", "router-mode.txt")).strip()
    return t.splitlines()[0][:40] if t else ""


def start_run(cmd_template, pkg_path, cwd):
    pid = os.path.splitext(os.path.basename(pkg_path))[0]
    do = package_do(pkg_path)
    argv = [tok.replace("{do}", do).replace("{id}", pid).replace("{file}", pkg_path) for tok in shlex.split(cmd_template)]
    kw = {"cwd": cwd, "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    subprocess.Popen(argv, **kw)
    return pid


def run(lab, run_cmd=DEFAULT_RUN_CMD, idle_min=10, dry_run=False, now=None):
    now = time.time() if now is None else now
    inbox = list_pkgs(os.path.join(lab, "relay", "inbox"))
    running = list_pkgs(os.path.join(lab, "relay", "running"))
    act_path = os.path.join(lab, "logs", "cod-activity.jsonl")
    fb_path = os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md")
    log_path = os.path.join(lab, "logs", "watchdog.log")
    state_path = os.path.join(lab, "logs", "watchdog-state.json")
    st = load_state(state_path)
    rows = read_activity(act_path)
    last_act = max([mtime(act_path), mtime(fb_path)] + [float(r.get("ts", 0) or 0) for r in rows[-1:]])
    quiet_min = (now - last_act) / 60.0 if last_act else 9999.0
    blocks_1h = sum(1 for r in rows if r.get("blocked") and now - float(r.get("ts", 0) or 0) <= 3600)
    recent_block = bool(rows) and bool(rows[-1].get("blocked")) and now - float(rows[-1].get("ts", 0) or 0) <= idle_min * 60
    since_start = (now - float(st.get("last_start", 0) or 0)) / 60.0

    if running or quiet_min < idle_min or since_start < idle_min:
        cod = "blocked" if recent_block else "busy"
    else:
        cod = "idle"
    if cod == "blocked" and not running and quiet_min >= idle_min:
        cod = "idle"

    # idle minutes: time since the previous run counts only while Cod was idle at that run
    gap = min(max((now - float(st.get("last_run", now))) / 60.0, 0.0), idle_min) if st.get("last_run") else 0.0
    idle_total = int(st.get("idle_minutes", 0) or 0) + (int(round(gap)) if st.get("last_cod") == "idle" else 0)

    action = ""
    if not inbox:
        action = "IDLE (inbox empty)"
    elif cod == "busy" or cod == "blocked":
        action = "none (Cod %s)" % cod
    else:
        pkg_path = os.path.join(lab, "relay", "inbox", inbox[0])
        if dry_run:
            action = "would start %s" % os.path.splitext(inbox[0])[0]
        else:
            try:
                pid = start_run(run_cmd, pkg_path, os.path.dirname(os.path.abspath(lab)))
                action = "started %s" % pid
                st["last_start"] = now
                st["last_pkg"] = pid
                cod = "busy"
            except Exception as e:
                action = "START FAILED %s: %s" % (inbox[0], str(e)[:100])

    line = "%s | %s | cod=%s inbox=%d running=%d quiet_min=%d blocks_1h=%d idle_min_total=%d" % (
        now_str(now), action, cod, len(inbox), len(running), min(int(quiet_min), 9999), blocks_1h, idle_total)
    append(log_path, line)

    if blocks_1h >= 3 and now - float(st.get("last_problem", 0) or 0) > 3600:
        append(os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md"),
               "%s | watchdog | %d classifier/permission blocks in the last hour (see logs/cod-activity.jsonl) | none, watchdog only counts | "
               "look at the blocked tools and widen the allow list or change the package plan" % (now_str(now), blocks_1h))
        append(log_path, "%s | PROBLEM raised: %d blocks in one hour" % (now_str(now), blocks_1h))
        st["last_problem"] = now

    st["last_run"] = now
    st["last_cod"] = cod
    st["idle_minutes"] = idle_total
    if not dry_run:
        try:
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(st, f)
        except OSError:
            pass

    status = ["# STATUS (written by tools/watchdog.py; read this, not the terminal of Cod)",
              "time: %s" % now_str(now),
              "cod: %s (last activity %s min ago)" % (cod, "?" if quiet_min >= 9999 else int(quiet_min)),
              "inbox: %d  %s" % (len(inbox), ", ".join(os.path.splitext(n)[0] for n in inbox[:3]) + (" ..." if len(inbox) > 3 else "")),
              "running: %d  %s" % (len(running), ", ".join(os.path.splitext(n)[0] for n in running[:3])),
              "last watchdog action: %s" % action,
              "blocks in last hour: %d" % blocks_1h,
              "last COMMITTED: %s" % last_committed(lab)]
    rm = router_mode(lab)
    if rm:
        status.append("router mode: %s" % rm)
    try:
        sp = os.path.join(lab, "plan", "STATUS.md")
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        with open(sp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(status[:15]) + "\n")
    except OSError:
        pass
    return action, cod


def main(argv=None):
    ap = argparse.ArgumentParser(description="Starts one non-interactive Cod run when work is queued and Cod is idle.")
    ap.add_argument("--lab", default=os.environ.get("UEFN_LAB") or os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), "Claude"))
    ap.add_argument("--run-cmd", default=DEFAULT_RUN_CMD, help="command line; {do}, {id}, {file} are replaced")
    ap.add_argument("--idle-min", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        action, cod = run(a.lab, a.run_cmd, a.idle_min, a.dry_run)
        print("%s | cod=%s" % (action, cod))
    except Exception as e:
        print("watchdog error: %s" % str(e)[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
