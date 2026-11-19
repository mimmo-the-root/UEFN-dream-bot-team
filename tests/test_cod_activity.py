#!/usr/bin/env python3
"""Tests for the Cod activity hook: ok tool, denied tool, failure, garbage input, cap."""
import json, os, subprocess, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
hook = os.path.join(root, "project-template", "Claude", "hooks", "cod_activity.py")
lab = tempfile.mkdtemp()
os.makedirs(os.path.join(lab, "relay", "running"))
open(os.path.join(lab, "relay", "running", "247-t-089.md"), "w").write("x")
log = os.path.join(lab, "logs", "cod-activity.jsonl")
env = dict(os.environ, UEFN_LAB=lab)
for k in ("UEFN_PACKAGE_ID", "COD_PACKAGE_ID", "CLAUDE_PACKAGE_ID"):
    env.pop(k, None)


def run(stdin, e=env):
    r = subprocess.run([sys.executable, hook], input=stdin, capture_output=True, text=True, env=e, timeout=30)
    assert r.returncode == 0, r.returncode
    assert r.stdout == "", "hook printed to stdout: %r" % r.stdout
    return r


def rows():
    return [json.loads(l) for l in open(log, encoding="utf-8").read().splitlines()]


run(json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_response": {"stdout": "hi"}}))
r = rows()[-1]
assert r["event"] == "PostToolUse" and r["tool"] == "Bash" and r["ok"] and not r["blocked"] and r["pkg"] == "247-t-089", r
run(json.dumps({"hook_event_name": "PermissionDenied", "tool_name": "Bash", "reason": "x" * 500}))
r = rows()[-1]
assert r["blocked"] and not r["ok"] and len(r["reason"]) == 200, r
run(json.dumps({"hook_event_name": "PostToolUseFailure", "tool_name": "Edit", "error": "Permission to use Edit has been denied by the classifier"}))
r = rows()[-1]
assert r["blocked"] and not r["ok"] and r["reason"], r
run(json.dumps({"hook_event_name": "PostToolUseFailure", "tool_name": "Bash", "error": "exit 1"}))
r = rows()[-1]
assert not r["ok"] and not r["blocked"], r
run(json.dumps({"hook_event_name": "Stop"}), dict(env, UEFN_PACKAGE_ID="pkg-9"))
assert rows()[-1]["pkg"] == "pkg-9"
n = len(rows())
for g in ("", "not json {{", "[1,2]", "null", "\x00\xff"):
    run(g)
assert len(rows()) == n, "garbage input must not write"
# cap: preload 1999 lines then add 5 events
with open(log, "w", encoding="utf-8") as f:
    for i in range(1999):
        f.write(json.dumps({"event": "old", "i": i}) + "\n")
for i in range(5):
    run(json.dumps({"hook_event_name": "Notification", "message": "m%d" % i}))
rs = rows()
assert len(rs) == 2000, len(rs)
assert rs[-1]["event"] == "Notification" and rs[0].get("i") == 4, rs[0]
print("test_cod_activity: ok")
