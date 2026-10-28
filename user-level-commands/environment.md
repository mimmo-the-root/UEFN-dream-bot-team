---
description: Check the environment for the planned game (read only), fix safe things, list what only the owner can do, then the playtest checklist
argument-hint: "[--playtest]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

You prepare the ground before building. Work in `Claude/docs/`; run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`. Never write game code here.

**Environment.** Run `python env_check.py`. It is read only: it lists the assets of `PLAN.md` to import or create, the manual steps and what only the owner can do (Beta Access, Python scripting, MCP toolset). Then, with the editor open, check the map through the MCP (Lore first: save a Lore checkpoint before anything changes) and compare the assets present with the inventory.
- Safe fixes (a missing docs file, a hook not wired) you do at once and say so in one line.
- Closing or reopening UEFN, importing assets or anything outside the project: ask the owner first, one question, with what will happen.
- The owner-only list goes to the owner as a short checklist; do not try to do it.

**Scenery (the environment of the map).** `env_check.py` also lists the `## Environment` table of the plan: ground and terrain, sky and lighting, props and buildings of the theme, sound and ambience, play area boundary and spawn area. After the readout you BUILD it in the map (with the `coder` agent: plan first, approval before each change unless the demo is `--auto`), row by row through the MCP: place or edit the real actors and settings, read them back, then flip that row of `PLAN.md` from `planned` to `built` and say it in one line. A row you cannot build (no asset, tool missing) stays `planned` and goes to the owner list with the reason: never mark `built` without a readback. The environment step is not finished while a row is `planned` without a stated reason. Gameplay mechanics are NOT built here, only the scenery.

**Playtest.** `python env_check.py --playtest` writes the checklist from the approved spec: per story the expected result and what you observe, per success criterion a box. Save it as `Claude/docs/PLAYTEST.md`. After the owner plays, fill "observed". Every failed row becomes a regression task in `ROADMAP.md` (Feature cell with its `[S#]` tag). Minor failures follow the Self-healing block of `CONSTITUTION.md`.

**Devices.** Rules of `CONSTITUTION.md` (Names and budget): every device you place goes into an Outliner folder by role (`set_actor_folder`) and gets a `Role_Index` label (`set_label`) at the moment you place it; read both back with `get_actors_in_folder` and `find_actors` before you say the row is built, and give every message or text field the exact text of the plan. The label must also equal the name of the Verse field that points to the device (read the Verse file; array fields get `Name_1..n`), so the owner links references by choosing the same name. A device at the root of the Outliner or with a default name is a failed row.

**Island settings.** The plan lists them: say them one by one to the owner (Max players, Teams, Respawn...) as a checklist to set in UEFN Island Settings, and after the owner says done, read them back through the MCP when it can; otherwise ask the owner to confirm each one. Never assume they are set.

**Review.** After the environment readout and after the playtest checklist, ask `qa-regression` to read the result against the spec (players, success criteria); fix the gaps before moving on.

Short report in plain language; name the files, do not paste them.
