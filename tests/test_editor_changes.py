"""Editor change record, undo plan and the one-writer lock."""
import json, os, shutil, sys, tempfile, time
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import editor_changes as ec, editor_lock as el, mcp_work_log as W
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
r = W.row_from_payload({"session_id": "abc123", "tool_input": {"toolset_name": "A.B", "tool_name": "Make", "arguments": {}}, "tool_response": "{}"})
ok(r["sid"] == "abc123" and len(r["d"]) == 10, "ledger rows carry session id and date")
ok(ec.is_write("SpawnActor") and ec.is_write("SetProperty") and not ec.is_write("GetActors") and not ec.is_write("CaptureViewport"), "reading vs writing tools by name")
d = tempfile.mkdtemp()
try:
    logs = os.path.join(d, "Claude", "logs"); os.makedirs(logs)
    rows = [
        {"d": "2026-10-23", "sid": "s1", "t": "10:00:00", "toolset": "A.Level", "tool": "SpawnActor", "args": json.dumps({"path": "/g/p/Wall"}), "r": "ok", "src": "work"},
        {"d": "2026-10-23", "sid": "s1", "t": "10:01:00", "toolset": "A.Level", "tool": "GetActors", "args": "{}", "r": "ok", "src": "work"},
        {"d": "2026-10-23", "sid": "s1", "t": "10:02:00", "toolset": "A.Level", "tool": "SetProperty", "args": json.dumps({"path": "/g/p/Wall", "v": 1}), "r": "ok", "src": "work"},
        {"d": "2026-10-23", "sid": "s1", "t": "10:03:00", "toolset": "A.Level", "tool": "SpawnActor", "args": "{}", "r": "rejected", "src": "work"},
        {"d": "2026-10-24", "sid": "s2", "t": "09:00:00", "toolset": "A.Assets", "tool": "CreateAsset", "args": json.dumps({"path": "/g/p/Mat"}), "r": "ok", "src": "work"},
        {"d": "2026-10-24", "sid": "s2", "t": "09:01:00", "toolset": "A.Assets", "tool": "SpawnActor", "args": json.dumps({"p": "/lab/x"}), "r": "ok", "src": "explore"},
    ]
    open(os.path.join(logs, "explore-ledger.jsonl"), "w").write("\n".join(json.dumps(x) for x in rows) + "\n")
    ss = ec.sessions(ec.load(d))
    ok([k for k, _ in ss] == ["s1", "s2"] and [len(v) for _, v in ss] == [2, 1], "only successful real writes are kept, grouped by session")
    k, v = ec.pick(ec.load(d))
    ok(k == "s2", "default session is the newest")
    k1, v1 = ec.pick(ec.load(d), "s1")
    steps = ec.plan(v1)
    ok([s["action"] for s in steps] == ["manual", "delete"] and steps[1]["paths"] == ["/g/p/Wall"], "undo plan: newest first, creation = delete, value change = manual")
    os.environ["CLAUDE_PROJECT_DIR"] = d
    ok(ec.main(["undo-plan", "--session", "s1"]) == 0 and ec.main(["list"]) == 0, "CLI runs")
    # lock
    ok(el.decide(d, "s1", "GetActors")[0] == "allow" and el.read(d) is None, "reading never takes the lock")
    ok(el.decide(d, "s1", "SpawnActor")[0] == "allow" and el.read(d)["sid"] == "s1", "first writer takes the lock")
    ok(el.decide(d, "s1", "SetProperty")[0] == "allow", "same session keeps writing")
    v, why = el.decide(d, "s2", "SpawnActor")
    ok(v == "deny" and "Another Claude session" in why, "another session is denied while the lock is fresh")
    ok(el.decide(d, "s2", "GetActors")[0] == "allow", "the other session can still read")
    ok(el.decide(d, "s2", "SpawnActor", now=time.time() + 700)[0] == "allow" and el.read(d)["sid"] == "s2", "a stale lock is taken over")
finally:
    shutil.rmtree(d, ignore_errors=True)
