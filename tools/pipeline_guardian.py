#!/usr/bin/env python3
"""pipeline_guardian.py - keeps the relay pipeline alive without a Windows scheduler.

Usage: python tools/pipeline_guardian.py supervise [--lab DIR] [--interval-min N]
       python tools/pipeline_guardian.py once [--lab DIR]
       python tools/pipeline_guardian.py status [--lab DIR]
       python tools/pipeline_guardian.py stop [--lab DIR]

supervise runs one cycle every pipeline.interval_min minutes (default 5, 1-60). A cycle runs the
components of pipeline.components in order: orchestrate (--lab LAB --integrate-cmd ""), watchdog,
pm_routine (LAB --apply), the optional dc_auto and the optional second-brain hot update. A step that
raises or exits non-zero is logged and skipped; the loop does not die. STOP in the lab stops the
guardian at the next cycle; pipeline.enabled false turns the pipeline off. A newer VERSION in the
file on disk makes the guardian exit after the current cycle so ensure-pipeline.ps1 starts the new
one. Logs: LAB/logs/pipeline-guardian.log and LAB/logs/pipeline-guardian.json (heartbeat).
Stdlib only. No live LLM, no MCP, no pushes.
"""
import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
import time

VERSION = "1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT, "tools")
HOOKS_DIR = os.path.join(ROOT, "project-template", "Claude", "hooks")
DEFAULT_COMPONENTS = ["orchestrate", "watchdog", "pm_routine", "dc_auto", "brain_hot_update"]
OPTIONAL = ("dc_auto", "brain_hot_update")
STEP_TIMEOUT = 900


def lab_dir(lab=None):
    env_lab = os.environ.get("UEFN_LAB")
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.abspath(lab or env_lab or os.path.join(project, "Claude"))


def log_path(lab):
    return os.path.join(lab, "logs", "pipeline-guardian.log")


def heartbeat_path(lab):
    return os.path.join(lab, "logs", "pipeline-guardian.json")


def stop_path(lab):
    return os.path.join(lab, "STOP")


def append_log(lab, message):
    try:
        p = log_path(lab)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8", newline="\n") as f:
            f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), message))
    except OSError:
        pass


def write_heartbeat(lab, state):
    data = dict(state)
    data["ts"] = time.time()
    data["time"] = datetime.datetime.now().isoformat(timespec="seconds")
    data["version"] = VERSION
    try:
        p = heartbeat_path(lab)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)
    except OSError:
        pass
    return data


