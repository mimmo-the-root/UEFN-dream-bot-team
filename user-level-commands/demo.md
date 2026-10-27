---
description: Bring the Chicken Roundup pilot demo (spec, constitution, plan, tasks, playtest) into this project, to see the whole flow or to relaunch it
argument-hint: "[--load]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read
---

The kit ships a complete pilot (Chicken Roundup, from the Epic farm example) so you can see what each step produces. Run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`.

- No argument: `python demo_pilot.py copy` puts the files in `Claude/docs/demo-chicken-roundup/`. Your own docs are not touched.
- `--load`: `python demo_pilot.py load` puts them in `Claude/docs/` ONLY in a NEW empty test project (never in your real map): the Docs page then shows Idea, Spec and Plan filled. It refuses when the project already has a spec, a plan or tasks, and it never overwrites a file.

If the person has no test project, tell them how to make one: a new empty UEFN project, Claude Code opened in its folder, the kit installed with `/kit-update`. Say in two lines what was copied and where, then explain the next step: `/spec` (to start your own game) or `/ambiente --playtest` (to see the checklist). Do not edit the demo files.
