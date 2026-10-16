# MCP area: editor-logs (EditorAppToolset, LogsToolset, + GetClientLogEntries of SessionToolset)

Date: 2026-10-15. UEFN version: 42.40 (from previous-findings.md, same editor). Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (LAB_ROOT = GUID mount, PowerShell, run scripts from `Content`), task T-003. 42 tools (37 EditorAppToolset + 4 LogsToolset + `GetClientLogEntries`, which lives in SessionToolset); 42 tried, 41 answered, `GetClientLogEntries` only returned its error (see section 4).

## 1. What the area is for, and the tools

Read the editor's live log, set log verbosity, read/set editor state (camera, show flags, view mode, editor mode, CVars, content browser, selection, collections, captures). Toolset names: `EditorToolset.EditorAppToolset`, `EditorToolset.LogsToolset`.

| Tool | R/W | Tried |
|---|---|---|
| LogsToolset/GetLogEntries | read | yes |
| LogsToolset/GetLogCategories | read | yes (131 KB) |
| LogsToolset/GetVerbosity | read | yes |
| LogsToolset/SetVerbosity | write | yes |
| EditorApp/GetActiveEditorModes, ListEditorModes, SetEditorMode | R, R, W | yes |
| EditorApp/GetCameraTransform, SetCameraTransform | R, W | yes |
| EditorApp/GetContentBrowserPath, SetContentBrowserPath | R, W | yes |
| EditorApp/GetSelectedActors, SelectActors, FocusOnActors | R, W, W | yes (only with `[]`, see traps) |
| EditorApp/GetSelectedAssets, SelectAssets, GetAssetThumbnails | R, W, R | yes |
| EditorApp/GetSelectedOutlinerFolders, SelectOutlinerFolders | R, W | yes (select: error only) |
| EditorApp/GetVisibleActors, GetOpenAssets, OpenEditorForAsset | R, R, W | yes |
| EditorApp/ListCollections, CreateCollection, DestroyCollection, GetCollectionAssets, AddAssetsToCollection, RemoveAssetsFromCollection | R,W,W,R,W,W | yes |
| EditorApp/ListShowFlags, GetShowFlag, SetShowFlag | R,R,W | yes (ListShowFlags 22 KB) |
| EditorApp/SearchCVars, GetCVarValue, SetCVarValue | R,R,W | yes |
| EditorApp/SetViewportViewMode | W | yes |
| EditorApp/WorldPosToScreenCoords, ScreenCoordsToWorld | R,R | yes |
| EditorApp/ShowNotification | R (toast) | yes |
| EditorApp/CaptureViewport, CaptureEditorImage, CaptureAssetImage | R | yes (CaptureAssetImage: error on a widget BP) |
| SessionToolset/GetClientLogEntries | read | yes, error only |

## 2. Verified recipes (exact arguments)

All through `call_tool {toolset_name, tool_name, arguments}`. `R` = `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`.

### 2.1 KEY RECIPE: read only the NEW editor log lines after an action

`GetLogEntries` has no offset or cursor. It only has `category`, `pattern` (regex) and `maxEntries` (taken from the END of the log, chronological order, 0 = all). Lines look like `[2026.10.15-19.01.10:405][915]LogScript: Warning: ...` (timestamp, frame number, category). Cursor recipe (proven, ~2.3 s for a whole round trip):

1. `GetLogEntries {"category":"","maxEntries":1}` -> `returnValue[0]` is the CURSOR (the last line now). Keep the exact string.
2. Do the action (any tool call).
3. `GetLogEntries {"category":"","maxEntries":300}` -> list `buf`.
4. New lines = `buf[ last_index_of(cursor) + 1 : ]`. If the cursor is not in `buf`, the action wrote more than 300 lines: repeat step 3 with a larger `maxEntries` (0 = whole log, ~20000 lines, 2.4 MB, 0.4 s: fine but heavy).
5. Optional noise filter: add `"pattern":"^(?!.*LogModelContextProtocol)"` in step 3 (negative lookahead works) to hide the MCP dispatch lines (every call, including the reads themselves, adds two `LogModelContextProtocol` lines). Note the pattern is applied before `maxEntries`, so the cursor must be taken with the SAME pattern if you filter (or filter locally after reading).
6. Use `last` index, not first: 2 duplicate lines exist in the full log (same text), the timestamp+frame number makes real collisions rare.

Python helper (works from a scratch script via `mcp_lab`):
```
def tail(n, pattern=''):
    return L.call(G,'GetLogEntries',{'category':'','maxEntries':n,'pattern':pattern})['returnValue']
def new_lines(action, n=300):
    cur = tail(1)[0]; action(); buf = tail(n)
    i = len(buf) - 1 - buf[::-1].index(cur)   # raises if cursor scrolled out
    return buf[i+1:]
```
Proof: cursor taken, then `GetVerbosity {"category":"LogNoSuchCat"}` failed on purpose; the diff returned `LogModelContextProtocol: Running tool...`, `...Dispatching toolset tool: 'EditorToolset.LogsToolset.GetVerbosity'` and `LogScript: Warning: Log category 'LogNoSuchCat' not found. ...` (3 lines, only the new ones).

