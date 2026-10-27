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

**Playtest.** `python env_check.py --playtest` writes the checklist from the approved spec: per story the expected result and what you observe, per success criterion a box. Save it as `Claude/docs/PLAYTEST.md`. After the owner plays, fill "observed". Every failed row becomes a regression task in `ROADMAP.md` (Feature cell with its `[S#]` tag). Minor failures follow the Self-healing block of `CONSTITUTION.md`.

**Island settings.** The plan lists them: say them one by one to the owner (Max players, Teams, Respawn...) as a checklist to set in UEFN Island Settings, and after the owner says done, read them back through the MCP when it can; otherwise ask the owner to confirm each one. Never assume they are set.

**Review.** After the environment readout and after the playtest checklist, ask `qa-regression` to read the result against the spec (players, success criteria); fix the gaps before moving on.

Short report in plain language; name the files, do not paste them.
