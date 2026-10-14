# A working day

How to talk to the team, how a task moves from idea to done, and what runs by itself after a playtest.

## Calling an agent

Inside a session opened in the project's `Content/` folder you can:

- ask in plain words: *use the coder agent to implement the respawn checkpoint*;
- name the agent to be certain it is the one that answers: `@"coder (agent)" implement the respawn checkpoint`;
- or just describe the task and let Claude pick the agent from each agent's description.

## The first session on a project

Ask for **project-bootstrap**. With code already there it writes, in a few minutes, a map of the project (`SPEC.md`), a list of bugs with a fixing order (`BUGS.md`) and retention ideas (`RETENTION-NOTES.md`). With an empty project it asks you questions and writes the answers into `ROADMAP.md` and `STATUS.md`. It never invents what you did not say. Use it once; later sessions use the normal flow below.

## The normal flow

1. Open the project in UEFN, then start `claude` in its `Content/` folder.
2. Ask the **coder** for what you need.
3. Let **qa-regression** check the logs, or let it run by itself after a playtest.
4. Before you close, ask **planner-docs** to update `STATUS.md`.
5. Next time, say *read the project status* and Claude knows where you left off.

## Plan first: ROADMAP and STATUS

The whole team follows one order: **request, task opened, code, review, task closed.** Nobody writes code before there is a task.

The `Tasks` table in `ROADMAP.md` is the single source of truth.

| ID | Feature | Status | Acceptance criteria | Priority |
|---|---|---|---|---|
| T-014 | Double-jump | Done | Player can jump a second time mid-air, once per fall | MVP |
| T-015 | Storm shrink phase 2 | In progress | Storm radius is 50% at the 3-minute mark | MVP |
| T-016 | Leaderboard UI | To do | Top 5 players shown at round end | Later |

Only **planner-docs** adds a row, edits it or marks it **Done**, and only after the coder has two PASS verdicts. The coder may move a row between To do, In progress and Blocked, nothing more.

A feature request, step by step:

1. You say *add a double jump*. No task matches yet.
2. The coder stops and asks for one line of acceptance criteria instead of guessing.
3. The planner opens task T-014.
4. The coder marks it In progress and asks **intent-gate** whether the criteria are concrete enough. If not, the question comes to you, not to the coder's best guess.
5. The coder writes the code and compiles it.
6. **intent-reviewer** checks that the result matches the criteria, then **compliance-reviewer** checks the kit's mechanical rules. Either can send the work back.
7. The planner marks the task Done and updates `STATUS.md`. Before a release, **release-gate** checks that every MVP task is Done.

> **Note** `growth-manager`, `second-brain-librarian` and small fixes that live in `BUGS.md` do not need a task. Rule 13 in `~/.claude/CLAUDE.md` draws the exact line.

## The base rules

A few rules live in `~/.claude/CLAUDE.md` and apply to every project without being repeated in each one:

- **Naming:** new content in `custom_*` folders, Outliner folders named for the areas of the map, devices named `<DeviceType>_<Function>`.
- **One logger:** a single `DebugLoggingEnabled` pattern. When logs are not enough, the first move is to add logging, not to guess.
- **Always multiplayer:** the coder and the QA agent reason about authority and several players, not just solo preview.
- **Performance:** the bootstrap flags per-tick work, unbounded loops and deprecated API calls; QA flags frame drops at playtest.
- **State machines** for phase-based logic.
- **A header comment** in every Verse file with what it does, a date and a version, because there is no Git history inside the project.
- **A DemoDisplay stand** for each custom Verse device, with its devices placed on it. Devices whose position matters for gameplay stay where they are.
- **Support devices outside the play area,** grouped on their stand, so players never see or reach them.

## After every playtest

Claude Code has hooks: commands that run when an event happens. The kit uses one that fires after a playtest ends. The MCP server exposes a single generic tool, so the hook cannot tell a stop from any other call by its name. A small script reads the call and acts only when it is really a game stop. Then, by itself:

1. **qa-regression** reads the logs and adds any problem to `BUGS.md`, under "Newly reported";
2. **planner-docs** updates `STATUS.md` and sorts the new bugs;
3. everything is also written to `Claude/logs/`.

Any other MCP call exits at once and costs nothing.

> **Tip** Once per project, run a playtest and check that a log appears in `Claude/logs/` only when you **stop** it. For the first weeks, read `BUGS.md` and the logs now and then, so you can correct a report that was wrong.

## Many projects at once

Every project's `STATUS.md` has the same format, so a short script can scan all your project folders and build one table with the last update, the next step and the open issues. The kit does not ship it because it depends on how you lay out your disk.
