---
description: Measure the open map with the profiler during a play session and write Claude/docs/PERFORMANCE.md (metrics against budget, worst areas, fixes); never changes the map
argument-hint: "[memory | spatial | trace]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit
---

You measure how the open map performs and write the result down. Input: `$ARGUMENTS` (empty = Spatial Profiler metrics and a memory reading; `memory` = only the memory budget; `spatial` = only the spatial metrics; `trace` = also record a trace file). This command is new and has not been tried on a real map yet: when something does not answer as the skill says, write exactly what you saw in the report; that is the test.

Read first: the skill `uefn-profiling` (the tools, the order, what is untested) and, for the memory unit and the publish budget, `uefn-version-upgrade`.

1. **Check the ground.** The UEFN MCP must answer (one cheap read) and a play session must be running (`GetSamplingStatus`, `ListSources`, `ListTargets` twice). No session: say so in one line, tell the owner to start one with the editor's own play button, and stop. Never start a session yourself, never close or restart the editor.
2. **Choose and enable the metrics.** List them (`ListMetrics`), keep the few that matter (memory, entity count, device count, whatever the map's genre stresses; read `Claude/docs/.genre`), enable only those. Clear old samples first and say so.
3. **Measure.** Start sampling, ask the owner to play the heaviest part for about a minute (or, in a demo, do nothing: the numbers are for the moment), stop sampling. Then read the totals and the worst areas with a small `maxResults`. With `trace`, record a trace and give its path.
4. **Write `Claude/docs/PERFORMANCE.md`** (you write it, from the table `perf-profiler` returns; the profiler has no Write tool) (replace the file, keep the previous one as `PERFORMANCE.previous.md`): the date, the map name, the UEFN version, one line on how it was played, a table `| Metric | Value | Budget | Worst area | State |` (State = within, near, over), then "What to fix", at most five lines, each with the area and one idea. Add what you could not measure and why.
4b. Every row whose State is near or over is a finding: number it `PERF #1`, `PERF #2`... in "What to fix" and ask `planner-docs` to add one task each (Kind `perf`, Source `PERF #N`). Without a measurement (no play session) write PERFORMANCE.md anyway with "not measured" and its reason, so the console shows the state.
5. **Report in five lines:** the worst metric, its number against the budget, the area, the first fix, and what was not measured. Change nothing in the map because of a number; the owner decides.

Safety: read-only toward the level. If the editor stops answering after a profiler call, say which call it was, do not repeat it, and tell the owner.
