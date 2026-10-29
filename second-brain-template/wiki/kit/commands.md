---
tags: [kit, manual]
created: kit-1.114.0
updated: kit-1.114.0
sources: [docs/manual/commands.md]
type: kit
status: current
---
# All the commands

Type a command in Claude Code's chat. A command never runs by itself: you type it, and every change still waits for your approval. This list is written from the command files, so it is always the real one.

## From idea to game, in order

| Command | What it does | When |
|---|---|---|
| `/spec [idea or material] [--new-idea] [--improve N] [--jam] [--days N] [--theme "..."]` | Start a game from an idea, or iterate its spec: genre, scored idea, 5-line loop, spec v0, technical risks, one approval | You have an idea, or none: start here. |
| `/game-plan [--jam]` | Turn the approved game spec into the principles (CONSTITUTION.md) and the technical plan (PLAN.md), with one approval | The spec is approved. |
| `/task-list` | Break the approved plan into tasks (T-xxx) with verifiable criteria, stories, dependencies and parallel marks, ready for coder | The plan is approved. |
| `/consistency` | Read-only coherence check of spec, plan and tasks with a severity per finding, before building or after a change | Before building: do spec, plan and tasks agree? |
| `/environment [--playtest]` | Check the environment for the planned game (read only), fix safe things, list what only the owner can do, then the playtest checklist | Before building and before the playtest. |
| `/audit [fix]` | Audit the finished game for bugs: fix the minor ones by itself within the limits, list the serious ones for the owner | A build is ready: check it against the rules, Fab and island compliance. |
| `/delivery` | Before delivery: the list of what only the owner can do, the private release, the memory check with the owner's flags, then the playtest | Before the private release. |

## See the kit work

| Command | What it does | When |
|---|---|---|
| `/demo [--auto]` | The whole kit flow on a pilot game, from idea to playtest, timed: /demo with you, /demo --auto without a single question | You want to watch the whole flow on a pilot game, in a new empty test project. |

## Fab and jam

| Command | What it does | When |
|---|---|---|
| `/fab-check` | Run all the Fab checks on this product, then propose a fix for every problem and apply the ones the owner picks |  |
| `/concept-card` | Score a game idea on Epic's seven jam criteria plus feasibility and scope (out of 100) and write the concept card |  |
| `/jam-check` | Check a jam entry before handing it in (Verse headers, asset names and path length, dev log, concept card) plus the manual list |  |
| `/devlog` | Write the jam dev log (what was built, day by day, and how AI was used) from the kit's logs |  |
| `/text-scan` | Scan publication texts for emoji, decorative Unicode and invisible characters |  |
| `/ui-kit-check` | Check that Epic's Verse UI Kit and its AGENTS.md are installed, and whether Epic changed the guide |  |

## Verse and the editor

| Command | What it does | When |
|---|---|---|
| `/verse-check` | Ask the open UEFN to build the Verse project and report clean / errors / not analyzed |  |
| `/verse-map` | Build or refresh the Verse map (index, component cards, symbols, wiring) so nothing has to be re-read |  |
| `/editor-changes` | What the agents changed in the open editor, session by session, and a plan to undo the newest session |  |
| `/mcp-snapshot` | Map UEFN's MCP now (the kit also does it by itself) and show what is new |  |
| `/learn-map` | Learn now from the Verse code, the project documentation and the devices in the level; queue skill proposals; report where documents disagree with code |  |

## Safety and continuity

| Command | What it does | When |
|---|---|---|
| `/restore-point` | Restore points for Verse code and docs: create one, see what changed since, or undo |  |
| `/handoff` | Write a short HANDOFF.md so a fresh session (or another model) can continue without re-reading everything |  |

## The kit itself

| Command | What it does | When |
|---|---|---|
| `/kit-update` | Update this project to the newest kit version now; with --fetch first download the latest release from GitHub |  |
| `/kit-doctor` | Check this project's kit health and repair common problems (versions, hooks, .verse backups, second brain path) |  |

## Other

| Command | What it does |
|---|---|
| `/relay` | Be the worker of the mailbox: poll Claude/relay/inbox, run the commands one by one, answer in outbox (or show the state with `status`) |

## Two ways to see the flow work

- `/demo`: the whole round on a pilot game (idea, spec, plan, tasks, environment, build, audit, delivery), asking you at each approval.
- `/demo --auto`: the same round, no questions: the AI approves for you and writes it down. The Docs page shows the clock.

## Sources
- The kit manual, chapter "All the commands" (docs/manual/commands.md), kit v1.114.0. Rebuilt on every kit release: do not edit this page, edit the manual.
