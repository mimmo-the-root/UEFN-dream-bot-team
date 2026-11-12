"""Cod resumes after a usage limit: the StopFailure hook records the limit, the watcher waits for the reset, opens ONE new window,
never twice, never when the owner already continued, never when switched off; the hook reaches existing projects through kit_sync."""
import json, os, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
import limit_resume as L
import kit_sync as K

# 1. the settings template wires the hook, and an old project gets it through the additive merge
tpl = json.load(open(os.path.join(HERE, "..", "project-template", ".claude", "settings.json"), encoding="utf-8"))
sf = tpl["hooks"]["StopFailure"]
assert sf[0]["matcher"] == "rate_limit" and "limit-resume.ps1" in sf[0]["hooks"][0]["command"]
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, ".claude"))
json.dump({"hooks": {}}, open(os.path.join(d, ".claude", "settings.json"), "w"))
tdir = tempfile.mkdtemp(); os.makedirs(os.path.join(tdir, ".claude"))
json.dump(tpl, open(os.path.join(tdir, ".claude", "settings.json"), "w"))
assert any(a.startswith("StopFailure:") for a in K.merge_settings(d, tdir))
assert not any(a.startswith("StopFailure:") for a in K.merge_settings(d, tdir)), "idempotent"

# 2. reset time parsing
now = time.mktime((2026, 11, 12, 20, 0, 0, 0, 0, -1))
r = L.parse_reset_text("5-hour limit reached - resets 9pm", now); assert time.localtime(r).tm_hour == 21 and r > now
r = L.parse_reset_text("resets 7:30 PM", now); assert time.localtime(r).tm_mday == 13 and time.localtime(r).tm_hour == 19  # already past today -> tomorrow
assert L.parse_reset_text("nothing here", now) is None
assert abs(L.find_reset({"resets_at": now + 600}, now) - (now + 600)) < 1
assert abs(L.find_reset({"resetsAt": int((now + 600) * 1000)}, now) - (now + 600)) < 1

# 3. hook + watcher
def project():
    p = tempfile.mkdtemp(); os.makedirs(os.path.join(p, "Claude", "relay", "outbox")); return p
p = project(); os.environ["CLAUDE_PROJECT_DIR"] = p
tr = os.path.join(p, "t.jsonl"); open(tr, "w").write("x")
reset = time.time() + 120
out = L.hook(json.dumps({"error_type": "rate_limit", "resets_at": reset, "transcript_path": tr, "session_id": "s1"}), spawn=False)
rec = json.load(open(os.path.join(p, "Claude", "relay", "outbox", "LIMIT.json")))
assert out["ok"] and rec["state"] == "waiting" and abs(rec["resets_at"] - reset) < 1
assert not L.hook(json.dumps({"error_type": "overloaded"}), spawn=False)["ok"], "only rate limits"

clock = [time.time()]
def fake_now(): return clock[0]
def fake_sleep(s): clock[0] += s + 1
opened = []
assert L.watch(p, sleep=fake_sleep, now_fn=fake_now, run=lambda c: opened.append(c)) == "resumed"
assert len(opened) == 1 and any("Claude/docs/STATUS.md" in x or "STATUS.md" in x for x in opened[0]), opened
assert clock[0] >= reset + 90, "waits for the reset plus a margin"
assert L.watch(p, sleep=fake_sleep, now_fn=fake_now, run=lambda c: opened.append(c)) == "resumed" and len(opened) == 1, "never twice for one limit"

# 4. the owner already continued (the transcript changed after the reset)
p = project(); os.environ["CLAUDE_PROJECT_DIR"] = p
tr = os.path.join(p, "t.jsonl"); open(tr, "w").write("x")
reset = time.time() + 30
L.hook(json.dumps({"error_type": "rate_limit", "resets_at": reset, "transcript_path": tr}), spawn=False)
clock = [time.time()]; opened = []
os.utime(tr, (reset + 200, reset + 200))
assert L.watch(p, sleep=fake_sleep, now_fn=fake_now, run=lambda c: opened.append(c)) == "resumed-by-owner" and not opened

# 5. switched off, and the daily cap
p = project(); os.environ["CLAUDE_PROJECT_DIR"] = p
open(os.path.join(p, "Claude", "relay", "NO-RESUME"), "w").write("")
assert not L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 60}), spawn=False)["ok"]
os.remove(os.path.join(p, "Claude", "relay", "NO-RESUME"))
json.dump({"max_per_day": 1}, open(os.path.join(p, "Claude", "relay", "RESUME.json"), "w"))
os.makedirs(os.path.join(p, "Claude", "logs"), exist_ok=True)
open(os.path.join(p, "Claude", "logs", "limit-resume.log"), "w").write(time.strftime("%Y-%m-%d %H:%M:%S ") + "resume window opened\n")
L.hook(json.dumps({"error_type": "rate_limit", "resets_at": time.time() + 30}), spawn=False)
clock = [time.time()]; opened = []
assert L.watch(p, sleep=fake_sleep, now_fn=fake_now, run=lambda c: opened.append(c)) == "gave-up" and not opened

# 6. unknown reset time: waits 30 minutes, then tries
p = project(); os.environ["CLAUDE_PROJECT_DIR"] = p
L.hook(json.dumps({"error_type": "rate_limit"}), spawn=False)
clock = [time.time()]; opened = []
assert L.watch(p, sleep=fake_sleep, now_fn=fake_now, run=lambda c: opened.append(c)) == "resumed" and clock[0] - time.time() >= 29 * 60
print("limit resume OK")
