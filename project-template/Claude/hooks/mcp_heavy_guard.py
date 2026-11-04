#!/usr/bin/env python3
"""mcp_heavy_guard.py - PreToolUse hook: refuses the UEFN MCP reads that are known to be huge, before they reach the editor.
No AI, no network. A rule in a skill is a request; this is a key.

  find_assets / FindAssets with none of folder_path, name, asset_type, tags     ~120 MB, the MCP connection closes
  GetLogEntries with maxEntries 0 and no pattern                    ~2.4 MB

On a refusal the reason tells what to pass instead (see the skill uefn-mcp-heavy-calls). Switch off with UEFN_KIT_GUARD=0.
Never fails loudly: any error allows the call."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcp_names as N

FIND_FILTERS = ("folder_path", "name", "asset_type", "tags")
# UEFN 43.00 writes them camelCase and nested: {"filter": {"folderPath": ..., "name": ..., "assetType": ..., "tags": ...}}
FIND_NORMS = ("folderpath", "name", "assettype", "tags", "path", "class")


def has_filter(args):
    """True when a FindAssets call carries at least one real filter, in the old flat form or the 43.00 nested camelCase form."""
    stack = [args if isinstance(args, dict) else {}]
    if isinstance(stack[0].get("filter"), dict):
        stack.append(stack[0]["filter"])
    for d in stack:
        for k, v in d.items():
            if "".join(c for c in str(k).lower() if c.isalnum()) in FIND_NORMS and v not in (None, "", [], {}, False):
                return True
    return False


def _args(ti):
    a = ti.get("arguments", ti.get("args", {}))
    if isinstance(a, str):
        try:
            a = json.loads(a or "{}")
        except ValueError:
            a = {}
    return a if isinstance(a, dict) else {}


def verdict(tool, args, script=""):
    """Returns '' to allow, or the reason to refuse. `tool` may be any shape (find_assets, FindAssets, EditorToolset_AssetToolset_FindAssets).
    `script` is the text of a programmatic call: a script that calls FindAssets with none of the filter names written in it is refused too."""
    if script and N.is_tool("FindAssets", "FindAssets") and "findassets" in N.norm(script) and not any(k in script for k in FIND_FILTERS + ("folderPath", "assetType")):
        return ("Refused by the kit: this script calls FindAssets with no filter (folder_path, name, asset_type or tags), which returns about 120 MB and closes the MCP connection. "
                "Add a filter inside the script. See the skill uefn-mcp-heavy-calls. Do not work around this refusal.")
    if N.is_tool(tool, "find_assets") and not has_filter(args):
        return ("Refused by the kit: find_assets without a filter returns about 120 MB and closes the MCP connection. "
                "Pass folder_path (for the farm props: /CR_Legacy/Playsets/PlaysetProps) plus name, or asset_type or tags. "
                "See the skill uefn-mcp-heavy-calls and Claude/docs/demo-chicken-roundup/SCENERY.md. Do not work around this refusal.")
    if N.is_tool(tool, "GetLogEntries") and str(args.get("maxEntries", "")) == "0" and not args.get("pattern"):
        return ("Refused by the kit: GetLogEntries with maxEntries 0 and no pattern returns about 2.4 MB. "
                "Pass a pattern (see the skill uefn-mcp-heavy-calls). Do not work around this refusal.")
    return ""


def avoided(call):
    """The tools that stopped the editor (mcp-avoid.json next to this file, and the avoid.json the map made on this computer). '' to allow."""
    try:
        key = "%s/%s" % (call["toolset"], call["tool"])
        here = os.path.dirname(os.path.abspath(__file__))
        places = [os.path.join(here, "mcp-avoid.json"), os.path.join(os.environ.get("UEFN_KIT_MCP_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills", "mcp-tool-contracts", "references", "map"), "avoid.json")]
        low = key.lower()
        for p in places:
            try:
                data = json.load(open(p, encoding="utf-8-sig")).get("avoid", {})
            except (OSError, ValueError):
                continue
            for k, v in data.items():
                if k.lower() == low or N.norm(k) == N.norm(key):
                    return ("Refused by the kit: %s stopped the editor before (%s). Ask the owner, who can try it in a throwaway project and then remove it from mcp-avoid.json. "
                            "Do not work around this refusal." % (k, (v or {}).get("why", "no reason saved")))
    except Exception:
        pass
    return ""


def wrong_owner(payload, call):
    """A sub-agent of the kit calling a tool that belongs to another agent (hooks/mcp_owner.py). The main session is never limited, and a payload
    that does not name an agent is not judged. Switch off with UEFN_KIT_OWNERS=0. '' to allow."""
    try:
        if os.environ.get("UEFN_KIT_OWNERS") == "0":
            return ""
        agent = str((payload or {}).get("agent_type") or "")
        if not agent or not call.get("tool"):
            return ""
        import mcp_owner as O
        if O.allowed(agent, call["toolset"], call["tool"]):
            return ""
        return O.refusal(agent, call["toolset"], call["tool"])
    except Exception:
        return ""


def main():
    try:
        if os.environ.get("UEFN_KIT_GUARD") == "0":
            return 0
        p = json.loads(sys.stdin.read() or "{}")
        c = N.read(p)
        why = verdict(c["tool"], c["args"] if c["shape"] == "new" else _args(p.get("tool_input") or {}), N.script_text(c)) or avoided(c) or wrong_owner(p, c)
        if why:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
