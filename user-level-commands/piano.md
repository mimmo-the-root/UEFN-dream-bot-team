---
description: Turn the approved game spec into the principles (CONSTITUTION.md) and the technical plan (PLAN.md), with one approval
argument-hint: "[--jam]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

You plan the game. The spec says WHAT; the plan says HOW. Work in `Claude/docs/`; run scripts from `Claude/hooks` (`py -3` on Windows). Input: `$ARGUMENTS`. Never write game code here and never edit `GAME-SPEC.md`: a change to the spec goes through `/spec`.

**Gate.** Run `python spec_check.py --gate`. If it blocks (no approval, score under 60 without the owner's forced yes, open `[NEEDS CLARIFICATION]`), say why in one line and stop: the owner fixes it with `/spec`. Nothing below starts without a ready spec.

**0. Study (before writing).** Read `## Sources consulted` of `GAME-SPEC.md` and add what the plan needs, in `## Sources consulted` of `PLAN.md` (one line each, "none found" is allowed, never invent): second brain (`second-brain-librarian`), genre lessons (`python ~/.claude/hooks/skills_lib.py patterns <slug>` and `consult <slug>`), `uefn-lessons`, `uefn-device-gotchas`, `uefn-level-devices`, `mcp-tool-contracts`, and the recipes below. The study comes before the device choices.

**1. Principles (`CONSTITUTION.md`).** If it does not exist, copy `Claude/docs-template/CONSTITUTION.md` and fill it in one page from the genre skill, the lessons already learned and the kit rules: names, performance budget, scope limits, what is forbidden (words the plan and tasks must never contain), and the Self-healing block (keep the closed list of minor bugs; the owner may extend it). Each principle has a reason and a source. Show it and ask the owner to approve or change; write `Approved: yes` only after the yes. In a jam use the short version: five principles at most.

**2. Plan (`PLAN.md`).** Copy `Claude/docs-template/PLAN.md` and write ONE section per story of the spec (`## S1 - ...`, S1 is Story 1):
- Devices: for each need, use `python ~/.claude/hooks/skills_lib.py recipes mechanics` and the skills `uefn-level-devices`, `uefn-device-gotchas`, `uefn-lessons` to mark it `recipe` (proven), `skill` (documented) or `explore` (try it in the Lab first). A device that exists comes before a new Verse file.
- Placement: follow rule 7 of `~/.claude/CLAUDE.md` and the skill `uefn-device-gotchas` (`demodisplay-sizing.md`). Each custom Verse device gets one `DemoDisplay` stand outside the play area, grouped by function; devices that only configure it (Timer, HUD, Score, Round and Team settings) go on the stand, off the scene. Devices whose position is gameplay (spawners, volumes, player spawn pads, storm) stay in place and are only named in the stand's description. Write the placement per device in the story (`stand` or `in place`).
- Verse files: name and one line each, or `none`.
- Assets inventory: first look at what exists (project, Fortnite and Fab libraries through the MCP when the editor is open); mark each asset `present`, `import` or `create`. Never invent an asset by its name.
- Manual steps: everything only the owner can do (`@editable` references, editor settings), each with how to verify.
- Build order: Pass 1 (structure: S1 first, the loop playable at the end), Pass 2 (details), and one sample to try alone before making a series.
- Island settings: a table (Max players, Min players to start, Teams, Round, Respawn, Join in progress...) written FROM the spec (Players and Teams). Most of them are set by hand in UEFN Island Settings: say which ones and how to verify.
- Risks to tasks: each risk of the spec (numbered R1, R2... in table order) gets the first task that reduces it; the high ones must be in the first three tasks.
In a jam (`--jam` or `Mode: jam`): a one-page plan, high risks first.

**Review.** After 1 and after 2, ask the agent `intent-reviewer` to read the file against the spec with fresh eyes (gaps, contradictions, a missing player case). Fix what it finds; a doubt about the spec goes back to `/spec`, never into the plan.

**3. Check and approve.** Run `python plan_check.py --stage plan`. Fix every CRITICAL and HIGH line; a CRITICAL is a conflict with the constitution and is never argued away. Then ONE question to the owner: approve the plan, or change something. Write `Approved: yes` in `PLAN.md` only after the yes, add one line to `Claude/docs/STATUS.md`, and say the next step is `/compiti`.

Short report in plain language; name the files, do not paste them.
