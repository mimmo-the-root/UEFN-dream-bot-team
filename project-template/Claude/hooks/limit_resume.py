#!/usr/bin/env python3
"""Cod continues by itself, in the SAME session, after a usage limit (v1.123.19).

Claude Code stops at the 5-hour or the weekly limit and waits for a person. The StopFailure hook (matcher rate_limit) runs
`limit_resume.py hook --pid <claude process>`: it records the limit in Claude/relay/outbox/LIMIT.json and starts ONE detached watcher.
The watcher waits for the reset and then types a short "continue" message into the console of that same Claude Code process
(limit-wake.ps1: the Windows console input of the process, so it needs no focus and works in any tab or window). It then checks that the
session really moved (its transcript changed) and, if not, tries again every few minutes, with no limit on the number of tries, until it works,
the session is closed, or the owner switches it off. It opens no other window.

Usage: limit_resume.py hook [--pid N] < payload.json   |   limit_resume.py watch <project dir>   |   limit_resume.py status <project dir>
Off switch: create the file Claude/relay/NO-RESUME. Settings (optional) in Claude/relay/RESUME.json:
  {"prompt": "...", "extra_wait_seconds": 90, "retry_seconds": 300, "unknown_reset_seconds": 600}"""
import json, os, re, subprocess, sys, time, datetime

DEFAULT_PROMPT = ("The usage limit has reset. Continue exactly where you stopped: finish the task in progress, then go on with the next open task "
                  "of Claude/docs/ROADMAP.md. Keep working without waiting for me: I am away. Do not redo work that is Done.")
VERIFY_SECONDS = 150


def _dirs(project):
    r = os.path.join(project, "Claude", "relay")
    return r, os.path.join(r, "outbox", "LIMIT.json"), os.path.join(project, "Claude", "logs", "limit-resume.log")


def _log(project, msg):
    try:
        lg = _dirs(project)[2]
        os.makedirs(os.path.dirname(lg), exist_ok=True)
        with open(lg, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def _read_json(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _write_json(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, p)


def pid_alive(pid):
    """Is this process running? (os.kill(pid, 0) must NOT be used: on Windows it ends the process.)"""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, SystemError):
        return False


def parse_reset_text(text, now=None):
    """'resets 9pm', 'resets at 11:30 PM', 'resets 21:00' -> epoch seconds of the next such local time, else None."""
    now = now or time.time()
    m = re.search(r"reset[s]?\s*(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*([ap]m)?", text or "", re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
    if ap == "pm" and h < 12:
        h += 12
    if ap == "am" and h == 12:
        h = 0
    if h > 23 or mi > 59:
        return None
    t = datetime.datetime.fromtimestamp(now).replace(hour=h, minute=mi, second=0, microsecond=0)
    if t.timestamp() <= now:
        t += datetime.timedelta(days=1)
    return t.timestamp()


def find_reset(payload, now=None):
    """The reset time (epoch seconds) from the hook payload, else from the end of the transcript, else None."""
    now = now or time.time()
    for k in ("resets_at", "resetsAt"):
        v = payload.get(k)
        if isinstance(v, (int, float)) and v > now - 60:
            return float(v) / (1000.0 if v > 1e12 else 1.0)
    for k in ("error_message", "error_details", "message"):
        r = parse_reset_text(str(payload.get(k) or ""), now)
        if r:
            return r
    tp = payload.get("transcript_path")
    if tp and os.path.isfile(tp):
        try:
            with open(tp, "rb") as f:
                f.seek(0, 2)
                f.seek(max(0, f.tell() - 60000))
                tail = f.read().decode("utf-8", "replace")
        except OSError:
            tail = ""
        for m in reversed(list(re.finditer(r"\"(?:resetsAt|resets_at)\"\s*:\s*(\d{9,13})", tail))):
            v = float(m.group(1))
            v = v / 1000.0 if v > 1e12 else v
            if v > now - 60:
                return v
        r = parse_reset_text(tail[-4000:], now)
        if r:
            return r
    return None


def _settings(project):
    d = _read_json(os.path.join(_dirs(project)[0], "RESUME.json"), {})
    return d if isinstance(d, dict) else {}


def _watcher_alive(project):
    d = _read_json(os.path.join(_dirs(project)[0], "limit-watch.lock"), {})
    return bool(d.get("pid")) and time.time() - d.get("ts", 0) < 900 and pid_alive(d.get("pid"))


def hook(stdin_text, claude_pid=None, now=None, spawn=True):
    """StopFailure: record the limit and start the watcher. Never raises, never blocks."""
    now = now or time.time()
    try:
        payload = json.loads(stdin_text or "{}")
    except ValueError:
        return {"ok": False, "why": "bad payload"}
    if str(payload.get("error_type") or payload.get("error") or "") not in ("rate_limit", "429"):
        return {"ok": False, "why": "not a rate limit"}
    project = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    rd, lim, _ = _dirs(project)
    if os.path.isfile(os.path.join(rd, "NO-RESUME")):
        return {"ok": False, "why": "NO-RESUME"}
    prev = _read_json(lim, {})
    # sub-agents can fire many StopFailure for one limit: one record, one watcher
    if prev.get("state") == "waiting" and _watcher_alive(project):
        return {"ok": True, "why": "already waiting"}
    reset = find_reset(payload, now)
    rec = {"state": "waiting", "hit_at": now, "hit_at_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
           "resets_at": reset, "resets_at_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset)) if reset else "unknown (trying every 10 minutes)",
           "session_id": payload.get("session_id"), "transcript_path": payload.get("transcript_path"),
           "claude_pid": int(claude_pid) if claude_pid else prev.get("claude_pid"), "wakes": 0}
    _write_json(lim, rec)
    _log(project, "limit hit; resets %s; session process %s" % (rec["resets_at_text"], rec["claude_pid"]))
    if spawn:
        _spawn_watcher(project)
    return {"ok": True, "record": rec}


def _spawn_watcher(project):
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    try:
        p = subprocess.Popen([sys.executable or "python", os.path.abspath(__file__), "watch", project], **kw)
        _write_json(os.path.join(_dirs(project)[0], "limit-watch.lock"), {"pid": p.pid, "ts": time.time()})
    except OSError as e:
        _log(project, "could not start the watcher: %s" % e)


def _transcript_mtime(rec):
    try:
        return os.path.getmtime(rec["transcript_path"]) if rec.get("transcript_path") else 0
    except OSError:
        return 0


def wake_command(pid, text):
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "limit-wake.ps1")
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-TargetPid", str(int(pid)), "-Text", text]


def _run_wake(cmd):
    try:
        r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:]
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)


