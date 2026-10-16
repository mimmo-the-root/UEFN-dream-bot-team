# MCP area: session-regression (SessionToolset + the cycle modify -> compile -> PushChanges -> log -> verdict)

Date: 2026-10-15. UEFN version: 42.40. Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (PowerShell, run from `Content`; Git Bash mangles LAB_ROOT). Task T-006, 4th attempt (the first 3 were blocked, cause found, see section 3). Activation: `$env:LAB_AGGRESSIVE="1"; $env:LAB_ROOT="/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab"`. Scratch: `Claude/logs/_explore/s6_h.py` (helpers), `s6_b.py` (session), `s6_c.py` (cycle).

## 1. Tools

Toolset `ValkyrieToolset.SessionToolset` (8 tools, 8 tried, 7 answered ok, GetClientLogEntries only returned its error). Async tools return `Completed` | `Failed` | `StillRunning`.

| Tool | R/W | Tried |
|---|---|---|
| GetSessionStatus {} | R | ok: Disconnected / Connected / UpdatingContent (see C2 update) |
| GetGameState {} | R | ok: Unconnected / CanStart / Running |
| StartSession {location?, rotation?} | W | ok `Completed` after 67-87 s (the reply text can be a stale error: check GetSessionStatus) |
| StartGame {} | W | ok `Completed` 0.3-0.4 s, state -> Running; `The Start Game command is not currently available.` unless status is Connected after the content update (C2 update) |
| PushChanges {bVerseOnly?} | W | ok `Completed` 7.9 s after a real change; `The Refresh command is not currently available.` when nothing changed or right after connect |
| GetClientLogEntries {pattern (required, not empty), maxResults?, startLine?} | R | only error: `No client log was found; start a play-in-client session first.` (also while GetGameState = Running) |
| StopGame {} | W | ok `Completed` 1.5 s |
| StopSession {} | W | ok null, <0.1 s, status back to Disconnected |

## 2. Verified recipes (exact arguments; `S` = `ValkyrieToolset.SessionToolset`, `V` = `ValkyrieToolset.VerseToolset`)

R1 Full session, always in try/finally (ledger ok, 2 runs):
1. ping with a cheap read (`editor_toolset.toolsets.scene.SceneTools/get_current_level`, 0.3-1.6 s) before every action; stop if it fails.
2. `S/StartSession {}` -> `Completed` after 67-79 s; then `GetSessionStatus` = `Connected`, `GetGameState` = `CanStart`.
3. `S/StartGame {}` -> `Completed`; `GetGameState` = `Running` at once.
4. finally: `S/StopGame {}` (1.5 s) then `S/StopSession {}`; `GetSessionStatus` = `Disconnected`.

R2 Why a StartSession fails (discovery recipe): `EditorToolset.LogsToolset/GetLogEntries {"category":"","maxEntries":0,"pattern":"UEFNValidation"}` returns e.g. `UEFNValidation: Error: Disallowed reference to /Script/Engine.TargetPoint, Referenced by: ...` and `UEFNValidation: Error: \t TargetPoint_Spawn (...)`. The MCP answer is only `Failed: Validation failed`; the reason is ONLY in the editor log.

R3 Regression cycle with verdict and timings (one iteration, ~10 s without StartSession):
1. `V/WriteFile {path: R+"LabSessionCycle.verse", content, bCreateIfMissing:true}` 0.7 s (R = `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/`).
2. `V/BuildAll {}` 1.0-2.3 s; `[]` = PASS, otherwise FAIL with code and span.
3. only if PASS and a session is Connected: `S/PushChanges {"bVerseOnly":true}` 7.9 s.
4. read the new editor log lines with the cursor recipe of editor-logs.md 2.1.
5. verdict.

R4 Deliberate failing test: `V/Replace` puts `BadValue : int = "not an int"` in `OnBegin`; `BuildAll` returned `[{"severity":"Error","code":3509,...,"span":{"startLine":13,...}}]` -> the cycle detects it at the BUILD step (FAIL, 2.3 s), before any push. Reverting with `V/Replace` + `BuildAll` = `[]` PASS. With the session open, `PushChanges` on the broken source answered `The Refresh command is not currently available.` (no crash, session healthy), so the BUILD result is the gate, not the push result.

