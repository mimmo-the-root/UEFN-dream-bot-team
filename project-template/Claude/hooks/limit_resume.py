#!/usr/bin/env python3
"""Cod resumes by itself after a usage limit (v1.123.18).

Claude Code stops when the 5-hour or weekly limit is reached and waits for a person. The StopFailure hook (matcher rate_limit) runs
`limit_resume.py hook`: it records the limit in Claude/relay/outbox/LIMIT.json and starts ONE detached watcher (`watch`). The watcher
waits for the reset time and then opens a NEW Claude Code window in the project with a fixed resume prompt (the work state lives in
ROADMAP.md, STATUS.md and the relay mailbox, so a new session continues from the next task; the SessionStart hook starts /relay).
It never types into an existing window, never touches the editor, and never resumes twice for one limit.

Usage: limit_resume.py hook < payload.json   |   limit_resume.py watch <project dir>   |   limit_resume.py status <project dir>
Off switch: create the file Claude/relay/NO-RESUME. Settings (optional) in Claude/relay/RESUME.json:
  {"prompt": "...", "claude_args": ["--permission-mode", "acceptEdits"], "extra_wait_seconds": 90, "max_per_day": 4}"""
import json, os, re, subprocess, sys, time, datetime

DEFAULT_PROMPT = ("You are Cod, resuming after a usage limit. Read Claude/docs/STATUS.md, Claude/docs/ROADMAP.md and the newest entries of "
                  "Claude/docs/DEVLOG.md. Check what was in progress (a task In progress, a file in Claude/relay/running/) and finish it safely, "
                  "then continue with the next open task in the same order and rules as before. Start the relay worker (/relay). "
                  "Do not redo work that is already Done; read the editor state before repeating anything that changes it. "
                  "One line first: say you resumed after the limit and which task you continue with.")
FALLBACK_WAIT = 30 * 60      # reset time unknown: look again every 30 minutes
MAX_UNKNOWN_TRIES = 4


def _dirs(project):
    r = os.path.join(project, "Claude", "relay")
    return r, os.path.join(r, "outbox", "LIMIT.json"), os.path.join(project, "Claude", "logs", "limit-resume.log")


def _log(project, msg):
    _, _, lg = _dirs(project)
    try:
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
    base = datetime.datetime.fromtimestamp(now)
    t = base.replace(hour=h, minute=mi, second=0, microsecond=0)
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
    lock = os.path.join(_dirs(project)[0], "limit-watch.lock")
    d = _read_json(lock, {})
    pid, ts = d.get("pid"), d.get("ts", 0)
    if not pid or time.time() - ts > 8 * 3600:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, SystemError):
        return False


def hook(stdin_text, now=None, spawn=True):
    """StopFailure: record the limit and start the watcher. Never raises, never blocks."""
    now = now or time.time()
    try:
        payload = json.loads(stdin_text or "{}")
    except ValueError:
        return {"ok": False, "why": "bad payload"}
    if str(payload.get("error_type") or payload.get("error") or "") not in ("rate_limit", "429"):
        return {"ok": False, "why": "not a rate limit"}
    project = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    if not os.path.isdir(os.path.join(project, "Claude")):
        project = os.path.dirname(project) if os.path.isdir(os.path.join(os.path.dirname(project), "Claude")) else project
    rd, lim, _ = _dirs(project)
    if os.path.isfile(os.path.join(rd, "NO-RESUME")):
        return {"ok": False, "why": "NO-RESUME"}
    prev = _read_json(lim, {})
    # one StopFailure per sub-agent can fire many times for one limit: keep the first record while it is still waiting
    if prev.get("state") == "waiting" and prev.get("resets_at", 0) > now - 600 and _watcher_alive(project):
        return {"ok": True, "why": "already waiting"}
    reset = find_reset(payload, now)
    rec = {"state": "waiting", "hit_at": now, "hit_at_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
           "resets_at": reset, "resets_at_text": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reset)) if reset else "unknown (checking every 30 minutes)",
           "session_id": payload.get("session_id"), "transcript_path": payload.get("transcript_path"), "tries": 0}
    _write_json(lim, rec)
    _log(project, "limit hit; resets %s" % rec["resets_at_text"])
    if spawn:
        _spawn_watcher(project)
    return {"ok": True, "record": rec}


def _spawn_watcher(project):
    script = os.path.abspath(__file__)
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    exe = sys.executable or "python"
    try:
        p = subprocess.Popen([exe, script, "watch", project], **kw)
        _write_json(os.path.join(_dirs(project)[0], "limit-watch.lock"), {"pid": p.pid, "ts": time.time()})
    except OSError as e:
        _log(project, "could not start the watcher: %s" % e)


