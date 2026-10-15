---
description: Map UEFN's MCP now (the kit also does it by itself) and show what is new
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

The kit maps UEFN's MCP server by itself: at each session start it checks, and when UEFN is open and the map is older than 6 hours it re-maps in the background and tests the safe tools. This command does the same right now.

Run from the project folder: `py -3 Claude/hooks/mcp_map.py --now` (use `python` if `py` is missing). It needs UEFN open. It prints one JSON line:

- `first_snapshot`, `unchanged` or `changed` (with the new, removed and changed tools and what each new one does), plus how many tools the kit uses and what the tests found (`stopped_working` lists tools that worked before and now fail).
- `not_reachable`: UEFN is closed or the MCP is off. Say so; the saved map stays as it was.
- `odd_reply`: the server answered in a format the kit does not understand yet. Run `py -3 Claude/hooks/mcp_map.py --probe Claude/logs/mcp-probe.json` and tell the owner; do not build a map by hand from memory.

Report in at most 8 lines, then at most three ideas (clearly marked as proposals) for what the news could do for the owner's maps. Change nothing because of them without a yes. The map is searchable with `mcp_map.py --find <words>`.
