"""mcp_readonly_allow.py: read-only UEFN tools pass without a prompt, tools that change the map keep asking."""
import json, os, subprocess, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import mcp_readonly_allow as m
ALLOW = ["mcp__unreal-mcp__AIAssistantEditor_AIAssistantToolset_GetProjectContext", "mcp__unreal-mcp__find_assets",
         "mcp__unreal-mcp__list_actors", "mcp__unreal-mcp__GetDeviceProperties", "mcp__unreal-mcp__ListDeviceProperties"]
ASK = ["mcp__unreal-mcp__SetDeviceProperties", "mcp__unreal-mcp__delete_actor", "mcp__unreal-mcp__execute_python",
       "mcp__unreal-mcp__GetAndSetThing", "mcp__unreal-mcp__search_and_replace", "mcp__other__get_x", "Bash",
       "mcp__unreal-mcp__x_SequencerControlRigTools_set_world_transform", "mcp__unreal-mcp__spawn_actor"]
bad = [t for t in ALLOW if m.decide(t) != "allow"] + [t for t in ASK if m.decide(t) is not None]
assert not bad, bad
run = lambda t, env=None: subprocess.run([sys.executable, os.path.join(H, "mcp_readonly_allow.py")], input=json.dumps({"tool_name": t}),
                                        capture_output=True, text=True, env=dict(os.environ, **(env or {}))).stdout
assert json.loads(run(ALLOW[0]))["hookSpecificOutput"]["permissionDecision"] == "allow"
assert run(ASK[0]) == "" and run(ALLOW[0], {"UEFN_KIT_MCP_READ_ALLOW": "0"}) == ""
s = json.load(open(os.path.join(root, "project-template", ".claude", "settings.json"), encoding="utf-8"))
assert any("mcp_readonly_allow.py" in h["command"] for b in s["hooks"]["PreToolUse"] if b["matcher"] == "mcp__unreal-mcp__.*" for h in b["hooks"])
print("ok mcp_readonly_allow")
