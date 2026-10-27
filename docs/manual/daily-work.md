# A working day

How to talk to the team, how a task moves from idea to done, and what runs by itself after a playtest.

## Calling an agent

Inside a session opened in the project's `Content/` folder you can:

- ask in plain words: *use the coder agent to implement the respawn checkpoint*;
- name the agent to be certain it is the one that answers: `@"coder (agent)" implement the respawn checkpoint`;
- or just describe the task and let Claude pick the agent from each agent's description.

## Starting a new game: from the idea

Want to see the whole path first? Run `/demo --load` in a new empty test project (never in your real map): it brings a finished example, Chicken Roundup. The details are in *From an idea to a playable game*.

A new game starts from an idea, yours or Claude's. You do not need a design document: a few sentences are enough.

1. **Make a new, empty UEFN project.** Open a session from its `Content` folder. The kit asks whether it is a map or a Fab product; answer **map**, give your yes, and wait for the setup to finish.
2. **Give Claude the idea.** There are two ways, and you can mix them.
   - *You have an idea.* Say it in plain words: what the player does, where, and why it is fun. For example: "a 4-player race through a collapsing temple, last one standing wins, rounds of three minutes".
   - *You do not have one yet.* Ask for some: "give me 5 game ideas for UEFN that two people can finish in 4 days", and add what you care about (a genre, a theme, solo or team, mobile or not). Claude uses the genre skills and what the kit knows about retention and about what UEFN can really do. Do not take the first answer: ask for variations, for a smaller version, or for a mix of two.
3. **Run `/spec`.** It starts from your idea (or proposes three), asks the minimum (idea, players, round length, theme, days left), and gives you the genre to confirm: the genre is your decision, and in a jam it is proposed from the theme. It then scores three variants out of 100 with the concept card (seven quality criteria, plus whether UEFN can do it and whether it fits the time you have). Below 60 it says how to raise the score; you may still go on, and that is your call.
4. **Write the loop and approve the spec.** With the winner `/spec` writes the playable loop in five lines (action, rule, reward, end, why you play again), then `Claude/docs/GAME-SPEC.md`: a first story that is the whole loop, three to five measurable success criteria, every choice it made for you (assumptions), what is cut, and a table of technical risks (what the API cannot do, steps you must do by hand such as `@editable` references, assets, performance). `python Claude/hooks/spec_check.py` is the spec's test list: it must say *Spec is ready*. You approve once, spec and score together. A new mechanic later is a new story, and a change to an approved spec asks you again.
5. **Run `/piano`.** Only with an approved spec. It writes `CONSTITUTION.md` (the rules that never change: names, budget, what is forbidden, which small bugs the kit may fix by itself) and `PLAN.md`: one section per story with the devices (a proven recipe, a documented skill, or something to try in a test project first), the assets that really exist, the steps only you can do, and the build order in two passes. You approve once.
6. **Run `/compiti`.** It breaks the plan into tasks in `ROADMAP.md`, each with a test you can do in play, the story it belongs to, what it waits for, and what can run in parallel. The first three tasks reduce the riskiest parts. `/coerenza` is the read-only check of spec, plan and tasks at any time; a task or plan that goes against the constitution is a CRITICAL finding and is never argued away.
7. **Run `/ambiente` before building.** It reads the plan and tells you, without changing anything, which assets are still to import or create, which manual steps are yours, and what only you can do (Beta Access, Python scripting, the MCP toolset). Safe fixes are done at once; closing or reopening UEFN is asked first, and a Lore checkpoint is saved before the first playtest.
8. **Build the first playable version, then playtest.** Ask the coder for the first task of the plan, and let the checks run (`/verse-check`). `/ambiente --playtest` writes `PLAYTEST.md` from the spec: per story what you expect and what you observe, per success criterion a box. A failed row becomes a regression task; minor bugs follow the Self-healing block of the constitution. Then the normal flow below takes over.

