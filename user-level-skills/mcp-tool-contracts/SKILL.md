---
name: mcp-tool-contracts
description: Canonical, single-source-of-truth mapping of "what I want to do via UEFN's MCP server" to "the exact tool that actually works for it in this kit's setup" — referenced by coder, qa-regression, and project-bootstrap instead of each describing the check in its own words.
---

# MCP tool contracts

Every agent that talks to UEFN's MCP server needs to do the same handful of things (verify which
project is open, list real project content, and so on). This file is the ONE place that says which
tool actually does each of those things in this kit's setup — every agent file references this
file by name instead of restating the instruction in its own prose.

**Why this file exists**: a v1.67 incident traced back to the exact same generic instruction
("list a couple of files through the MCP tools") appearing, worded slightly differently, in three
separate agent files (`coder.md`, `qa-regression.md`, `project-bootstrap.md`). `coder` picked
`AssetTools.find_assets` on `/Game` — the intuitive-sounding choice — which silently returns
nothing useful for this kit's custom project content even with the right project open, and reads
exactly like "the wrong project is open in UEFN," sending debugging in the wrong direction. Fixing
the wording in all three files at once worked, but it relied on remembering to touch all three
every time this file's contents change. A single referenced file can't diverge from itself.

## Contract: verifying which project UEFN has open

**Use:** `ValkyrieToolset.VerseToolset.ListFiles`, called through `mcp__unreal-mcp__call_tool` (`toolset_name` = `ValkyrieToolset.VerseToolset`, `tool_name` = `ListFiles`): the dotted names in this file are values of those arguments, never separate tools to look for in the tool list

**Don't use:** `AssetTools.find_assets` on `/Game` — it silently returns nothing useful for this
kit's custom project content even when the correct project is open in UEFN. This is a
configuration-specific quirk of this MCP/UEFN setup, not documented anywhere in Epic's own docs as
of this writing — see the entry in `~/.claude/skills/uefn-lessons/SKILL.md`'s "MCP / tooling
quirks" for the original discovery.

**Procedure:** list the project's real Verse/asset content with `ValkyrieToolset.VerseToolset.ListFiles`
and check the path/name against the value already written at the top of the project's `CLAUDE.md`,
in the "Project identity" section — never the current folder's name (`Content`, identical across
every project). If the listing doesn't match, or is ambiguous, STOP and warn the owner: UEFN
probably has a different project open. Every agent that touches MCP before writing/modifying
anything runs this check first (`coder`, `qa-regression` before a play-session, `project-bootstrap`
during initial analysis).

## Contract: detecting MCP mode (before reading or changing anything in the level)

**How the tools are called:** in this kit the UEFN tools are reached through the single MCP tool `mcp__unreal-mcp__call_tool` (the name of the MCP server can differ per machine, look for a `call_tool`), with arguments like `{"toolset_name": "ValkyrieToolset.VerseToolset", "tool_name": "ListFiles", "arguments": {}}`. A tool list that shows only `...call_tool` is NOT `offline`: make the call through it. If the first call answers with a schema error, the tool exists: read the schema it returns and retry with the right arguments. Only when no such MCP tool exists, or the call fails with a connection error, is the mode `offline` (UEFN closed or the MCP not running): then say which of the two it was.

**Modes:** `live` = the UEFN MCP answers (`ValkyrieToolset.VerseToolset.ListFiles` works and matches the project identity, see above). `offline` = no MCP tools, or the check fails.

**Procedure:** run the project-identity check once per session. In `live` mode you may read devices and wiring in the level (read-only unless the task is a change). In `offline` mode work from the Verse map and the code only, and name in the report exactly which devices, settings and wiring were not inspected. Never skip the level silently and never guess device settings.

## Contract: reading the devices placed in the level (read-only, only when the mode is `live`)

**Tools seen working in this kit's logs** (names can change with UEFN updates; if one is missing, call `describe_toolset` on its toolset and use the closest read tool): `editor_toolset.toolsets.scene.SceneTools.find_actors` (which device actors of a class exist and where), `ValkyrieToolset.DeviceToolset.ListEventBindings` (wiring between devices), `ValkyrieToolset.DeviceToolset.GetDeviceProperties` / `ListDeviceProperties` (settings), `editor_toolset.toolsets.object.ObjectTools.get_properties`.

**Procedure:** first reuse what is already written: if the project has `Claude/docs/DEPENDENCY-MAP*.md` or `Claude/docs/map/DEVICES.md`, learn from it and do not call the MCP again for the same facts. Otherwise read only the device classes that the Verse map cards reference (`@editable` types), one class at a time, and write the result compactly to `Claude/docs/map/DEVICES.md` (class, count, who wires it to whom, the few settings that matter). Counts per class are only the start: the wiring (`ListEventBindings`) and the key settings (`GetDeviceProperties`) are the information the next sessions need, so read them in the same pass (max 40 devices per pass, most-referenced first, list the rest). Never change anything in the level while learning. Facts only: a device nobody references in the sources you searched is "no reference found in <sources>", never "unused".

## Contract: reading the island configuration and deducing the shape of the game (read-only, `live` mode)

**Use:** the Island/Experience Settings device (class name contains `IslandSettings`, seen as "Experience Settings"), the team and inventory settings, and the Player Spawner devices, found with `find_actors` and read with `GetDeviceProperties` or `ObjectTools.get_properties`. Read them in the first learning/bootstrap pass, together with the device wiring.
**Don't use:** the owner. Max players, teams, rounds, time limit, win condition, spawn mode, vehicles per player are FACTS in the level: never put them in a "to confirm" list. Never change a setting.
**Procedure:** read the settings and group the Player Spawners by position cluster, `priorityGroup`, `useAsIslandStart`, `visibleInGame`, team and outgoing bindings. Deduce and write, each with its evidence and marked `[I]`: (1) max players and teams; (2) a cluster flagged island-start, hidden in game and with no bindings is a PRE-LOBBY (Epic's pregame-lobby pattern), a cluster whose spawn event drives vehicles, loadouts or a countdown is the GAME START; (3) compare capacity: game-start pads and vehicles per player versus max players, and report the gap as a finding, not as a question; (4) rounds, time limit and win condition from the settings. Write the result as `## Island configuration` in `Claude/docs/map/DEVICES.md` and as deduced facts in SPEC.md. When a deduction rule worked, queue it as a pattern in the genre skill (`skills_lib.py propose --section run-loop` or `devices`) so the next map starts from it.

## Adding a new contract

When a new MCP-tool gotcha gets discovered (a tool that seems right by name but doesn't do what's
expected, or two tools that both technically work but one is clearly the intended one for this
kit), add it here as a new `## Contract:` section with the same three fields — Use / Don't use /
Procedure — rather than describing it inline in whichever agent file happened to discover it. Also
add a short entry to `~/.claude/skills/uefn-lessons/SKILL.md` if the gotcha would help on a
different island, not just this project (see that skill's own guidance on the "would this help on
a different island?" test).