Timings measured: StartSession 67-79 s, StartGame 0.4 s, PushChanges 7.9 s, BuildAll 1.0-2.3 s, StopGame 1.5 s, StopSession <0.1 s; cycle build+push ~10 s.

## 3. Traps

- ROOT CAUSE of the 3 earlier `StartSession -> Failed: Validation failed` (then MCP hang for minutes): the actor `TargetPoint_Spawn` (class `/Script/Engine.TargetPoint`, placed in T-004) triggered `UEFNValidation: Error: Disallowed reference to /Script/Engine.TargetPoint` (+ 2 warnings "Illegal property override" on SpriteComponent/ArrowComponent). It was NOT args, stale client, Verse build or leftover state (earlier notes guessed those). After the owner removed the actor StartSession worked again.
- After a validation failure the editor MCP stops answering for minutes; ping before every action and stop (never loop) if it does not answer.
- StartSession is slow (67-79 s) but returns `Completed` only once connected.
- `GetClientLogEntries {pattern:""}` -> `Pattern must not be empty.`
- `PushChanges` -> `The Refresh command is not currently available.` right after connecting or with no change since the last push; make a Verse change first.
- The editor log has no client lines (searched `T006CYCLE`, 0 hits): an unplaced device's `Print` never runs, and placing the lab-built device class is refused by the lab guard (T-005 gap).

## 4. What does not work or is forbidden

- `GetClientLogEntries` never returned a log in 7+ attempts over 2 sessions in T-006 and again in 3 sessions of T-015 C2 (a real FortniteClient WAS running and writing its own log; see the C2 update). The `startLine = lastEntryLine+1` cursor is therefore unverified.
- Runtime "missing event" test not possible: needs a placed Verse device (class path refused by the guard).
- Bad actor class test (placing a disallowed `/Script/Engine` class to see StartSession fail) NOT repeated: the owner forbade placing such classes and the cause is already proven by the earlier failures plus the log lines in R2.
- Editor quit/restart: refused by design.

## 5. Tasks for a subagent

1. "Session health": `GetSessionStatus` + `GetGameState`; return both strings. Read-only.
2. "Always-close": if status is not Disconnected call `StopGame` then `StopSession` in try/finally; return the final status.
3. "Why did StartSession fail": `GetLogEntries {category:"",maxEntries:0,pattern:"UEFNValidation"}`; return the `Error:` lines and actor names.
4. "Regression verdict": write/replace Verse -> `BuildAll` -> if `[]` and session Connected `PushChanges {bVerseOnly:true}` -> new log lines -> PASS/FAIL with timings per step.
5. "Full smoke": R1 with a ping before each step; return timings.

## 6. Tools never tried and why

None skipped. `GetClientLogEntries` only returned its error (see 4 and the C2 update: 3 sessions, a live client, every state, still no client log).

## Update 2026-10-16 (T-014 pass B, item 5)

GetClientLogEntries with a live client: NOT run. The probe needs `lab_client_probe` (LabClientProbe.verse, BuildAll clean, class `/<guid>/_Verse.root_ai_lab-lab_client_probe`) placed in the level, and the guard refuses every route that attaches it (see level-devices.md update: PlaceDevice, set_properties script). No session was started (nothing to log; level has no disallowed actor). File deleted again, BuildAll `[]`.

## Update 2026-10-16 (T-015 pass C2: GetClientLogEntries + StartGame availability; scripts `_explore/j1.py`..`j10.py`, LAB_SESSION=1)

Corrects sections 1, 3, 4 above. Setup: throwaway `LabClientProbe.verse` (class `/<guid>/_Verse.root_ai_lab-lab_client_probe`, prints `LABMARK_4711 begin` and a tick every 3 s), BuildAll `[]`, PlaceDevice ok; after 3 sessions: device removed, file deleted, BuildAll `[]`, 25 actors, no TargetPoint.

**1. What the session really is.** StartSession uploads the project to a cloud server, connects the beacon, launches the REAL Fortnite client (`FortniteLauncher.exe -VK.JoinEditOnLaunch ...` -> `FortniteClient-Win64-Shipping.exe`), cooks for client and server and returns when the server is loaded. Log timeline (UTC, run 1): `Play succeeded` +11 s, `Valkyrie Beacon Connected` +18 s, `Launching client [0]` +18 s, cooking until +87 s, `StartGame` dispatch, `MinigameStateChanged InProgress` +0.8 s, `LogVerse: : LABMARK_4711 begin` the same instant.

