# MCP area: verse-build (VerseToolset, BuildAll)

Date: 2026-10-15. UEFN version: 42.40 (from previous-findings.md, same editor; not re-queried). Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (LAB_ROOT = GUID mount, PowerShell, scripts run from `Content`), task T-005. 10 tools in the area, 10 tried ok. Scratch scripts: `Claude/logs/_explore/v0.py`..`v11.py`.

Toolset name: `ValkyrieToolset.VerseToolset` (NOT `VerseToolset.VerseToolset`: that is "not found"). Answers `{"returnValue": ...}`. `LAB_SESSION=1` was NOT needed: in lab mode (`LAB_AGGRESSIVE=1`) BuildAll and Verse writes pass the guard on paths under LAB_ROOT.

Verse path space: the project's own source lives under `/<guid>/root_ai_lab/` (here `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/`), which is exactly LAB_ROOT, so the lab guard accepts it. `ListFiles {path:"", bRecursive:false}` lists the roots: the project folder `/<guid>`, `/<owner>@fortnite.com/root_ai_lab (<guid>/Assets)` (read-only digest), and Verse.org / UnrealEngine.com / Fortnite.com digests. Line and character numbers (spans, error locations) are 0-based.

## 1. What the area is for, tools

Read, search, create, edit and compile the project's Verse files, and read compile errors as structured data.

| Tool | R/W | Tried |
|---|---|---|
| ReadFile {path, span?} | R | yes ok |
| ListFiles {path, bRecursive} (both required) | R | yes ok |
| Grep {pattern, pathGlob} (both required) | R | yes ok |
| WriteFile {path, content, bCreateIfMissing, span?} (bCreateIfMissing is required) | W | yes ok |
| Replace {path, oldString, newString, bReplaceAll?} | W | yes ok |
| Move {sourcePath, destPath} | W | yes ok |
| Copy {sourcePath, destPath, bRecursive} (bRecursive required) | W | yes ok |
| Delete {path, bRecursive} (bRecursive required) | W | yes ok |
| CreateDirectory {path} | W | yes ok |
| BuildAll {} | W (compiles) | yes ok |

## 2. Verified recipes (all in `recipes.json`)

`V` = `ValkyrieToolset.VerseToolset`, `R` = `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/`.

R1 Create, break, read the exact error, fix, rebuild (the T-005 core loop, ledger ok each step):
1. `V/WriteFile {"path":"R+LabProbeTest.verse","content":"<verse source>","bCreateIfMissing":true}` returns null. Source used: header block (`# File / # Summary / # Last modified`), `using` lines, a `creative_device` class with the `Log` pattern, and in `OnBegin` the line `BadValue : int = "not an int"`.
2. `V/BuildAll {}` returns (about 2 s): `[{"severity":"Error","code":3509,"message":"This variable expects to be initialized with a value of type int, but this initializer is an incompatible value of type []char.","filePath":"R+LabProbeTest.verse","span":{"startLine":19,"startCharacter":26,"endLine":19,"endCharacter":36}}]`. A clean build returns `[]`.
3. `V/Replace {"path":"R+LabProbeTest.verse","oldString":"BadValue : int = \"not an int\"","newString":"GoodValue : int = 42"}` null (oldString must occur exactly once).
4. `V/BuildAll {}` returns `[]` = clean.

R2 Read a region: `V/ReadFile {"path":"R+LabProbeTest.verse","span":{"startLine":17,"startCharacter":0,"endLine":19,"endCharacter":200}}` returns the text of those lines (out-of-range clamped). No span = whole file.

R3 Search: `V/Grep {"pattern":"BadValue","pathGlob":"**/*.verse"}` returns `[{filePath, span, lineText}]` (literal, case-insensitive). A full-path glob (`R+LabProbeTest.verse`) and `""` also work.

