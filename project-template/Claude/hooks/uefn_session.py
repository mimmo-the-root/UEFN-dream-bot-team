"""uefn_session: read the state of the UEFN editor and, after a crash only, relaunch it (stdlib only, Windows).

Ported and trimmed from KirChuvakov/uefn-mcp-server (MIT): uefn_session.py + win_procs.py. Credit and thanks to that project.

  python uefn_session.py status [--project P] [--no-ports]   read-only: not_running | starting | hub | opening | project_open
                                                              | open_failed | other_project_open | crash_dialog
  python uefn_session.py recover [--project P] [--close-crash-reporter]
  python uefn_session.py set-load-on-startup HomeScreen|LastProject [--dry-run]   (only while UEFN is closed, with backup)

Rule (owner decision 2026-10-16): a RUNNING editor is NEVER closed or killed. `recover` starts the editor only when ALL hold:
  1. no editor process runs;  2. the last run ended in a crash (crash reporter present or fatal marker in the editor log);
  3. opt-in: `auto-recover: yes` in Claude/LAB-PROJECT.txt or UEFN_AUTO_RECOVER=1 (default OFF);
  4. the project is the one that was open before the crash;  5. at most 2 attempts in 30 minutes, then it stops and asks the owner.
Every call is logged to Claude/logs/explore-ledger.jsonl. No mouse or keyboard input is ever simulated: on the HUB the owner opens the project.
"""
import argparse, ctypes, datetime as dt, glob, json, os, re, shutil, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.normpath(os.path.join(HERE, ".."))
LOGS = os.path.join(CLAUDE, "logs")
LEDGER = os.path.join(LOGS, "explore-ledger.jsonl")
ATTEMPTS = os.path.join(LOGS, "uefn-recover-attempts.json")
MARKER = os.path.join(CLAUDE, "LAB-PROJECT.txt")

EDITOR = "UnrealEditorFortnite-Win64-Shipping"
CRASH = "CrashReportClientEditor"
MAX_ATTEMPTS, WINDOW_SEC = 2, 30 * 60
SECTION, LOAD_KEY, LAST_KEY = "/Script/ValkyrieEditor.ValkyrieEditorConfig", "ValkyrieLoadAtStartupMostRecentProject", "LastProjectFileName"
LOAD_VALUES = {"homescreen": "HomeScreen", "hub": "HomeScreen", "lastproject": "LastProject", "mostrecentproject": "LastProject"}
FATAL = re.compile(r"=== Critical error: ===|Fatal error!|Unhandled Exception: EXCEPTION_")
OPENING = re.compile(r"LogValkyrie: Opening project '([^']+)'")
OPENED = re.compile(r"LogValkyrie: Display: Successfully opened project '([^']+)'")
ENGINE = re.compile(r"LogInit: Display: Engine is initialized")
BROWSER = re.compile(r"LogValkyrie: Searching for projects under")
SHUTDOWN = re.compile(r"HttpListener stopping listening on Port|Valkyrie Login Module Shutting down|LogExit: Exiting\.")  # the editor is closing
EXIT = re.compile(r"LogExit: Exiting\.|Log file closed")  # written only by a clean shutdown
OPEN_END = re.compile(r"OpenProject_End - Begin \(bSuccess=(\d)")


# --- paths -------------------------------------------------------------------------------------------------------
def saved_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.environ.get("UEFN_SAVED_DIR") or os.path.join(base, "UnrealEditorFortnite", "Saved")


def log_file():
    return os.path.join(saved_dir(), "Logs", "UnrealEditorFortnite.log")


def settings_file():
    return os.path.join(saved_dir(), "Config", "WindowsEditor", "EditorPerProjectUserSettings.ini")


def _norm(p):
    return os.path.normcase(os.path.normpath(p or ""))


