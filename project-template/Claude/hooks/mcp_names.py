#!/usr/bin/env python3
"""mcp_names.py - one place that reads a UEFN MCP tool call from a hook payload, whatever shape the call has.

Two shapes exist:
  old   tool_name "mcp__unreal-mcp__call_tool", tool_input {toolset_name, tool_name, arguments}
  new   tool_name "mcp__unreal-mcp__<Toolset>_<Tool>" (one name per tool, UEFN 43.00), tool_input = the arguments themselves

`read(payload)` returns {"toolset", "tool", "args", "shape"}; "tool" is the short name (FindAssets, GetLogEntries, PlaceDevice...).
`norm(name)` lowercases and drops underscores so FindAssets, find_assets and EditorToolset_AssetToolset_FindAssets compare with endswith.
Never raises: unknown input gives empty strings."""
import json
import re

PREFIX = "mcp__unreal-mcp__"
SCRIPT_TOOLS = ("executetoolscript", "executepython")


def norm(name):
    return re.sub(r"[_\W]", "", str(name or "")).lower()


def is_unreal(payload):
    return str((payload or {}).get("tool_name") or "").startswith(PREFIX)


def _split(full):
    """(whole name after the prefix, toolset, short tool name), toolset written like the tool map keys it (EditorToolset, editor_toolset).
    CamelCase tools end with their own segment (EditorToolset_AssetToolset_FindAssets); snake_case tools keep their snake_case tail."""
    rest = full[len(PREFIX):] if full.startswith(PREFIX) else full
    last = rest.rsplit("_", 1)[-1]
    if last[:1].isupper():
        return rest, rest.split("_", 1)[0], last
    m = re.match(r"^(animation_toolset|editor_toolset)(?:_toolsets_[a-z_]+?_[A-Za-z]+)?_([a-z].*)$", rest)
    if m:
        return rest, m.group(1), m.group(2)
    return rest, rest.split("_", 1)[0], last


def read(payload):
    p = payload or {}
    ti = p.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
    top = str(p.get("tool_name") or "")
    if top.endswith("call_tool") or ("tool_name" in ti and "toolset_name" in ti):
        args = ti.get("arguments", ti.get("args", {}))
        if isinstance(args, str):
            try:
                args = json.loads(args or "{}")
            except ValueError:
                args = {}
        return {"toolset": str(ti.get("toolset_name") or ""), "tool": str(ti.get("tool_name") or ""),
                "args": args if isinstance(args, dict) else {}, "shape": "old"}
    if top.startswith(PREFIX):
        rest, toolset, short = _split(top)
        return {"toolset": toolset, "tool": short, "args": ti, "shape": "new", "full": rest}
    return {"toolset": "", "tool": "", "args": {}, "shape": ""}


def is_tool(name, *wanted):
    """True when `name` (any shape) ends with one of the wanted short names, compared without case or underscores."""
    n = norm(name)
    return any(n.endswith(norm(w)) for w in wanted)


def script_text(call):
    """The script of a programmatic call (execute_tool_script / execute_python), or ''."""
    if not is_tool(call.get("full") or call.get("tool"), *SCRIPT_TOOLS):
        return ""
    a = call.get("args") or {}
    return " ".join(str(v) for v in a.values() if isinstance(v, str))