R4 Directory ops: `CreateDirectory {"path":"R+LabProbe"}`; `Copy {"sourcePath":"R+LabProbe","destPath":"R+LabProbeDir2","bRecursive":true}`; `ListFiles {"path":"R","bRecursive":true}`; `Delete {"path":"R+LabProbeDir2","bRecursive":true}`; `Move {"sourcePath":"R+A.verse","destPath":"R+B.verse"}`.

R5 Edit + build in ONE call (ProgrammaticToolset, about 5 s for two builds): the script calls `execute_tool("ValkyrieToolset.VerseToolset.Replace", json.dumps({...}))` and `execute_tool("ValkyrieToolset.VerseToolset.BuildAll", "{}")["returnValue"]`, and returns the diagnostics. Proven: break, build (1 error), fix, build (`[]`) inside one `execute_tool_script`.

R6 Other diagnostics seen: `X +` at end of file gives `{"severity":"Error","code":3100,"message":"vErr:S71: Expected expression, got end of file following \"+\""}`; an unknown identifier gives `{"code":3506,"message":"Unknown identifier `Undefined`.\nUsed inside function ..."}`; a duplicated definition (file copied) gives `code 3532 ... is ambiguous with this definition`.

Build time measured: empty project 2.5 s, 1-file errors 1.0 to 2.2 s, 2 files 2.1 s, script with two builds 4.9 s. No warnings were ever returned (only `severity: Error`).

Previous findings re-run: "Verse file operations are sandboxed to the creator's project": **riconfermata** (`WriteFile` to `C:/temp/X.verse`: `WriteFile refused: a path on the disk outside the project` from the lab guard; to `R+LabProbe.txt`: `... is not a Verse source file.`). "execute_tool_script batches calls (full dotted name, json.dumps args)": **riconfermata**, also for Verse tools. Nothing else in previous-findings concerns this area.

## 3. Traps (exact messages)

1. Toolset name: `Toolset 'VerseToolset.VerseToolset' not found.` The right name is `ValkyrieToolset.VerseToolset`.
2. A "required" argument that looks optional: `WriteFile` without `bCreateIfMissing`: `Function "WriteFile", input param "bCreateIfMissing" is required by the function input schema Json, but is missing from the incoming function input params Json.` Same for `bRecursive` (ListFiles/Delete/Copy) and `pathGlob` (Grep).
3. Regex Grep is unusable from the lab: a pattern wrapped in slashes (`/Bad.*Value/`) starts with `/`, so the guard reads it as a path: `refused even in the laboratory, path outside /09e4...: /Bad.*Value/`. Literal match only (case-insensitive).
4. Grep `pathGlob`: `"*"` and a bare file name (`LabProbeTest.verse`) returned `[]`; `""`, `"**/*.verse"` and a full path work. `(?i)goodvalue` without slashes is literal and finds nothing.
5. `WriteFile` span: `span start character 100 is past the end of line 20 (line length 36).` Spans are NOT clamped on write (clamped on read).
6. `Replace` ambiguous oldString: `OldString matches multiple locations in '<path>'; add more context to disambiguate.` (or `bReplaceAll: true`).
7. `Delete` non-empty directory without recursion: `'<dir>' is a non-empty directory; pass bRecursive=true to delete recursively.`; missing file: `file does not exist: '<path>'.` (ReadFile), `'<path>' does not exist.` (Delete).
8. A syntax error (S71) in one file hid semantic errors; rebuild after each fix, one BuildAll is not the full list of problems.
9. Copying a file inside the same package duplicates its definitions: the next build fails with `3532 ... is ambiguous` (Copy itself returns null).
10. A Verse device class built by BuildAll appears in `DeviceToolset/ListDeviceAssets {"nameFilter":"lab_probe"}` as `/<guid>/_Verse.root_ai_lab-lab_probe_test` (`bIsVerseDevice` true), a path OUTSIDE LAB_ROOT: `PlaceDevice` and `add_to_scene_from_class` with it are refused by the lab guard. A guessed class path `R+LabProbeTest.lab_probe_test`: `Parameter error: ... is not valid Class for property 'actor_type'.`