Shortcuts: `GetLogEntries {"category":"LogScript","maxEntries":2}` = last 2 lines of one category (works for categories that exist); `{"category":"","pattern":"T003","maxEntries":0}` = all matches of a marker.

### 2.2 Verbosity
- `GetVerbosity {"category":"LogTemp"}` -> `"Warning"` (LogTemp and LogScript are Warning by default: Log-level lines never appear in the log until raised).
- `SetVerbosity {"category":"LogTemp","verbosity":"Log"}` -> null; read back `"Log"`. Restore with `"Warning"`.
- `GetLogCategories` -> sorted names WITHOUT the `Log` prefix in the list (e.g. "ActorSerialization") but verbosity calls use the `Log...` form (LogTemp). 131 KB: call once.

### 2.3 Editor state
- `GetCameraTransform {}` -> `{location{x,y,z}, rotation{pitch,yaw,roll}, scale}`; `SetCameraTransform {"transform": <same object>}` -> null, read back equal.
- `SetShowFlag {"flagName":"Grid","bEnabled":false}` then `GetShowFlag {"flagName":"Grid"}` -> false; restore true.
- `SetViewportViewMode {"viewMode":"VMI_Wireframe"}` then `{"viewMode":"VMI_Lit"}` (enum values are `VMI_*`).
- `SetEditorMode {"modeId":"EM_Landscape"}` -> `GetActiveEditorModes` = ["EM_Landscape"]; restore `EM_Default`.
- `SetContentBrowserPath {"path":"R/UI_T001"}` -> `GetContentBrowserPath` returns it.
- `SelectAssets {"assetPaths":["R/UI_T001/WBP_T001"]}` -> `GetSelectedAssets` returns `["R/UI_T001/WBP_T001.WBP_T001"]`.
- `OpenEditorForAsset {"assetPath":"R/UI_T001/WBP_T001"}` -> `GetOpenAssets` lists it.
- Collections: `CreateCollection {"collectionName":"T003Coll","shareType":"Local"}`, `ListCollections` -> `[{name,shareType}]`, `AddAssetsToCollection {"collection":{"name":"T003Coll","shareType":"Local"},"assetPaths":[...]}`, `GetCollectionAssets {collection}`, `RemoveAssetsFromCollection`, `DestroyCollection {collection}`.
- `WorldPosToScreenCoords {"position":{"x":0,"y":0,"z":0}}` -> `{x,y}` normalized; `ScreenCoordsToWorld {"coords":{"x":0.5,"y":0.5}}` -> world point.
- `GetCVarValue {"name":"r.VSync"}` -> `"0"` string; `SearchCVars {"name":"r.ScreenPercentage"}` -> a JSON TEXT string (parse it) with help+value per cVar. `SetCVarValue {"name":"r.VSync","value":"0"}` -> null.
- `CaptureViewport {}` -> `{image: "urn:toolresult:...", cameraLocation, cameraRotation}`; `CaptureEditorImage {}` and `GetAssetThumbnails` return `urn:toolresult:` references (the image is not inline text).

## 3. Traps (exact messages)

