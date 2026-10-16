# MCP area: scripting-batch (ProgrammaticToolset, ValkyriePythonToolset)

Date: 2026-10-15. UEFN version: 42.40 (from previous-findings.md, same editor). Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (LAB_ROOT = GUID mount, PowerShell, scripts run from `Content`), task T-007. 4 tools in the area, 4 tried ok. Scratch scripts: `Claude/logs/_explore/s0.py`..`s10.py`.

## 1. What the area is for, tools

Run a short Python script inside the editor that calls other MCP tools in one round trip (fewer calls, less editor load), and check/enable the editor's Python.

| Tool | R/W | Tried |
|---|---|---|
| ProgrammaticToolset/execute_tool_script {script} | W (whatever the inner tools do) | yes ok |
| ProgrammaticToolset/get_execution_environment {} | R | yes ok |
| ValkyriePythonToolset/IsPythonEnabledInUEFN {} | R | yes ok (true) |
| ValkyriePythonToolset/EnablePythonInUEFN {} | W | yes ok (null, already enabled) |

Toolset names: `editor_toolset.toolsets.programmatic.ProgrammaticToolset` and `ValkyrieToolset.ValkyriePythonToolset`. Inside a script the tool is named `<toolset>.<tool>` (full dotted name).

## 2. Verified recipes (all in `recipes.json`)

R1 Batch of 8 reads in one call (0.4 s per call, 0.069 s inside the script; ledger row 820): `execute_tool_script` with the script in recipe `execute_tool_script#batch_reads`: level, content browser path, widget blueprint count, game state, session status, Verse ListFiles, supported Verse field types (length), Python flag, plus `secs` timing. Reply: `{"returnValue": "<JSON text of the dict>"}` (the dict comes back as a JSON STRING: `json.loads` it).

R2 Script shape (from `get_execution_environment`): define `run()` returning a dict; call `execute_tool("<Toolset>.<Tool>", json.dumps(args))["returnValue"]`; arguments MUST be a JSON string, not a dict. Allowed modules: json, math, datetime, copy, re, time.

R3 Create and build a widget in ONE script (recipe `create_widget_chain`): CreateWidgetBlueprint, AddWidget Overlay (`parentWidget` None), AddWidget StackBox under it, GetWidgets, CompileWidgetBlueprint (true), `save_assets` (true), `exists` (true), `is_dirty` (false). Verified in one script (ledger row 866, 2.14 s: compile true, saved true, exists true, is_dirty false, 2 widgets), then deleted with `AssetTools/delete {path: R+"/Scr007b"}` (row 867, true; row 868 `exists` false). Earlier attempt with VerticalBox was refused (rows ~848-851).

R4 Edit Verse and build in one script: see recipe `execute_tool_script#verse_edit_build` and verse-build.md R5 (two builds, 4.9 s).

R5 Python flag: `IsPythonEnabledInUEFN` returns `true`; `EnablePythonInUEFN` returns `null` and leaves it `true` (idempotent). Both also callable from inside a script.

Previous findings re-run: "execute_tool_script batches calls with the full dotted name and json.dumps args; allowed imports json, math, datetime, copy, re, time": **riconfermata** (6 reads, then 8 tools across 6 toolsets). "Output schemas are not in the tool list": **riconfermata** (read each reply once). "execute_tool_script can write too (added a widget and read the count back)": **riconfermata** (R3). "Parent widget must be explicit; first widget a panel": **riconfermata** (Overlay root with `parentWidget: None`).

## 3. Traps (exact messages)