**2. StartGame availability rule (verified twice by polling from a second process while StartSession ran).**
| GetSessionStatus | GetGameState | StartGame |
|---|---|---|
| Disconnected | Unconnected | not available |
| Connected (first ~8 s after the beacon, before the cook starts) | CanStart | `The Start Game command is not currently available.` |
| UpdatingContent (cook/send project, ~65 s) | CanStart | `The Start Game command is not currently available.` (13 attempts) |
| Connected (content update finished, StartSession returns) | CanStart | `Completed` 0.27 s |
| Connected | Running | n/a (match running) |

So `GetGameState = CanStart` does NOT mean StartGame works: wait for `GetSessionStatus = Connected` AFTER `UpdatingContent` (simplest: StartGame only after the StartSession call returned and a status read says Connected). This explains the soak/session-loop "not currently available" (StartGame at 16 s = still Connected-early/UpdatingContent). Poll log of run 3: `_explore/j9b.out`.

**3. GetClientLogEntries: NOT produced, cause not found.** Tried in Disconnected, Connected-early, UpdatingContent, Connected/CanStart, Running (up to 160 s after StartGame, every 4 s, 40 polls) and after StopGame/StopSession; patterns `LABMARK`, `.`, `LogWindows`, `Log`, `LogNet`; with `startLine` 0 and 1 and `maxResults`. Always `No client log was found; start a play-in-client session first.` (0.01 s: fails before reading anything). Facts: (a) the launched client (editor 29548 -> FortniteLauncher 17528 -> FortniteClient_EAC_EOS 24660 -> FortniteClient-Win64-Shipping 28728) was alive and writing `%LOCALAPPDATA%\FortniteGame\Saved\Logs\FortniteGame.log` (opened ~6 s after the launch, 28 MB, 0 LABMARK lines because Verse `Print` runs on the SERVER); (b) the tool does not use that file; the editor log only shows `LogScript: Warning: No client log was found ...` per call; (c) no other client log file appeared under the project, `UnrealEditorFortnite/Saved` or Temp. Needed condition: unknown. Hypothesis, unproven: a local "play in client" launch that tracks its own process/log path; no MCP tool starts one (`mcp_map.py --find play client` returns only SessionToolset tools). The cursor `startLine = lastEntryLine+1` stays unverified because no entries ever come back.

**4. Verse Print in a running session.** Server `Print` lines are forwarded to the EDITOR log as `LogVerse: : <text>` and are readable with `LogsToolset/GetLogEntries {category:"", maxEntries:0, pattern:"LABMARK"}`: empty at +0.1 s after StartGame, present at +4 s (begin, tick 1, tick 2), then one tick per 3 s. This is the working way to read Verse runtime output (cursor recipe of editor-logs.md 2.1 applies).

**5. New traps.**
- The MCP reply text of StartSession can be an unrelated error: run 1 returned `GetObjectProperties on '...FortStaticMeshActor_UAID_...' the following prope...`, run 2 (second process polling) returned `No client log was found...`, while the session was in fact Connected/CanStart. Always read GetSessionStatus after StartSession.
- The real FortniteClient processes SURVIVE StopSession (pids 24660/28728 alive 15+ min later, 4.5 GB; not killed on purpose); a later StartSession reused them (no new pids). Status shows Disconnected/Unconnected anyway.
- Two processes calling MCP at the same time can get each other's replies; use one process for session actions and poll from a second one only with read tools.
- `delete_folder` after `remove_from_scene` of the last actor: `Folder does not exist` (the folder vanishes on its own).
- During the first run the level briefly listed 26 actors (a `SimulationEntity` next to `LevelEntity`); a later find_actors gave 25 with nothing removed by us (editor-owned).

**Timings (3 sessions):** StartSession 83.8 / 85.6 / 87.3 s; StartGame 0.27 s; StopGame 1.28 s; StopSession <0.1 s; Verse begin 0.8 s after StartGame; status/state reads 0.01 s.

**Recipe R1 corrected:** step 2: `StartSession {}`, ignore the reply text, `GetSessionStatus` must be `Connected`; step 3: `StartGame` only then; to read the game's Print output use LogsToolset (item 4), not GetClientLogEntries.
