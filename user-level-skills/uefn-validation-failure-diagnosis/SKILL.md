---
name: uefn-validation-failure-diagnosis
description: Diagnosing "StartSession Failed: Validation failed" or an editor MCP that stays silent for minutes after session start, by reading the UEFNValidation log.
last_reviewed: 2026-10-16
sources: [original]
---
# uefn-validation-failure-diagnosis

## When
`ValkyrieToolset.SessionToolset/StartSession` replies `Failed: Validation failed`, or the MCP stops responding right after.

## Procedure (verified)
1. The MCP reply does not contain the cause. Call `EditorToolset.LogsToolset/GetLogEntries` con `{"category":"","maxEntries":0,"pattern":"UEFNValidation"}` (recipe `GetLogEntries#why_startsession_failed`, verified). ALWAYS with the pattern: without a filter ~2.4 MB.
2. Extract the lines `UEFNValidation: Error:` and the names of the actors that follow.
3. Verified cause: an actor `/Script/Engine.TargetPoint` in the level (`Disallowed reference to /Script/Engine.TargetPoint`).
4. Fix in the level: `SceneTools/remove_from_scene {"actor":{"refPath":"<attore>"}}` (verified), then ONE single new StartSession attempt.

## Pitfalls
- After a failure the MCP may stay silent for minutes (T-006): ping, wait, never loop.
- A failed call writes a line `LogScript: Warning:`: the log is never empty; filter out `LogModelContextProtocol` (`GetLogEntries#filter_noise`).
- `SceneTools/replace_actors_with_class` TargetPoint->StaticMeshActor fails (log only): do not use it as a fix.

## Don't
Placing forbidden classes to "test"; repeating StartSession in a loop; guessing the cause from the arguments; bypassing a guard refusal; improvising when the recipe fails (exact error and stop). Paths always in GUID form `/<guid>/<project>/...`.

## To try (not verified)
Other forbidden classes besides TargetPoint: not observed in the lab.