- `GetLogEntries {}` with no category: `Log category 'LogsToolset' not found.` (the default category is the toolset's own name). ALWAYS pass `"category":""` for the whole log.
- Unknown category: `Log category 'ScriptLog' not found.` (the real one is `LogScript`).
- Invalid regex pattern returns `[]` with no error.
- Every call you make is itself in the log (MCP dispatch lines, and `LogScript: Warning:` for every failed call): a "diff" is never empty; filter `LogModelContextProtocol`.
- `ShowNotification` does not write a log line (toast only), so it cannot be used as a log marker. A failing call (e.g. `GetVerbosity` on a missing category) writes a `LogScript: Warning:` line carrying the text you chose: usable as a marker.
- `SetViewportViewMode {"viewMode":"Wireframe"}`: `Function "SetViewportViewMode", could not convert incoming function input params Json to a UStruct...` -> use the `VMI_` enum value.
- `SelectOutlinerFolders {"folderPaths":["UI"]}`: `Folder(s) not found in any outliner: UI` (needs a folder that exists in the level outliner; the lab guard also refuses `/`).
- `CaptureAssetImage` on a widget blueprint: `Asset type does not support image capture: <path>.WBP_T001` (meant for meshes, materials, textures).
- Lab guard quirk: `SelectActors`/`FocusOnActors` with a real actor path (`/09e4e8d3-.../root_ai_lab.root_ai_lab:PersistentLevel.Brush_0`) -> `refused even in the laboratory, path outside /09e4e8d3-.../root_ai_lab` because the actor path continues with `.` not `/` after the root. Not circumvented; with `[]` the tools answer ok. (To confirm in level-devices T-004.)
- `SetContentBrowserPath` with the lab root itself is refused by the guard; a subfolder works.
- `GetOpenAssets` always lists the level's DaySequence besides assets you opened.
- `GetLogCategories` ~125 KB, `ListShowFlags` ~22 KB, `GetVisibleActors` ~3 KB: fine; `maxEntries 0` on the log ~2.4 MB.

## 4. What does not work or is forbidden

- `GetClientLogEntries {pattern, maxResults, startLine}` (returns `{entries[], lastEntryLine}`; `startLine = lastEntryLine+1` is the built-in cursor, per its schema): NOT verified. After `StartSession` (status `Connected`, GetGameState `CanStart`) it answered `No client log was found; start a play-in-client session first.` in 3 attempts (waits of 83 s, 250 s and 134 s, with and without `StartGame`; `StartGame` -> `The Start Game command is not currently available.`). Sessions were always closed with `StopSession` in `finally`. Still open after T-006 and T-015 C2: nothing found makes the client log appear (see the C2 update below).
- Quit/restart editor and disk paths: refused by the lab by design; not tried.
- Removing a log line or clearing the log: no tool.

## 5. Tasks for a subagent (and what to return)

1. "Run action X and return only the new log lines": cursor recipe 2.1 with the noise filter; return the list of lines, count, and whether any contains `Error`.
2. "Is the editor healthy?": `GetActiveEditorModes`, `GetOpenAssets`, `GetVerbosity LogScript`, tail 20 with pattern `Error|Warning`; return the lines.
3. "Find a marker": `GetLogEntries {"category":"","pattern":"<marker>","maxEntries":0}`; return matches.
4. "Snapshot the viewport state": `GetCameraTransform`, `GetShowFlag` for 3 flags, `GetActiveEditorModes`; return as JSON so it can be restored.
5. "Raise then restore verbosity": `GetVerbosity`, `SetVerbosity` Log, action, diff, `SetVerbosity` back; return the diff and confirm the restore.

## 6. Tools never tried

None skipped. Not fully proven: `SelectActors` / `FocusOnActors` / `SelectOutlinerFolders` with a real target (lab guard / no matching outliner folder), `CaptureAssetImage` on a supported type (mesh/material), `GetClientLogEntries` (tried with a live client in T-015 C2: still no client log; the guard is not the reason).

## 7. Previous findings re-run (previous-findings.md, editor part)

- Read tools answering without arguments: `GetActiveEditorModes`, `GetCameraTransform`, `GetContentBrowserPath`, `GetSelectedActors`, `GetSelectedAssets`, `GetSelectedOutlinerFolders`, `GetVisibleActors`, `ListCollections`, `ListEditorModes`, `ListShowFlags`, `SearchCVars` (needs `name`, diversa: not argument-free), `GetLogCategories`: riconfermata (all answer; `GetLogCategories` ~125 KB riconfermata).
- Session reads `GetGameState`/`GetSessionStatus`: riconfermata ("Disconnected" without session; "CanStart" and "Connected" with one).
- "Too big without filter" for `GetLogCategories`: riconfermata (131423 chars).
- Batch via `execute_tool_script`: not re-run here (belongs to scripting-batch).

## Update 2026-10-16 (T-014 pass B)

GetClientLogEntries still unverified: the Verse probe (`Print` marker on begin) built clean but could not be placed as a device (guard refuses the `/_Verse` class path), so no session was started. Everything else in this file is unchanged.


## Update 2026-10-16 (T-015 pass C1)
`SelectOutlinerFolders {folderPaths:["/"]}` and with an existing folder: the guard passes it now; the editor answers `Folder(s) not found in any outliner: /` because no scene Outliner panel is open (no MCP tool opens one). `[]` returns null. `GetClientLogEntries` is pass C2 (not run in C1).

## Update 2026-10-16 (T-015 pass C2)
- `GetClientLogEntries` with a live client: NOT closed. 3 sessions (StartSession + StartGame, a real FortniteClient process running and writing `%LOCALAPPDATA%\FortniteGame\Saved\Logs\FortniteGame.log`), every state, patterns `LABMARK`/`.`/`LogWindows`/`Log`/`LogNet`, `startLine` 0 and 1: always `No client log was found; start a play-in-client session first.` (0.01 s, no cursor ever returned). Timeline and states in session-regression.md (C2 update).
- Working replacement for runtime output: a Verse device `Print("LABMARK_n ...")` shows in the EDITOR log as `LogVerse: : LABMARK_n ...` (empty at +0.1 s, 3 lines at +4 s after StartGame); read with `GetLogEntries {category:"", maxEntries:0, pattern:"LABMARK"}` (0.1 s). The cursor recipe 2.1 applies unchanged.
- Useful session lines to filter in the editor log: `LogValkyrie: Launching client [0]`, `LogValkyrieSummary: Connected to Session`, `LogValkyrieActivityTracker: Session -> Start Activity: LoadingNewContent`, `LogValkyrieBeacon ... MinigameStateChanged: EFortMinigameState::InProgress`.