def read_heartbeat(lab):
    try:
        with open(heartbeat_path(lab), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def config(lab):
    try:
        if TOOLS_DIR not in sys.path:
            sys.path.insert(0, TOOLS_DIR)
        import kit_config
        enabled = kit_config.get("pipeline.enabled", lab, True)
        interval = kit_config.get("pipeline.interval_min", lab, 5)
        components = kit_config.get("pipeline.components", lab, DEFAULT_COMPONENTS)
    except Exception:
        enabled, interval, components = True, 5, DEFAULT_COMPONENTS
    if not isinstance(interval, int) or isinstance(interval, bool) or not 1 <= interval <= 60:
        interval = 5
    if not isinstance(components, list):
        components = list(DEFAULT_COMPONENTS)
    return enabled is not False, interval, components


def version_of(text):
    m = re.search(r'^VERSION\s*=\s*"([0-9][0-9.]*)"', text, re.M)
    return m.group(1) if m else ""


def disk_version():
    try:
        with open(os.path.abspath(globals().get("__file__", "")), encoding="utf-8") as f:
            return version_of(f.read()) or VERSION
    except OSError:
        return VERSION


def newer_version(found, running=VERSION):
    def parts(v):
        try:
            return tuple(int(x) for x in str(v).split("."))
        except ValueError:
            return (0,)
    return parts(found) > parts(running)


def brain_hot_script(lab):
    names = ("brain_hot_update.py", "brain_hot.py")
    dirs = (os.path.join(lab, "Claude", "hooks"), HOOKS_DIR, os.path.join(ROOT, "hooks"), TOOLS_DIR)
    for d in dirs:
        for name in names:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def resolve_component(component, lab):
    if isinstance(component, str):
        name = component
        script = os.path.join(TOOLS_DIR, name + ".py")
        if name == "orchestrate":
            return name, [sys.executable, script, "--lab", lab, "--integrate-cmd", ""]
        if name == "watchdog":
            return name, [sys.executable, script, "--lab", lab]
        if name == "pm_routine":
            return name, [sys.executable, script, lab, "--apply"]
        if name == "dc_auto":
            return name, [sys.executable, script] if os.path.isfile(script) else None
        if name == "brain_hot_update":
            hot = brain_hot_script(lab)
            return name, [sys.executable, hot, "--lab", lab] if hot else None
        return name, None
    if isinstance(component, dict):
        name = str(component.get("name") or "custom")
        raw = component.get("cmd")
        if isinstance(raw, str):
            cmd = shlex.split(raw)
        elif isinstance(raw, list):
            cmd = [str(x) for x in raw]
        else:
            cmd = []
        cmd = [x.replace("{lab}", lab) for x in cmd]
        return name, cmd or None
    return "unknown", None


def run_cycle(lab, cycle, components, logger=None):
    log = logger or (lambda m: append_log(lab, m))
    results = []
    for component in components:
        name, cmd = resolve_component(component, lab)
        if cmd is None:
            if name not in OPTIONAL and name != "unknown":
                log("cycle %d | %s | skipped (not installed)" % (cycle, name))
            continue
        try:
            r = subprocess.run(cmd, cwd=lab, capture_output=True, text=True, timeout=STEP_TIMEOUT,
                               encoding="utf-8", errors="replace")
            result = "ok" if r.returncode == 0 else "failed (rc=%d)" % r.returncode
        except Exception as e:
            result = "failed (%s)" % type(e).__name__
        log("cycle %d | %s | %s" % (cycle, name, result))
        results.append({"name": name, "result": result})
    return results


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def status_text(lab):
    enabled, interval, _ = config(lab)
    lines = ["Pipeline is enabled." if enabled else "Pipeline is disabled (pipeline.enabled is false)."]
    if enabled:
        if os.path.isfile(stop_path(lab)):
            lines.append("STOP file is present: the guardian will stop at the next cycle.")
        hb = read_heartbeat(lab)
        age = time.time() - float(hb.get("ts", 0) or 0) if isinstance(hb.get("ts", 0), (int, float)) else 10 ** 9
        if pid_alive(hb.get("pid")) and age <= max(interval * 120, 120):
            lines.append("Pipeline guardian is running (pid %s, version %s, last cycle %s)." % (
                hb.get("pid"), hb.get("version", "?"), hb.get("time", "?")))
        else:
            lines.append("Pipeline guardian is not running (no fresh heartbeat).")
        lines.append("Interval: %d minute(s)." % interval)
        lines.append("Log: %s" % log_path(lab))
    return "\n".join(lines)


def stop(lab):
    try:
        with open(stop_path(lab), "w", encoding="utf-8", newline="\n") as f:
            f.write("")
    except OSError as e:
        append_log(lab, "stop failed: %s" % type(e).__name__)
        return 1
    append_log(lab, "stop requested (STOP file created)")
    print("Pipeline stop requested: the guardian stops at the next cycle.")
    return 0


def once(lab):
    enabled, interval, components = config(lab)
    if os.path.isfile(stop_path(lab)):
        print("Pipeline is stopped (STOP file present).")
        return 0
    if not enabled:
        print("Pipeline is disabled (pipeline.enabled is false).")
        return 0
    results = run_cycle(lab, 1, components)
    write_heartbeat(lab, {"pid": os.getpid(), "cycle": 1, "interval_min": interval,
                          "status": "idle", "steps": results})
    failed = sum(1 for r in results if r["result"] != "ok")
    print("Pipeline cycle finished: %d step(s), %d failed." % (len(results), failed))
    return 0


def supervise(lab=None, interval_min=None, sleep=time.sleep, max_cycles=None, clock=time.time):
    lab = lab_dir(lab)
    cycle = 0
    append_log(lab, "guardian v%s on (pid %d, lab %s)" % (VERSION, os.getpid(), lab))
    while max_cycles is None or cycle < max_cycles:
        if os.path.isfile(stop_path(lab)):
            try:
                os.remove(stop_path(lab))
            except OSError:
                pass
            append_log(lab, "guardian off: STOP file found")
            write_heartbeat(lab, {"pid": os.getpid(), "cycle": cycle, "status": "stopped", "steps": []})
            return "stopped"
        enabled, interval, components = config(lab)
        if interval_min is not None and isinstance(interval_min, int) and 1 <= interval_min <= 60:
            interval = interval_min
        if not enabled:
            append_log(lab, "guardian off: pipeline.enabled is false")
            write_heartbeat(lab, {"pid": os.getpid(), "cycle": cycle, "status": "disabled", "steps": []})
            return "disabled"
        cycle += 1
        try:
            results = run_cycle(lab, cycle, components)
        except Exception as e:
            results = []
            append_log(lab, "cycle %d error: %s" % (cycle, type(e).__name__))
        write_heartbeat(lab, {"pid": os.getpid(), "cycle": cycle, "interval_min": interval,
                              "status": "idle", "steps": results})
        found = disk_version()
        if newer_version(found):
            append_log(lab, "hot update: file has %s, running %s: exiting for ensure-pipeline" % (found, VERSION))
            write_heartbeat(lab, {"pid": os.getpid(), "cycle": cycle, "status": "hot-update", "steps": results})
            return "hot-update"
        if max_cycles is None or cycle < max_cycles:
            sleep(interval * 60)
    return "rounds"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pipeline guardian (supervise / once / status / stop)")
    sub = ap.add_subparsers(dest="mode")
    for mode in ("supervise", "once", "status", "stop"):
        p = sub.add_parser(mode)
        p.add_argument("--lab")
        if mode == "supervise":
            p.add_argument("--interval-min", type=int)
    args = ap.parse_args(argv)
    if not args.mode:
        ap.print_help()
        return 2
    lab = lab_dir(args.lab)
    if args.mode == "supervise":
        outcome = supervise(lab, getattr(args, "interval_min", None))
        print("Pipeline guardian: %s." % outcome)
    elif args.mode == "once":
        return once(lab)
    elif args.mode == "status":
        print(status_text(lab))
    elif args.mode == "stop":
        return stop(lab)
    return 0


if __name__ == "__main__":
    sys.exit(main())
