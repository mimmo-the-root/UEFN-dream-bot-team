#!/usr/bin/env python3
"""Tests for repeat_guard.py and claim_guard.py"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

H = Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
RG = str(H / "repeat_guard.py")
CG = str(H / "claim_guard.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))


def run(hook, payload, env=None, project_root=None):
    e = dict(os.environ); e.update(env or {})
    p = json.dumps(payload)
    d = project_root or tempfile.mkdtemp()
    Path(d).joinpath("Claude", "logs").mkdir(parents=True, exist_ok=True)
    e['CLAUDE_PROJECT_DIR'] = d
    r = subprocess.run([sys.executable, hook], input=p, capture_output=True, text=True, env=e)
    return r.returncode, (json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None), d


def test_repeat_guard():
    print("Testing repeat_guard.py...")
    # Test 1: 3 identical failures block on 3rd call
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    for i in range(2):
        code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
        assert code == 0 and out is None, f"call {i+1} should not block"
    code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    assert code == 0 and out is not None and "STOP: this call failed 3 times" in out["additionalContext"], "3rd identical failure should block"
    ok(True, "3rd identical failure triggers STOP")

    # Test 2: different error is a different key, does not block the old key's streak
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error B"}}, project_root=d)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error B"}}, project_root=d)
    code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error B"}}, project_root=d)
    assert code == 0 and out is not None, "3rd Error B should block"
    code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    assert out is None, "Error A still at streak 2 (different key kept its own count), should not block yet"
    ok(True, "different error is a separate key; old key keeps its own streak")

    # Test 3: success resets streak
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {}}, project_root=d)  # success resets
    code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, project_root=d)
    assert out is None, "after success, Error A streak resets to 1, should not block"
    ok(True, "success resets streak")

    # Test 4: UEFN_KIT_GUARDS=0 switches off
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    for i in range(5):
        code, out, _ = run(RG, {"tool_name": "TestTool", "tool_input": {"a": "v"}, "tool_result": {"error": "Error A"}}, env={"UEFN_KIT_GUARDS": "0"}, project_root=d)
        assert code == 0 and out is None, "guard disabled should never block"
    ok(True, "UEFN_KIT_GUARDS=0 switches off guard")

    # Test 5: bad input never blocks
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(RG, {"not": "json"}, project_root=d)
    assert code == 0 and out is None
    ok(True, "bad input never blocks")
    print("repeat_guard: ALL TESTS PASSED")


def test_claim_guard():
    print("Testing claim_guard.py...")
    # Test 1: claim without write blocks once
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {"transcript": [{"role": "assistant", "content": "I have written the file test.txt successfully."}]}, project_root=d)
    assert code == 0 and out is not None and out.get("permissionDecision") == "deny", "claim without write should block"
    assert "You said a file was written but no write succeeded" in out["permissionDecisionReason"]
    ok(True, "claim without write blocks once")

    # Test 2: never block twice in a row
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    run(CG, {"transcript": [{"role": "assistant", "content": "I have written the file test.txt successfully."}]}, project_root=d)
    code, out, _ = run(CG, {"transcript": [{"role": "assistant", "content": "I have written the file test.txt successfully."}]}, project_root=d)
    assert code == 0 and out is None or out.get("permissionDecision") != "deny", "should not block twice in a row"
    ok(True, "never blocks twice in a row")

    # Test 3: claim with Write succeeds -> passes
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {
        "transcript": [
            {"role": "assistant", "content": "I have written the file test.txt successfully."},
            {"tool": "Write", "result": {"success": True}}
        ]
    }, project_root=d)
    assert code == 0 and (out is None or out.get("permissionDecision") != "deny"), "claim with write should pass"
    ok(True, "claim with write passes")

    # Test 4: claim with Bash file write passes
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {
        "transcript": [
            {"role": "assistant", "content": "I have written the file output.txt successfully."},
            {"tool": "Bash", "tool_input": {"command": "echo hello > output.txt"}, "result": {"exit_code": 0}}
        ]
    }, project_root=d)
    assert code == 0 and (out is None or out.get("permissionDecision") != "deny"), "claim with Bash write should pass"
    ok(True, "claim with Bash file write passes")

    # Test 5: Italian verbs detected
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {"transcript": [{"role": "assistant", "content": "Ho creato il file test.txt con successo."}]}, project_root=d)
    assert code == 0 and out is not None and out.get("permissionDecision") == "deny", "Italian verbs should be detected"
    ok(True, "Italian verbs detected")

    # Test 6: no claim = no block
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {"transcript": [{"role": "assistant", "content": "I will now check the file."}]}, project_root=d)
    assert code == 0 and (out is None or out.get("permissionDecision") != "deny"), "no claim should not block"
    ok(True, "no claim = no block")

    # Test 7: UEFN_KIT_GUARDS=0 switches off
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    for i in range(3):
        code, out, _ = run(CG, {"transcript": [{"role": "assistant", "content": "I have written the file test.txt successfully."}]}, env={"UEFN_KIT_GUARDS": "0"}, project_root=d)
        assert code == 0 and (out is None or out.get("permissionDecision") != "deny"), "guard disabled should never block"
    ok(True, "UEFN_KIT_GUARDS=0 switches off guard")

    # Test 8: bad input never blocks
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "Claude", "logs"), exist_ok=True)
    code, out, _ = run(CG, {"not": "json"}, project_root=d)
    assert code == 0 and (out is None or out.get("permissionDecision") != "deny")
    ok(True, "bad input never blocks")
    print("claim_guard: ALL TESTS PASSED")


if __name__ == "__main__":
    test_repeat_guard()
    test_claim_guard()
    print("\nALL TESTS PASSED")