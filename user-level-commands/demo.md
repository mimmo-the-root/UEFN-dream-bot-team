---
description: The whole kit flow on a pilot game, from idea to playtest, timed: /demo with you, /demo --auto without a single question
argument-hint: "[--auto]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

The demo does the COMPLETE round of the kit on the pilot game Chicken Roundup (the Epic farm example): idea, spec, plan, tasks, the map built in UEFN, audit, delivery list, playtest. `/demo` and `/demo --auto` do exactly the same work; the ONLY difference is that `--auto` never stops to ask. Run it in a NEW empty test project, never in a real map (if there is already the owner's own spec, plan or tasks, stop and say so). Run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`.

- **`/demo` (interactive):** at every approval point ask the owner with AskUserQuestion; the answers are theirs.
- **`/demo --auto`:** no questions. The AI approves every point of the flow on the owner's behalf and writes "approved by the AI (--auto demo)" next to it. It starts, works and finishes by itself.

**First action, always:** `python demo_timer.py start --mode interactive` (or `--mode auto`). If a clock is already running: interactive asks whether to stop it, `--auto` stops it and starts again. If a previous demo is in the docs, `python demo_pilot.py load` moves its files to `_to_delete` (never deletes) and you start from an empty project.

**Inputs of the pilot** (the answers `--auto` uses; interactive proposes them): idea = the farm game Chicken Roundup, collect the escaped chickens and bring them to the pen before the round ends; 4 players, co-op (ask the players first, multiplayer must be guaranteed); forbidden: leaderboard, pvp. The files in `Claude/reference/demo-chicken-roundup/` are the expected result: compare at the end, never copy them.

**The round, each phase timed** with `python demo_timer.py phase "<name>"` (the Docs page shows the total big and the running phase small):
1. `idea and spec`: `/spec` (study of the kit's knowledge, three scored variants, players, Island settings needs), review, approval.
2. `constitution and plan`: `/piano` (Island settings table, where each device goes: a DemoDisplay outside the play area, gameplay-position devices in place), review, approval.
3. `tasks and coherence`: `/compiti`, `/coerenza`.
4. `environment`: `/ambiente` (what the owner must have: Beta Access, Python scripting, MCP).
5. `build`: the map in UEFN task by task with the `coder` agent (plan first, approval before each change, Verse with editable parameters instead of references the MCP cannot assign, Island settings set and read back, build clean), validation and review after each step. Check the Verse digest for what the game needs before choosing the mechanic; if a command does not exist, say it in the plan and use the design that works without it.
6. `audit`: `/audit` (fix minor findings alone, record serious ones with the recommendation), including the Fab and island compliance scan.
7. `delivery list`: `/consegna` (what only the owner can do, private release, Publishing Validation and memory flags to confirm). Stop here: the private release and the publish are the owner's.
8. `playtest checklist`: `/ambiente --playtest` with the real number of players.

Never launch or relaunch UEFN; if it or the MCP is not reachable, stop the clock and say why. Never delete: park in `_to_delete`. When the last file exists run `python demo_timer.py stop`, then `python demo_timer.py report`.

At the end say in a few lines what was made, the total time, the slowest phase, what the audit found and what is left for the owner. Do not edit the demo reference files.