1. Forbidden import: `Import of 'os' is not permitted. Allowed modules: frozenset({'json', 'time', 'math', 'datetime', 'copy', 're'})` (same for subprocess, sys, unreal). `__import__("os")` gives the same as a ValueError.
2. `run()` missing: `Script must define a callable run() function.`; wrong return type: `run() must return a dict[str, Any], returned list`; syntax error: `invalid syntax (<unknown>, line 1)`.
3. A failing inner tool CANNOT be caught: `try/except Exception`, `except RuntimeError` and bare `except:` all fail to catch it; the whole script aborts with the tool's own message (e.g. `line 3: RuntimeError: Script error in ValkyrieToolset.VerseToolset.ReadFile:\npath did not resolve under ...`, or just `file does not exist: '...'`). So the script is not a place for "try this, else that": check with `exists`/read tools first. Ordinary Python exceptions (ValueError raised by the script) ARE catchable: `except Exception as e` works.
4. NO ROLLBACK: a script that aborts keeps every write done before the error. Seen: a script created `WBP_Scr007`, added the Overlay, then `AddWidget VerticalBox` raised `AddWidget: WidgetClass 'VerticalBox' is not permitted in this project.`; the blueprint with its Overlay stayed in the project. Always clean up after a failed script.
5. Arguments as dict: `TypeError: the JSON object must be str, bytes or bytearray, not dict` (use `json.dumps`).
6. Unknown tool: `ToolsetIsNotRegistered: No.Such is not registered`.
7. Recreating an existing asset: `CreateWidgetBlueprint: Failed to create blueprint 'WBP_Scr007' at '...` (script aborts).
8. The return value is a JSON string; also `eval` and `exec` are `NameError: name 'eval' is not defined`.
9. The lab guard sees only the outer call (`execute_tool_script` and its script text), not the inner tool calls: the ledger has ONE row per script. Inner calls are bounded by the editor itself (e.g. `AssetTools.delete` of `/root_pillars/Nothing`: `FolderPath "/root_pillars/Nothing" is outside this project's valid asset roots ...`), not by the lab. Treat script contents as if they had no guard: only put LAB_ROOT paths in them.

## 4. What does NOT work or is forbidden here

- Modules other than json, math, datetime, copy, re, time (os, subprocess, sys, unreal all refused); `eval`, `exec` not defined.
- File writes: `open(..., "w")` gives `ValueError: Mode 'w' is not permitted. Allowed modes: ['r', 'rb', 'rt']`. Reads are only allowed in the editor's allowed directories: a path in this project's `Content\Claude` folder was refused (`Path '...' resolves to '...', which is outside all allowed directori...`); a relative name resolves against the Fortnite install folder. No disk access outside the project was exercised on purpose (a first probe omitted the mode and failed before reading anything).
- No state survives between scripts (globals hold only `__builtins__` and `run`).
- Not tried on purpose: sandbox-escape attempts beyond import/open/eval/exec (not in the lab's scope). Note that dunder attribute access (`(1).__class__.__mro__`) is possible, so the Python sandbox is a convenience filter, not a security boundary.
- Scripts cannot catch tool errors (trap 3), cannot roll back (trap 4).

## 5. Limits measured

- Time: 5 million loop iterations 0.12 s; 100 million iterations 2.1 s with no timeout hit; `time.sleep(3)` works (call took 4.4 s). Typical overhead per call 0.3 to 0.4 s.
- Result size: a 2 MB string came back whole (no truncation seen). Keep returns small anyway; Epic warns heavy calls can hitch the editor.
- Nesting: a script can call `execute_tool_script`'s sibling `get_execution_environment` and `IsPythonEnabledInUEFN`.

## 6. Tasks for a subagent

1. "Batch read": given up to 8 read tools with arguments, build one script returning a dict keyed by tool; return the parsed dict and seconds.
2. "Build widget": run recipe `create_widget_chain` with a folder and name under LAB_ROOT; return compile/save flags, then delete the folder and report `exists` false.
3. "Edit and build Verse": recipe `verse_edit_build`; return diagnostics.
4. "Safe script": before a write script, check `exists` in the script itself, and on any failure return nothing: list what was written (no rollback) and delete it.
5. "Python check": `IsPythonEnabledInUEFN`; if false, `EnablePythonInUEFN` then re-check.
Return to the orchestrator: the dict, seconds, and every path created or deleted.

## 7. Tools not tried and why

None: all 4 tools were called with real arguments (ledger ok). Not tried: scripts longer than 100 million operations (no timeout found up to 2 s; the real limit is unknown), and results over 2 MB.
