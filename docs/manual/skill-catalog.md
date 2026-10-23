# Skills catalog

Skills are small folders of knowledge that Claude reads only when the task needs them. Each has a short description (so Claude knows when it is relevant without loading it), a dense body, and a `references/` folder for detail that is loaded on demand. That keeps your sessions cheap. For the skills that learn from your own maps, read [Skills and lessons](ch:skills-and-lessons).

## Building the map

| Skill | What it gives you |
|---|---|
| `verse-patterns` | Reusable Verse idioms: state machines, multiplayer authority, central logging and timers, item pools, round progression. The coder reads the matching file before it writes a common pattern from scratch. |
| `uefn-device-gotchas` | Quirks of individual device types: DemoDisplay sizing and orientation, Elimination Manager and Item Granter timing, Storm Controller and Player Spawner placement. |
| `uefn-lessons` | Verse, UEFN and MCP mistakes seen across all your projects. Read before writing or debugging Verse, and extended when something non-obvious is found. |
| `mcp-tool-contracts` | One table of "what I want to do through the MCP server" and "the exact tool that works for it". The coder, QA and bootstrap agents all use it instead of each describing the check in their own words. |
| `performance-uefn-checklist` | The short checklist the bootstrap runs in its static review and QA uses when it watches frame rate. |
| `brand-collections-uefn` | Recognises which official Fortnite collection (TMNT, LEGO, Fall Guys and others) a project is built on, and how to record markers for a new one. |
| `game-ui-designer` | A style guide for in-game screens such as shops, missions or teleporters. Still a draft that grows as you add reference examples. |
| `verse-ui-kit` | How to build and wire screens with Epic's free Verse UI Kit: focus, gamepad, Back, shared click events, and what to do when Epic updates its guide. Still a draft. |
| `project-scoring` | How the console's Score page measures the project against its plan: what each criterion counts, how tasks are linked to criteria, and how a new criterion is proposed and approved. |
| `fab-product` | Prepares a Fab product: checks the package against Epic's rules, creates the Documentation and FabListing texts from the code, and writes a clean zip. |
| `economy-sim` | Plans a tycoon or arena economy with numbers: how long each milestone takes, which generator is never worth buying. Pure arithmetic, no editor needed. |
| `genre` | Your genre skills, filled from your real maps. See [Skills and lessons](ch:skills-and-lessons). |

## Keeping token use down

| Skill | What it gives you |
|---|---|
| `token-aware-coding` | Habits for any agent: targeted search instead of reading a whole file, precise file mentions, not re-reading what is already in context. |
| `second-brain-query` | Rules for asking the second brain narrowly, so an answer stays short. |
| `discover-retention` | The facts about the signals Discover uses (bounce rate, QPTR and others) plus a log of retention ideas tried and what happened. |

## Growing the map

These eight skills are about what happens once the map exists: being found, clicked, played longer and visited again. You do not need to know their names. Talk to **growth-manager** in plain words (*help me plan the launch*, *why is my CTR low*, *write a thumbnail for this map*) and it picks one skill or chains several in a sensible order. You can also name a skill yourself: *use the fortnite-thumbnail-pro skill for this*.

| Skill | When it is used |
|---|---|
| `fortnite-analytics-coach` | You paste Creator Portal numbers (CTR, playtime, day 1 and day 7 retention, CCU) or ask for a performance read. It returns a prioritised plan. |
| `fortnite-competitor-analyzer` | You ask what works in your genre. It studies top maps from public trackers and finds where you can stand out. |
| `fortnite-marketing-launch` | You are about to launch, or want to push a live map. A pre-launch, launch and post-launch plan with a content calendar. |
| `fortnite-retention-gamedesign` | Players leave too early. Design-level fixes for onboarding, the core loop, progression and pacing. |
| `fortnite-social-trailer` | Trailer scripts, short-video hooks and captions built around a strong first second. |
| `fortnite-thumbnail-pro` | Thumbnail concepts and generation prompts that respect Epic's rules (1920x1080, no clickbait). |
| `fortnite-title-description` | The whole publishing package: title, description, genre, four tags and three how-to-play lines, with character counts checked, plus a community blog text. |
| `fortnite-update-writer` | Patch notes, short Discord versions and announcements that make players want to come back. |
| `fortnite-growth-lessons` | The shared record of what really worked or flopped in growth work. Read before the eight above, and extended when a real result is known. |

> **Note** `growth-manager` does not touch Verse or devices and never writes `STATUS.md`, `ROADMAP.md` or `BUGS.md`.

## UEFN MCP skills

Fourteen skills built from the 388 tools of Epic's MCP, tested in a lab project. Per-area detail, recipes (each with a `verified` or `unverified` status) and the coverage report live in the `mcp-tool-contracts` references.

| Skill | What it gives you |
|---|---|
| `uefn-mcp-lab-guard` | How an agent tries MCP tools safely in the lab project: GUID path form, what the guard refuses and why, never work around a refusal. |
| `uefn-validation-failure-diagnosis` | What to do when `StartSession` fails with `Validation failed` (for example a stray TargetPoint actor) and how to read the validation log. |
| `uefn-create-use-remove-one-script` | Create, use and remove a test object in ONE script call, so a failure never leaves clutter in the level. |
| `uefn-mcp-heavy-calls` | Cost limits for heavy MCP reads and writes: which calls are slow or large, and how to batch or filter them. |
| `uefn-ui-widgets` | Widget Blueprints through the MCP: widget tree, text, Verse fields, MVVM bindings, animations. |
| `uefn-assets-data` | Create, find, copy, move and delete assets and data tables through the MCP. |
| `uefn-editor-logs` | Read only the NEW editor log lines after an action; log filters and the client-log limits. |
| `uefn-level-devices` | Place and edit actors and devices, tags, folders, event bindings, entities and device properties. |
| `uefn-verse-build` | Read, write, build and fix Verse through the MCP: the write, BuildAll, read errors, fix loop. |
| `uefn-session-regression` | Play-in-editor smoke test: StartSession, StartGame readiness, log verdict, StopGame, StopSession. |
| `uefn-scripting-batch` | Run five or more MCP calls in one server-side script, and the traps (no rollback, guard blind inside scripts). |
| `uefn-materials` | Materials and material instances: create, parameters, parent, usage flags. |
| `uefn-vfx-niagara` | Niagara systems and emitters: create, add and set modules, read and restore. |
| `uefn-physics-mesh` | Static and skeletal meshes, physics assets and textures through the MCP, with the tools known to be refused or crash-prone. |

## Where they live

User-level skills are installed in `~/.claude/skills/<name>/`. The kit does not delete skills you added yourself. A project can override any agent by putting an agent with the same name in its own `.claude/agents/` folder; the project's version wins, only there.
