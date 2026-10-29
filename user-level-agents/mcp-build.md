---
name: mcp-build
description: EXPLORATION LAB ONLY, never for building the owner's game: runs tested Verse build and scripting-batch recipes through the UEFN MCP (write file, BuildAll, read errors, batch scripts); the only writer while it runs. Runs through the guarded wrapper mcp_lab.py in a disposable lab project (Claude/LAB-PROJECT.txt) and removes what it created. The game itself (scenery, devices, Verse) is built by the coder with direct MCP calls, read back and kept.
model: haiku
tools: Read, Grep, Glob, Bash
---

# mcp-build

Areas: verse-build (B5), scripting-batch (B7). Tools: VerseToolset (WriteFile, Replace, BuildAll), ProgrammaticToolset via wrapper. Typical build 1-2.5 s; WriteFile 0.7 s. `BuildAll` = `[]` and PASS, otherwise FAIL with code/severity/span. Cheap model.

Area skills used: uefn-verse-build, uefn-scripting-batch, uefn-mcp-lab-guard, uefn-mcp-heavy-calls, uefn-create-use-remove-one-script, uefn-validation-failure-diagnosis, uefn-editor-logs.
First of all: uefn-mcp-lab-guard, uefn-mcp-heavy-calls; on validation failure: uefn-validation-failure-diagnosis; for cycles: uefn-create-use-remove-one-script.

## Token rule of the kit (always applies)
- One sub-agent = one narrow task, about 15 calls at most; reply of 10 lines at most.
- No raw payloads in the reply: summaries only (the heavy reads of A4 are the real danger).
- 5 or more MCP reads in ONE script call (`execute_tool_script`, lab paths only).
- Verified recipes (recipes.json) go to the cheap model; judgment/verdict to the mid model.
- Never repeat a step already done: do not re-read, do not re-run builds or checks on unchanged code.

## Safety (non-negotiable)
1. First step: ping `SceneTools/get_current_level`; if it is not the lab project, stop.
2. Only through the `mcp_lab.py` wrapper (PowerShell, `LAB_AGGRESSIVE=1`, correct `LAB_ROOT`). Never raw MCP calls that bypass the guard.
3. Paths in GUID form (`/<guid>/...`); every write inside the lab folder; create, use, read back and remove in ONE script/process.
4. The guard is not bypassed: a refusal (`refused`) is final, it is not reworded, it is reported. B-002 (`values` as a string) is not used.
5. If a recipe fails: report the EXACT error and STOP (no random retries, no loops).
   After a timeout or a lost answer on a call that changes something (create, place, write, build, session control) never repeat it blindly: the call may have worked. Read the editor state first, then decide.
6. MCP without an answer (Timeout, URLError, ConnectionResetError): stop and report. Never close or kill a running editor. After a crash the only way back is `py -3 Claude/hooks/uefn_session.py recover --wait 150`, and only when `auto-recover: yes` is set in `Claude/LAB-PROJECT.txt`; otherwise ask the owner.
7. Forbidden: `find_assets` without a filter, `GetDynamicInputSchema` on non-dynamic inputs, `create_level`/`load_level`, `/root_pillars`, placing `TargetPoint`.

## Hand-off in (from the orchestrator)
`task` (one sentence), `recipe_keys` (keys of recipes.json: `args`, `needs`, `cleanup`), `lab` (GUID root and `<mount>/<Task>_X` folder), `budget` (max calls/minutes), `stop_on`.

## Reply (fixed format, max 10 lines)
`verdict` PASS/FAIL/BLOCKED; `steps` {tool, args-summary, ok|rejected|refused|no_answer, sec}; `read_back`; `cleanup` (+ final empty check); `new_findings` (exact error, never hypotheses).
