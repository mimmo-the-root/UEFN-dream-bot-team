# From an idea to a playable game

The whole path of a new game in the kit, step by step: what you type, what Claude writes, what you decide, and what you see on the Docs page. It is the same path in a normal project and in a game jam.

## The path at a glance

| Step | You type | Claude writes | You decide | The Docs page shows |
|---|---|---|---|---|
| 1. Idea and genre | `/spec "a farm game: round up the chickens"` | the idea card, three variants with a score | the genre, the variant | tab **Idea**, with the score and the genre badge |
| 2. Spec | (same command) | `GAME-SPEC.md`: loop in five lines, stories, success criteria, risks | one approval for spec and score together | tab **Spec**, with the stories and the risk levels |
| 3. Principles and plan | `/game-plan` | `CONSTITUTION.md` and `PLAN.md` | one approval of the plan | tab **Plan**, one block per story |
| 4. Tasks | `/task-list` | the Tasks table in `ROADMAP.md` | nothing, unless you want to reorder | tab **Roadmap**, the next task on top |
| 5. Check | `/consistency` | a read-only report, CRITICAL to LOW | what to fix first | the next-action banner |
| 6. Environment | `/environment` | a read-only readout, then the safe fixes | closing or reopening UEFN, the steps only you can do | tab **Status** |
| 7. Build and playtest | `/environment --playtest`, then the coder | `PLAYTEST.md`, regression tasks | what is a bug, what is fine | tab **Bugs** and **Roadmap** |
| 8. Audit | `/audit` | `AUDIT.md`: minor bugs fixed alone, the rest listed | each serious finding | tab **Bugs** |
| 9. Delivery | `/delivery` | `DELIVERY-GATE.md` | you tick every box, write the memory %, publish privately | tab **Status** |

You can stop after any step. Each file is plain text in `Claude/docs/`, so you can read or edit it with any editor.

## Step 1 and 2: `/spec`

`/spec` starts from an idea: yours, or three that Claude proposes from the genre skills and, in a jam, from the theme. **Before proposing anything it studies**: the second brain, the genre lessons the kit has learned, the retention and competitor skills, the feasibility skills (device gotchas, level devices, MCP contracts) and the proven recipes. What it found is written under *Sources consulted* in the spec; "none found" is an honest answer and the check warns when the section is empty.

Then it asks the minimum (idea, **how many players**, round length, theme, days left), asks you to confirm the genre, scores three variants (the 70 judging points plus 30 buildable) and writes the loop: **Action, Rule, Reward, End, Replay**. The spec says what and why, never how. The quality list, `spec_check.py`, is its test: a first story that is the whole loop with a test you can do in play, measurable success criteria, a risk table, no open question. Below 60 points you may still go on: you force it, and it is written down.

![Idea tab](shot-docs-idea.png)

![Spec tab](shot-docs-spec.png)

## Step 3: `/game-plan`

Only with an approved spec (`python spec_check.py --gate`). It writes the **constitution** (principles with their reason and source, forbidden words, names and budget, and the **Self-healing** block: which small bugs the kit may fix by itself, with 3 attempts per bug and 10 fixes per session) and the **plan**: per story the devices (a proven recipe, a documented skill, or "explore": try it first), the Verse files, the assets (present, import, create), the manual steps only you can do, the build order in two passes with one sample tried alone first, and the first task that reduces each risk. The study comes first here too.

![Plan tab](shot-docs-plan.png)

## Step 4 and 5: `/task-list` and `/consistency`

`/task-list` turns the plan into tasks, each with a test you can do in play, the story it serves, what it waits for and what can run in parallel. The first three tasks cover the high risks. `/consistency` can be run at any time: it never changes a file, it lists what does not fit (a story without a task, a task without a test, a word the constitution forbids). A conflict with the constitution is always CRITICAL.

![Roadmap tab](shot-docs-road.png)

## Step 6 and 7: `/environment` and the playtest

