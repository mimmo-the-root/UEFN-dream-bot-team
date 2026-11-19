#!/usr/bin/env python3
"""Tests for tools/watchdog.py with fake relay folders. The run command is a fake that only writes a marker file."""
import json, os, subprocess, sys, tempfile, time
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wd = os.path.join(root, "tools", "watchdog.py")


def mklab():
    lab = os.path.join(tempfile.mkdtemp(), "Claude")
    for d in ("relay/inbox", "relay/running", "logs", "plan"):
        os.makedirs(os.path.join(lab, d))
    return lab


def pkg(lab, folder, name, do="do the thing"):
    open(os.path.join(lab, "relay", folder, name), "w").write("id: x\ntitle: t\ndo: %s\nrisk: low\n" % do)


def old(p, minutes=60):
    t = time.time() - minutes * 60
    os.utime(p, (t, t))


def watchdog(lab, marker):
    fake = '%s -c "import sys;open(sys.argv[1],\'w\').write(sys.argv[2])" %s {do}' % (sys.executable.replace("\\", "/"), marker.replace("\\", "/"))
    r = subprocess.run([sys.executable, wd, "--lab", lab, "--run-cmd", fake], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return r.stdout


def wait_marker(m):
    for _ in range(50):
        if os.path.exists(m):
            return True
        time.sleep(0.1)
    return False


def log(lab):
    return open(os.path.join(lab, "logs", "watchdog.log")).read()


# 1. idle with work: starts exactly ONE run for the oldest package
lab = mklab(); m = os.path.join(lab, "marker.txt")
pkg(lab, "inbox", "246-b.md", "second"); pkg(lab, "inbox", "245-a.md", "first job")
watchdog(lab, m)
assert wait_marker(m) and open(m).read() == "first job", "run not started for oldest package"
assert "started 245-a" in log(lab), log(lab)
os.remove(m)
watchdog(lab, m)  # second call right after: own start guard, no second run
time.sleep(0.5)
assert not os.path.exists(m), "second run started"
assert log(lab).count("started") == 1
st = open(os.path.join(lab, "plan", "STATUS.md")).read()
assert len(st.splitlines()) <= 15 and "cod:" in st

# 2. busy (something in running): does nothing
lab = mklab(); m = os.path.join(lab, "marker.txt")
pkg(lab, "inbox", "250-a.md"); pkg(lab, "running", "249-r.md")
watchdog(lab, m); time.sleep(0.5)
assert not os.path.exists(m) and "none (Cod busy)" in log(lab)

# 3. recent activity: does nothing; old activity: starts
lab = mklab(); m = os.path.join(lab, "marker.txt")
pkg(lab, "inbox", "250-a.md")
act = os.path.join(lab, "logs", "cod-activity.jsonl")
open(act, "w").write(json.dumps({"ts": int(time.time()), "event": "PostToolUse", "ok": True, "blocked": False}) + "\n")
watchdog(lab, m); time.sleep(0.5)
assert not os.path.exists(m)
open(act, "w").write(json.dumps({"ts": int(time.time()) - 3600, "event": "Stop", "ok": True, "blocked": False}) + "\n")
old(act)
os.remove(os.path.join(lab, "logs", "watchdog.log")) if os.path.exists(os.path.join(lab, "logs", "watchdog.log")) else None
watchdog(lab, m)
assert wait_marker(m)

# 4. empty inbox: logs IDLE, writes STATUS with last COMMITTED and router mode
lab = mklab(); m = os.path.join(lab, "marker.txt")
open(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md"), "w").write("# h\nCOMMITTED 224 r1/t063 abc\n")
old(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md"))
open(os.path.join(lab, "logs", "routing.json"), "w").write('{"mode": "free"}')
out = watchdog(lab, m)
assert "IDLE" in log(lab) and not os.path.exists(m)
st = open(os.path.join(lab, "plan", "STATUS.md")).read()
assert "COMMITTED 224" in st and "router mode: free" in st and "cod: idle" in st, st

# 5. 3 blocks in one hour: one line in PROBLEMS-FROM-COD.md, only once
lab = mklab(); m = os.path.join(lab, "marker.txt")
now = int(time.time())
with open(os.path.join(lab, "logs", "cod-activity.jsonl"), "w") as f:
    for i in range(3):
        f.write(json.dumps({"ts": now - 1500 - i, "event": "PermissionDenied", "ok": False, "blocked": True}) + "\n")
watchdog(lab, m); watchdog(lab, m)
pr = open(os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md")).read()
assert pr.count("watchdog |") == 1 and "3 classifier" in pr, pr
print("test_watchdog: ok")
