"""Cod continues after a usage limit in the SAME session: the StopFailure hook records the limit, the watcher waits for the reset, types the continue
message into that session (no new window), retries with no cap until the session moves, stops if the session is closed or the owner switched it off;
the hook reaches existing projects through kit_sync."""
import json, os, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
import limit_resume as L
import kit_sync as K

# 1. settings wiring and additive merge
tpl = json.load(open(os.path.join(HERE, "..", "project-template", ".claude", "settings.json"), encoding="utf-8"))
sf = tpl["hooks"]["StopFailure"]
assert sf[0]["matcher"] == "rate_limit" and "limit-resume.ps1" in sf[0]["hooks"][0]["command"]
assert "NEW Cod window" not in json.dumps(tpl)
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, ".claude"))
json.dump({"hooks": {}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
tdir = tempfile.mkdtemp(); os.makedirs(os.path.join(tdir, ".claude"))
json.dump(tpl, open(os.path.join(tdir, ".claude", "settings.json"), "w"))
assert any(a.startswith("StopFailure:") for a in K.merge_settings(d, tdir))
assert not any(a.startswith("StopFailure:") for a in K.merge_settings(d, tdir)), "idempotent"

# 2. reset time parsing
now = time.mktime((2026, 11, 12, 20, 0, 0, 0, 0, -1))
r = L.parse_reset_text("5-hour limit reached - resets 9pm", now); assert time.localtime(r).tm_hour == 21 and r > now
r = L.parse_reset_text("resets 7:30 PM", now); assert time.localtime(r).tm_mday == 13 and time.localtime(r).tm_hour == 19
assert L.parse_reset_text("nothing here", now) is None
assert abs(L.find_reset({"resets_at": now + 600}, now) - (now + 600)) < 1
assert abs(L.find_reset({"resetsAt": int((now + 600) * 1000)}, now) - (now + 600)) < 1

# 3. hook
def project():
    p = tempfile.mkdtemp(); os.makedirs(os.path.join(p, "Claude", "relay", "outbox")); os.environ["CLAUDE_PROJECT_DIR"] = p
    tr = os.path.join(p, "t.jsonl"); open(tr, "w").write("x"); return p, tr
LIM = lambda p: os.path.join(p, "Claude", "relay", "outbox", "LIMIT.json")
p, tr = project(); reset = time.time() + 120
out = L.hook(json.dumps({"error_type": "rate_limit", "resets_at": reset, "transcript_path": tr, "session_id": "s1"}), claude_pid=4242, spawn=False)
rec = json.load(open(LIM(p)))
assert out["ok"] and rec["state"] == "waiting" and rec["claude_pid"] == 4242 and abs(rec["resets_at"] - reset) < 1
assert not L.hook(json.dumps({"error_type": "overloaded"}), spawn=False)["ok"], "only rate limits"

# 4. watcher: types into the same session once the reset passes, verifies, no new window
clock = [time.time()]
now_fn = lambda: clock[0]
def sleep_fn(s): clock[0] += s + 1
calls = []
def wake_ok(pid, text):
    calls.append((pid, text)); os.utime(tr, (clock[0] + 1, clock[0] + 1)); return True, "typed"   # the session answers: transcript moves
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: True) == "resumed"
assert len(calls) == 1 and calls[0][0] == 4242 and "ROADMAP.md" in calls[0][1] and "away" in calls[0][1], calls
assert clock[0] >= reset + 90, "waits for the reset plus a margin"
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: True) == "resumed" and len(calls) == 1, "never twice for one limit"

# 5. no daily cap, unlimited retries: the first 6 attempts do not move the session, the 7th does
p, tr = project(); L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 30, "transcript_path": tr}), claude_pid=77, spawn=False)
clock = [time.time()]; calls = []
def wake_late(pid, text):
    calls.append(pid)
    if len(calls) >= 7: os.utime(tr, (clock[0] + 1, clock[0] + 1))
    return True, "typed"
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_late, alive=lambda pid: True) == "resumed" and len(calls) == 7
# a failed injection is retried too
p, tr = project(); L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 30, "transcript_path": tr}), claude_pid=77, spawn=False)
clock = [time.time()]; calls = []
def wake_flaky(pid, text):
    calls.append(pid)
    if len(calls) < 3: return False, "cannot attach"
    os.utime(tr, (clock[0] + 1, clock[0] + 1)); return True, "typed"
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_flaky, alive=lambda pid: True) == "resumed" and len(calls) == 3

# 6. the owner already continued; the session is closed; switched off
p, tr = project(); reset = time.time() + 30
L.hook(json.dumps({"error_type": "rate_limit", "resets_at": reset, "transcript_path": tr}), claude_pid=5, spawn=False)
clock = [time.time()]; calls = []; os.utime(tr, (reset + 200, reset + 200))
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: True) == "resumed-by-owner" and not calls
p, tr = project(); L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 30, "transcript_path": tr}), claude_pid=5, spawn=False)
clock = [time.time()]; calls = []
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: False) == "session-closed" and not calls
p, tr = project(); L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 30, "transcript_path": tr}), claude_pid=5, spawn=False)
open(os.path.join(p, "Claude", "relay", "NO-RESUME"), "w").write("")
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: True) == "cancelled"
p, tr = project(); open(os.path.join(p, "Claude", "relay", "NO-RESUME"), "w").write("")
assert not L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 60}), spawn=False)["ok"]

# 7. unknown reset time: tries after 10 minutes
p, tr = project(); L.hook(json.dumps({"error_type": "rate_limit", "transcript_path": tr}), claude_pid=9, spawn=False)
clock = [time.time()]; t0 = clock[0]; calls = []
assert L.watch(p, sleep=sleep_fn, now_fn=now_fn, wake=wake_ok, alive=lambda pid: True) == "resumed" and 590 <= clock[0] - t0 < 700

# 8. the wake script and the hook script exist; no leftover new-window code
hd = os.path.join(HERE, "..", "project-template", "Claude", "hooks")
w = open(os.path.join(hd, "limit-wake.ps1"), encoding="utf-8").read()
assert "AttachConsole" in w and "WriteConsoleInputW" in w and "CONIN$" in w
assert "-claude_pid" not in L.wake_command(1, "x") and L.wake_command(12, "hi")[-4:] == ["-TargetPid", "12", "-Text", "hi"]
assert "claude_args" not in open(os.path.join(hd, "limit_resume.py"), encoding="utf-8").read()
print("limit resume OK")
