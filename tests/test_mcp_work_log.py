import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import mcp_work_log as W
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
ok = W.row_from_payload({"tool_input": {"toolset_name": "A.B", "tool_name": "Make", "arguments": {"x": 1}}, "tool_response": "{\"ok\": true}"})
check("a good call is logged as work/ok", ok and ok["r"] == "ok" and ok["src"] == "work" and ok["toolset"] == "A.B" and ok["tool"] == "Make")
bad = W.row_from_payload({"tool_input": {"toolset_name": "A.B", "tool_name": "Make", "arguments": {}}, "tool_response": {"isError": True, "content": "bad path"}})
check("an error is logged as rejected with a reason", bad["r"] == "rejected" and "bad path" in bad["why"])
fl = W.row_from_payload({"hook_event_name": "PostToolUseFailure", "tool_input": {"toolset_name": "A.B", "tool_name": "Load", "arguments": {"p": "/x"}}, "error": "Unable to load /x"})
check("a PostToolUseFailure event is logged as rejected", fl and fl["r"] == "rejected" and "Unable to load" in fl["why"] and fl["src"] == "work")
check("other tools are ignored", W.row_from_payload({"tool_input": {"command": "ls"}}) is None)
check("junk does not raise", W.row_from_payload({}) is None)
import recipes_status as R, mcp_lessons as L
check("work rows are not battery rows", not L.is_battery(ok))
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