def watch(project, sleep=time.sleep, now_fn=time.time, wake=None, alive=None):
    """Wait for the reset, type the continue message into the session, check it moved, retry forever. Returns the final state."""
    rd, lim, _ = _dirs(project)
    wake = wake or (lambda pid, text: _run_wake(wake_command(pid, text)))
    alive = alive or pid_alive
    beat = lambda: _write_json(os.path.join(rd, "limit-watch.lock"), {"pid": os.getpid(), "ts": now_fn()})
    beat()
    next_try = None
    while True:
        rec = _read_json(lim, {})
        if rec.get("state") != "waiting":
            return rec.get("state", "gone")
        if os.path.isfile(os.path.join(rd, "NO-RESUME")) or os.path.isfile(os.path.join(rd, "STOP")):
            rec["state"] = "cancelled"; _write_json(lim, rec); _log(project, "cancelled (NO-RESUME or STOP)")
            return "cancelled"
        if not rec.get("claude_pid") or not alive(rec["claude_pid"]):
            rec["state"] = "session-closed"; _write_json(lim, rec)
            _log(project, "the Claude Code session is closed (process %s): nothing to continue; the next session starts /relay by itself" % rec.get("claude_pid"))
            return "session-closed"
        st = _settings(project)
        reset = rec.get("resets_at")
        if next_try is None:
            next_try = (reset + int(st.get("extra_wait_seconds", 90))) if reset else rec["hit_at"] + int(st.get("unknown_reset_seconds", 600))
        left = next_try - now_fn()
        if left > 0:
            sleep(min(left, 30)); beat()
            continue
        if _transcript_mtime(rec) > max(rec["hit_at"], reset or 0) + 30:
            rec["state"] = "resumed-by-owner"; _write_json(lim, rec); _log(project, "the session already moved after the limit: nothing to do")
            return rec["state"]
        t0 = now_fn()
        ok, out = wake(rec["claude_pid"], st.get("prompt") or DEFAULT_PROMPT)
        rec["wakes"] = rec.get("wakes", 0) + 1; rec["last_wake_text"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0))
        _log(project, "wake %d: %s %s" % (rec["wakes"], "typed" if ok else "FAILED", out))
        _write_json(lim, rec)
        waited = 0
        while ok and waited < VERIFY_SECONDS and _transcript_mtime(rec) <= t0:
            sleep(10); waited += 10; beat()
        if ok and _transcript_mtime(rec) > t0:
            rec["state"] = "resumed"; rec["resumed_at"] = now_fn(); _write_json(lim, rec)
            _log(project, "the session moved: resumed")
            return "resumed"
        # no sign of life: still limited, or the text did not reach the session. Try again later, with no cap on the tries.
        next_try = now_fn() + int(st.get("retry_seconds", 300))


def status(project):
    rd, lim, _ = _dirs(project)
    rec = _read_json(lim, {})
    return "\n".join(["limit record: %s" % (json.dumps(rec) if rec else "none"), "watcher alive: %s" % _watcher_alive(project),
                      "off switch (NO-RESUME): %s" % os.path.isfile(os.path.join(rd, "NO-RESUME"))])


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a and a[0] == "hook":
            pid = a[a.index("--pid") + 1] if "--pid" in a and a.index("--pid") + 1 < len(a) else None
            print(json.dumps(hook(sys.stdin.read(), claude_pid=pid)))
        elif len(a) > 1 and a[0] == "watch":
            watch(a[1])
        elif len(a) > 1 and a[0] == "status":
            print(status(a[1]))
        else:
            print(__doc__)
    except Exception as e:  # a hook must never break the session
        print(json.dumps({"ok": False, "why": str(e)}))
    sys.exit(0)
