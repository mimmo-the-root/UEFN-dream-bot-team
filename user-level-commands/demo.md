---
description: Run the Chicken Roundup pilot demo of the whole flow with a stopwatch (with you, or --auto with no questions)
argument-hint: "[--auto]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

The kit ships a complete pilot (Chicken Roundup, from the Epic farm example) so you can see what each step produces. It runs in a NEW empty test project, never in a real map (if the project already has the owner's own spec, plan or tasks, stop and say so). Run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`. Only two ways to run it, nothing else to choose:

- **No argument (interactive):** the owner is with you. At each approval ask with AskUserQuestion; the answers are theirs.
- **`--auto`:** no questions at all. The AI approves every step on the owner's behalf, exactly as in the Lab test, and writes "approved by the AI, --auto demo" in the approval lines. It starts and finishes by itself.

**First action, always:** `python demo_timer.py start --mode interactive` (or `--mode auto`). If a clock is already running, ask whether to stop it first (in `--auto` stop it and start again). Then `python demo_pilot.py load`: it brings the pilot files by itself, and if a previous demo is there it moves those files to `_to_delete` (never deletes). 

**Phases, each timed:** at the start of each phase run `python demo_timer.py phase "<name>"` (the Docs page shows the total big and the running phase small): `idea and spec` (`/spec`), `constitution` , `plan` (`/piano`), `tasks` (`/compiti`), `coherence` (`/coerenza`), `playtest checklist` (`/ambiente --playtest`). In the interactive run the time spent waiting for the owner counts too: it is the real time. When the last file exists run `python demo_timer.py stop`, then `python demo_timer.py report`.

At the end say in two lines what was made, the total time and the slowest phase, and that the old demo files (if any) wait in `_to_delete` and are cleaned from the What's new page. Do not edit the demo files.