# --- processes (read-only toolhelp snapshot) ------------------------------------------------------------------------
def processes(pattern=""):
    """[{pid, name}] of running processes whose exe name contains `pattern` (case-insensitive). Empty off Windows."""
    if sys.platform != "win32":
        return []
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class PE(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260)]
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.Process32FirstW.argtypes = k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PE)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)
    out = []
    try:
        e = PE()
        e.dwSize = ctypes.sizeof(PE)
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            if pattern.lower() in e.szExeFile.lower():
                out.append({"pid": int(e.th32ProcessID), "name": e.szExeFile})
            ok = k32.Process32NextW(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    return out


def terminate(pid):
    """Stops ONE process. Used only for an orphan crash reporter (never the editor)."""
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k32.OpenProcess(0x0001, False, pid)
    if not h:
        return False
    try:
        return bool(k32.TerminateProcess(h, 1))
    finally:
        k32.CloseHandle(h)


def tcp_open(port, timeout=0.4):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


# --- editor log ---------------------------------------------------------------------------------------------------
def read_text(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return ""
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return ""


def scan_log(text):
    """Pure: project state and crash flag from one editor log. state: none | opening | open | open_failed."""
    last_open = last_ok = fatal = engine = browser = clean = closing = None
    path, ended_bad = None, False
    for n, line in enumerate(text.splitlines()):
        m = OPENING.search(line)
        if m:
            last_open, path, ended_bad = n, m.group(1), False
        m = OPENED.search(line)
        if m:
            last_ok, path = n, m.group(1)
        m = OPEN_END.search(line)
        if m and last_open is not None and m.group(1) == "0":
            ended_bad = True
        if FATAL.search(line):
            fatal = n
        if ENGINE.search(line):
            engine = n
        if BROWSER.search(line):
            browser = n
        if EXIT.search(line):
            clean = n
        if SHUTDOWN.search(line):
            closing = n
    if last_open is not None and (last_ok is None or last_ok < last_open):
        state = "open_failed" if ended_bad else "opening"
    elif last_ok is not None:
        state = "open"
    else:
        state = "none"
    return {"state": state, "path": path, "fatal": fatal is not None, "engine_ready": engine is not None or browser is not None,
            "clean_exit": clean is not None, "closing": closing is not None}


def classify(*, editor_running, crash_dialog, log, wanted_path=None, hub_seen=False):
    """Pure state decision (unit-tested)."""
    if crash_dialog:
        return "crash_dialog"
    if not editor_running:
        return "not_running"
    if log.get("closing") and not log.get("fatal"):
        return "closing"
    s = log["state"]
    if s in ("opening", "open_failed"):
        return s
    if s == "open":
        return "other_project_open" if wanted_path and _norm(log["path"]) != _norm(wanted_path) else "project_open"
    return "hub" if hub_seen else "starting"


def is_crash(*, crash_dialog, log, editor_running=True):
    """The last run ended in a crash: crash reporter present, a fatal marker in the (last) editor log, or - when no editor
    runs - a log that got as far as the engine start but never wrote the clean-shutdown line (the process was killed or hung).
    A normal close writes that line, so a deliberate close is never a crash."""
    if crash_dialog or log.get("fatal"):
        return True
    return bool(not editor_running and log.get("engine_ready") and not log.get("clean_exit"))


# --- settings ini (Load on Startup) -----------------------------------------------------------------------------------
def ini_get(text, section, key):
    inside = False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            inside = s[1:-1].lower() == section.lower()
        elif inside and "=" in s and s.split("=", 1)[0].strip().lower() == key.lower():
            return s.split("=", 1)[1]
    return None


def ini_set(text, section, key, value):
    """Set key=value in [section], keeping other lines and the line endings. Returns (new_text, old_value)."""
    eol = "\r\n" if "\r\n" in text or not text else "\n"
    lines = text.split("\n")
    start = end = None
    for i, raw in enumerate(lines):
        s = raw.strip()
        if start is None:
            if s.lower() == "[%s]" % section.lower():
                start = i
        elif s.startswith("[") and s.endswith("]"):
            end = i
            break
    if start is None:
        sep = "" if not text or text.endswith("\n") else "\n"
        return text + sep + "[%s]%s%s=%s%s" % (section, eol, key, value, eol), None
    end = len(lines) if end is None else end
    for i in range(start + 1, end):
        k, eq, v = lines[i].rstrip("\r").partition("=")
        if eq and k.strip().lower() == key.lower():
            lines[i] = "%s=%s%s" % (k, value, "\r" if lines[i].endswith("\r") else "")
            return "\n".join(lines), v
    lines.insert(start + 1, "%s=%s%s" % (key, value, "\r" if eol == "\r\n" else ""))
    return "\n".join(lines), None


def set_load_on_startup(value, dry_run=False, path=None):
    path = path or settings_file()
    v = LOAD_VALUES.get(re.sub(r"[\s_-]", "", value or "").lower())
    if not v:
        raise ValueError("value must be HomeScreen or LastProject")
    if processes(EDITOR) and not dry_run:
        raise RuntimeError("UEFN is running and rewrites the settings file on exit: close it first (this tool never closes it)")
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        data = b""
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    text = data[len(bom):].decode("utf-8")
    new, old = ini_set(text, SECTION, LOAD_KEY, v)
    res = {"path": path, "old": old, "new": v, "changed": new != text, "dry_run": dry_run}
    if dry_run or new == text:
        return res
    if data:
        res["backup"] = "%s.mcp-bak-%s" % (path, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(path, res["backup"])
    with open(path, "wb") as f:
        f.write(bom + new.encode("utf-8"))
    return res


# --- opt-in, attempts, ledger ------------------------------------------------------------------------------------------
def auto_recover_enabled():
    if os.environ.get("UEFN_AUTO_RECOVER") == "1":
        return True
    for ln in read_text(MARKER).splitlines():
        if ln.lower().startswith("auto-recover:"):
            return ln.split(":", 1)[1].strip().lower() in ("yes", "true", "1", "on")
    return False


def attempts_allowed(history, now, limit=MAX_ATTEMPTS, window=WINDOW_SEC):
    """Pure: True if fewer than `limit` attempts happened in the last `window` seconds."""
    return len([t for t in history if now - t < window]) < limit


def _load_attempts():
    try:
        with open(ATTEMPTS, encoding="utf-8") as f:
            return [float(x) for x in json.load(f)]
    except (OSError, ValueError, TypeError):
        return []


def _save_attempts(items):
    os.makedirs(LOGS, exist_ok=True)
    with open(ATTEMPTS, "w", encoding="utf-8") as f:
        json.dump(items, f)


def _log(rec):
    try:
        os.makedirs(LOGS, exist_ok=True)
        rec = dict(rec, ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), tool="uefn_session")
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


# --- install + launch ------------------------------------------------------------------------------------------------
def find_exe():
    cands = [os.environ.get("UEFN_EDITOR_EXE", "")]
    pd = os.environ.get("ProgramData") or "C:\\ProgramData"
    for item in glob.glob(os.path.join(pd, "Epic", "EpicGamesLauncher", "Data", "Manifests", "*.item")):
        try:
            d = json.loads(read_text(item))
        except ValueError:
            continue
        if d.get("AppName") == "Fortnite_Studio" or str(d.get("LaunchExecutable", "")).lower().endswith("unrealeditorfortnite-win64-shipping.exe"):
            if d.get("InstallLocation") and d.get("LaunchExecutable"):
                cands.append(os.path.join(d["InstallLocation"], d["LaunchExecutable"]))
    if os.environ.get("ProgramFiles"):
        cands.append(os.path.join(os.environ["ProgramFiles"], "Epic Games", "Fortnite", "FortniteGame", "Binaries", "Win64", EDITOR + ".exe"))
    return next((os.path.normpath(c) for c in cands if c and os.path.isfile(c)), None)


def launch(project_path):
    exe = find_exe()
    if not exe:
        raise RuntimeError("UEFN editor exe not found; set UEFN_EDITOR_EXE")
    flags = 0x00000008 | 0x00000200
    for f in (flags | 0x01000000, flags):
        try:
            p = subprocess.Popen([exe, project_path] if project_path else [exe], cwd=os.path.dirname(exe), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=f, close_fds=True)
            return {"exe": exe, "pid": p.pid}
        except OSError:
            continue
    raise RuntimeError("could not start " + exe)


# --- status / recover ---------------------------------------------------------------------------------------------------
def crash_dialog_shown(*, editor_running, reporter, log):
    """Pure. UEFN starts its crash reporter (CrashReportClientEditor) WITH the editor as a watchdog, so the reporter process
    alone is normal, and a closing editor has its ports down while the process is still alive (both verified in the lab,
    2026-10-16). A crash dialog means: the reporter is there AND (the editor log has a fatal marker, OR the editor is gone
    without having written the clean-shutdown line)."""
    if not reporter:
        return False
    if log.get("fatal"):
        return True
    return bool(not editor_running and not log.get("clean_exit"))


def status(project_path=None, probe_ports=True):
    ed, crash = processes(EDITOR), processes(CRASH)
    log = scan_log(read_text(log_file()))  # the log of the last run is also the crash evidence once the editor is gone
    ports = {"toolset_8000": tcp_open(8000), "verse_1962": tcp_open(1962)} if (probe_ports or crash) else {}
    dialog = crash_dialog_shown(editor_running=bool(ed), reporter=bool(crash), log=log)
    out = {"state": classify(editor_running=bool(ed), crash_dialog=dialog, log=log, wanted_path=project_path,
                             hub_seen=log["engine_ready"]),
           "editor_pids": [p["pid"] for p in ed], "crash_reporter_pids": [p["pid"] for p in crash], "open_project": log["path"],
           "last_run_crashed": is_crash(crash_dialog=dialog, log=log, editor_running=bool(ed))}
    if probe_ports:
        out["ports"] = ports
    return out


def recover(project_path=None, close_crash_reporter=False, now=None):
    now = time.time() if now is None else now
    st = status(project_path, probe_ports=False)
    why = None
    if st["editor_pids"]:
        why = "an editor process runs: a live editor is never closed or killed"
    elif not auto_recover_enabled():
        why = "opt-in is off (auto-recover: yes in Claude/LAB-PROJECT.txt, or UEFN_AUTO_RECOVER=1)"
    elif not st["last_run_crashed"]:
        why = "the last run did not end in a crash: not relaunching (ask the owner)"
    else:
        target = project_path or st["open_project"]
        if project_path and st["open_project"] and _norm(project_path) != _norm(st["open_project"]):
            why = "the crashed session had another project open (%s): ask the owner" % st["open_project"]
        elif not target:
            why = "no project known: pass --project"
        elif not attempts_allowed(_load_attempts(), now):
            why = "already %d attempts in the last 30 minutes: stopped, ask the owner" % MAX_ATTEMPTS
    if why:
        res = {"recovered": False, "reason": why, "state": st["state"]}
        _log({"action": "recover", "result": "refused", "reason": why})
        return res
    actions = []
    if st["crash_reporter_pids"]:
        if not close_crash_reporter:
            res = {"recovered": False, "reason": "orphan crash reporter present: pass --close-crash-reporter or ask the owner to close it", "state": st["state"]}
            _log({"action": "recover", "result": "refused", "reason": res["reason"]})
            return res
        actions.append({"stopped_crash_reporter": [p for p in st["crash_reporter_pids"] if terminate(p)]})
    _save_attempts([t for t in _load_attempts() if now - t < WINDOW_SEC] + [now])
    info = launch(project_path or st["open_project"])
    actions.append({"launch": info})
    res = {"recovered": True, "actions": actions, "next": "wait for the project to open (30-90 s); if the state is 'hub', ask the owner to open the project"}
    _log({"action": "recover", "result": "launched", "project": project_path or st["open_project"]})
    return res


def wait_open(project_path=None, timeout=150, interval=5, status_fn=None, sleep=time.sleep, clock=time.time):
    """After a relaunch: poll `status` until the project is open (state project_open) or the timeout. The editor passes through
    starting and hub on its way, and with Load on Startup = LastProject it opens the project by itself (measured in the lab:
    47-48 s after the launch), so a check at 30 s that says 'hub' only means 'not yet'. Returns the last state and the seconds."""
    status_fn = status_fn or (lambda: status(project_path, probe_ports=False))
    t0 = clock()
    seen = []
    while True:
        st = status_fn()
        if not seen or seen[-1] != st["state"]:
            seen.append(st["state"])
        if st["state"] == "project_open" or clock() - t0 >= timeout:
            return {"state": st["state"], "seconds": round(clock() - t0, 1), "states_seen": seen}
        sleep(interval)


def main(argv):
    ap = argparse.ArgumentParser(prog="uefn_session.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--project", default="")
    s.add_argument("--no-ports", action="store_true")
    r = sub.add_parser("recover")
    r.add_argument("--project", default="")
    r.add_argument("--close-crash-reporter", action="store_true")
    r.add_argument("--wait", type=int, default=0, metavar="SEC", help="after the relaunch, wait up to SEC seconds for the project to open")
    l = sub.add_parser("set-load-on-startup")
    l.add_argument("value")
    l.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "status":
            out = status(a.project or None, not a.no_ports)
        elif a.cmd == "recover":
            out = recover(a.project or None, a.close_crash_reporter)
            if out.get("recovered") and a.wait:
                out["opened"] = wait_open(a.project or None, a.wait)
        else:
            out = set_load_on_startup(a.value, a.dry_run)
    except Exception as e:
        print(json.dumps({"error": "%s: %s" % (type(e).__name__, e)}))
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
