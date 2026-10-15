# Exploration mission for UEFN's MCP (reusable)

Use it to learn what the MCP really does after a UEFN update, or to cover tools nobody has tried. The agent that runs it is Claude Code in a project; the lab module is `Claude/hooks/mcp_lab.py` (every call is logged to `Claude/logs/explore-ledger.jsonl`, refusals are enforced by the code).

## Where to run it

- **Laboratory (preferred, aggressive):** a clean, disposable project. Steps: copy the project template into it, create the file `Claude/LAB-PROJECT.txt` (any text), enable "Python Editor Scripting" and "UEFN MCP Toolsets", open Claude Code in it, and in PowerShell set `$env:LAB_AGGRESSIVE = "1"` and `$env:LAB_ROOT = "/<project name>"` (for example `/lab_mcp`) before running any script. The lab refuses to start unless the marker file exists AND the open level lives under `LAB_ROOT`. Inside it everything is allowed (delete, level writes, sessions, Verse edits, Python); quitting or restarting the editor and any disk path outside the project are still refused.
- **A real project (careful):** do not set LAB_AGGRESSIVE. Assets only in `<root>/KitTest`; `LAB_LEVEL=1` and `LAB_SESSION=1` only for the phases that need them.

## Phases (one knowledge file per area after each discovery)

1. Assets and UI: UMGToolSet, MVVMToolset, WidgetAnimationToolset, VerseFieldsToolset, AssetTools, DataTable, CurveTable. Text in widgets probably goes through a template (`ReplaceWidgetWithTemplate`).
2. Materials, Niagara, Physics, SkeletalMesh (work on copies in a real project, directly in the lab).
3. Editor and live logs: EditorAppToolset (camera, show flags, selection, viewport capture: where is the file saved?), LogsToolset (how to read only the NEW lines after an action; verbosity with restore).
4. Level and devices: Actor, Scene, Entity, Device toolsets: place a device, read and set its properties, bind an event, entities and components, tags, folders; then remove what was created.
5. Verse: read files, create a new file, `BuildAll`, read the compile errors, fix, rebuild.
6. Game session and regressions: StartSession, wait for connected, GetGameState, StartGame, GetClientLogEntries with a pattern, StopGame, StopSession (always, in a finally); then the loop "edit, compile, push, read the client log, verdict" with timings.
7. Batch scripts: ProgrammaticToolset `execute_tool_script` template chaining 5 or more tools.
8. Close: `L.coverage()`, list the tools never tried and why, restore any editor state changed.

## Rules for the explorer

- Three attempts per tool at most; write the exact error and move on.
- Save knowledge per area, immediately after each discovery, in `Claude/logs/explore-area-<area>.md` with this fixed shape: what the area is for and its tools (tried yes/no); verified recipes with exact arguments and call order; traps (exact message and the way around); what does not work or is forbidden; small tasks a sub-agent of that area could receive and what it returns to the orchestrator; tools never tried and why. Keep `Claude/logs/explore-status.md` current every ten minutes and `Claude/logs/recipes.json` for verified recipes (placeholders such as `{widget_bp}`, `{sandbox}`, `{actor}`).
- If UEFN does not answer for 60 seconds: write a note in the status file and stop.
- Never work around a refusal of the lab; report it.

## What happens with the result

The owner's assistant consolidates the area files into `references/areas/<area>.md` (kept in the kit, never to be redone), the recipes feed the automatic coverage battery (about 20% of the tools per run), and each solid area becomes a skill for a sub-agent. The coder is the orchestrator: it splits a job into small tasks, hands each to the area sub-agent, and the reviewers close the loop (the diamond: one orchestrator, area specialists in the middle, reviewers at the end).