## 4. What does NOT work or is forbidden here

- Placing a device of a freshly built Verse class (and so `SetDeviceProperty` / `GetDeviceProperties` on it) is blocked by the lab guard (trap 10), not worked around. The class does exist after BuildAll, so the "needs a built Verse device" blocker in level-devices is satisfiable, just not testable in this lab.
- Non-.verse files, disk paths outside the project, regex Grep (trap 3).
- BuildAll returns no warnings; it cannot list style problems.
- No session push was tried (session-regression area).

## 5. Tasks for a subagent

1. "Compile check": call `BuildAll`, return `clean` or the list of `{severity, code, filePath, startLine+1, message}` (add 1 to the 0-based line).
2. "Find a symbol": `Grep` literal with `pathGlob "**/*.verse"`; return filePath, line, lineText, max 20 hits.
3. "Fix one compile error": given filePath and message, `ReadFile` the span +/- 3 lines, `Replace` with a unique oldString, `BuildAll`; return the new diagnostics. Max 3 loops (kit cap is 5 per error).
4. "Create a Verse file": `WriteFile` with header block and Log pattern (kit rules), `BuildAll`, return the diagnostics and the class path from `ListDeviceAssets`.
5. "List the Verse tree": `ListFiles {path: LAB_ROOT, bRecursive: true}`; return file names only.
6. "Cleanup": `Delete` the given files/directories (bRecursive for directories), then `BuildAll` must return `[]`.
Return to the orchestrator: paths touched, exact diagnostics, build seconds.

## 6. Tools not tried and why

None: all 10 tools were called with real arguments at least once (ledger ok). Not exercised: a successful middle-of-file `span` replace with `WriteFile` (only the error case and whole-file writes), `Move` of a directory, and BuildAll during a play session (session-regression area).

## Update 2026-10-16 (T-015 pass C1, corrected guard, scripts `_explore/i1.py`..`i21.py`)

Corrects trap 3, trap 10 and part 4 above (they described the old guard).
- **Regex Grep works.** `Grep {pattern:"/(Bad|Good)Value/", pathGlob:"**/*.verse"}` is a regex: slashes are the delimiters; `(?i)`, `\s`, `^`, alternation and classes work (`/(?i)goodvalue/`, `/lab_[a-z_]+probe/`, `/^\s+Log\(/`). Without slashes the pattern stays literal (`Bad.*Value` -> `[]`). The guard now passes any slash-wrapped pattern that contains a regex metacharacter; `/BadValue/` (no metacharacter) is refused as a path: `refused even in the laboratory, path outside /root_ai_lab: /BadValue/` (drop the slashes, it is a literal anyway). Flags after the closing slash (`/x/i`) match nothing. `**/*.verse` also searches the digest files (`/Fortnite.com (Fortnite)/Fortnite.digest.verse`): narrow the glob.
- **A built Verse device can be placed.** Verse file with `lab_device_probe := class(creative_device)` (editable `ProbeValue : int`, `ProbeText : string`, `ProbeButton : button_device`, Log pattern) -> `BuildAll` `[]` -> `DeviceToolset/ListDeviceAssets {nameFilter:"lab_device_probe"}` gives `/<guid>/_Verse.root_ai_lab-lab_device_probe` -> `PlaceDevice` returns `...PersistentLevel.VerseDevice_C_UAID_...`. Details in level-devices.md (T-015 update). Cleanup: remove_from_scene, `VerseToolset/Delete` the file, `BuildAll` `[]`.
- Build trap: `OnX<public> : listenable(tuple()) = event(){}` -> `3509 ... expects listenable(tuple()), but this initializer is ... event(tuple())`. Use `event()` for an event you Signal yourself; `listenable` needs a `subscribable` source.