`/environment` reads the plan and tells you, without touching anything, which assets are still to import or create and what only you can do (Beta Access, Python scripting, the MCP toolset). The scenery of the map (the `## Environment` table of the plan: ground, sky and light, props, sound, boundary) is part of the game: after the readout it is built in the map row by row and each row is marked `built` only after reading it back. A Lore checkpoint is saved before the first playtest. `/environment --playtest` writes `PLAYTEST.md` from the spec: per story what you expect and what you observe, per success criterion a box. A failed row becomes a regression task; a small bug follows the Self-healing block.

## Players and Island settings

The number of players is asked in step 1 and written in the spec (`Players:`, `Teams:`): a multiplayer game cannot be fixed on later. `/game-plan` then writes an **Island settings** table (max players, min players to start, teams, round, respawn, join in progress). Most of them are set by hand in UEFN Island Settings: `/environment` reads them to you one by one, and the playtest checklist has the cases with 1 player and with all of them. The check blocks a plan whose max players is lower than the spec.

## Review after every step

Each step is checked by its script and then read with fresh eyes by a second agent (`intent-reviewer`, `qa-regression`) before you decide. Anything that needs a decision comes to you as a question. If you change the spec, the plan and the tasks are listed as to be redone.

## Step 8 and 9: `/audit` and `/delivery`

When the build is finished, `/audit` looks for bugs. Small ones on the constitution's list are fixed by the kit (3 attempts per bug, 10 per audit, with a restore point); a bug that breaks a success criterion or touches the spec is **never** fixed alone: it comes to you with a recommendation. `/delivery` writes `DELIVERY-GATE.md`: what Claude cannot do (Beta Access, Python scripting, Island settings, the manual steps), the private release, and `Memory used: NN%` that you read from UEFN. **Only you tick the boxes.** 100% memory blocks, 85% warns. After a good playtest the game is delivered and the cycle starts again: new ideas, `/spec`, `/game-plan`, `/task-list`.

## Reading the Docs page

The page keeps its header and the three progress rings (Roadmap, Bug fixing, Release status). Under them:

- **Next action**: the one thing to do now, in a fixed order (Found, Advice, Then, and last the Question for you), with a **Copy command** button (paste it in the chat). When everything Claude could build is built and only waits for your playtest, it says "Your turn".
- **Tabs** Idea, Spec, Plan, then Roadmap, Bugs, Status, Documents. A dot says where each step is: grey = not started, amber = this one now, green = done. Old projects that already have tasks and no game spec do not see the first three tabs.
- **Documents** has one card per file; the new files carry a NEW badge, and a file that does not exist yet says "not created yet".
- The page follows the files and redraws within about five seconds.

![Documents tab with the pilot demo card](shot-docs-docs.png)

## The pilot demo: Chicken Roundup

The demo is the whole kit at work, on a small game built from the Epic farm example. It does the **complete round**: idea, spec (with the number of players asked first), plan with the Island settings, tasks, the environment check, the map built in UEFN task by task, the audit with the Fab and island compliance scan, the delivery list and the playtest checklist. It stops before the private release and the publish, which are yours.

There are two ways to run it and the work is exactly the same: **`/demo`** asks you at every approval, **`/demo --auto`** never stops to ask (the AI approves every point on your behalf and writes it next to the approval). A stopwatch runs from the start to the moment everything is ready; the Docs page shows the total big and, smaller, the phase that is running with its own time. Handy for timing a promo video.

**Do not run it in your real map.** The demo needs a test project:

1. In UEFN make a **new empty project** just for tests (Fortnite > Create).
2. Open Claude Code in its `Content` folder and install the kit (`/kit-update`).
3. On the Docs page, **Documents** tab, press **Copy /demo** or **Copy /demo --auto** and paste it in the chat. That is all.


The demo refuses when the project already has your own spec, a plan or tasks, and it never overwrites a file. To run it again in the same test project, just run it again: the files of the earlier demo are moved to `_to_delete`. It never launches UEFN and never deletes anything.

## When something is not clear

- The spec says "not ready": run `python spec_check.py` from `Claude/hooks` and read the BLOCK lines.
- `/game-plan` stops at the gate: the spec has no approval, or has an open question. Fix it with `/spec`.
- A tab is missing: the project has tasks and no `GAME-SPEC.md`; run `/spec` or the demo in a test project.