def _resumed_by_someone(rec):
    """True when the session that hit the limit has written to its transcript after the reset: a person already continued."""
    tp, reset = rec.get("transcript_path"), rec.get("resets_at") or rec.get("hit_at", 0)
    try:
        return bool(tp) and os.path.getmtime(tp) > max(reset, rec.get("hit_at", 0)) + 30
    except OSError:
        return False


def launch_command(project, st):
    prompt = st.get("prompt") or DEFAULT_PROMPT
    args = [a for a in (st.get("claude_args") or []) if isinstance(a, str)]
    content = project  # the project folder that holds Claude/ is the Content folder, where Cod works
    if os.name == "nt":
        q = lambda s: "'" + s.replace("'", "''") + "'"
        ps = "Set-Location -LiteralPath %s; claude %s %s" % (q(content), " ".join(q(a) for a in args), q(prompt))
        return ["cmd.exe", "/c", "start", "Cod - resumed", "powershell.exe", "-NoExit", "-NoProfile", "-Command", ps]
    return ["claude"] + args + [prompt]


def _launches_today(project):
    try:
        txt = open(_dirs(project)[2], encoding="utf-8").read()
    except OSError:
        return 0
    return len(re.findall(r"^%s .*resume window opened" % re.escape(time.strftime("%Y-%m-%d")), txt, re.M))


def watch(project, sleep=time.sleep, now_fn=time.time, run=None):
    """Wait for the reset and open ONE new Cod window. Returns the final state string."""
    rd, lim, _ = _dirs(project)
    run = run or (lambda cmd: subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    _write_json(os.path.join(rd, "limit-watch.lock"), {"pid": os.getpid(), "ts": now_fn()})
    while True:
        rec = _read_json(lim, {})
        if rec.get("state") != "waiting":
            return rec.get("state", "gone")
        if os.path.isfile(os.path.join(rd, "NO-RESUME")) or os.path.isfile(os.path.join(rd, "STOP")):
            rec["state"] = "cancelled"; _write_json(lim, rec); _log(project, "cancelled (NO-RESUME or STOP)")
            return "cancelled"
        st = _settings(project)
        reset = rec.get("resets_at")
        target = (reset + int(st.get("extra_wait_seconds", 90))) if reset else rec.get("hit_at", now_fn()) + FALLBACK_WAIT * (rec.get("tries", 0) + 1)
        left = target - now_fn()
        if left > 0:
            sleep(min(left, 30))
            _write_json(os.path.join(rd, "limit-watch.lock"), {"pid": os.getpid(), "ts": now_fn()})
            continue
        if _resumed_by_someone(rec):
            rec["state"] = "resumed-by-owner"; _write_json(lim, rec); _log(project, "the owner already continued: nothing to do")
            return rec["state"]
        if _launches_today(project) >= int(st.get("max_per_day", 4)):
            rec["state"] = "gave-up"; rec["why"] = "max_per_day reached"; _write_json(lim, rec); _log(project, "gave up: too many resumes today")
            return rec["state"]
        try:
            run(launch_command(project, st))
        except OSError as e:
            rec["state"] = "failed"; rec["why"] = str(e); _write_json(lim, rec); _log(project, "could not open the window: %s" % e)
            return "failed"
        _log(project, "resume window opened")
        if not reset:  # unknown reset time: the new session may hit the limit again; its own StopFailure will record a new wait
            rec["tries"] = rec.get("tries", 0) + 1
        rec["state"] = "resumed"; rec["resumed_at"] = now_fn(); _write_json(lim, rec)
        return "resumed"


def status(project):
    rd, lim, lg = _dirs(project)
    rec = _read_json(lim, {})
    out = ["limit record: %s" % (json.dumps(rec) if rec else "none"), "watcher alive: %s" % _watcher_alive(project),
           "off switch (NO-RESUME): %s" % os.path.isfile(os.path.join(rd, "NO-RESUME"))]
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a and a[0] == "hook":
            print(json.dumps(hook(sys.stdin.read())))
        elif len(a) > 1 and a[0] == "watch":
            watch(a[1])
        elif len(a) > 1 and a[0] == "status":
            print(status(a[1]))
        else:
            print(__doc__)
    except Exception as e:  # a hook must never break the session
        print(json.dumps({"ok": False, "why": str(e)}))
    sys.exit(0)