If you change your mind, say so in the chat and ask the planner to update `ROADMAP.md`: the plan follows you, not the other way round.

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
- **A header comment** in every Verse file with an up-to-date description in English, the real date and the version. It holds no change history: every change is written as one line in `Claude/logs/verse-changes.jsonl` (what changed, why, the outcome), next to `verse-errors.jsonl`. On the first session after the update the kit moves any old history lines out of existing headers into `Claude/docs/archive/`; the code is never touched.
- **A DemoDisplay stand** for each custom Verse device, with its devices placed on it. Devices whose position matters for gameplay stay where they are.
- **A file that cannot be deleted is parked, not forced:** when a file has to go (replaced in an update, obsolete, a test leftover) and the team is not allowed to delete it, it moves to a `_to_delete` folder at the project root, in a dated subfolder, and tells you. You empty that folder when you are sure. The same holds for the kit when it updates.
- **Support devices outside the play area,** grouped on their stand, so players never see or reach them.

## After every playtest

Claude Code has hooks: commands that run when an event happens. The kit uses one that fires after a playtest ends. The MCP server exposes a single generic tool, so the hook cannot tell a stop from any other call by its name. A small script reads the call and acts only when it is really a game stop. Then, by itself:

1. **qa-regression** reads the logs and adds any problem to `BUGS.md`, under "Newly reported";
2. **planner-docs** updates `STATUS.md` and sorts the new bugs;
3. everything is also written to `Claude/logs/`.

Any other MCP call exits at once and costs nothing.

> **Tip** Once per project, run a playtest and check that a log appears in `Claude/logs/` only when you **stop** it. For the first weeks, read `BUGS.md` and the logs now and then, so you can correct a report that was wrong.

## Long sessions and handing over

A long session slows down and gets expensive because the conversation fills up. Three habits keep it healthy:

- **`/handoff`** writes a short note, `Claude/docs/HANDOFF.md` (goal, what is done and verified, files touched, what failed, next steps). Then run `/clear` (or switch model with `/model`) and start the new session with "read Claude/docs/HANDOFF.md and continue". The new session reads a page, not the whole old conversation.
- **`/compact` with instructions**, for example `/compact keep the plan, the failing builds and the files we changed; drop the exploration`. Without instructions the summary keeps whatever it guesses matters.
- **`/rewind`** (or press Esc twice) goes back to an earlier point, in the code, the conversation or both. It only undoes edits Claude made with its own file tools: changes made through shell commands, by helper agents, or by you outside Claude Code are not undone. Your project's restore points (`/restore-point`) and Git cover those.

If you leave a session running overnight with UEFN open, Claude Code can wait out "overloaded" errors instead of stopping. Set `CLAUDE_CODE_RETRY_WATCHDOG=1` (needs a recent Claude Code, 2.1.186 or later) and, to cap the wait, `CLAUDE_CODE_RETRY_WATCHDOG_MAX_WAIT_MS=1800000` (30 minutes; 2.1.295 or later). The computer and UEFN must stay awake and open, and an error about a spending limit still stops the run.

## Commands that run without asking

New projects come with a short list of pre-approved commands in `.claude/settings.json`: the kit's read-only checks (`verse_check`, `verse_map`, `text_scan`, `agent_cost`, and `ui_kit_check` with `--check` or `--diff`, run with `py -3`, `python` or `python3`) and the read-only Git commands `git status`, `git diff` and `git log`. Everything that writes, deletes or publishes still asks you. Projects made before 1.105.0 keep their own settings untouched: to get the same convenience, copy the `allow` list from the kit's `project-template/.claude/settings.json` into your project's file, or add the rules one by one with `/permissions`.

## Many projects at once

Every project's `STATUS.md` has the same format, so a short script can scan all your project folders and build one table with the last update, the next step and the open issues. The kit does not ship it because it depends on how you lay out your disk.
