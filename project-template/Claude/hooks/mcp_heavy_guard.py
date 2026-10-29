#!/usr/bin/env python3
"""mcp_heavy_guard.py - PreToolUse hook: refuses the UEFN MCP reads that are known to be huge, before they reach the editor.
No AI, no network. A rule in a skill is a request; this is a key.

  find_assets with none of folder_path, name, asset_type, tags     ~120 MB, the MCP connection closes
  GetLogEntries with maxEntries 0 and no pattern                    ~2.4 MB

On a refusal the reason tells what to pass instead (see the skill uefn-mcp-heavy-calls). Switch off with UEFN_KIT_GUARD=0.
Never fails loudly: any error allows the call."""
import json, os, sys

FIND_FILTERS = ("folder_path", "name", "asset_type", "tags")


def _args(ti):
    a = ti.get("arguments", ti.get("args", {}))
    if isinstance(a, str):
        try:
            a = json.loads(a or "{}")
        except ValueError:
            a = {}
    return a if isinstance(a, dict) else {}


def verdict(tool, args):
    """Returns '' to allow, or the reason to refuse."""
    if tool == "find_assets" and not any(args.get(k) for k in FIND_FILTERS):
        return ("Refused by the kit: find_assets without a filter returns about 120 MB and closes the MCP connection. "
                "Pass folder_path (for the farm props: /CR_Legacy/Playsets/PlaysetProps) plus name, or asset_type or tags. "
                "See the skill uefn-mcp-heavy-calls and Claude/docs/demo-chicken-roundup/SCENERY.md. Do not work around this refusal.")
    if tool == "GetLogEntries" and str(args.get("maxEntries", "")) == "0" and not args.get("pattern"):
        return ("Refused by the kit: GetLogEntries with maxEntries 0 and no pattern returns about 2.4 MB. "
                "Pass a pattern (see the skill uefn-mcp-heavy-calls). Do not work around this refusal.")
    return ""


def main():
    try:
        if os.environ.get("UEFN_KIT_GUARD") == "0":
            return 0
        p = json.loads(sys.stdin.read() or "{}")
        ti = p.get("tool_input") or {}
        why = verdict(str(ti.get("tool_name") or ""), _args(ti))
        if why:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
