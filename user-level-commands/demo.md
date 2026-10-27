---
description: Run the Chicken Roundup pilot demo of the whole flow with a stopwatch (with you, or --auto with no questions)
argument-hint: "[--auto | --copy | --load]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

The kit ships a complete pilot (Chicken Roundup, from the Epic farm example) so you can see what each step produces. It runs in a NEW empty test project, never in a real map. Run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`.

**Stopwatch.** The demo is timed (for the owner's promo video): `python demo_timer.py start --mode interactive` (or `--mode auto`) as the very first action, `python demo_timer.py mark "step"` when each step is done, `python demo_timer.py stop` when everything is ready. The Docs page shows the clock. Never stop it before the last file exists.

- No argument (with the owner): `python demo_pilot.py load`, then take the owner through the flow step by step: `/spec` (idea, 3 variants, score), constitution, `/piano`, `/compiti`, `/coerenza`, `/ambiente --playtest`. At each approval ask the owner with AskUserQuestion; the answers are theirs. Mark a lap after every step.
- `--auto`: no questions at all. Do the same flow on the pilot without asking: the AI approves every step on the owner's behalf, exactly as in the Lab test (write "approved by the AI, --auto demo" in the approval lines), keep the pilot's own choices (4 players, forbidden: leaderboard, pvp), mark a lap per step, stop the clock at the end and print `python demo_timer.py report`. Start to finish in one go.
- `--copy`: only `python demo_pilot.py copy` (files in `Claude/docs/demo-chicken-roundup/`, nothing of yours touched). No stopwatch.
- `--load`: only `python demo_pilot.py load`, in a NEW empty project. It refuses when the project already has a spec, a plan or tasks and never overwrites. No stopwatch.

If the person has no test project, tell them how: a new empty UEFN project, Claude Code opened in its folder, the kit installed with `/kit-update`. If the clock is already running, ask whether to stop it first. At the end say in two lines what was made, the total time and the slowest step. Do not edit the demo files.
