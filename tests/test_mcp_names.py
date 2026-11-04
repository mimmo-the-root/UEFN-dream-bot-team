"""mcp_names.py reads a UEFN MCP call in both shapes (old call_tool, new one-name-per-tool), and the hooks that use it keep working."""
import json, os, subprocess, sys
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import mcp_names as N
import mcp_work_log as W
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
P = "mcp__unreal-mcp__"
r = N.read({"tool_name": P + "ValkyrieFortniteToolset_DeviceToolset_PlaceDevice", "tool_input": {"x": 1}})
check("new shape: toolset and short tool name", r["toolset"] == "ValkyrieFortniteToolset" and r["tool"] == "PlaceDevice" and r["args"] == {"x": 1} and r["shape"] == "new")
r = N.read({"tool_name": P + "call_tool", "tool_input": {"toolset_name": "A.B", "tool_name": "FindAssets", "arguments": "{\"name\": \"x\"}"}})
check("old shape: call_tool arguments (also as a JSON string)", r["tool"] == "FindAssets" and r["toolset"] == "A.B" and r["args"] == {"name": "x"} and r["shape"] == "old")
r = N.read({"tool_name": P + "animation_toolset_add_spawnable_from_class", "tool_input": {}})
check("snake_case tools keep their tail", r["toolset"] == "animation_toolset" and r["tool"] == "add_spawnable_from_class")
r = N.read({"tool_name": P + "editor_toolset_toolsets_python_scripting_PythonScriptingTools_execute_python", "tool_input": {"script": "x"}})
check("python scripting tool maps to editor_toolset/execute_python", r["toolset"] == "editor_toolset" and r["tool"] == "execute_python")
check("junk does not raise", N.read({})["tool"] == "" and N.read(None)["tool"] == "")
check("is_tool ignores case and underscores", N.is_tool("EditorToolset_AssetToolset_FindAssets", "find_assets") and not N.is_tool("PlaceDevice", "find_assets"))
# heavy guard with the new names
G = os.path.join(H, "mcp_heavy_guard.py")
def guard(tool_name, tool_input):
    p = json.dumps({"tool_name": P + tool_name, "tool_input": tool_input})
    o = subprocess.run([sys.executable, G], input=p, capture_output=True, text=True).stdout.strip()
    return json.loads(o)["hookSpecificOutput"] if o else None
check("new name FindAssets with no filter is refused", (guard("EditorToolset_AssetToolset_FindAssets", {}) or {}).get("permissionDecision") == "deny")
check("43.00 nested camelCase filter passes", guard("EditorToolset_AssetToolset_FindAssets", {"filter": {"folderPath": "/CR_Legacy/Playsets/PlaysetProps", "name": "Hay"}}) is None)
check("43.00 nested filter with only an empty value is refused", (guard("EditorToolset_AssetToolset_FindAssets", {"filter": {"name": ""}}) or {}).get("permissionDecision") == "deny")
check("new name FindAssets with a filter passes", guard("EditorToolset_AssetToolset_FindAssets", {"folder_path": "/x", "name": "y"}) is None)
check("new name GetLogEntries maxEntries 0 without pattern is refused", (guard("ConsoleToolset_GetLogEntries", {"maxEntries": 0}) or {}).get("permissionDecision") == "deny")
check("new name GetLogEntries with a pattern passes", guard("ConsoleToolset_GetLogEntries", {"maxEntries": 0, "pattern": "Error"}) is None)
check("a script that calls FindAssets without any filter is refused", (guard("editor_toolset_toolsets_programmatic_ProgrammaticToolset_execute_tool_script", {"script": "async def run():\n  return await execute_tool('EditorToolset.AssetToolset.FindAssets', {})"}) or {}).get("permissionDecision") == "deny")
check("a script with a filter passes", guard("editor_toolset_toolsets_programmatic_ProgrammaticToolset_execute_tool_script", {"script": "async def run():\n  return await execute_tool('EditorToolset.AssetToolset.FindAssets', {'name': 'x'})"}) is None)
check("other new tools are never touched", guard("ValkyrieFortniteToolset_DeviceToolset_PlaceDevice", {}) is None)
# work log with the new shape
row = W.row_from_payload({"tool_name": P + "VerseToolset_VerseToolset_BuildAll", "tool_input": {}, "tool_response": "{\"ok\": true}"})
check("work log: new shape is logged with toolset and tool", row and row["toolset"] == "VerseToolset" and row["tool"] == "BuildAll" and row["r"] == "ok")
# editor lock with the new names
import editor_lock as E, tempfile
with tempfile.TemporaryDirectory() as d:
    v, _ = E.decide(d, "s1", "GetActorTransform"); check("reading tools never take the lock", v == "allow" and not os.path.exists(E.lock_path(d)))
    v, _ = E.decide(d, "s1", "PlaceDevice"); check("a writing tool takes the lock", v == "allow" and os.path.exists(E.lock_path(d)))
    v, why = E.decide(d, "s2", "SetProperties"); check("a second session writing is refused", v == "deny")
    v, _ = E.decide(d, "s2", "Exists"); check("Exists is a read", v == "allow")
check("a tool that stopped the editor is refused (avoid list)", (guard("SceneCaptureToolset_SceneCaptureToolset_ListViews", {}) or {}).get("permissionDecision") == "deny")
check("a sibling tool of the same set is not refused", guard("SceneCaptureToolset_SceneCaptureToolset_ListModes", {}) is None)
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
