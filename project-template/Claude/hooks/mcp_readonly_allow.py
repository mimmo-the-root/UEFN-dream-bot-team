"""mcp_readonly_allow.py - PreToolUse hook (v1.124.21): UEFN editor tools that only LOOK (get, list, find, search, describe...)
are allowed without a permission prompt. Without it, a session that nobody is watching (the mailbox worker, `claude -p`,
free models) stops at the first read of the level and waits for a click that never comes.
Tools that change something (set, spawn, delete, save, build, run Python...) are untouched: they keep asking as before.
The other guards (mcp_heavy_guard, editor_lock) still run and can still refuse: a refusal wins over this allow.
Switch off: UEFN_KIT_MCP_READ_ALLOW=0."""
import json, os, re, sys

READ = {"get", "list", "find", "search", "describe", "read", "query", "inspect", "count", "check", "validate", "preview",
        "status", "info", "lookup", "fetch", "show", "is", "has", "exists", "help", "explain", "summarize", "summary", "snapshot"}
CHANGE = {"set", "spawn", "create", "add", "delete", "remove", "destroy", "save", "write", "build", "compile", "exec", "execute",
          "run", "python", "import", "move", "rename", "duplicate", "replace", "apply", "place", "attach", "detach", "modify",
          "update", "edit", "launch", "start", "stop", "publish", "push", "undo", "redo", "load", "open", "close", "and"}


def action(tool):
    """The verb of a UEFN tool name: GetProjectContext -> get, find_assets -> find, ..._Toolset_ListLevels -> list."""
    name = tool.split("__", 2)[-1]
    tail = re.split(r"(?:Toolset|Tools)_", name)[-1]
    m = re.match(r"([A-Za-z][a-z]*)", tail)
    return (m.group(1).lower() if m else ""), tail


def words(s):
    return [w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", s)]


def decide(tool):
    """allow for a read-only UEFN tool, None for everything else (the normal permission flow decides)."""
    if not tool.startswith("mcp__unreal-mcp__"):
        return None
    verb, tail = action(tool)
    if verb in READ and not (set(words(tail)[1:]) & CHANGE):
        return "allow"
    return None


def main():
    if os.environ.get("UEFN_KIT_MCP_READ_ALLOW") == "0":
        return
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if decide(data.get("tool_name", "")) == "allow":
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                                 "permissionDecisionReason": "read-only UEFN editor tool (kit rule)"}}))


if __name__ == "__main__":
    main()
