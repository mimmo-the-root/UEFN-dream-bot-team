# Contract: use the whole MCP (map first)

**Why:** the MCP is the engine and it grows fast, often without announcement. The kit maps it by itself (`Claude/hooks/mcp_map.py`, run at session start when UEFN is open) into one private catalog shared by all projects: `~/.claude/skills/mcp-tool-contracts/references/map/` (`MAP.md` overview, `NEWS.md` what is new, `tests.json` which safe tools were called and worked).

**Use:** before any MCP work, `py -3 Claude/hooks/mcp_map.py --find <keywords>` (a few words about what you want to do; in a Fab product, which has no `Claude/hooks`, run `~/.claude/kit-template/Claude/hooks/mcp_map.py`). To rename or move an asset the tool is `AssetTools/move`, found this way. Prefer a purpose-built tool from the map over scripting around it. A read-only tool the contracts below do not cover is fine to use after `describe_toolset`; a writing tool follows the rules of the contract it belongs to and asks first.

**Don't use:** a tool name from memory or guesswork; a map older than a UEFN update (run `py -3 Claude/hooks/mcp_map.py --now`, UEFN open). If the map is missing or says `not_reachable`, work from `describe_toolset` and say so.

**Procedure:** when the session start brings "MCP news", tell the owner in two lines what is new and what it could do, and propose; when a new tool proves itself in real work, add a contract here and its name to `Claude/reference/mcp-known-tools.json`.