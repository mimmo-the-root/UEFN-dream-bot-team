# Changelog

## v1.114.0 — Study with the kit's knowledge, `/environment`, playtest checklist, the idea in the Docs page

- **Workflow arrows on the Docs page.** Idea, Spec, Plan, Tasks, Environment, Build, Audit, Delivery: the step in progress is lit and alive, a finished one turns green, and when a step finishes the next page opens by itself. Build and Environment rows light up when they change. Steps with no data yet are shown greyed, with the command that fills them.
- **Ideas kept, up to 5.** `GAME-SPEC.md` has an `## Ideas` section (one block per idea: pitch, idea score, verdict, weak points, iterations, status). `/spec` starts from the owner's material if there is any, or in assisted mode with three scored ideas if there is none; `/spec --improve N` reworks an idea to raise its score, `/spec --new-idea` adds another (max 5). The Idea page has one tab per idea (Idea 1 always first) and a Compare tab.
- **All command names are English.** `/piano` is now `/game-plan`, `/compiti` `/task-list`, `/ambiente` `/environment`, `/coerenza` `/consistency`, `/consegna` `/delivery` (`/plan` and `/tasks` are Claude Code's own commands, so they are not reused). `update-my-profile` removes the old command files from your profile. Older entries below keep the names they had at the time.
- **The flow stops on red.** A task `Blocked` on something only the owner can do turns the Build arrow red, the next action says "Stopped: your turn" with the steps and a text to tell Claude Code when done, and the Build page shows the same box. `/demo` (also `--auto`) now stops there: no audit, no game session, no "it works" until the owner has done it and the references are read back.
- **The demo box orb beats too.** The Chief of Staff in the demo box of the Docs page now beats green with faster rings while the demo runs or the main session is working, like on the Console page.
- **No fake playtests.** `/demo` and the `mcp-session` agent now say that `StartSession`/`StartGame` through the MCP is a match with nobody in it (the editor stays in editing mode): it is a smoke test, never a playtest nor proof of the gameplay; tasks are verified by a clean build, the read-back of the properties and `[SIGNAL]` log lines, and the real playtest is the owner's.
- **The Chief of Staff counts when it works alone.** The Console page counted only sub-agents as working, so it said 0 (and looked still) while the main session was building by itself. Now the chief of staff counts as one working agent and its core beats green with faster rings.
- **The build follows the timer.** While the demo builds `build: T-00N`, the Build page shows that task as In progress even before the roadmap row is updated; `/demo` now says, at the start of the build phase, to set each row In progress before touching UEFN and Done when its check passes.
- **Status tab = tasks table.** The Status tab of the Docs page opens with a table of all tasks (ID, task, status, release, priority), empty at T0 with a hint pointing to `/compiti`, like the bugs table; it no longer repeats the start boxes. The old "Pilot demo" card in the Documents tab is removed: the demo box next to the next action is the only place.
- **Not started is grey, and it is zero.** On the Score page a new map (nothing done, nothing in progress) scores 0 everywhere: Feasibility no longer starts with free points; Documentation counts as soon as the spec or the plan is written, Scope as soon as there is a plan. Criteria with nothing planned or proven show the grey icon (also in the legend and in the "Where to act" count) and no red gap bar; each tile says in one line what it counts; with a single release the one-dot chart is hidden and the forecast says it needs two closed releases; the empty Evidence box is hidden. Before a plan exists the page says "Not started" and points to /spec and /piano; on a new map the bug ring of the Docs page is empty, not full green.
- **A new map starts differently.** No example rows count as tasks or bugs; the top cards show the journey (0/8), bugs 0 and the release not started; the Status tab offers only two actions: `/spec` or the demo (`/demo`, `/demo --auto`), each with a copy button.
- **Demo clock in a box that is always there**, next to the next action: hours, minutes and seconds in tiles (00:00:00 until a demo starts, with a line that invites you to put the kit's speed to the test), the running phase and the task or scenery row in progress under it. The chief of staff of the console, animated, sits in the corner of the box and turns green while the demo runs. The demo phases are now the eight keys of the arrows (`idea`, `spec`, `plan`, `tasks`, `environment`, `build`, `audit`, `delivery`).
- **The environment is built.** `PLAN.md` has an `## Environment` table (ground, sky and light, props, sound, boundary); `/ambiente` builds each row in the map, reads it back and marks it `built`; `plan_check.py` warns when the table is missing; the demo does not finish with an empty environment.
- **One header on every page.** Island strip (always there, with a fallback while the map is not published) on every page; the session, tokens and project cards stay on the Console page only; a line of the commands useful on that page.
- **All commands.** New manual chapter `commands`, written by `tool/gen_commands.py` from the command files; every footer links to it.
- **First choices.** When the owner opens Claude Code with no task on an empty project, the choices offered are: start from an idea (`/spec`), the demo with you, the automatic demo, or analyze an existing map.
- **The study step uses the kit's own knowledge.** `/spec` and `/piano` now start by consulting the second brain, the genre lessons (`skills_lib.py patterns` and `consult`), the retention and competitor skills, the feasibility skills and the proven recipes, and write what they found under `## Sources consulted` (new section in `GAME-SPEC.md` and `PLAN.md`). "None found" is an honest answer; `spec_check.py` warns and `plan_check.py` reports a LOW when nothing is written.
- **New command `/ambiente` and `env_check.py`.** A read-only readout of the environment from the plan: assets to import or create, manual steps, and the checklist only the owner can do (Beta Access, Python scripting, MCP toolset). Safe fixes are automatic, closing or reopening UEFN is asked first, and a Lore checkpoint comes before the first playtest.
- **Playtest checklist from the spec.** `/ambiente --playtest` writes `PLAYTEST.md`: per story the expected result and the observed one, per success criterion a box. A failed row becomes a regression task; minor bugs follow the Self-healing block of `CONSTITUTION.md`.
- **The Docs page shows the idea.** Tabs Idea, Spec, Plan beside Roadmap, Bugs, Status and Documents, with the next action on top; header, three rings, release status, phases, timeline and footer are unchanged. Old projects with tasks and no game spec do not see the new tabs. The console server serves `GAME-SPEC.md`, `CONSTITUTION.md` and `PLAN.md` to the page.
- **Players are asked in step 0.** `GAME-SPEC.md` has `Players:` and `Teams:`; `spec_check.py` blocks without them. A multiplayer spec needs an `## Island settings` table in `PLAN.md` (max players, min players, teams, round, respawn, join in progress): `plan_check.py` reports a HIGH if it is missing or if max players is lower than the spec. `/ambiente` reads the settings to the owner as a checklist for UEFN Island Settings, and the playtest checklist adds the cases with 1 and N players.
- **A review after every step.** `/spec`, `/piano` and `/ambiente` have the checker plus a fresh-eyes read by `intent-reviewer` or `qa-regression` before the owner decides.
- **New command `/audit` and `audit_log.py`.** After the build: `codebase-auditor`, `qa-regression` and `compliance-reviewer` look, every finding is classed minor, medium or major, minor ones are fixed by the kit (3 attempts per finding, 10 per audit, enforced), medium and major ones go to the owner.
- **New command `/consegna` and `release_gate.py`.** `DELIVERY-GATE.md`: what Claude cannot do (Beta Access, Python scripting, Island settings, manual steps), the private release, `Memory used: NN%` and the playtest. Only the owner ticks the boxes; 100% memory blocks, 85% warns.
- **Compliance in the audit and the gate.** `/audit` runs the read-only Fab/island scan; `DELIVERY-GATE.md` now has five sections: configuration, compliance (with the `Scan:` result), private release, UEFN Publishing Validation and memory (Memory Usage, Download Size, Cooked for Platforms, Project Size), playtest. The Docs page Status tab has a "Delivery check" card (audit findings, gate progress, memory, scan) with links to `AUDIT.md`, `DELIVERY-GATE.md` (the manual steps) and the Fab details page.
- **Privacy rule.** Where a personal name would be written, write `***anonymized***` (GDPR, Regulation (EU) 2016/679), only in the user's own files, never in Epic assets. It is in the constitution template, the skills, `/fab-check`, `CLAUDE.md` and the glossary. `fab_assets.py` uses asterisks and has an opt-in `--clean`; `fab_pack.py check` never modifies a map project.
- **Timed demo.** `/demo` now runs the whole pilot flow with a stopwatch (`demo_timer.py`): with the owner it asks at each approval, `/demo --auto` asks nothing and the AI approves every step on the owner's behalf, start to finish. Only two buttons on the Docs page, and both do the same complete round (idea, spec, plan, tasks, the map built in UEFN, audit with compliance scan, delivery list, playtest checklist); `--auto` is the one that never stops to ask. The clock starts with the demo and stops when everything is ready: total on top, the running phase smaller below, laps per phase in `DEMO-TIMER.md`. Made for timing a promo video.
- **`_to_delete`, in the open.** New `to_delete.py`: the kit parks, never deletes. A previous demo run is parked when the demo is run again, and `docs_migrate.py` parks the old demo copy folder of earlier projects on `/kit-update`. The What's new page has "Files parked for cleaning": open the folder to inspect, delete one parked folder or everything (second click to confirm); the server only deletes inside `_to_delete`.
- **Device placement rule in the plan and the audit.** `/piano` writes where each device goes (on the DemoDisplay stand outside the play area, or in place when its position is gameplay); `/audit` checks it.
- **The console says which project it is on.** For a UEFN project the folder is `<name>\Content`, so the console showed "Content"; it now shows `<name>`, on the console and on the Docs page (connection line and next-action banner).
- **"Next action" is only a text.** The banner shows what to paste in Claude Code (`Implement T-001 with the coder agent. Show me the plan first and ask before each change.`), button "Copy text", and says that nothing runs by itself.
- **Fixes found by the Lab test.** The Docs page no longer counts the template example bug and shows Players and the Island settings card; `run_log.py stop` refuses a phase that is not open; `/spec` lists the eight `concept_card` keys on the 1 to 5 scale.
- **`run_log.py`** writes phase times and tokens (counts, never a price) and prints a report table.
- **`/demo` and the Docs page button.** The pilot Chicken Roundup is now a 4-player co-op example. Use it in a new empty test project, never in your real map.
- Tested in a test project with the Epic farm example (Chicken Roundup).

## v1.113.0 — From the spec to the tasks: `/piano`, `/compiti`, `/coerenza`

- **New command `/piano`.** Only with an approved spec. It writes `CONSTITUTION.md` (principles with their reason, forbidden words, names and budget, scope limits, and the closed list of minor bugs the kit may fix by itself) and `PLAN.md`: one section per story with devices (recipe, skill or explore), the assets inventory (present, import, create), the manual steps only you can do, the build order in two passes and the first task that reduces each risk. One approval.
- **New command `/compiti`.** Breaks the plan into tasks through `planner-docs`, keeping the ROADMAP table contract: the story `[S1]`, parallel `[P]`, dependencies `(after T-001)` and the risk `[R1]` live in the Feature cell. `intent-gate` checks every task; the first three tasks must cover every high risk.
- **New command `/coerenza` and `plan_check.py`.** A read-only check of spec, plan and tasks with a severity per finding (CRITICAL, HIGH, MEDIUM, LOW, 50 at most). A conflict with the constitution is always CRITICAL. It finds stories without a plan or a task, tasks without a verifiable criterion, missing or circular dependencies, and high risks no early task reduces.
- **New templates `CONSTITUTION.md` and `PLAN.md`.** `spec_check.py` and `plan_check.py` now also find the project's docs when run from `Claude/hooks`.
- Tested in the Lab project with the Epic farm example: coherent spec, plan and tasks pass; a task that adds a forbidden leaderboard is a CRITICAL.

## v1.112.0 — Start a game from the spec: `/spec`, spec check, risks

- **New command `/spec`.** A game starts from an idea (yours, or three proposed): minimal card, the genre you confirm (in a jam, proposed from the theme), three variants scored with `/concept-card` (60 to go on, your call to force), the loop in five lines, spec v0, technical risks, one approval. A new mechanic is a new story (P2, P3) with its own test; a change to an approved spec asks you again.
- **New `GAME-SPEC.md` template and `spec_check.py`.** The spec says what and why, never how. The check is its test list: a P1 story with an independent test and a Given/when/then, measurable success criteria, assumptions, a risk table with levels, no open `[NEEDS CLARIFICATION]`. `--gate` is what planning will run: approval and a score of 60 or more (or your forced yes). `--jam`: the theme line warns before 11 November and blocks after.
- **`project-bootstrap` and the manual point to `/spec`.** `SPEC.md` stays the spec deduced from code; the new game spec is a separate file, so an existing-map check never mistakes one for the other.
- Tested in the Lab project with the Epic farm example (Chicken Roundup): empty template blocked, spec ready, gate before and after approval, jam before and after the theme day.

## v1.111.1 — Fab products: reliable start, checked documents, /fab-check

- **Fab product session start no longer times out.** The console autostart probed four ports one by one and, with 8766 taken by another console, waited far beyond the 30 s of the session hook, so the agent got no Fab context. Probes are now fast and the product's console takes the first free port.
- **`/fab-check` proposes the fixes and does the one that needs UEFN closed.** After the report it lists a fix for every problem and asks which to apply. New `fab_clean_cycle.py`: with the owner's yes it closes UEFN politely, cleans the texture source paths (backup outside the project), reopens the project, waits until it is open and re-checks; it never forces a close that asks to save unless told.
- **The Fab check verifies the documents and `/fab-check` fixes them.** A TODO left in README, AUTHOR, listing or third_party, a README that points to a SETTINGS.md that does not exist, or a third_party.md that says "nothing detected" while the textures come from other authors are now reported. `fab_pack.py listing-fill` fills the Technical details from the product, fills the README parts the assets answer (what is inside, setup, plugins) and lists the texture authors in third_party.md (the names are kept in the lab, so they survive the path clean).
- **Fab console shows the whole listing description** (it was cut at 300 characters with "...", although it is the text you copy into the portal).
- **New command `/fab-check`** (user level, installed by `update-my-profile.cmd`): runs the Fab package check, the asset scan and the listing checklist, and reports in plain words.

## v1.111.0 — One workflow to share: states, buttons and release

- **Lessons reach the kit at each release, by themselves.** `publish.ps1` runs `promote-genre-skills.py --community-only`: the lessons you approved are written as community packs in the repo (privacy checked per file; a file with findings is skipped and reported) and users receive them as one proposal per skill in To approve. The Lessons tab has an *In the kit* column and a *Not in the kit yet* filter. A recipe of yours that is already in the kit shows *in the kit* on the Recipes tab and leaves To share.
- **Skills tab: which skills are new.** A *In the kit* column (in the kit / new, with its creation date, goes out at the next release / nothing to ship yet) and a *New, not in the kit* filter. At each release `publish.ps1` runs `promote-genre-skills.py --auto`: a skill already in the kit gets only its lessons pack, a new skill that has lessons of yours or an official pack goes in whole (SKILL.md and references are checked for secrets, personal paths and your private terms, not for markdown); `Claude/community/kit-skills.json` lists what ships.
- **Maps & products finds the recipes of a Fab product.** A recipe stores only the hash of the name the agent gave to the product, so a product named in other words (without `root_`, with spaces, without FAB) showed 0 recipes. The page now tries those variants.
- **Tests no longer leave folders in your profile.** Three Fab tests wrote lab folders (`prod`, `Proj`, ...) in `~/.claude/fab-lab`, and they showed up in Maps & products as if they were your projects. They now use a temporary folder; delete the two leftovers by hand.
- **Tests no longer write in your project registry either.** One Fab test registered temporary projects (`prod`) in `~/.claude/kit-projects.json`, so they appeared in Maps & products. If you see `prod` or `Proj` there, remove those entries by hand.
- **This product (Fab):** the empty recipes box says what really happens (the agent writes the recipes when you press Learn) instead of promising the kit does it from Verse code.
- **Contribute to the community is ON by default.** So creators see what their work produces (*ready to send* in To share). Nothing leaves the computer until you press the button and see the exact JSON; the switch in the Community tab turns it off, and an explicit off is kept.
- **The same states and the same buttons in every tab.** Lessons, Recipes, Skills, To share and the UEFN MCP box all show a *State* column (Collected → Ready → Shared, or Private) and the same buttons: **Keep private** / **Make shareable** per row, **Promote all** / **Keep all private** for the list on screen. No more check boxes or "not yet" chips; the filters are the states. The UEFN MCP *Not in the kit yet* box lists the proven recipes with the same buttons (a recipe kept private is not released). *Maps & products* now names the skills each project feeds.
- **To share has one life for everything: Collected → Ready → Shared, or Private.** Lessons, recipes and the MCP proof follow the same states, and the filters are the states. *Collected*: learned, waiting for something (the map is published, or Contribute is on), with the reason. *Ready*: users press Contribute; on the maintainer's computer it simply goes out with the next release. *Shared*: sent (users) or released (maintainer). *Private*: every lesson and recipe has a **Keep private** button (and **Make shareable** to undo) until it is shared. Nobody chooses a section any more (the kit picks it from the words of the lesson) and nobody decides recipe by recipe: a recipe goes out unless you keep it private.
- **Sending to the community: you only click on GitHub.** The GitHub page opens with the commit title and the description already written, and (once you save your GitHub name in the Community tab) with the file already named after you, so there is no rename step. On the maintainer's computer a *View* switch (Maintainer / Contributor) in the Community tab shows what a user sees, to test it. Buttons now have a visible border.
- **The maintainer does not send through GitHub.** `update-my-profile.cmd` (and the release tool) mark the profile of the computer that holds `publish.ps1`. There, To share shows lessons, approved recipes and the MCP proof as *goes into the kit at the next release* (no Contribute button) and the release boxes appear; other users keep the GitHub flow and never see the boxes.
- **Release boxes on the Skills page.** Each new skill (Genre skills table) and each lesson not yet in the kit has a *release* box, ticked by default. Untick it and `publish.ps1` leaves that skill or lesson out of the release (kept in `skills/release-hold.json` in your profile, never shipped).
- **UEFN MCP tab: what is not in the kit yet, and clearer words.** A *Not in the kit yet* block (recipes proven by your work, new tools in your UEFN, recipes to replay because Epic changed their tool) and, at each release, `publish.ps1` runs `tool/collect_mcp_evidence.py`: the recipes your work proved become *proven* in the kit (status only, same file layout, never arguments or names). The proof is kept in your profile (`~/.claude/mcp-evidence.json`, only the names of the argument fields), written by the work hook at every call, so deleting a project from the disk loses nothing; ledgers still on disk are read once as backfill. The tab is now *UEFN MCP tools* and the first entry reads *first list of the UEFN tools saved*, then *N tools added, N removed, N changed*.
- **Lessons tab:** the condition no longer reads "when when".

## v1.110.2 — Fab: Checklist and documents, rules for the agent

- **The Checklist tab appears once.** On the Checklist page the server added a second tab next to the one the page already has.
- **`/EntityFramework` is an Epic library.** Its imports no longer raise "No reference to assets of another project".
- **Documents of a Fab product.** `docs` always creates `Documentation/AUTHOR.md` with your saved signature (never overwritten); `SETTINGS.md` only when the product has Verse code; the listing template has no Price and no Subcategory section; `zip` no longer tells you to test the archive in a clean project.
- **Rules in the skill fab-product.** Blocks, warnings and notes are counted apart (a note is never a warning); `Collections` and `Developers/<user>` belong to the project; price, subcategory, licences and `third_party.md` are the owner's (the agent writes nothing there); no zip unless asked; no screenshots or thumbnails by the agent; tags only among the portal's suggested ones (`fab_checklist.py tags`).

## v1.110.1 — Security: recipe endpoints

- **Fixed the 5 CodeQL alerts (path injection) in `skills_lib.py`.** The recipe buttons of the Skills page (send, export, approve from the inbox, list) took the skill name from the request through a text check. They now look the name up among the skills that exist on disk, like every other console endpoint, so the request can never steer a file path. A skill that does not exist has an empty recipe list instead of an error.
- **The tests of the Fab Checklist no longer depend on the kit installed in your profile.** One test failed on GitHub (where no profile exists) and turned the release red; it now uses the kit files of the checkout.

## v1.110.0 — Fab: the Checklist page and the asset checks

- **The Skills page by tabs, for maps and for Fab products.** Four cards on top (Waiting for you, Lessons, Recipes, Learning from, with rings), a LEARN block, and tabs in groups: To approve, To share, Lessons, Recipes, Skills, Maps & products, This map / This product, UEFN MCP, Community. Every list has a filter row and five items per page, the counters of the tabs match the lists, and what you approve or send leaves its queue. The Classic view is gone: editing a lesson, approving a pack and *Approve all* now live in To approve.
- **LEARN for maps too.** *Learn from this map* prepares the recipes of the map by itself (no AI) and asks the agent, once, at the end of its next answer, to read code, documents and devices, write the blueprint and propose how-to lessons. Same idea as the Fab button.
- **Maps & products list.** Every project the kit learns from, with its lessons, recipes and a learning bar; maps are named after their folder (the one above Content), so two maps no longer share a recipe key.
- **The Fab console opens by itself.** At the start of a session in a Fab product the kit starts the console (replacing an old one) and opens it in the browser; if that fails, the agent is told to start it itself in its first reply.
- **The Checklist tab is always there on a Fab product.** The server added it only when the page did not contain `href="agent-console-fab.html"`, but every page carries that text in its fallback script, so the server never added it and the tab depended on the script. Now it checks for the real link (and the test too).
- **Assets are cleaned by themselves.** Before every `check` and `zip`, Windows user names and the names of your other projects found in the source paths inside the `.uasset` files are replaced with `x` of the same length (file size unchanged, backup outside the project, a note says what changed). Nobody has to ask for it, and it works on every Fab product.
- **A folder called FAB is a Fab product, by itself.** `root_FAB_rainbow` no longer gets the map-or-product question or the map template: the kit registers it as a Fab product at session start (your explicit choice, map or fab, always wins).
- **The Fab console never shows stale pages.** `fab_lab.py console` now checks the version of a console already running for the same product: an older one is asked to quit and replaced, so no more restarts by hand after an update.
- **New console page "Checklist" (Fab products only).** Seven stations (Project, Content, Build, Listing, Extra, Zip, Submit; Extra is the memory calculation and a private release, one more round of validation before the zip) with every check in plain language: what was looked at, what to do, who checks it (the kit, the editor, you, or "extra" for checks added after a rejection). A verdict (NOT READY, NOT YET, READY) with a bar and the percentage of checks passed. Items only you can judge are tickable by hand. The UEFN validation log is pasted and recorded (errors and warnings counted); without a clean record the upload stays blocked. Buttons: run all checks, make the zip (locked while a block remains), re-read the finished zip (unzipped in a temporary folder and checked again). The tab appears only in a Fab product's console; everything is stored in the lab folder in your profile, never in the project.
- **Asset scan (`fab_assets.py`).** Reads the `.uasset` files and finds imports of another project's assets (the cause of "Disallowed reference" in two Fab rejections), assets that still carry another project's internal name, and Windows user names saved in the import paths. Part of `fab_pack.py check` and of the Checklist.
- **The zip leaves out** `.lore`, `.urc`, `.loreignore`, `.urcignore` and `*.code-workspace`.
- **Maps: traces of other projects (`map_trace.py`).** The same asset scan for normal maps, as a warning only: `/kit-doctor` mentions it and `map_trace.py --apply` records one bug row ("Assets keep traces of other projects") in `BUGS.md`, once. Nothing is changed in the assets.
- **MCP contract: changing a reference or an array of references.** Read it first, set it only when asked, read it back, and stop and ask if it differs (a rewiring through the MCP had left a manager with 0 participants). Troubleshooting entry added.
- **Fab agents get the rules learned from the rejections** (skill `fab-product` and the Fab start message): scan first, no hand-copied assets, no `update_metadata_tags`, exact parameter names, no `list_properties` on textures, no byte edits, never close the editor.
- **Skills page: a button to learn from a Fab product.** Section "FAB LAB": the button collects candidates from the failed calls (no AI) and asks the agent, once, at the end of its next answer (Stop hook `fab_lab.py stop`), to queue lessons with `fab_lab.py propose`. You edit, approve or reject them on the page; approved ones go to `~/.claude/fab-lessons.json` and every Fab product reads them at start (`fab_lab.py lessons`). Lessons are never shared outside your computer without the existing community flow.
- **Skills page: "Recipes the skills know" shows the latest 20, 5 per page.**  The genre table pages 5 at a time too.
- **Skills page for a Fab product: "This map" becomes "This Fab product"** (it was empty: a product has no genre or blueprint). It shows the Verse files of the product, recorded calls, approved lessons, recipes and closing cards.
- **New skill "mechanics": recipes to REBUILD a stand-alone device, a game mechanic or a whole map template** (steps, devices, settings, wiring, Verse files with their code, assets, how to verify). `fab_lab.py draft-recipe <project> "<name>"` writes the draft from the product (Verse files and the editor calls that worked, in order), the agent fills the TODOs and saves it with `skills_lib.py recipe-add mechanics`; reuse with `skills_lib.py recipes mechanics <keyword>`. The kit also prepares the recipe BY ITSELF, with no AI and no agent: from the Verse code and the README of the product (devices it needs, settings with their defaults, Verse files with their code, assets, setup steps, what to check). It runs when the Fab console reads the product and again on Learn, and only when the Verse files changed. The Learn button and the Fab start message ask the agent to refine it. The Fab Learn candidates now start from what worked, not only from errors.
& as confirmed at once** (a map still needs a second use); no approval step.
- The empty `Collections` folders (Content and Developers/<you>) are no longer reported: the editor creates them.
- **The Checklist reads the UEFN validation by itself.** "Run all checks" asks the open editor (MCP, read only) for the validation lines of its log and uses the latest run: an error blocks, a warning is a warning, validation lines without problems pass. With no validation line in the log it stays "to do" (the editor validates when you start a play session or publish), never a guess. Pasting a log is only a fallback.
- **Verse build is automatic too:** "Run all checks" asks the open editor to build the Verse code (`verse_check.py`): 0 errors passes, warnings warn, errors block, editor closed stays "to do".
- Checklist: the Custom Inventory item is removed; the tags are only a suggestion (the portal offers a fixed list); a missing `third_party.md` is recreated; in the Zip station the order is fixed (make it, then re-read it).
- **Technical information follows the portal form** (UEFN Source, Game Systems): `listing.md` now has the real fields with their allowed values, and the Listing card of the Checklist page shows them with the allowed values and a suggested value for each (they are information for the form, not a check) (Verse code is framework Other, 1 project, 0 C++ classes, UI from the widget assets).
- **Tags: the portal's suggested list** (Rendering style, Period/theme, Animation, Features, Engine, Materials) is in the Listing card; your tags outside it are marked, never blocked.
- **One zip, one name.** `fab_pack.py zip` always writes `<Project>.zip` and replaces the old one (before, a second run wrote a file with the date next to the first, and it was unclear which was current); the Checklist re-reads exactly that file.
- **The Listing card opens the product's documents:** README.md and SETTINGS.md (setup and settings for the customer) and listing.md, third_party.md, screenshots.md (portal texts), read-only, in the console; a missing one is shown as missing.
- **The verdict does not count the upload itself.** Station 7 (sending it on the portal) is the last act, not a check: with every check of stations 1 to 6 green the page shows READY TO PUBLISH and 100%.
- **No `screenshots.md`:** the kit no longer creates it (the listing images are made by hand); an existing one is left alone. The "No redirectors" item is yours to do in the editor.
- A user name already replaced by `xxxx` in an import path is no longer reported.
- `update-my-profile.cmd` copies `fab_checklist.py` and `map_trace.py` into the profile. New test `test_fab_checklist.py`.

## v1.109.1 — Fab: the generated files go inside the project

- **Fab lab: lessons from Fab products.** A Fab product holds no kit files, so nothing was recorded while you worked on it. Now a hook in your profile (`fab_lab.py hook`, installed by `update-my-profile.cmd`) records the UEFN MCP calls of every project registered as Fab in `~/.claude/fab-lab/<Product>/`, outside the project (nothing is added to the zip). `fab_lab.py card` writes a draft closing card for a finished material or mechanic, and `fab_lab.py console` opens the Agent Console on that data (`UEFN_FAB_LAB`). Maps are unaffected. Test: `tests/test_fab_lab.py`.
- **Fab products can use the kit scripts.** In a Fab project there is no `Claude/hooks`, so commands such as `mcp_map.py --find`, `skills_lib.py recipes` and `recipe-add` failed and agents guessed tool names (for example for renaming an asset: `AssetTools/move`). The start message, `coder`, `fab-product` and `mcp-tool-contracts` now point to the profile copy, and `mcp_map.py --find` answers from the 388 known tool names when no live map exists yet.
- **No `Claude/` folder is ever created inside a Fab project.** `recipes_status.progress()` no longer creates `Claude/logs` when it does not exist, and the Fab console runs with the lab folder as working directory.
- **Fab lab keeps the full arguments** of the editor calls (scripts, parameter names), the closing card lists the calls that worked in order, and the hook also records sub-agent start/stop so agents such as `materials-expert` show up in the console.
- **Skills page: "Recipes the skills know".** Official recipes and the ones learned from your work (hypothesis until a second map uses them) are now listed; before, only patterns were shown.
- **Fab wants the whole project zipped, so `Documentation/` and `FabListing/` now live inside `Content`**, in the folder that holds the product's assets (`Content/<Product>/`), not next to `Content`. `fab_pack.py zip` packs the whole project and no longer leaves `FabListing` out; `check` no longer blocks `FabListing` inside Content. `docs --apply` moves the folders an older version made next to `Content` into the new place (nothing overwritten, empty old folders removed). `--product NAME` chooses the folder when Content has several.
- `third-party.md` is now `third_party.md`: names inside the archive may not contain a hyphen (an older file is renamed when moved).
- **Static Verse check: no false warning for `Print` inside a device class** (the class inherits it; a published map builds without the import).
- **Widget calls keep the exact upper/lower case of the asset name** (skill `uefn-ui-widgets`): a call with the wrong case made the editor save `WB_main.uasset` as `WB_Main.uasset`, and Lore reported a name case mismatch.
- **The change log no longer lands in `Claude/Claude/logs`** when a sub-agent runs from a deeper folder: `verse_changes.py` walks up to the folder that holds `Claude/hooks`.
- **Manual: how to start a game.** New section "Starting a new game: from the idea" (your own idea or ideas from Claude, `/concept-card`, `project-bootstrap`, first playable version), a "first hours on theme day" section in the jam chapter, and a pointer in the Quick start.

## v1.109.0 — Fab products, economy, log signals, delivery, safe editing

- **Fab products.** New skill `fab-product` and helper `fab_pack.py` (in your profile, never in the project). `check` tests the package against Epic's Fab rules (no `.py`, no `Saved`/`Intermediate`, no kit files, names with letters, digits and underscore, paths up to 140 characters counted from the top-level folder). `docs` creates `Documentation/` (README and a `SETTINGS.md` generated from the `@editable` settings and Verse summaries) and `FabListing/` (listing texts, third-party declaration, image list). `zip` writes a clean archive. `grid` puts the listing captures in a panoramic grid on a plain background. Nothing is written without `--apply`, existing documents are never overwritten. A new project answered "Fab product" points the agents to this skill.
- **Verse style for Fab products.** Every Verse file is a small manual: header with what it does, why it is useful, quick setup, good to know, version and date, then your signature block (ASCII art and links, saved once with `fab_pack.py signature save`, kept in your profile). `fab_pack.py header <Name>` prints a new header; `check` warns when a part or the signature is missing. Fab products only; the generated `SETTINGS.md` reads the `WHAT IT DOES` text too.
- **Economy simulator.** New skill `economy-sim` and helper `economy_sim.py`: from the planned prices and incomes it shows when each milestone arrives and which generator is never worth buying (pure arithmetic, no AI, no editor).
- **Log signals.** The logger template gets `Signal(Name, Details)`, which prints `[SIGNAL] name key=value`. The helper `log_signals.py` counts them, checks optional rules in `Claude/docs/signals.json` and reports expected signals that never appeared. `qa-regression` uses it.
- **Delivery document.** `Claude/hooks/delivery.py` writes `Claude/docs/DELIVERY.md`: the state of the map (finished tasks by release, open bugs, verdict) rebuilt from the project's documents, with free parts for the pitch, controls and credits that are kept. `planner-docs` knows it.
- **Editor change record and "undo session".** The call ledger now keeps the session and the date. `/editor-changes` lists what the agents wrote to the editor per session; `editor_changes.py undo-plan` prints the steps that would undo the newest one (creations can be deleted; changed values cannot, so those say "manual"). It never touches the editor.
- **A real lock on the editor.** Only one session at a time may write; a second one is refused with a clear message (reading is never blocked). It goes stale after ten minutes; `editor_lock.py status` and `release`; `UEFN_KIT_LOCK=0` turns it off.
- **Recipes after a new UEFN.** `recipes_status.py --stale` lists the recipes whose tool changed or was removed in a newer UEFN (from the saved map history); `--retested` stamps today.
- **Static check of Verse.** `verse_static.py` finds the certain mistakes without the editor (unbalanced brackets, mixed tabs and spaces, `@editable` on a `var`, `OnBegin` without `<override>`, a class defined twice, missing imports). `/verse-check` runs it first. It is not a build.
- **Console proof.** `tool/shoot_consoles.py` starts the real console on a demo project, opens all seven pages in a browser, fails on JavaScript errors or an empty page, and saves dark screenshots. It already caught the Score page showing its empty state on a project without the criteria file.
- `update-my-profile.cmd` copies the new helpers too.
- Token budget baseline raised for the two new skills (`fab-product`, `economy-sim`): they load only when the topic comes up.

## v1.108.4 — Counting installs, dark Score page

- **A way to see how many machines take each release.** Every release now carries a `kit.zip` file and the automatic update downloads that file, so GitHub counts its downloads (GitHub does not show the number on the Releases page: read it with `python tool/installs.py`). Nothing is sent from your computer and no one is identified; a download is roughly one machine taking that version. `python tool/installs.py` prints the numbers per release. The README shows the total as a public "kit downloads" badge. The count starts with the machines that already run this version or later, because a kit downloads with the code it already has.
- **Score page is dark like the other console pages**, also when the system uses a light theme (the manual screenshot was light before).

## v1.108.3 — The kit updates itself from GitHub

- **Automatic profile update.** Until now only the step "profile to project" was automatic; the step "GitHub to your profile" needed `/kit-update --fetch` or `update-my-profile.cmd`, so a new release never arrived by itself. Now the global SessionStart hook starts, at most once every 6 hours, a background check of the newest GitHub release (`kit_fetch.py --auto`). A newer release is downloaded into `~/.claude` without delaying the session, and the project picks it up at its next session start ("KIT UPDATED"). The check writes one line to `~/.claude/kit-auto-update.log`. Switch it off with `UEFN_KIT_AUTOUPDATE=0` or an empty file `~/.claude/kit-auto-update.off`.
- **The global hook updates itself too.** `kit_fetch.py` now also installs `user-level-hooks` into `~/.claude/hooks`. The version file is written last, so an interrupted update is retried.
- **One manual step, once:** run `/kit-update --fetch` (or `update-my-profile.cmd`) after this release. It brings the new `kit_sync.py` and `kit_fetch.py` into your profile and projects; from the next session on, releases arrive by themselves. Kits older than this release cannot do it alone: nothing in them looks at GitHub.

## v1.108.2 — Score page in the manual

- **The manual covers the Score page:** the console chapter now says seven pages and shows the Score page with demo data; the README lists it in the console menu and in What's new.
- **Score page legend:** the traffic-light note no longer quotes example release names.
- **Jam release video and posts:** `docs/release-videos/release-1.108.1-jam.mp4` (our own neon temple graphics, no Epic artwork) and the X and Discord texts.

## v1.108.1 — Score page and jam tools

- **`/concept-card`** scores an idea on Epic's seven jam criteria (ambition, theme, fun, gameplay, visuals, level design, audio: 70 points) plus our feasibility and scope (30 points) and gives a verdict out of 100.
- **Score page in the console (new tab "Score"):** how far the project is against its own plan, release by release. A chart of plan, built and proven with a forecast, a traffic light per criterion (red act now, yellow watch, green fine) and a priority number. Primary criteria are the contest's own (70 points), additional ones are ours (30 points). It is computed live by `score.py` from ROADMAP, BUGS and the release-readiness verdict, so it moves when you close tasks or bugs in the docs; a snapshot is saved when a release closes. New criteria are proposed through the Skills page (new skill `project-scoring`, no new agent).
- **`robots.txt` and a sitemap badge:** the manual publishes a `robots.txt` that points to its `sitemap.xml`, and the README badge row links to the sitemap.
- **Manual:** three new chapters: *2026 Epic AI MegaJam* (how the kit helps and what we added), *A UEFN map project* and *A Fab product project* (what is installed and which documents each produces; the Fab documents are marked as planned for 1.109). **Repo:** `sync-skills.ps1` and one message in `mcp_lessons.py` are now in English (the confirmation answer is `y`).

## v1.108.0 — Ready for the jam

- **A new project asks: map or Fab product?** Open a session from the `Content` folder of a UEFN project with no kit: for a map the kit shows a dry run (how many files), asks for a yes, copies `project-template/` without overwriting anything and runs the setup steps. For a Fab product it installs nothing (its components are added to the customer's project later) and remembers the answer outside the project. New `kit_install.py` in your user profile.
- **Verse headers keep only the present.** An English summary that is always up to date, the real date and the version; no change history in the file. Every change is one line in the new `Claude/logs/verse-changes.jsonl` (file, summary, reason, outcome), next to `verse-errors.jsonl`. Old history lines are moved out of existing headers into `Claude/docs/archive/` on the first session, code untouched. The reviewer now blocks a header with history or a change without a log line.
- **`/concept-card`** scores an idea from 1 to 5 on six criteria (feasibility, scope, hook, showability, retention, originality) and gives a verdict out of 100.
- **`/devlog`** builds `Claude/docs/devlog.md` day by day from the two logs; your "How AI was used" text is kept.
- **`/jam-check`** checks Verse headers, asset names, path length (140 with the project folder name), dev log and concept card, then lists what only you can confirm (private version code, 30-60 s video, licences, Fortnite rules).
- **What's new page:** a "Changes" tile shows how many things the release changed, so the top row is never all zeros.
- **Epic AI MegaJam timer on the What's new page (with a link to the jam page):** days, hours, minutes and seconds to the start of the jam, then to the deadline, shown in your local time. The dates are one line (`JAM`) at the top of the page script.
- **One number for the agents: 22** (17 team agents plus the 5 UEFN MCP sub-agents) in the README, the manual, the badge and `docs/kit-stats.json`.
- **Lab test of 1.107.6:** the guard refuses `save_assets` with no list and lets one with named assets pass; `SelectAssets` answers in 1.4-1.7 s whether UEFN is in front or not, so the earlier timeouts did not come from the editor running in the background. Texts corrected in the guard skill and the manual.
- **Manual:** new chapter "Kit for the jam". **Repo:** `sync-skills.ps1` and one message in `mcp_lessons.py` are now in English (the confirmation answer is `y`).

## v1.107.6 — Safer calls to UEFN

- **A call that changes something and times out is never repeated blindly.** The five MCP sub-agents, the lab guard skill and the manual now say it: the call may have worked, so the agent reads the editor state first (no second device, entity, file or session).
- **`save_assets` without a list of assets is refused** by the lab guard: it would save every unsaved asset of the project. Name the assets, or pass `allow_save_all: true` on purpose.
- **Known crashers, with safe ways out.** The `get_lod_count` entry now says what to read instead (the `Triangles` tag, `static_materials`, the bounding box, Nanite settings). New in the traps: `EDIT COPY` with no world, opening asset editors from Python, the editor throttled in the background, rotators by name, and the two new questions of UEFN 42.40. A new test fails if a skill, agent or command names a tool marked `avoid`.
- **The doctor checks "Load on Startup".** If UEFN opens on the home screen, a relaunch after a crash cannot reopen your project; the doctor says how to change it.
- **Skills:** binding limits for UI (`uefn-ui-widgets`), the Verse build compiles only the open project (`uefn-verse-build`), and agents tag what they create with `kit:<run id>` (`uefn-level-devices`).
- **Repo:** a `docs/adr` folder with the decisions, a secret scan (gitleaks) on every push, and `KIT-VERSION.tmp` is no longer tracked.

## v1.107.5 — Easier to find on Google

- **SEO for the manual:** every page has a search title, a description, a canonical link, social-card tags and structured data (JSON-LD), plus a `sitemap.xml`. Titles and descriptions live in `docs/manual/manual.json` under `seo`.
- **README:** it now opens with the main search terms (UEFN, Verse, UEFN MCP, Claude Code, AI agents) and badges: licence, release, tests, stars, the keywords and live numbers (MCP tools mapped, proven recipes, agents, skills).
- **Numbers that stay true:** the badges read `docs/kit-stats.json`, written by `tool/build_kit_stats.py`; a test fails if the file is out of date.

## v1.107.4 — Skills point to the proven recipes

- **Skills check:** every skill and agent that calls UEFN MCP tools now sends the AI to the proven recipes (14 of 35 skills and 11 of 22 agents; the others do not use MCP tools). Two were missing: `verse-ui-kit` now points to `uefn-ui-widgets` and the recipes, and `planner-docs` reads the level devices through the level-devices recipes instead of an old tool name.

## v1.107.3 — A manual with every tool, and a status for known traps

- **New manual chapter "Tool reference":** all 388 UEFN MCP tools by toolset, with the parameters of their tested recipe, whether they write, and how far the recipe is proven. It is generated by `tool/build_tool_reference.py`, so it stays in step with the recipes. Epic's own descriptions are not in it: they stay on your computer, `mcp_map.py --find` shows them.
- **A recipe can be `avoid`:** a known trap (the static-mesh `get_lod_count` crashes the editor) is documented, never replayed and left out of the totals, like the multi-step notes.
- **Recipes:** final notes for the three that still fail (ApplyStackIssueFix, GetClientLogEntries, SelectAssets). State: 387 proven, 4 unverified, 3 failed.

## v1.107.2 — Recipes proven by a validation battery

- **Recipes for 381 of the 388 UEFN MCP tools, 387 recipes `proven`** (377 tools have a proven recipe; before, 225 tools had a recipe). Every tool that answered in the lab now has one, and every recipe was replayed with its own arguments, area by area. 11 entries are multi-step notes and 4 stay `unverified` with the reason written down: SelectAssets (it times out), GetClientLogEntries (needs a live client), ApplyStackIssueFix (the first call errors while a compile runs) and `get_lod_count` on a static mesh (it crashes the editor). Of the 29 tools that never worked, 22 now work: most had been called with wrong arguments or were locked by our own test lab, not by UEFN. 5 do not work in this project (AddViewModelProperty, AddUIComponent, MoveUIComponent, RemoveUIComponent, diff) and 2 (create_level, load_level) are left untested on purpose.
- **Honest numbers on the UEFN MCP card.** The first line used to say "The kit uses 359 of 388 tools", which only meant "answered at least once in the lab". It now says "Recipes cover X of 388 tools (Y proven)" and keeps the answered count as a small line. Multi-step notes are counted apart, "failed" no longer counts a recipe that failed once and worked later, and the recipes line says "proven by use (real work or a replay)".
- **A replay counts as proof.** While an agent runs a validation replay it creates `Claude/logs/replay.on`; calls made meanwhile (by the hook and by `mcp_lab.py` scripts) are noted as `src: "replay"` and count like real work. Exploration rows of the coverage battery still never count. New: `recipes_status.py --todo [--area NAME]` (what is left to replay) and `--gap` (tools that answered but have no recipe yet, with the last good call).
- **Lab guard: one folder on disk is allowed.** `import_file` and `export_png` may now use a file inside `Claude/logs/_explore/` of the project (the real path is checked: no `..`, no symlink out); every other tool still refuses paths on the disk. This lets the lab test the import tools without opening the guard anywhere else.
- **Fix: long arguments.** A call with a very long argument (a whole script in `execute_tool_script`) was cut at 400 characters, which broke the JSON, so the recipe could never become `proven`. Long strings are now shortened and the JSON stays valid.
- **Fix: recipes.** `execute_tool_script#verse_edit_build` (run() must return a dict), `delete_folder` (the folder must exist first), a short toolset name now matches the full class name, and several notes.

## v1.107.1 — The UEFN MCP card shows the real numbers

- **Fix: the UEFN MCP card showed "The kit uses 18 of 388 tools".** In v1.107.0 the count read only the short list in `reference/` and ignored `hooks/mcp-known-tools.json` (the 388-tool file with what the lab found for each tool). It now adds every tool the lab marked `ok` or `recipe`, and matches full names (`Toolset/Tool`) and short ones. With the shipped data the card shows 359 of 388 (92.5%).

## v1.107.0 — The MCP, mapped, learned and proven

- **Console as a small solar system.** The chief of staff is the sun; five planets (BUILD, CONTROL, RELEASE, MEMORY, UEFN MCP) orbit it, and every other agent is a moon turning the other way, more slowly. The five MCP sub-agents are on the map (22 agents). Coloured arcs show the tokens of each group, a click opens a detail card, agents can be pinned, a `⏳` label marks a group with agents waiting, numbers show the chain of working agents, and a red line says when something needs you. Six round switches under the map show or hide each of these and are remembered.
- **14 UEFN MCP skills and 5 MCP sub-agents** (`mcp-build`, `mcp-session`, `mcp-level`, `mcp-ui-assets`, `mcp-material-vfx`) ship in the kit, with references for ten areas (`mcp-tool-contracts/references/areas/`: 246 recipes, coverage 357 of 388 tools). The `coder` can hand UEFN work to them (one editor writer at a time).
- **Recipes know how sure they are:** `unverified`, `tool-ok` (the tool answered once in the lab) or `proven` (the same kind of call worked in real work). A small hook (`mcp_work_log.py`, on success and on failure) notes real calls locally; `recipes_status.py --report` shows the count and the Skills page shows it as four rings, a bar per area and a weekly line.
- **Share what you proved:** in the Skills tab, "Contribute to the community" now has a line for the UEFN MCP recipes you proved. It sends counts only, never arguments, paths or names, and you finish on GitHub yourself.
- **UEFN restart after a crash (opt-in):** `uefn_session.py` tells what the editor is doing (`status`) and starts it again only after a crash (`recover`: no editor running, last run a crash, your opt-in, max 2 tries in 30 minutes). A running editor is never closed or killed. Tested live on a throw-away project.
- **Known tools:** `mcp-known-tools.json` (388 tools: what the lab found for each) and `mcp_map.py --find` shows "ask the owner first" where it applies. `mcp_lessons.py` lists recurring MCP errors that the skills do not mention yet.
- **Lab guard, second pass:** catalogue mounts accepted only as the source of create/duplicate/place, `extra-root` for imported models in the same throw-away project, and a token rule for long jobs.
- **Fix:** a battery that could not reach the MCP is no longer counted as finished.
- Manual: new sections in "The MCP engine" (how sure is a recipe, when UEFN closes or crashes, known traps of UEFN 42.20), new screenshots of the Console and the UEFN MCP card.

## v1.106.0 — Epic's Verse UI Kit

- **New skill `verse-ui-kit`:** how to build and wire in-game screens with or without Epic's free Verse UI Kit (the kit is a teacher and a shortcut, never a requirement; a section covers building UI without it) (focus, gamepad and keyboard, Back, shared click events, public modules, the order compile, save, build), written in this kit's own words, with code snippets marked "not compiled" until `/verse-check` builds them. The coder and `game-ui-designer` point to it.
- **`/ui-kit-check`:** tells whether the kit is installed (optional: it never blocks a task), whether its separate `AGENTS.md` download is in place, and whether Epic changed it since the version this kit was written against. Only a SHA-256 fingerprint is compared; Epic's guide is never copied into the kit because the Fab licence does not allow handing it on. It is kept once on your computer for all projects (`~/.claude/skills/verse-ui-kit/references/epic/`, stored with `--store`), not in each project. `--diff` and `--accept` support the review after an Epic update; nothing changes without your yes.
- **The kit maps UEFN's MCP by itself, and tests it.** At every session start it checks whether the MCP answers; if so, and the last full map is older than six hours, it maps every toolset and tool in the background (`mcp_map.py`, no AI tokens, silent when UEFN is closed) and calls the safe tools to see that they work: read-only, no arguments, never a writer. First real map on UEFN 42.40: 28 toolsets, 388 tools, of which the kit documented 6. One private catalog for all projects (it holds Epic's descriptions, so it stays on your computer), with a read or write guess and a tested mark per tool, a NEWS file (added, removed, changed, **stopped working**), a history and a change log. The next session start tells the agent, who tells you in two lines and proposes ideas; nothing changes without your yes. It works whether or not a kit release is published.
- **Console, Skills page: new "UEFN MCP" section** with the share of tools the kit uses (e.g. 6 of 388), read and write counts, the test results, tools that stopped working and the latest news. Served by both console servers (`/uefn-mcp-map`).
- **Agents use the whole MCP:** the coder, QA and bootstrap agents search the map (`mcp_map.py --find <words>`, pre-approved) before working through UEFN and never guess a tool name; `mcp-tool-contracts` has a new first contract for it. `/mcp-snapshot` runs the same mapping on demand; `/kit-doctor` notes a missing or month-old map. New manual chapter "The MCP engine". The mapper is tested against a fake MCP server (tool lists, event-stream replies, odd replies, changes, tools that stop working).
- **Rule: when a file cannot be deleted, it is parked in `_to_delete`.** New block `no-delete` in every project's `CLAUDE.md` (and rule 15 in the base rules): if a delete is refused or not possible, agents move the file to `_to_delete/<date-time>/` and tell you; you empty the folder. The kit follows it too, also in updates: removing a skill file from the console and `sync-skills.ps1` replacing a skill try to delete first and park the old copy in `_to_delete` only if the system refuses. Scratch files (locks, temp, markers) are simply removed. `_to_delete/` is already ignored by git.
- **Batching proven:** the MCP's `ProgrammaticToolset/execute_tool_script` ran four read calls in a single request on a real project. `read-tools-proven.md` now documents the script shape, the widget and actor read chains, and that object references are plain path strings.
- **Console, Docs page: it now follows the files.** The page kept the first copy of STATUS, ROADMAP and BUGS for as long as the tab stayed open, so documents written meanwhile never appeared. It now checks the six documents every 5 seconds and redraws only when one changed.
- **Console, Flow page: a U-shaped board.** The belt and the truck are gone. The 12 stations run along a U (intake down the left, build and gate along the bottom, ship up the right); each has a card (agent, state, tokens, time, last verdict, two bars) and the agent's own icon on the track, so you see who is where. Zone progress bars on top, the Control Tower with the gate outcomes in the middle and a Pipeline pulse under it. Tokens come from `/agent-costs`; steps with no agent show no invented numbers.
- **Exploration lab for the MCP (`Claude/hooks/mcp_lab.py`):** an agent can try any MCP tool through it; every call is logged (`Claude/logs/explore-ledger.jsonl`) and the safety rules are enforced by the code. Normal mode (a real project): writes only inside `KitTest`, level and session tools behind switches, no delete. **Laboratory mode** (`LAB_AGGRESSIVE=1`, for a disposable project): it starts only if `Claude/LAB-PROJECT.txt` exists and the open level lives under `LAB_ROOT`; then delete, level writes, sessions, Verse edits and Python are allowed inside the project, while quitting the editor and any disk path outside the project are always refused. The reusable mission (phases, one knowledge file per area, recipes) is `mcp-tool-contracts/references/exploration-mission.md`. Roadmap: the findings become area knowledge files, a coverage battery (about 20% of the tools per run) and one skill per area, with the coder as orchestrator of area sub-agents (the diamond).
- **Long batteries for the MCP (`mcp_cover.py`, `mcp_queue.py`):** schema-driven, no hand-written test per tool. The coverage suite builds a dependency graph from the object kinds in the tools' own schemas, makes its fixtures by calling the producers (a tool that returns a WidgetBlueprint), then calls every tool (several passes; destructive tools last; listing tools scoped so they cannot return the whole engine) and writes `Claude/docs/mcp/coverage.json` and `COVERAGE.md` (with `--fraction 0.2` each run takes the 20% least covered). Other suites: `soak` (repeat create-edit-compile-save-delete and watch the latency drift), `session` (game-session loop with timings, always stopped) and `mapcheck`. `mcp_queue.py` waits in a second terminal (no tokens) until the exploration is finished (`lab-done.flag`, or a quiet ledger) and then runs the four suites one after the other, resumable, with `QUEUE-REPORT.md`. Meant for a disposable project (`LAB_AGGRESSIVE=1`).
- **Deep test of the MCP (`mcp_map.py --deep`):** calls every read-only tool once with harmless made-up values (never writers, captures, builds or Python), in separate files (`deep-tests.json`, `DEEP-TESTS.md`), and checks that the map files stay byte-identical. Answers over 1 MB are skipped next time. First real run on UEFN 42.40: 169 tools tried, 39 answered, 130 alive but asking for a real object, none silent. New reference `mcp-tool-contracts/references/read-tools-proven.md`.
- Found in the first real run and fixed: `ui_kit_check` accepts the project folder as a plain argument; `toolset_diff` warns when tool names have no `Toolset/` prefix (names like `diff` collide between toolsets); `mcp-tool-contracts` now lists the UI, Verse, session, entity and asset toolsets seen on UEFN 42.40 (28 toolsets, 388 tools).
- Both commands are delivered to existing projects by `/kit-update`; `ui_kit_check --check` and `--diff` are pre-approved in new projects (never `--accept`). Manual and skill catalog updated; tests for both scripts. The skill entry-point token baseline was raised on purpose (one new skill).

## v1.105.0 — Fewer questions, easier handovers

- **Safe commands are pre-approved in new projects:** the kit's read-only checks and `git status`, `git diff`, `git log` no longer ask every time. Anything that writes, deletes or publishes still asks. Existing projects keep their own permissions untouched (the manual says how to copy the list).
- **`/handoff`:** writes `Claude/docs/HANDOFF.md` so a fresh session or another model can continue from a page instead of the whole conversation.
- **Manual:** new sections "Long sessions and handing over" (handoff, `/compact` with instructions, what `/rewind` does and does not undo, unattended retry settings) and "Commands that run without asking". The Claude Code commands and settings quoted there were checked against the official documentation.
- **Fix:** `/verse-check` and `/text-scan` (added in 1.102.0 and 1.103.0) are now delivered to existing projects by `/kit-update`; before, only new projects got them.

## v1.104.0 — Tokens per agent

- **A new table on the Console page**, "Tokens per agent (last 30 days)": for each agent, runs, calls, input, output, cache read, cache write, total and model. It comes from the transcripts Claude Code keeps for each helper agent; each model answer is counted once (the same answer is written on several lines with growing counts).
- **Honest by design:** if the transcripts are not on this computer the table says "not available", never zero. Counts only, no prices. The main session stays in the tokens box above.
- Read once and cached in `Claude/logs/agent-costs-cache.json`; later openings only read new runs. Works in both console servers.

## v1.103.0 — Lessons from build errors, publication text scan

- **Build errors are remembered.** Every build that ends with errors is noted in `Claude/logs/verse-errors.jsonl` (error codes and a short excerpt, no paths). `verse_check.py --recurring` lists the errors seen in two or more builds; the coder then proposes a Verse lesson and writes it only after your yes.
- **`/text-scan`:** offline check of publication texts (`Claude/docs/publish/` or the files you name) for emoji, fake-bold letters, arrows, box symbols and invisible characters. Reports line and column, never edits. The title and description skill and the update writer run it before handing over a final text.
- Tests for both (recurring errors, paths stripped, normal typography left alone). The privacy scan now skips the git-ignored `_spike` folder.

## v1.102.0 — Verse build check

- **`/verse-check`:** asks the open UEFN to build the whole Verse project (through UEFN's own Verse Workflow Server, the channel Visual Studio Code uses) and reports **clean**, **errors** (with the build log) or **not analyzed** when UEFN is not reachable. Never a guess: an odd or missing answer is "not analyzed", not "clean".
- The **coder** confirms the build with it before calling a task Done; the **release gate** runs it before a verdict (errors block, not analyzed caps the verdict at "ready with reservations").
- New manual section "Checking that the code builds". Tests use a fake server for the three states.

## v1.101.1 — Code scanning fix, screenshots for every page

- **The console chapter now has a screenshot for every page** (Console, Stats, Docs, Flow, Skills, What's new), all with demo data and the new logo.
- **README images refreshed** (console with the live mini-flow rail, header, Docs and Flow pages, all with demo data and the logo) and a short "What's new" for the manual.
- **Fix:** the console's `/manual/` route now takes the file name from the folder listing instead of from the request, which closes the two CodeQL alerts "Uncontrolled data used in path expression" (same remedy as for the skills engine). Nothing changes for you; the route already refused anything but plain chapter names.

## v1.101.0 — The manual, complete

- **Thirteen chapters.** New: Full installation (plugins, upgrades, updating a project safely), A working day (calling agents, plan-first, base rules, what runs after a playtest), Skills catalog, Questions and answers, Glossary, About. The long setup guide's useful content now lives here, kept up to date.
- **Screenshots** of the Console, Flow and Skills pages (demo data) in the manual. The console servers now also serve the manual's `.png` files.
- **Public copy on GitHub Pages:** `https://mimmo-the-root.github.io/UEFN-dream-bot-team/`. A workflow publishes it after every change to the manual (one-time: Settings, Pages, Source: GitHub Actions).
- **`SETUP-GUIDE.md` is now a short pointer** to the manual; the old long guide stays in the history at v1.100.0. README and issue links point to the manual.
- **The project logo** is on top of the README and the manual home, and every console page shows its emblem next to the title and as the browser tab icon (embedded in the page, works offline).
- Tests keep the manual honest: every agent, every user-level skill and every console page must be described in it, every image and link must exist, and screenshots stay under 400 KB.

## v1.100.0 — The manual, part 1

- **A manual that opens in your browser.** Seven chapters (what the kit is, quick start, your team and their models, the console page by page, skills and lessons, community, troubleshooting) at `http://127.0.0.1:8765/manual/` while the console server runs. Plain HTML, no scripts, works offline, light and dark. It is copied into every project by `/kit-update`.
- **"Help for this page" on every console page** opens the matching chapter.
- **Every console page now has a footer** with the GitHub repo, the MIT license note (free to use, copy and change, no warranty), the author's X profile and the Epic trademark notice.
- The manual is built from `docs/manual/*.md` by `tool/build_manual.py`; `publish.cmd` rebuilds it and a new test fails if the shipped copy is out of date.
- More chapters, screenshots and a public copy on GitHub Pages follow in 1.101.0.

## v1.99.2 — Cleaner console, honest reports

- **Agent reports say what was checked.** `qa-regression`, `release-gate` and `codebase-auditor` now end every report with `Verified:` and `NOT verified:`, so a PASS is never mistaken for "it builds". The reviewers and the helper agents keep their reports under 250 words, because those reports land in the most expensive context.
- **The agent ring no longer overlaps.** Twenty names now sit on an ellipse that fills the stage instead of a circle, the Obsidian Vault sits a little closer to the hub, cards shrink on a narrow window, and a name cut short shows in full on hover. Measured with an automatic overlap check: from 30 overlapping pairs at the worst moment to 3.
- **The long help text under the ring is folded** in "How to read this page"; only the line about starting the local server stays visible.
- **Stats shows one clear message** when Epic has no numbers yet, instead of nine identical empty tiles. The chart caption is in English (two Italian words slipped in).
- **Fix: the "What's new" tab showed a stray backslash** (`What\'s new`) on the other five pages.
- **What's new** now says why the map shows as "not published" (no island code, Epic has no data, or Epic not reachable).

## v1.99.1 — Test fixes for Windows and code scanning

- **Tests no longer depend on the console or the file system.** Two tests failed on Windows (a console that cannot print an invisible character, and file names that ignore upper and lower case). The kit itself was not affected.
- **What's new page stayed empty after `/kit-update`.** The update did not copy the release summary and the list of revoked community lessons into the projects. Both are now part of the update.
- **Code scanning alert closed.** A test checked a link with a pattern that CodeQL mistook for URL validation; the check is now a precise match.

## v1.99.0 — The community pack: share your lessons, see what changed

- **Share lessons with the community (voluntary, off by default).** A switch on the Skills page (section Community) and a **Contribute** button on each lesson you approved. You see the exact JSON, then GitHub opens a pull request from your own account. Only lessons, never map names, code, devices or blueprints.
- **Only lessons from a published map.** The kit checks that the project has an island code and that Epic has public data for it; a lesson from an unpublished map stays on your computer, and the page says so.
- **Intake without losing anything.** Lessons move through screened, hypothesis, confirmed and archived; nothing is deleted. A single lesson is a "to verify" hypothesis, two creators (or the maintainer) confirm it. A curator agent proposes the promotion; the maintainer validates before any release.
- **Defence against malicious lessons.** Fixed format, the id must be the content hash, screening of links, commands, hidden characters and phrases aimed at an assistant, an isolated classifier, a strict plain-English character filter (no look-alike or hidden characters), the statement regenerated by the curator, PRs may only add the author's lesson file (renames and deletions count, no symbolic links) and cannot edit the checks that judge them, revocation removes a lesson from everyone's skills and it never ships again. An independent security review was run and its findings fixed.
- **Reputation.** Lessons carry the creator's GitHub handle; the score grows with confirmed lessons and drops with revoked ones.
- **New page: What's new** (tab next to Skills). The last release, skills new or improved by the community, top contributors, the lessons that helped most, thanks, your own part, and a "Submit an issue" link to GitHub (with a form for a wrong community lesson).
- **A map type is one type however it is spelled.** `pillar` and `pillars` showed up as two types of the same map. New lessons, blueprints and the genre/type proposal now take the spelling that already exists in the genre (same word, singular or plural), and the session start merges the existing duplicates by itself (patterns, their evidence, waiting lessons, blueprints, the project's own type); by hand: `skills_lib.py variants-merge [genre] --project .`.
- **SETUP-GUIDE brought up to date.** New section 3f (the kit learns from your maps), `/kit-update`, `/kit-update --fetch` and `/kit-doctor`, the five console pages, how the console server follows the kit and the session. README updated too.

## v1.98.8 — Learning continues in long sessions, security fixes, the console tab opens once

- **Learning continues in a session that stays open for hours.** The learning was only requested at the session start, so a map developed for a whole day kept an out-of-date blueprint until the next launch. New `Stop` hook (`learn-nudge`, no AI tokens when nothing changed): at the end of an answer it checks whether the Verse code, the documents or the device map changed since the kit last learned them and, at most every 30 minutes and twice for the same state, asks Claude to continue with the learning (only what changed is read), then back to your work. It is silent while the genre/type is not confirmed and in the headless post-playtest runs. Existing projects get the hook with the next kit update.
- **Security: 15 CodeQL path-injection alerts.** They all started at the console's new genre-confirmation button (`/genre-confirm`): the genre sent by the browser reached the file helpers of `skills_lib.py`. `confirm_genre` and `propose_genre` now take the genre from the official list itself, not from the received string (same rule as `resolve_genre`), and refuse when the official list is missing.
- **The console tab opens once, not at every launch.** The session start opens the browser only when it had to (re)start the console server; a server that is already right keeps the tab you have.

## v1.98.7 — Skills page rebuilt, genre and map type confirmed by you, IP variants, blueprint that follows your development

- **The console shows all 17 agents.** It listed 15: `coder-prep` and `second-brain-scout` appeared only as temporary "clone" nodes. Now both are in the roster, hanging off the agent that dispatches them; `coder-prep` counts as coder work in the mini-flow and on the Flow page.
- **Releases in delivery order.** The Docs page lists releases as P0-R1, P1-R1, P1-R2... (not in the order of the table rows), with Later and tasks without release last.
- **IP variants as map types.** When the documents say a map is the same base game dressed for an IP, the kit proposes the IP as the map type (the shared base is type `base`) and the owner confirms it on the console. An IP blueprint records only what differs from the base.

- **Every analysed map now leaves something usable in the skill.** After the blueprint the kit asks, once per start (max two tries), to read the items it left in `unknown` through the MCP, and, in the same start, once to queue 3-5 general lessons from the blueprint for you to approve (they no longer wait for the unknown items). The console shows `written; unknown items still being read` / `general lessons still to propose` on the blueprint step.
- **Confirming on the console saves everything by itself.** The blueprint written while the genre was pending (`profile.json`) goes into the genre skill and the lessons the coder tried to queue (held in `lessons-held.json`) are queued, with no message to Claude and no wait for the next session.
- **The console server is found by its command line, not by the port owner.** The server is a PowerShell HttpListener, so Windows lists PID 4 (System) as the owner of port 8765 and the old rule never found it: a server of the previous project stayed alive and `exit` did not stop it. Session start and `SessionEnd` now stop the `agent-console-server` process by its command line.
- **One project = one blueprint.** Saving the blueprint under another map name no longer creates a second one (the project marker decides); `skills_lib.py profile-drop <genre> "Map N"` removes a duplicate and renumbers the rest.
- **The SKILLS tab blinks on every console page when lessons, a pack update or a genre/type confirmation wait for you.**
- **Approve all** in the lessons of this map's genre (contradictions stay for individual review).
- **Console server answers the new endpoints in both implementations** (PowerShell, the one started automatically, and Python); `/whoami` reports the kit version and the session start replaces an older server.
- **Skills page rebuilt (kit overview + this map).** Top: the whole kit (waiting lessons, maps/genres/types, pattern confidence, coder use, skills per genre, packs, privacy). Below: the genre of THIS map: genre and map type to confirm, learning steps (code, documents, devices, island configuration, blueprint), the map blueprint, what it learned (log) and the genre's patterns. The previous Skills content (edit wording, approve all, packs) stays in a collapsed "Classic view"; the Docs page is unchanged. New endpoints `/learning-data` and `/genre-confirm`.
- **The kit asks you to confirm the genre and the map type before touching the skills.** `propose-genre` only writes a proposal in the project; lessons and the blueprint are refused (`GENRE NOT CONFIRMED`) until you confirm or correct it on the console. The map type is a free name (pillars, red-vs-blue...) with the known types of the genre offered, and `+ New type`.
- **The console restarts after an update.** The server started by the session is the PowerShell one: it now answers `/learning-data` and `/genre-confirm` and reports its kit version, and the session start replaces a server started from an older kit version (every decision is logged in `Claude\logs\console-start.log`).
- **The blueprint follows your development.** It is marked out of date when code, documents or devices change after it was written, and rewritten at the next session.
- **Maps with 1-5 Verse files learn too:** the device-only learning of 1.97.1 only started with zero Verse files, so a map with a few template files (for example 4 in `custom_verse`) got no learning at all. Now any project with a genre and no code map (5 Verse files or fewer) announces learning: the few Verse files are read completely, then the documents and the devices of the level; `PROGRESS.md` shows what is missing.

- **Learning goes first:** a coder that was asked only for the project status answered it and offered to start the learning "if you want". The `LEARN`/`GENRE` session-start notes now say MANDATORY (before answering the first message, never optional) and the same rule is a managed CLAUDE.md block (`learning-first`) that every project receives at the next session start.

- **A published map is past the MVP:** when the project has an island code the map is already live, so planner-docs and project-bootstrap mark Phase 0 as Done (published), make Phase 1 the Active phase with releases `P1-R1`..., and no longer ask the owner for a written decision to leave Phase 0. An old ROADMAP.md with PH-0 still Active is corrected at the next planning pass.

- **The genre skill learns how a map is made (map blueprint):** until now it only collected technical lessons. New `skills_lib.py profile`: after the code, documents and devices the learning pass writes the blueprint of the map (concept, layout with counts, game loop, devices with role/settings/wiring, rules with the numbers observed, scoring, build order, what is still unknown). The starter (`references/starter.md`) opens with a generated "Map anatomy" section aggregated over the owner's maps (a value seen in several maps is a default, in one map an example), and the genre `SKILL.md` tells the coder to read it first when asked to plan or build such a map. Maps already analysed get their blueprint at the next session start (`PROGRESS.md`: "map blueprint NOT written yet").

- **Genre is chosen by the structure of the game, and can be corrected:** the `GENRE` note now fires whenever the project has content and no genre (pillars map: nothing was learned), is mandatory before the first answer, and tells the coder to pick one slug of Epic's list by the game's structure (players, round length, lobby) with the new `hint` of each genre in `fortnite-genres-official.json`: a last-one-standing arena with short rounds is Party & Mini Games, not Battle Royale. A new mechanic is learned inside its genre, never as a new genre. New `skills_lib.py retarget <wrong> <right>` moves the lessons still waiting for approval to the right genre when the owner corrects it.

- **No code, no code findings:** project-bootstrap and codebase-auditor no longer report logger, header, DemoDisplay, state-machine or other Verse findings on a map without Verse files (not even as "minor / not applicable"): a finding must point to something that exists. A device-only map is audited on devices, settings, wiring, performance and Outliner.

- **Old maps get `EnableVerseAssetReflection` automatically:** at every session start (`kit_sync.py`, also reached by the section 14 self-update) the project's `.uplugin` is checked; when `"EnableVerseAssetReflection": true` is missing it is added (text insertion, BOM and line endings kept, backup `<name>.uplugin.bak-YYYYMMDD`), because without it UEFN never generates the assets digest and the Verse build fails. A value you set to `false` is left alone and reported.

## v1.97.1 — Every genre gets the 8 starter sections; the console stops with the session

A genre without its own `references/starter-sections.json` (for example gun-game) used to get no sections, so patterns could not be assigned and no starter was generated. Now `skills_lib.py` falls back to 8 default sections in neutral wording (core loop, architecture, devices, progression, strategies around death/defeat, persistence, performance, launch checklist) and generates `references/starter.md` for every genre; a genre can still override them with its own file (roguelike does).

- **Console stops with the session:** new `SessionEnd` hook (`agent-console-shutdown.ps1`): when you type `exit` (or `/exit`, logout) the Agent Console server of this project is stopped. It does not stop on `/clear` or resume, and it leaves alone a console serving another project. Existing projects receive the hook automatically at the next session start (restart once).

- **Device-only maps learn too:** a map with no Verse files (native device wiring only) used to get no learning at all, because the whole pass hung on the Verse map. Now, with a genre set, the session start announces learning from the project documents and from the devices of the level (`DEVICES.md` with `WIRING-READ:`/`SETTINGS-READ:`), skipping the code steps; `PROGRESS.md` says "no Verse files" and what is missing.

- **Island configuration is read and deduced, not asked:** new contract in `mcp-tool-contracts`: the learning/bootstrap pass reads the Island/Experience Settings, team settings and Player Spawner groups, and deduces max players, teams, rounds, time limit and the game shape (a cluster of spawners flagged island-start, hidden and unwired is a pre-lobby; capacity of game-start pads and vehicles versus max players is reported as a finding). Results go to `DEVICES.md` (`## Island configuration`, third flag `ISLAND-CONFIG-READ:`), nothing of this goes to the owner's "to confirm" list, and every deduction rule that worked is queued as a genre pattern for the next map.

## v1.97.0 — Skills learn from code, documents and devices; starter fed by the owner's maps

Includes the unreleased 1.96.1 below. The learning pass now reads the COMPLETE Verse sources (first pass: every file; afterwards only changed files) in batches of 60k characters, each ending with a receipt token that `learned`/`docsdone` require, so a cut-off read can never be marked as done; devices are read from the level through the MCP (an old device map is only the baseline). New: the learning step also reads the project documentation (after the code) and reports where documents disagree with the code; `/learn-map devices` forces a device pass; UTF-8 output on Windows; the MCP mode is decided through `mcp__unreal-mcp__call_tool`.

- **Reverse engineering of the documents:** the learning pass writes verified corrections (stale numbers, moved or missing files, drafts that are implemented, missing systems) to `Claude/docs/map/doc-patches.json`; `verse_map.py docpatch list` checks that every anchor text exists exactly once, `docpatch apply` (ids or `--all`) applies them with exact matching and a backup in `Claude/logs/doc-backup/`, only when the owner says so. Systems without a document get a `DESIGN-<system>.md` from facts in the code. The coder never interviews the owner: what code, documents and level do not show is reported as unknown. `skills_lib.py similar` lists near-duplicate patterns; the starter keeps the original capitalisation; documents are re-read once with the new design-extraction instruction.

- **Learning no longer depends on Epic's API:** with no genre in `Claude/docs/.genre` (Epic answers 403 for unpublished maps, or no island code), the session start tells the coder to infer the genre from the code map and documents (closest slug of the official list), initialise the genre skill and start learning, without asking. The console's 403 message now says it is only missing public data and sends a User-Agent.
- **Documents can no longer be skipped:** `docsdone` refuses a batch unless every document has a recorded decision: corrections applied (`docpatch apply`) or a `reviewed` note saying it was compared with the code and is accurate. The `docs` output also lists status words (draft, planned, no code, to do, bozza...) to verify against the code, so a design marked as draft that is already implemented gets corrected.
- **No approval round for documents, and simple resume:** validated document corrections are applied at once (exact text, backup in `Claude/logs/doc-backup/`, `docpatch revert STAMP` undoes). There is no token accounting: a batch is marked only by `learned`/`docsdone`/`docpatch`, so if a session stops (out of tokens, closed window) the unmarked work is simply read again at the next session start. `verse_map.py status` and the generated `Claude/docs/map/PROGRESS.md` list what is learned and what is missing (code files, documents, document corrections, devices: wiring and settings read or not).

## v1.96.1 — Fix: the kit update message was silently dropped

- **Fix:** when a project had a Verse map (since 1.94.0), the session-start refresh printed a line ("map built: ...") before the hook's JSON. Claude Code then ignores the whole message, so the kit updated its files (and the console) but never told you to restart, and the rest stayed old until a restart. `kit_sync.py` now captures everything helpers print and emits exactly one JSON object.
- **Hook output:** besides the UI message, the model is told in `additionalContext` to say the update in its first reply, and `Claude/logs/kit-sync.log` records every run (the UI may not show a hook's systemMessage). A `LEARN` line now says "start now, do not ask"; `/learn-map` first decides the MCP mode (`live`/`offline`, must be stated in the report).
- **Starter fed by the owner's maps:** a pattern has a `section` (the genre's starter sections, `references/starter-sections.json`; roguelike: run-loop, architecture, devices, progression, death-strategies, persistence, performance, launch-checklist). `propose --section`, `skills_lib.py section` for existing patterns, and every render regenerates `references/starter.md` from the approved patterns: proven/confirmed/hypothesis/contested per section, with the open questions. It evolves with new maps (tiers) and with `/learn-map`. Section is exported with the shareable pack, so a new user without experience gets the community's starter.
- `kit_sync` rebuilds the generated parts of each genre's SKILL.md/starter.md from the learned pack at session start: `update-my-profile` copies the kit's empty versions over them.
- Test: `test_verse_map.py` runs the hook as Claude Code does and parses its output as JSON while a map exists.

## v1.96.0 — Learning without truncation, MCP detection, roguelike starter skeleton (plan P1-R1)

Includes the unreleased 1.95.0 and 1.95.1 entries below.

- **Fix:** `verse_map.py learn` now prints the next batch of unread cards complete (default 12, signal-only view: roles, links, subscriptions, per-player state, pitfall comments; `--full` for whole cards) and `learned` marks only the cards of the last batch (`--all` for every card). Before, a long output could be cut and every card was still marked as learned.
- `/learn-map` and planner-docs step 4b loop batch by batch until nothing is left, and explicitly handle the devices in the level.
- **mcp-tool-contracts:** new contract "Detecting MCP mode" (`live` or `offline`): in `offline` the report names the devices and wiring not inspected; nothing is skipped silently or guessed.
- **Roguelike:** `references/starter.md`, a structure-only skeleton for a new project (run loop, architecture, devices, progression, strategies around death and progress, persistence, performance, launch checklist). It contains no pre-written rules; strategies are learned as patterns.

## v1.95.1 — `/learn-map`: force the learning step

- **New:** `/learn-map` runs the learning step now (planner-docs step 4b): reads the cards not learned yet (the whole map the first time, afterwards only changed files), queues skill proposals for approval on the Skills page, then marks them learned. Delivered to projects by `kit_sync`.

## v1.95.0 — Skills learn from the whole map, every session (plan P1-R1)

- **New:** `verse_map.py learn` / `learned` (zero tokens): list the map cards the learning step has not read yet, the whole map the first time and afterwards only the cards of files that changed since the last learning, so a small update to an old map costs a few cards. State in `Claude/docs/map/learned.json`.
- **planner-docs** step 4b: every session, reads only those cards (plus device facts through the UEFN MCP, read-only, on the first full pass, like `template-reader` does for an Epic template), reuses existing pattern wording and queues observations with `skills_lib.py propose`. No minimum count: everything is queued at once, you approve it on the Skills page as before, and maturity (hypothesis, confirmed, proven, contested) evolves by itself from how many of your maps back a pattern.
- **Session start (`kit_sync`)**: an old project map is refreshed (also regenerated when the kit's map format changed); a project with more than 5 Verse files and no map gets one built automatically (script, no AI tokens). If a genre is set and cards are not learned yet, the session gets a one-line `LEARN:` instruction, so learning no longer depends only on a task being closed: what changed last session is learned at the start of the next one.
- **Restart after a kit update**: the session that applies an update leaves a marker (`Claude/logs/.post-update`) and does not announce learning yet, because its agents are still the old ones. The first session after the restart does a one-time post-update check: confirms the kit version, the map state and how many cards are waiting to be learned, then removes the marker.
- Test: `test_verse_map.py` covers first pass, incremental pass and the changed-card list.

## v1.94.0 — Verse map: no more re-studying the project (plan P1-R1)

- **New:** `Claude/hooks/verse_map.py` and `/verse-map`: reads the project's `.verse` files (read-only, no AI tokens) and writes `Claude/docs/map/`: `INDEX.md` (one line per file, about 2k tokens), one card per file (role from its `# Summary:` header, types, `@editable` bindings, events declared, event subscriptions, calls made on bound devices, per-player state, pitfall comments, which files use it), `WIRING.md` (file coupling, subscriptions), `symbols.tsv` and `meta.json` (hash per file). `check` lists files changed since the build, `symbol NAME` finds a definition, `role FILE "TEXT"` stores a role the code does not give (kept in `roles.tsv`).
- The first build is explicit (`/verse-map`, or the coder when the project has more than about 5 Verse files); after that `kit_sync` refreshes the map at session start. Level-placed device configuration and wiring are not in the code and stay unknown until read with the UEFN MCP tools.
- **coder** reads the INDEX and only the card of the file it touches, instead of the sources.
- Pilot on a 38-file, 13.5k-line roguelike project: index about 1.7k tokens, cards about 12 times smaller than their sources; the subscription and "used by" queries matched a grep of the code.
- Test: `test_verse_map.py`.

## v1.93.0 — Second brain: history, counter-evidence, log, honest answers (plan P0-R2)

- **second-brain-librarian**, for new and updated device/mechanic articles only (old ones are not rewritten for format): (1) the replaced Verse implementation moves to a dated `## History` entry, equally valid approaches are kept as `### Variant: <name>`; (2) a `## Counter-evidence` section (what did not work, where); (3) one line per write in `wiki/log.md`, no page is ever deleted, archiving is proposed instead; (4) every query answer ends with `Read:` and `Not covered:`.
- `names.json` knows the section names (History/Cronologia, Counter-evidence/Controprove); `vault_check.py stats` reports how many articles already use the new format and whether `log.md` exists.

## v1.92.0 — Second brain: read by section, no duplicate articles

- **Cheaper queries:** `vault_check.py sections` lists the headings of the vault's `CLAUDE.md` with their size, `section "<text>"` prints only the one needed. `second-brain-librarian` now reads the vault rules by section instead of the whole file (about 6.6k tokens): a query needs about 0.3k (Workflow: Query), a compile about 2.3k. The vault's own file stays the authority and is not changed.
- **No duplicate articles:** `vault_check.py dups` finds articles sharing an alias or title, or whose names differ only by release/versione; rename-redirect stubs (tag `rinominato`/`renamed`) are ignored and counted in `stats`. The librarian searches by concept, Verse identifiers and aliases (both languages) before creating an article, and updates the existing one.
- Test: `test_vault_check.py` extended.

## v1.91.0 — Second brain: mixed-language vaults and free checks (plan P0-R2)

- **Decision:** existing vaults are NOT migrated. A vault may mix English and Italian names (pages are copied from the web in both languages). The kit writes new notes in English and resolves names through a table.
- **New:** `second-brain-query/names.json` (canonical English name -> Italian synonyms for folders, index files, frontmatter fields and section titles) and `second-brain-query/scripts/vault_check.py names|links|stats`: read-only, no AI tokens. `names` warns when an English twin of an Italian folder exists, `links` finds broken `[[wikilinks]]`, `stats` counts articles and gaps.
- **Changed:** `second-brain-librarian` uses the vault's existing names and never creates the English twin of an existing Italian folder or index.
- Test: `test_vault_check.py`.

## v1.90.0 — /kit-update --fetch and restore points (plan P0-R1)

- **New:** `/kit-update --fetch` (`Claude/hooks/kit_fetch.py`): downloads the latest GitHub release (HTTPS to api.github.com only, zip paths checked, 60 MB cap, only the kit, agents and skills folders), updates `~/.claude/kit-template`, `agents` and `skills` (never `local/` or `pack/`, never `CLAUDE.md`), copies every replaced file to `~/.claude/kit-backup/<time>/`, then syncs the project. `--check` only compares versions; `--zip FILE` uses a downloaded release.
- **New:** restore points (`Claude/hooks/safety_net.py`, `/restore-point`): copies of all `.verse` files and `Claude/docs/*.md` as `.bak` files (UEFN never compiles them) in `Claude/logs/restore-points/`, newest 5 kept. `changes` lists added/modified/deleted files since a point, `restore ID` shows what it would do and `--apply` does it (after saving the current state; added files are left, nothing is deleted). Created automatically at session start when the newest is older than 6 hours; `coder` creates one before L tasks and refactors and puts the one-line `changes --brief` in the hand-off.
- Tests: `test_kit_fetch.py`, `test_safety_net.py`.

## v1.89.0 — Checks and /kit-doctor (plan P0-R1)

- **New:** `/kit-doctor` (script `Claude/hooks/kit_doctor.py`, no AI tokens): checks kit version vs your profile, kit files, `.verse` backups under `Claude/logs`, hook settings, second brain path, docs format and `.mcp.json` in `.gitignore`; `--fix` repairs what is safe. Delivered by the sync.
- **New:** GitHub workflow `.github/workflows/tests.yml` runs `tests/run_all.py` on every push and pull request (tests, privacy scan, skill validator, token budget); tag pushes need it green.
- **New checks (`tool/`):** `privacy_scan.py` (tokens, personal paths, e-mails, files that must not be committed), `validate_skills.py` (name/description, size caps, broken references; warns on missing `last_reviewed`/`sources`), `token_budget.py` (fails if the always-loaded text grows more than 10% over `tests/token-budget.json`).
- **New templates** in `docs-template/` (on demand, not seeded): `DEPENDENCY-MAP.md`, `DESIGN-SYSTEM.md`, `TEST-PLAN.md`; rule: no refactor code before the owner approves the design.
- **Changed:** personal paths removed from the repo (second brain path in rule 11 is now the placeholder `<SECOND_BRAIN_PATH>`; your own `~/.claude/CLAUDE.md` is never overwritten), weekly sync script uses its own folder, `tool/sync-skills.ps1` derives its default paths, test fixtures use "Map One".
- Tests: `test_repo_checks.py`, `test_kit_doctor.py`.

## v1.88.2 — Audit findings get their own release

- When an audit (codebase-auditor) produces findings, planner-docs groups every finding that becomes a task into ONE dedicated release of the Active phase (`P<phase>-R<n>`, theme `Audit fixes <date>`, tasks ordered by severity), never mixed into a feature release or left in the backlog. Small findings still go to BUGS.md. Rule added to CLAUDE.md block `delivery-standard`, codebase-auditor and planner-docs.

## v1.88.1 — /kit-update command

- **New:** `/kit-update` slash command in every project: runs the kit sync right now (from the profile's kit template), without closing Claude Code, and reports the result. Delivered by the sync itself (`.claude/commands/kit-update.md`), so it appears in a project after its first update to this version.

## v1.88.0 — Delivery standard: phases, releases, backlog, bugs

- **New standard** (CLAUDE.md block `delivery-standard`, planner-docs, project-bootstrap, coder, release-gate): ROADMAP.md gets a `## Phases` table (PH-0 MVP, PH-1 Launch, PH-2 Growth; one Active; exit criteria; Phase 0 exit = a playtest with up to 3 players completes the core loop without a blocking bug and the owner decides). Releases are `P<phase>-R<n>`, planned only for the Active and the next phase; everything else is Release `Later` (the backlog). Mid-release requests go to the backlog.
- **Bugs:** every bug is recorded in BUGS.md before it is fixed, never deleted (Fixed, then Closed after verification, same id reopened if it returns). coder may append one BUGS row mechanically (narrow exception).
- Also: at most 2 tasks In progress, Definition of Done, release close = 3-line note + 3-question retrospective in STATUS.md, release-gate checks the phase exit criteria.
- **Docs templates and lint:** new ROADMAP template with Phases; `docs_lint` checks the Phases table and the P<phase>-R<n>/Later release names, only for projects that have a `## Phases` section and only for open tasks (older projects and closed tasks keep their old names; planner-docs introduces the section on its next planning pass).
- **Console (Docs page):** Phases card (status, goal, exit criteria) and Backlog card (tasks with Release Later); backlog tasks are excluded from the release bars and the open-tasks-by-release list.
- Test: `tests/test_delivery_standard.py`.

## v1.87.4 — Approve all lessons

- **New (Skills page):** "Approve all N lessons" button above the waiting lessons (shown when 2 or more). It asks once, then approves them one by one and stops at the first error. Contradictions (they mark a pattern Contested) and pack updates are never bulk-approved and stay for individual review.

## v1.87.3 — Audits feed an empty skill

- **New:** after an audit, if the genre skill or a detected technique skill has fewer than 3 patterns backed by the owner's maps (`skills_lib.py needs-feeding <slug>`), `codebase-auditor` tells the main session to call ONE `skill-reflector` with the audit's verified findings as evidence. Lessons only reach the owner's approval queue (Skills page). Reference/official patterns do not count as owner-backed.
- skill-reflector accepts audit findings as evidence; CLAUDE.md block skill-harness gains duty 3. Test: needs-feeding in `tests/test_materials_skill.py`.

## v1.87.2 — Material recipes

- **New:** recipes in the materials skill: "start from this known asset, change these parameters". One official recipe (`ui-flat-shape`, from Epic's UI material docs, parameter names to be verified in the editor). `skills_lib.py recipes materials [keyword]` lists them, `recipe-add` saves a learned one in `local/recipes.json` (hypothesis; confirmed when a second map reuses it, each map counts once; never overwritten by profile updates).
- coder step 6c: for a materials task, use the closest recipe, try the UEFN MCP tools for material assets (tool names noted in `local/mcp-notes.md`), otherwise give the owner the steps; save the recipe after the owner confirms. materials-expert hands recipes to the coder.
- Test: recipes in `tests/test_materials_skill.py`.

## v1.87.1 — materials-expert agent

- **New:** `materials-expert` agent (sonnet, read-only): inventory and audit of materials, reuse search (project, then second brain), harvest of reusable materials as lessons for the materials skill (via one batched skill-reflector call, owner approval). Listed on the console (15 agents). The technique-skills rule delegates materials work to it.

## v1.87.0 — Materials technique skill, second brain before asking

- **New:** technique skill `materials` (same engine and growth rules: reference, then confirmed/proven from the owner's maps, approval on the Skills page). Official pack of 9 reference patterns (UI material instances, reuse through parents/functions, texture cost), built from Epic's material docs in our own words. Detected automatically from asset names (`M_`, `MI_`, `MF_`, `MPC_`, a `Materials` folder) or Verse markers.
- **New:** `python Claude/hooks/skills_lib.py materials <dir>`: read-only inventory of the material assets by folder and prefix, to harvest reusable materials from the owner's maps as lessons.
- **New:** rule "second brain before asking" (CLAUDE.md block `brain-before-asking`, user rule 11, coder / project-bootstrap / template-reader): before asking the owner, look in the second brain and the skills, and propose the solution found (asking only yes or alternative); bare questions only when nothing was found.
- `update-my-profile.cmd` also copies the materials official pack. Test: `tests/test_materials_skill.py`.

## v1.86.22 — Fix: history-trim backups broke the UEFN build

- **Fix (important):** the pre-trim backup of a `.verse` file was copied with its `.verse` extension into `Claude/logs/kit-backup/`; UEFN compiles every `.verse` under `Content/`, so the copies caused duplicate-definition errors. Verse backups are now written as `<name>.verse.bak`, and kit-sync renames any stray `.verse` under `Claude/logs/` to `.verse.bak` at session start.
- Test: `tests/test_history_trim.py` checks no `.verse` is left in the backup.

## v1.86.21 — Island strip position on Docs

- **Fix:** on the Docs page the island strip appeared above the title; it now sits right under the header, like on the other pages.

## v1.86.20 — Skills page: filtered, paginated patterns

- **Changed:** the patterns list of a genre/technique skill is sorted by confidence (contested, proven, confirmed, hypothesis, reference), shows 8 per page (Prev/Next), has tier chips with counts and a search box. Default view "Relevant" hides official reference patterns nobody has tested yet (0 support, 0 against); they stay one click away under "Reference" / "All". Only the visible page is rendered.

## v1.86.19 — Bug fixing progress card

- **Changed (Docs page):** the "Open bugs" card is now "Bug fixing progress": a ring with the % of closed bugs, "N bugs in total · C closed · O open", and the severity breakdown of the open ones, laid out like the roadmap progress card.
- Removed the misleading "N open bugs of M logged" footer under the open-bugs list.

## v1.86.18 — Automatic history trimming

- **New:** `history_trim.py`, run by kit-sync at session start: old STATUS.md log entries and resolved BUGS.md sections move to `Claude/docs/archive/`; long history comment blocks in `.verse` files over 20 KB are condensed to 3 lines plus a pointer (full text archived). Code lines are never touched (checked before writing), a backup goes to `Claude/logs/kit-backup/<ts>-trim/`, and a second run changes nothing. Opt out with an empty `Claude/docs/.no-history-trim`.
- CLAUDE.md `token-discipline` block: do not read `Claude/docs/archive/` unless the task is about history.
- Test: `tests/test_history_trim.py`.

## v1.86.17 — Island info strip on every console page

- **New:** the island strip (title, code, tags, project genre badge) that only the Stats page showed now appears under the header on Console, Docs, Flow and Skills too. Local data only; hidden if unavailable.
- Docs: SETUP-GUIDE suggests the optional third-party `caveman` plugin (Phase 1 step 11).

## v1.86.16 — Token discipline

- **New:** CLAUDE.md block `token-discipline`: never read ROADMAP/STATUS/BUGS in full (Current state + newest entry only; Grep the row by id), big Verse files by symbol with offset/limit, no re-reading, no long tool output pasted back, no re-running checks on unchanged code, `/compact` suggestion.
- **Changed:** user-level rule 9 (concise style) now forbids filler openers/closers, whole-file reprints and long subagent reports (max 15 lines).

## v1.86.15 — Genre taken from Epic's ranking when the project has none

- **Fixed:** a project with an island code but no `Claude/docs/.genre` never showed the genre badge on the Stats page (and its genre skill never started). `kit_sync` now reads the genre Epic ranks the island in from the console's cached rankings, validates it against the official genre list, writes `.genre`, creates the genre skill and says so. Never overrides an existing `.genre`; `epic-template` is left alone. `project-bootstrap` uses Epic's data before asking.

## v1.86.14 — Reminder repair also recognizes a hand-fixed hook

- **Fixed:** `kit_sync`'s repair of the Stop reminder now also matches a version already quoted by hand (`echo 'Reminder: ...'`), so it is replaced by the standard one instead of being duplicated.

## v1.86.13 — Fixed the Stop reminder hook (bash syntax error)

- **Fixed:** the Stop hook reminder added in v1.86.7 had unquoted parentheses and failed in bash ("syntax error near unexpected token"). The text is now quoted and has no parentheses. `kit_sync` repairs existing projects: any old or broken `echo Reminder:` Stop hook is replaced by the fixed one and duplicates are removed.

## v1.86.12 — Update messages start with a green check

- **Changed:** kit update messages start with "✅ KIT UPDATED" so they stand out in the session header.

## v1.86.11 — Clear update messages

- **Changed:** the update message now says where it comes from and what changed: "Kit updated from vA to vB: N files (M new); K hook settings; CLAUDE.md blocks: ...". When the project's own hook and the global hook both act in the same start, the second says "one more step of the same update was applied (what)" instead of repeating the full restart notice.

## v1.86.10 — Docs data follows the format; kit banner on every page

- **New:** `docs_migrate.py` aligns old ROADMAP.md / BUGS.md data to the current format (adds the Release column with "Unassigned", puts `B-NNN:` ids in bug Titles, folds a separate ID column into the Title, keeps every row, backs up first). `kit_sync` runs it at every session start, idempotent. Rule in CLAUDE.md block `docs-format` and in `planner-docs`.
- **Fixed:** the format check wrongly required an ID and a Release column in BUGS.md; the console reads bugs as `B-NNN: title` and never uses a bug Release. BUGS.md is back to `Title | Where | Severity | Probable cause | Status`.
- **Fixed:** the "new kit version" and "update available" bars never showed on the Skills page (no anchor element).

## v1.86.9 — Two simultaneous kit updates no longer collide

- **Fixed:** at session start the project's own `kit-sync` and the global one in your profile ran together on Windows, and one failed with "Permission denied" on a file the other was writing (the update itself still completed). `kit_sync` now takes a lock (`Claude/logs/.kit-sync.lock`, stale after 90 s) so only one instance writes and the other exits quietly, retries a busy file up to 4 times, and a file that stays busy no longer aborts the whole update: it is reported and done at the next session start.

## v1.86.8 — Console warns about a newer kit and restarts after an update

- **New:** when the kit in your profile is newer than the files of the project, every console page shows an amber bar "New kit version ready" (new local endpoint `/kit-status` on both servers). It tells you to reopen Claude Code on the project.
- **New:** when `kit_sync` replaces or adds files, it now restarts the console server of THAT project (only if the listener on 8765 answers `/whoami` with this project), so the new pages and endpoints are served immediately. Reload the browser tab.

## v1.86.7 — Cost discipline: fewer subagents, cheaper models

- **Fixed:** the post-playtest hook started three headless `claude -p` sessions on your default model each time; they now use `--model haiku` (the sessions only delegate; the real work stays in the agents).
- **Cheaper agents:** `planner-docs` and `skill-reflector` run on haiku (planner-docs is protected by the docs format check). Reviewers that judge intent, `coder`, `qa-regression` and `template-reader` stay on sonnet.
- **Planning:** `coder` sizes each task S/M/L and spawns only what that size needs (S = compliance-reviewer only, planner-docs batched at session end; no qa/skill-reflector/second brain per task; no helper fan-out under 3 independent files). Same rule as CLAUDE.md block `cost-discipline`.

## v1.86.6 — One fixed format for ROADMAP and BUGS, checked automatically

- **Fixed:** the docs templates did not match what the console reads (ROADMAP had no Release column, BUGS had no ID column), so agents invented formats and the release card stayed empty. Templates now carry the exact columns plus a FORMAT CONTRACT comment.
- **New:** `docs_lint.py` checks columns, `T-`/`B-` ids, status words, empty Release cells, duplicate ids and bugs written as prose. A PostToolUse hook (`docs-lint.ps1`/`.sh`) runs it right after any edit of ROADMAP.md/BUGS.md and tells Claude to fix problems (exit 2). Never fires for other files.
- **Rules:** `planner-docs` and `qa-regression` get an explicit "never reinvent the format" contract; CLAUDE.md block `docs-format`.

## v1.86.5 — Island code saved by a hook

- **Fixed:** the island code the owner types in chat used to end up in the assistant's memory instead of `Claude/docs/.island-code` (the rule was only a mention). A `UserPromptSubmit` hook (`island-code.ps1`/`.sh`) now writes it to the file, and a CLAUDE.md block forbids copying it elsewhere. A different code never overwrites the saved one: Claude asks first.

## v1.86.4 — Old kits update themselves too

- **New:** a global SessionStart hook (`user-level-hooks/kit-sync-global.py`, installed into `~/.claude` by `update-my-profile.cmd`) updates any project that has the kit, even one with no update hook of its own. Tested on a copy of a pre-1.84 project.

- **Fixed:** projects with a kit older than v1.84 never updated (no update hook yet). The user-level CLAUDE.md now has section 14: at session start Claude compares versions with the profile template and runs `kit_sync.py` itself. Copy the new user-level `CLAUDE.md` to your profile once.

## v1.86.3 — Technique skills engage automatically

- **New:** `skills_lib.py techniques <dir>` finds the technique skills a project uses (markers in the Verse code). The CLAUDE.md block, `coder` and `codebase-auditor` run it first and read the matching skills, so a plain "audit the map" uses them without being asked.

## Unreleased — tool

- **New (personal tool, not shipped):** `tool/promote-genre-skills.py` compares your profile genre/technique skills with the repo and promotes official packs, references, SKILL.md (patterns block emptied) and an exported community pack, after privacy and format checks. Report-only by default.

## v1.86.2 — Console shows template-reader and skill-reflector

- **New:** the Console orbit lists `template-reader` and `skill-reflector`, so template analysis and lesson queuing are visible while they run.

## v1.86.1 — Epic templates are recognized automatically

- **Fixed:** analyzing an Epic template no longer asks for a genre. The word "template" (or a template-looking folder name, or the `template-reader` agent) writes `epic-template` to `.genre`, creates no genre skill and teaches nothing to genre skills; knowledge goes to the technique skill.

## v1.86.0 — Technique skills and official reference patterns

- **New:** a fifth confidence level, **reference**, for official guidance (Epic docs and templates). It stays reference until your own maps back it (1 map = confirmed, 2 = proven; a map against = contested). Only packs loaded as official can carry it; community packs cannot.
- **New:** technique skills share the genre engine. First one: `llm-npc-conversations` (16 official patterns, audit checklist). Official packs in `<skill>/official/*.json` are queued for approval on the Skills page at session start; re-ingestion is idempotent.
- **New:** `template-reader` agent studies docs/templates read-only and writes a card plus an official pack in its own words.
- **Skills page:** blue "reference" segment in the confidence bars, OFFICIAL pill, "added as official reference" text.
- **CLAUDE.md:** KIT block `technique-skills`. `skills_lib.py merge --official`. Tests extended.
- Profile copy of skills: use `robocopy user-level-skills "%USERPROFILE%\.claude\skills" /E /XD local pack` so learned data is not overwritten.

## v1.85.0 — Security hardening of the Skills library (CodeQL alerts: 18 → 0)

- **Hardened:** every file access in `skills_lib.py` goes through one gate (`_inside`), which resolves `..` and symlinks and refuses anything outside the allowed folder. A blocked path is now a visible error instead of a silent "file not found".
- **Hardened:** the Skills page endpoints (`/skills-act`, `/skills-check`) resolve the genre and the proposal id against what actually exists on disk (`resolve_genre`, inbox listing) instead of using the text sent by the browser. An unknown genre now returns HTTP 400.
- **Hardened:** paths the owner types on the command line (`merge` pack file, `export` folder) get their own checks: an existing `.json` file under 2 MB, a folder that is not a file or a filesystem root. Export still works to any folder you choose.
- **Fixed:** slugs, variants and ids with a trailing newline (`survival\n`, `pr-0123456789\n`) were accepted because the validation regexes used `$`; they now use `fullmatch`.
- **Tests:** new `tests/test_skills_safety.py` (CLI output shapes, export/merge to external paths, hostile ids and slugs, symlink escapes). Run both `tests/test_skills_lib.py` and `tests/test_skills_safety.py`.
- **Repository:** added `SECURITY.md`, issue forms, a pull-request template, `CODEOWNERS`, `CODE_OF_CONDUCT.md` and `CONTRIBUTING.md` (GitHub community profile), and `docs/code-scanning-lessons.md` with the lessons and a checklist for reviewing Copilot Autofix pull requests.
- Includes the changes of v1.84.1 – v1.84.3 below.

## v1.84.3 — Roadmap progress ignores out-of-scope tasks

- Fixed: the Docs page progress ring counted "Out of scope" rows in the total (82 Done + 4 To do + 10 Out of scope showed 82 of 96, 85%). Out-of-scope means discarded, so it is now 82 of 86 (95%), with a note of how many were left out.

## v1.84.2 — Verse header history is pruned

- New rule (user-level CLAUDE.md section 6, `coder`, `compliance-reviewer`): header history lines in Verse files are capped at 15; when exceeded the oldest are merged into one rolled-up line and the newest 8 are kept. Summary and Last modified are never dropped.

## v1.84.1 — Docs page reads task status by its first word

- Fixed: ROADMAP task Status cells such as "Done (closed by owner decision ...)" or "Fatto - verificato in play" were counted as "To do"
  because the page compared the whole cell. It now matches the leading word (Done/Fatto/Closed/Risolto, In progress/In corso,
  Blocked/Bloccato); anything else is still "To do". The roadmap template says so, and STATUS.md has an "Owner actions" line.

## v1.84.0 — Automatic kit updates, Skills page fix, MCP troubleshooting

- **Automatic project updates.** New SessionStart hook `kit-sync` (`kit_sync.py`, `kit-sync.ps1/.sh`). The FIRST install
  is still a manual copy. After that, each new session compares the project's kit files with a reference copy in your
  user profile (`~/.claude/kit-template`, i.e. a copy of `project-template/`), replaces obsolete/missing files, saves the
  old versions under `Claude/logs/kit-backup/<timestamp>/`, adds new hooks to `.claude/settings.json` (additive only) and
  refreshes `<!-- KIT:BEGIN x -->` blocks in `CLAUDE.md`. When something changed it says "Kit updated — restart the session".
  Never touches `Claude/docs`, your logs, permissions or the rest of your `CLAUDE.md`. New file `Claude/KIT-VERSION`.
- **No manual genre init.** The same hook creates the genre skill for the genre in `Claude/docs/.genre`.
- **Community packs staging.** Packs dropped in `~/.claude/skills/genre/<slug>/local/incoming/*.json` are validated and
  queued as ONE proposal each on the Skills page; nothing changes until you approve. Processed files move to `incoming/done/`
  (or `incoming/rejected/`).
- **Fix: the Skills page did not open on Windows.** The PowerShell console server (`agent-console-server.ps1`) now serves
  `/skills`, `/skills-data`, `/skills-act`, `/skills-check`. The page says so if the running server is older than the page.
  `skills_lib.py act` accepts `--exclude`.
- SETUP-GUIDE: "If the MCP connection drops" (port 8000 check, editor log, Inspector, manual restart).

## v1.83.0 — Skill Harness, part 3 (reflection at playtest)

- New agent `skill-reflector` (user-level). After a playtest (`after-playtest.ps1/.sh` now has a third
  step), or when invoked after a release-gate pass, it reads the real evidence (BUGS/STATUS/
  RETENTION-NOTES, logs, code) and QUEUES at most 3 generalized lessons for the genre skill. It only
  proposes; it never edits skills. "Nothing to learn" is an allowed outcome.
- `project-template/CLAUDE.md` rule: read the genre skill before designing core gameplay, trust each
  pattern according to its confidence, feed it via `skill-reflector`. `release-gate` reminds the
  main session to invoke it after a READY verdict.
- `project-bootstrap` Step 0.5 now creates the genre skill with `skills_lib.py init` instead of hand-writing one.
- `skills_lib.py patterns <genre>` lists existing patterns with their exact wording (support for an
  existing pattern is matched by content).
- Not verified from the development environment: running `skill-reflector` through `claude -p` on
  Windows, and the PowerShell `skill-consult.ps1` hook (the bash version is tested).

## v1.82.0 — Skill Harness, part 2 (approval + merge)

- Skills page: approve / edit wording / reject each lesson; apply or skip a community pack update
  item by item. The local server gets `POST /skills-act` and `/skills-check`, protected by an origin
  check and a custom header.
- Merge engine (`skills_lib.py merge`): an incoming pack is validated (format, links, commands,
  instructions to the AI, private terms) and becomes ONE proposal: new patterns enter as community
  hypotheses, known patterns only sum support counts (never double-counted on re-merge), conflicts
  are kept as contested. Your own evidence always wins; community support never raises a tier.
- `skill-consult` hook (PreToolUse on Read) counts when the coder reads a genre skill, feeding "Used by coder".

## v1.81.0 — Skill Harness, part 1 (layers, validator, Skills page)

- Genre skills learn from the first map: confidence ladder hypothesis -> confirmed (2 maps) -> proven
  (3+ maps or 2 + retention metric); a contradicting map marks the pattern contested. Replaces the
  "3 maps before anything is used" rule.
- Three layers per genre skill: generated `SKILL.md`, shareable `pack/patterns.json` (generalized
  patterns, stable IDs, support counts), private `local/` (map names, task IDs, notes, ledger,
  decisions, inbox). `local/` is git-ignored; `tool/sync-skills.ps1` no longer promotes `genre`.
- `skills_lib.py`: deterministic validator + secret/PII redaction (adapted from autoharness, MIT), privacy check
  and export (refuses to export if a map name, code, task ID, link or command is found), provenance ledger.
- New page `agent-console-skills.html` ("Skills") with a summary row (waiting for you, learning from,
  pattern confidence, used by coder) and a fifth entry in the menu of every console.
- Seed genre skills (survival, roguelike) restructured; the old per-variant `evidence.md` templates were moved to `_to_delete/`.
- Tests: `python3 tests/test_skills_lib.py`.

## v1.80.0

- New: update notice on all four consoles. Reads the latest published GitHub Release (checked at most every 6h, silent if offline) and shows a dismissible bar when it is newer than the running version.
- All four consoles (Console, Stats, Docs, Flow) now share one page chrome: same theme (font, background), container width, header spacing, title + version, and right-side view switch with page info. UI text is English (project standard).
- (was) Docs and Flow consoles now share the main console header (title + version). All UI text in the Docs console is English (project standard).
- Docs & Status console redesigned around what is still OPEN (mockup-approved):
  - Fixed "Open bugs = 0": `parseBugsBacklog` now scans the whole BUGS.md for every bug table
    (B-xxx rows), not just the one after the first "## Backlog" heading.
  - Roadmap card: open tasks only, grouped by the new ROADMAP.md "Release" column, with a
    done/total % per release; table columns ID | Status (priority + status) | Description.
  - Bug card: open bugs sorted by severity, table ID | Severity | Status | Description.
  - Hero: "Last update" replaced by a "Release status" card; Open bugs shows a severity breakdown.
  - Timeline nodes tagged bug fix / feature, plus a banner naming the current In progress task.
  - "Recent status" now shows task/bug priorities and explicit owner actions from STATUS.md.
  - Live rail: per-active-agent call-count sparkline (real /log events in 5s buckets) and a
    pulsing badge on the task/bug row that agent's latest log line references.
- Table parser fix: a paragraph following a closed table row is no longer merged into the last
  row's last cell.

## v1.79.11

- Added a "Recent roadmap tasks" card to the Docs & Status console
  (`agent-console-docs.html`), same readable-list treatment as the existing "Recent bug backlog"
  card: code — description, with a status badge (Done/In progress/Blocked/To do/Out of scope,
  reusing the existing `statusBucket()` bucketing) and a priority pill (MVP/nice-to-have/backlog/
  out of scope, normalized from ROADMAP.md's free-text Priority column the same way
  `bugSeverityPill()` already normalizes BUGS.md's Severity column). Still-outstanding tasks
  (in progress/blocked, then to-do) surface first, done and out-of-scope rows sink to the bottom;
  shows up to 10 rows with a link to the full ROADMAP.md. Previously the roadmap card only ever
  showed a progress ring and counts, never the individual tasks themselves.

## v1.79.10

- **Root cause found and fixed** for the Control Tower token gauge showing a stale active
  agent/station (e.g. "QA-REGRESSION") while the header above it correctly said "idle".
  `agent-console.html` (main console) has always pruned `active` stack entries whose `start`
  event never got a matching `stop` within 45 minutes (`STALE_ACTIVE_MS`, in `tickTimers()`) —
  this handles a session/subagent that crashed or was killed before its `SubagentStop` hook
  fired, which otherwise leaves a permanent orphaned entry. `agent-console-flow.html` never had
  this pruning, so a single orphaned start from days earlier could pin its gauge/truck/station
  rows to that agent indefinitely. Confirmed against the real project's `agent-console.jsonl`:
  several `start` events (qa-regression, verse-reviewer, intent-reviewer, an "unknown"-agent
  entry) going back to Sep 5 had no matching `stop` anywhere in the log. Added the same
  `STALE_ACTIVE_MS` (45 min) pruning to `agent-console-flow.html`, run every tick.
- Also fixed the stop-event matching in `agent-console-flow.html` to close the *most recent*
  unmatched start for an agent (LIFO) instead of the oldest (`findIndex` → manual reverse scan) —
  matters once stale/orphaned entries can coexist with a fresh, genuinely-running call for the
  same agent id.

## v1.79.9

- Added a visible version tag next to the title on the Flow of Flows console
  (`agent-console-flow.html`), matching the main console's existing one. The user reported the
  token gauge still showing a stale reading after 6 hard refreshes even though the v1.79.8 fix
  was confirmed correct and present on disk — with no version tag on this page, there was no way
  to tell whether the browser tab was actually loading the fixed file or a stale
  server/browser-cache copy. This tag makes that a glance, not a guess (see the main console's
  own header comment on why this exists).

## v1.79.8 — Control Tower gauge stuck showing a stale "current" reading at idle

Found by the owner comparing a live screenshot against `agent-console-flow.html`'s Control Tower
card: the header correctly read "CONTROL TOWER — idle" / "no active task" (green LED), but the
token-usage gauge directly below it still showed a non-zero needle, "65122.0K tok" and station
"QA-REGRESSION" — implying that station was actively burning tokens right now, contradicting the
header one line above it.

Root cause, in `pollTokensGauge()`: the needle angle, station label, and pulse glow were already
correctly gated on `topAgent` (the same `active.length ? active[active.length-1].agent : null`
check `refreshStations()` uses to drive the header), and correctly went to their idle state when
`topAgent` was falsy. But `readout.textContent = (t.total/1000).toFixed(1) + 'K tok'` ran
*unconditionally*, before that idle branch — so once any station had run and pushed a real token
total, the numeric readout kept displaying that last-seen total forever, never resetting, no
matter how long the system had been idle. It wasn't a stale-cache bug; it simply never had a code
path that cleared it.

Fix: moved the readout update inside the same `if (topAgent) { … } else { … }` branch already
driving the needle/station/pulse, using the exact same idle signal the header consumes — no new or
duplicate "is anything active" check was introduced. When idle, the readout now shows `0 tok` and
the station shows `idle`, matching the header directly above it. `sessionMaxTokens` (the
`maxRecorded`-style running max used to scale the needle's swing) is untouched by this fix and is
never reset on idle — it's explicitly a persistent scaling reference, not a live reading, and the
`tg-max` "session total" label keeps showing it across idle periods, exactly as intended.

Also bumped `KIT_VERSION` in `agent-console.html` (unrelated file, same kit) to keep the kit-wide
version number in step with this fix.

## v1.79.7 — Bug backlog card: overlong free-text Severity broke row layout

Found by the owner comparing a live screenshot against `renderBugBacklog()`'s output on the real
`root_harrow_TWD` `BUGS.md`: the bottom 4 rows (B-007..B-004) rendered a consistent one-line
`[severity pill] [status badge] [title]` layout, but the top 2 rows (B-009, B-008) showed an
overlong pill wrapping the title onto its own line below. The row template's HTML is identical and
unconditional for every row — this was not a structural markup difference, purely content-driven
wrap: the pill used to dump the raw `Severity` cell straight in (lowercased, otherwise unmodified).
Most rows have a clean one-word Severity (`Major`, `Minor`, `Non-blocking`), but on a real
long-running project that column is sometimes free text blurring severity and status together, e.g.
B-009's real cell is `Major (was reopened 2026-09-09; RESOLVED 2026-09-10)` and B-008's is `Was
blocking (sole remaining open item on T-028 — part (b) PASSed 2026-09-08)` — both far too long for a
pill, and B-008's even reads as a status phrase rather than a severity word. **Fix**: added
`bugSeverityPill()`, a keyword-match bucketer (same approach as the existing `bugStatusBadge()`) that
maps anything containing "block" (but not "non-block") to `blocking`, "major" to `major`, "minor" to
`minor`, "non-block" to `non-blocking`, empty to `unspecified`, and anything else to its first word
as a short fallback — the extra parenthetical context is dropped from the pill (it's redundant with
"Probable cause"/the full BUGS.md) and kept only in the pill's `title` tooltip. Verified against the
real B-004..B-009 rows: B-004/B-005/B-006/B-007 = `Non-blocking` → pill "non-blocking" (grey);
B-008 = `Was blocking (...)` → pill "blocking" (red); B-009 = `Major (...)` → pill "major" (amber).
All six rows' Status column is `Closed` → green "Resolved" badge in every case, and all six now
render the identical `pill → badge → title` single-line layout regardless of Severity cell length.

## v1.79.6 — Four real-project parser/UX bugs found by hand-verifying against a live ROADMAP.md/STATUS.md/BUGS.md

All four found by the owner testing `agent-console-docs.html` live against a real, long-running
project (`root_harrow_TWD`) and hand-counting the ground truth from the real docs.

**1. Task count was off by one, and "remaining" silently included Out-of-scope rows.**
`parseTableAfterHeading()`'s `looksLikeRowStart()` used to require the row's OWN opening line to
both start AND end with `|` (`/^\|.*\|\s*$/`), on the assumption a row always fits on one physical
line. A row whose last cell is itself long enough to contain real line breaks (long acceptance-
criteria prose, same shape the continuation-line handling already supports) opens with `| T-053 |
...` but that first physical line does not end with `|` — the closing `|` only appears several
lines later. That made the row's own first line fail the check and fall into the "continuation of
the previous row" branch instead, silently merging all of T-053 into T-052's last cell and dropping
it from the table entirely (confirmed against the real file: 64 real task rows parsed as only 63,
missing exactly T-053; not a T-005-shaped "the row doesn't exist" situation). **Fix**: row starts
are now recognized purely from the opening `| <ID>` shape (`/^\|\s*[A-Za-z]{1,4}-\d+\b/`), no
longer requiring the same physical line to also close with `|`. Separately, `statusBucket()` only
recognized done/active/blocked and defaulted everything else (including a deliberate "Out of
scope"/"Fuori scope" status) to "todo", so the hero card's "X remaining" summed Da fare + Out of
scope into one bucket. `statusBucket()` now returns a dedicated `"outOfScope"` bucket, and the
"remaining" count in `renderHeroInner()` only sums todo + active + blocked. Verified against the
real ROADMAP.md: 64 rows total, 53 Fatto, 6 Da fare, 5 Out of scope (53 + 6 + 5 = 64) — the card
now reads "53 of 64 tasks Done" / "6 tasks remaining" instead of "52 of 63 Done, 11 remaining".

**2. "Last update" showed a stale, months-old "In progress" line instead of the current one.**
The "In progress:" extraction used to run `/\*\*In progress:\*\*\s*([^\n]+)/i` against the WHOLE
`status.content`, requiring a BOLD `**In progress:**` label. A real STATUS.md's `## Current state`
section — documented in the file's own header comment as "REPLACED on every update", i.e. the only
authoritative snapshot — writes this as a plain, unbolded `In progress: ...` line, so the regex
never matched there and instead matched the first BOLD `**In progress:**` occurrence anywhere later
in the file, typically a stale dated Log entry near the bottom (confirmed: a real file's Log
contained `**In progress:** none — T-011 closed Fatto ... No task currently "In corso.")_`, which
the console was surfacing as if it were current). **Fix**: the extraction now first locates the
`## Current state` heading, scopes the search to that section only (bounded by the next `##`
heading), and matches `In progress:` with or without bold markers.

**3. "0 open bugs" showed "No bugs logged yet." even when bugs exist and are simply all resolved.**
`renderHeroInner()`'s open-bugs breakdown used the same fallback copy for "BUGS.md has no rows at
all" and "BUGS.md has rows but none are currently open" — misleading in the (common, healthy) case
where a project's backlog is fully resolved. **Fix**: the fallback now checks the unfiltered
backlog row count separately and shows "No open bugs right now — all logged bugs are currently
resolved." when bugs exist but none are open, reserving "No bugs logged yet." for a genuinely empty
Backlog table.

**4. Bug backlog card showed the oldest bugs (file order), not the most relevant/recent ones.**
`renderBugBacklog()` used to be `rows.slice(0, 6)` — literally the first 6 rows in file order,
i.e. the oldest bugs by id, regardless of how many newer or still-open bugs existed further down a
real BUGS.md. **Fix**: rows are now sorted before slicing — Open/Blocked bugs first (reusing the
existing `bugStatusBadge()` bucketing), "No status"/"In progress" next, Resolved last, and within
the same bucket the higher bug number (a safe structural proxy for "more recent", since ids are
assigned sequentially) sorts first, rather than parsing dates out of free-text Status/Probable
cause prose. On the real BUGS.md (10 rows, all Resolved) this changes the displayed set from
B-001..B-005/B-004b to B-004..B-009 — the six most recently-numbered bugs.

`KIT_VERSION` bumped to `v1.79.6` in both `agent-console.html` copies (`root_harrow_TWD`'s deployed
copy and the kit template, kept in sync); `agent-console-docs.html` fixes applied identically to
both copies (verified byte-identical after the change).

## v1.79.5 — Bug backlog: added a status badge alongside the severity pill

The "Recent bug backlog" card (`agent-console-docs.html`) showed only a severity pill (blocking/
major/minor/non-blocking) per bug — no indication of whether the bug was resolved, still open, or
in progress, even though the real `## Backlog` table already has a `Status` column and
`parseTableAfterHeading()` was already capturing it generically into `row.status` (via its
header-driven `row[header] = cell` parsing) — `renderBugBacklog()` just never displayed it.

Real Status cells are free text the project owner writes, not a fixed enum (mixed English/
Italian, e.g. "Closed — RISOLTO 2026-09-17, re-verified not re-fixed", "Open — coder adds on next
touch of this file", "Was blocking (sole remaining open item on T-028 — part (b) PASSed
2026-09-08)"). **Fix**: new `bugStatusBadge()` buckets a raw Status cell into a small badge,
checked in this order: (1) starts with "Closed" or contains "Risolto"/"Resolved" → green
"Resolved" (checked first so "...; T-028 has no other open item" isn't misread as still-open just
because "open" appears later in the text); (2) starts with "Open" → amber "Open"; (3) contains
"blocking" but not "non-blocking" (e.g. old "Was blocking (...)" rows with no leading Closed/Open
marker) → red "Blocked"; (4) anything else (or empty) → grey, showing the first few words of the
raw cell instead of hiding it. The badge (small dot + label, rounded-rect shape) renders right
after the existing round severity pill on the same line so the two are never visually confused;
`.bugrow` gained `flex-wrap:wrap` so long titles don't get cramped. Only `parseBugsBacklog()`'s
`## Backlog` table rows are affected — the separate "Newly reported (to be triaged)" free-text
section (not parsed into rows at all) is untouched. `KIT_VERSION` bumped to `v1.79.5`.

## v1.79.4 — Docs & Status console: three real parsing bugs found in live testing against a large real project

Real user bug report from live testing the Docs & Status console (`agent-console-docs.html`)
against `root_harrow_TWD`'s actual `Claude/docs/ROADMAP.md` (151KB, 63 real task rows) and
`STATUS.md` (256KB, real log history) — three concrete wrong-numbers/wrong-data issues, page
still loaded fine, nothing crashed:

**1. "Roadmap progress" showed "0 of 24 tasks Done"** while the timeline below correctly showed
most tasks as done. Root cause: the done/in-progress/todo counting logic (`t.status.toLowerCase()
=== "done"`) matched the literal English word only — this real project's rows use the Italian
status word "Fatto" (also "In corso" / "Da fare" / "Bloccato"), which is the PROJECT OWNER's own
data, not something we should force-translate. **Fix**: new `statusBucket()` helper buckets a raw
Status cell into done/active/blocked/todo case-insensitively, recognizing English and Italian
variants at minimum ("Done"/"Fatto", "In progress"/"In corso", "To do"/"Da fare",
"Blocked"/"Bloccato"); used everywhere a status was being compared (progress ring/count, timeline
dot color, current-task detection).

**2. Timeline stopped at T-025** even though real tasks go to T-065+. Root cause, two compounding
issues in `parseTableAfterHeading()`: (a) it stopped at the first blank line, but this real
ROADMAP.md has blank lines between rows (the owner groups rows visually by MVP/Nice-to-have/etc.
— still one continuous markdown table); (b) after fixing (a), a single very-long row (T-053's
acceptance-criteria cell) turned out to contain real embedded newlines instead of staying on one
markdown line, which also looked like "end of table" to the old strict per-line row matcher.
**Fix**: the parser now skips blank lines, recognizes a new row only when a line's first cell
looks like a real id (`T-053`, `B-001: …`), and treats any other non-heading line as a
continuation of the previous row's last cell — the table now only ends at a real heading or a
genuinely blank tail. Verified this reaches all 63 real rows through T-065. On top of that, the
timeline no longer dumps every parsed task unwindowed: `renderTimeline()` now shows a ~12-task
window centered on the current (In corso/In progress) task — a handful of done tasks leading up
to it, the current task, and a few upcoming ones — with a small note when the view is windowed,
since the strip itself already scrolls horizontally.

**3. "Last update" showed a stale/wrong entry** instead of STATUS.md's real newest log entry.
Root cause: the `_(updated: ...)_ ` regex required an exact `)_` right after the date to close
markdown italics, which this real project's long "Current state" prose (its own parentheses
inside) doesn't reliably produce — it silently returned `null` and fell back to a *file-wide*,
non-anchored `###` search with no guarantee it was even inside the `## Log` section. Per
STATUS.md's own documented convention ("New entry AT THE TOP on every update. Don't delete
history."), the correct source is the **first** `### YYYY-MM-DD` heading inside the `## Log`
section specifically — not the "Current state" snapshot block above it, and not any other `###`
occurrence. **Fix**: explicitly locate `## Log` first, then take the first dated heading after it.

All three fixes are in `Claude/hooks/agent-console-docs.html` (kit `project-template/` copy and
`root_harrow_TWD`'s deployed copy, kept in sync); `KIT_VERSION` bumped to `v1.79.4` in both
`agent-console.html` copies.

## v1.79.2 — Docs & Status console: fixed the real infinite-loading bug and removed all remaining mockup data

Real user bug report (live testing with screenshots) of the Docs & Status console
(`agent-console-docs.html`), two issues:

**1. "loading…" that could hang forever.** `fetchDoc()`'s `fetch("/doc?name=...")` had no bounded
timeout — a `try/catch` covered a thrown/rejected fetch, but nothing covered a request that just
never resolves (server mid-restart, stalled connection, etc.), which is a real gap even though it
did not reproduce in either of the two hypotheses named in the report: the server's `/doc` route
itself was already correct for every key including `spec` (whitelist lookup, always returns `200`
+ JSON, never hangs), and opening the page via `file://` already failed fast with a clear
"could not reach the local server" message rather than hanging — both verified with Playwright
before and after this fix. **Root cause actually found**: the markdown-table parser's separator-row
regex, `/^\|[\s:-]+\|\s*$/`, only matched a single-column separator like `|---|`, not a real
multi-column one like `|---|---|---|---|---|` (the `|` inside a character class only matched a
literal pipe once, not "one or more pipe-delimited groups"). Every doc's table (ROADMAP.md's Tasks
table, BUGS.md's Backlog table) silently failed to render as a table in `mdToHtml`, and once the
same parser was reused (below) to drive the hero/timeline/bug-backlog cards, those came back
empty. **Fix**: broadened the regex to `/^\|[\s:|-]+\|\s*$/` (both places it's used), and added a
6-second `AbortController` timeout to `fetchDoc()` so no fetch anywhere on this page can leave a
card on "loading…" indefinitely regardless of cause — success, honest-empty ("not created yet"),
and error ("could not reach the local server") are now the only three end states, all reachable
within a couple of seconds.

**2. Hardcoded mockup data still displayed as real.** Found and removed every one of these
leftover sample values, none of which were ever wired to a real file:
- "Recent bug backlog": `Storm collider not deactivating at round end`, `Respawn point duplicated
  in Zone 2`, `Missing logger in 3 custom files`, `DemoDisplay stand misaligned`
- Roadmap progress ring: hardcoded `68%`, `17 of 25 tasks Done`, `MVP release: 3 tasks remaining`
- Open bugs hero card: hardcoded `4` / `🔴1 blocking · 🟠2 major · 🟡1 minor`
- Last update hero card: hardcoded `Today, 14:20` / `planner-docs · T-017 marked Done`
- Roadmap task timeline: hardcoded nodes `T-013`…`T-020` with fake feature names ("Elimination
  Manager", "Player Spawner", "Item Granter", "Respawn cooldown UI", "Storm Controller",
  "DemoDisplay")

All five are now driven by real parsing of `Claude/docs/ROADMAP.md`'s Tasks table and
`Claude/docs/BUGS.md`'s Backlog table via the same `/doc?name=` mechanism the doc-card previews
already used (`renderHero()`, `renderTimeline()`, `renderBugBacklog()`). Each shows an honest
empty state ("ROADMAP.md has not been created yet" / "No bugs logged yet") when the file doesn't
exist or has no rows yet — never sample content.

**Verified with Playwright (chromium)** against the real running `agent-console-server.py`:
- Fresh project, no `Claude/docs/*.md` at all: every card/section shows its honest empty state
  within ~2.5s, zero `pageerror`/console errors.
- Populated project with distinctive test data (`ROADMAP.md` with tasks `T-101`–`T-106`, 3 Done /
  1 In progress / 2 To do; `BUGS.md` with `TESTBUG-Widget alignment off by 4px` (blocking),
  `TESTBUG-Save button unresponsive` (major), `TESTBUG-Tooltip wraps oddly` (minor); `STATUS.md`,
  `SPEC.md`, `RETENTION-NOTES.md`, `RELEASE-READINESS.md` each with a distinctive `TEST*-marker`
  string): the progress ring showed `50%` / `3 of 6 tasks Done`, open bugs showed `3` /
  `🔴1 blocking · 🟠1 major · 🟡1 minor`, the timeline rendered all 6 real task IDs with correct
  Done/In progress/To do dots, the bug backlog listed all 3 real `TESTBUG-` entries with correct
  severity pills, and all 6 doc-card preview modals (including SPEC.md) opened and rendered the
  real marker text within ~1.2s — no stuck loading anywhere, matching the test data exactly.
- `file://` (no server running): every card and the preview modal show
  "Could not reach the local server" / "disconnected — is agent-console-server running?" within
  seconds, not indefinite "loading…".

`KIT_VERSION` bumped to v1.79.2.

## v1.79.1 — Fixed Cost of Asking's halt→resume wait time (was measuring the wrong thing)

Independent QA re-verification of v1.79.0 found that the "Cost of Asking" card's average wait
time was silently wrong. It used "the next log entry of any kind after a halt" as the resume
signal, but that's not actually a safe signal: every agent's own `SubagentStop` hook logs a
`stop` line a moment after that agent finishes producing its halt verdict, as it exits — this is
the halting agent wrapping up its own invocation, not the owner responding. In a full simulated
run (intent-gate pass → coder → qa-regression reject → coder retry → qa-regression pass →
compliance-reviewer halt → **47-minute real gap** → coder resumes → compliance-reviewer pass →
release-gate pass), the card showed "~0.5 min/time" instead of the real ~47 minutes, because it
was measuring time-to-own-stop-hook, not time-to-owner-response.

**Fix**: the resume signal is now the next genuine `start` event (any agent) after the halt,
since a new invocation can only begin once the owner (or a scheduled resume) has actually acted —
falling back to the next entry only if the log ends right after the halt with no later start at
all. Re-verified against the same simulated run: now correctly shows "~47.0 min/time".

Also independently re-verified against a fresh/empty project (all 4 cards show their honest empty
states, zero console errors, zero unhandled 404s), against malformed/edge-case log lines (an
orphaned `verdict` with no matching `start`, an out-of-order-appended event, and a `verdict` with
an unparseable `ts`) — the UI degrades gracefully in all three cases, no crash, no silent
miscounting of the well-formed data — and against all 6 updated agent `.md` files, whose logging
instructions use one consistent event schema each with no duplicate/conflicting logging step.

`KIT_VERSION` bumped to v1.79.1.

## v1.79.0 — Flow console's 4 bottom cards now real, not sample layouts

v1.78.0 wired the Flow console's truck/gauge/Control Tower to real `/log`/`/tokens`/`/active-task`
data but left the 4 bottom cards (Decision Log, Model Tiers, Cost of Asking, Gate Outcomes) as
explicitly-labeled "(sample layout)" placeholders, because no agent logged the verdict/model-tier
data those cards need. This release adds that real data and wires the cards to it.

**New log event types** (appended to `Claude/logs/agent-console.jsonl`, same append-only
JSON-lines file and mechanism `agent-console-log.sh`/`.ps1` already use for `start`/`stop`):
- `{"agent":...,"event":"verdict","result":"pass"|"reject"|"halt","task":"<id>","ts":...,"detail":"..."}`
  — now logged by `intent-gate` (CLEAR→pass, AMBIGUOUS→halt), `intent-reviewer` (PASS→pass,
  REJECTED→reject, 5th-attempt escalation→halt), `compliance-reviewer` (same pattern as
  intent-reviewer), `qa-regression` (pass/reject based on whether it found blocking/major
  problems), and `release-gate` (READY[/WITH RESERVATIONS]→pass, NOT READY→reject). See each
  agent's own `.md` under `user-level-agents/` for the exact logging step added.
- `{"agent":"coder","event":"model_tier","tier":"from-scratch"|"second-brain"|"verse-patterns","task":"<id>","ts":...}`
  — logged once per task by `coder`, right after it settles on an implementation approach in its
  existing Step 0.5 (reused this kit's own existing vocabulary — second-brain query, verse-patterns
  reference, or neither — instead of inventing a generic cheap/mid/frontier scale).

**Flow console (`agent-console-flow.html`)** — all 4 cards now read real events from `/log`:
- **Decision Log**: the most recent real `verdict` events, colored by result (pass=green,
  reject=red, halt=magenta), same keyword styling as before. Empty state: "No decisions logged
  yet".
- **Model Tiers**: real percentage breakdown of `coder`'s logged `model_tier` events. Empty state:
  "No model-tier data yet".
- **Cost of Asking**: real halt count from `verdict` events with `result:"halt"`, and a real
  average wait time computed halt→resume, where "resume" is the kit's natural existing signal (the
  next log entry of any kind after a halt, since nothing else happens while the pipeline is
  genuinely waiting on the owner) — no dedicated resume event was added because none was needed.
  Empty state: "No halts recorded yet — nothing has required your input".
- **Gate Outcomes**: real pass/reject/halt counts aggregated across all gate/reviewer agents.
  Empty state: "No gate verdicts logged yet".
- The "(sample layout)" labels and the disclaimer text saying this data doesn't exist are gone;
  replaced with a comment describing the real data source for future maintainers.

**Audit of the rest of the console system (agent-console.html, -stats.html, -docs.html,
-flow.html)** for other fake/decorative elements: found none beyond what's already fixed. The
remaining `Math.random()` uses (missile-launch particle bursts, explosion-arc curvature) are
explicitly-documented cosmetic effects triggered only by real start/stop/verdict events, not stand-
ins for unavailable data, so they were left as-is.

`KIT_VERSION` bumped to v1.79.0.

## v1.78.0 — Docs & Flow consoles wired to real project data (they were mockups)

The two new consoles (`agent-console-docs.html`, `agent-console-flow.html`) looked finished but
never actually read anything real — every number and animation was hardcoded sample data or a
timer loop. This release wires both to the exact same real data sources
`agent-console.html` already uses (`/log`, `/tokens`, `/active-task`, and a new `/doc` endpoint),
instead of inventing a separate mechanism.

**Docs & Status console:**
- "Recent status" now shows the real "## Current state" section parsed out of the project's
  actual `Claude/docs/STATUS.md` (was: three hardcoded lines that never changed).
- Fixed SPEC.md, RETENTION-NOTES.md and RELEASE-READINESS.md not opening at all — they had no
  click handler and no data entry in the old hardcoded `DOCS` object, so clicking them did
  nothing. All six docs now fetch their real content from the new `/doc?name=<key>` server
  endpoint (added to both `agent-console-server.py` and `.ps1`) and render it (a small built-in
  markdown→HTML pass, plus the existing raw-markdown tab). A doc that genuinely doesn't exist yet
  in a fresh project (no SPEC.md until an agent writes one, for example) now shows a clear "not
  created yet" state instead of silently doing nothing — the doc-grid cards also dim and relabel
  themselves the same way on load.
- Removed the left icon-rail: every icon but "Status" was a dead, non-functional button. The main
  docs table/grid is now centered in the page with the freed-up width instead of sitting
  left-aligned next to empty space.

**Flow of Flows console:**
- The truck no longer animates on a fixed timer regardless of real activity. It now polls `/log`
  every second (same event stream and `active`-stack logic `agent-console.html` uses) and sits
  parked at the start of the belt, with every build/gate/ship machine effect dark, whenever no
  real agent in the 5-stage pipeline (`intent-gate → coder → intent-reviewer →
  compliance-reviewer → planner-docs`, matching the main console's own `MINIFLOW_PIPELINE`) is
  actually active. It only moves to, and animates, whichever real stage is currently running.
- The Control Tower's station-row highlighting no longer cycles through stations on a timer. It
  now reflects whichever real agent is topmost in the live `active` stack — genuine idle (no
  highlighted station, no cycling) when nothing is running.
- The token-usage gauge no longer performs a canned sweep with random numbers. It now reads the
  same `/tokens` session-cumulative total the main console's "Tokens this session" stat uses, and
  only shows a needle position/pulse while a real agent is active; at idle it sits flat at zero
  with "no usage data yet" / "idle" rather than implying false activity. **Honest limitation:**
  this kit does not currently log token usage per-agent or per-task, only a session-wide total —
  so the gauge shows the real session total scaled against its own session-high, not a genuine
  per-station breakdown. Real per-agent token metering would need a new logging hook (e.g. tagging
  `agent-console-tokens.ps1`/`.sh`'s writes with whichever agent is topmost in `/log`'s `active`
  stack at that moment) — left as documented future work rather than faked here.
- The four "Decision log / Model tiers / Cost of asking / Gate outcomes" cards and the top
  shipped/steps/decisions/sent-to-you counters remain illustrative sample layouts, labeled as such
  in the page: this kit does not yet log a structured per-decision audit trail or model-tier
  choices anywhere, so there's no real data to wire them to yet.

`KIT_VERSION` bumped to v1.78.0.

## v1.77.2

- Fixed: Docs and Flow console tabs did not open — nav wiring bug. The main console and Stats
  page nav used server-root-absolute hrefs (`/`, `/stats`, `/docs`, `/flow`), which resolve to a
  nonexistent local path when `agent-console.html` is opened directly (`file://`) instead of
  through `agent-console-server.py` — clicking Docs/Flow silently failed with
  `ERR_FILE_NOT_FOUND`. Also, the reverse links on the new Docs/Flow pages (plain relative
  filenames like `agent-console-stats.html`) fell through the server's catch-all route and
  rendered the wrong page when served over `http://`. Both are now unified: every console page's
  nav uses plain relative filenames, and `agent-console-server.py`'s `do_GET` explicitly maps both
  the short routes (`/stats`, `/docs`, `/flow`) and the filename routes
  (`agent-console-stats.html`, `agent-console-docs.html`, `agent-console-flow.html`) to the correct
  file, so navigation works identically via `file://` and via the local server. Also found and
  fixed `agent-console-server.ps1` (the Windows/PowerShell server), which never received `/docs`
  and `/flow` routes when those pages were added — only `/stats` existed there; both routes (and
  their filename aliases) are now added, matching the Python server. `KIT_VERSION` bumped to
  v1.77.2.

## v1.77.1 — Full Italian-to-English translation pass

Completed full Italian-to-English translation across the kit, including previously-intentional
status vocabulary (`Da fare`/`In corso`/`Bloccato`/`Fatto` → `To do`/`In progress`/`Blocked`/`Done`;
`CHIARO`/`AMBIGUO` → `CLEAR`/`AMBIGUOUS`) per explicit user request ("TRADUCI TUTTO" — translate
everything, no exceptions). This supersedes the v1.77.0 judgment call to leave that vocabulary
alone as an "intentional shared convention" — the owner's instruction here is total and overrides
that reasoning.

- Updated `ROADMAP.md`/`STATUS.md` templates, `CLAUDE.md`, `user-level-memory/CLAUDE.md`, and every
  agent file (`coder.md`, `intent-gate.md`, `intent-reviewer.md`, `planner-docs.md`,
  `project-bootstrap.md`, `release-gate.md`) that referenced the old Italian status/verdict labels
  as literal strings, so the enum values stay consistent everywhere they're written, compared, or
  displayed.
- Fully translated several `user-level-skills/*/SKILL.md` files that were still entirely in
  Italian (`fortnite-marketing-launch`, `fortnite-competitor-analyzer`, `fortnite-retention-
  gamedesign`, `fortnite-social-trailer`, `fortnite-thumbnail-pro`, `fortnite-title-description`,
  `fortnite-update-writer`, `fortnite-analytics-coach`), including their `description:` frontmatter
  and "Parla in italiano" style instructions (now "Speak in English").
- Translated the `genre/roguelike/` and `genre/survival/` skill trees (`SKILL.md`, `references/
  variants.md`, `references/evidence-shared.md`, and every `variants/*/evidence.md` file), and
  `genre/fortnite-tags-known.json`'s Italian internal notes/mechanism fields.
- Translated `second-brain-template/CLAUDE.md` in full, including its prescribed article section
  headers (`## Punti chiave` → `## Key points`, `## Connessioni e potenziali` → `## Connections
  and potential`, `## Fonti` → `## Sources`, etc.), frontmatter field names (`fonti` → `sources`,
  `visto_su` → `seen_on`, `data_creazione`/`data_aggiornamento` → `date_created`/`date_updated`,
  `versione_implementazione` → `implementation_version`), file names (`indice.md` → `index.md`,
  `indice_wiki.md` → `wiki-index.md`, `frontiere-conoscenza.md` → `knowledge-frontiers.md`,
  `evoluzione-kb.md` → `kb-evolution.md`), and the `sintetizza` command alias (now `synthesize`) —
  with matching updates in `second-brain-template/README.md`, the release-notes sync scripts, and
  `second-brain-librarian.md` so every cross-reference stays in sync.
- Fixed remaining stray Italian strings in `agent-console-stats.html` (chart title/empty-state
  text) and a couple of quoted owner remarks and file-path examples elsewhere.
- `KIT_VERSION` bumped to v1.77.1.

## v1.77.0 — Two new Agent Console views: Docs & Status navigator, Flow of Flows pipeline

Two new console pages, approved across many mockup rounds in `/tmp/console-mockups/` and
`/tmp/flow-jev/conveyor-5.html`, are now real files in `Claude/hooks/`, wired into the same
`view-switch` nav pattern and `agent-console-server.py` routing as the existing Console/Stats
pages. Also fixed stray Italian UI text the owner spotted on the Stats page.

**What changed:**
- New `Claude/hooks/agent-console-docs.html` ("Docs & Status Console"): icon rail, hero cards (SVG
  roadmap-progress ring, open-bug count, last update), a horizontal timeline of ROADMAP.md tasks
  with hover tooltips, a bug-backlog card, and a docs grid over `Claude/docs/*.md`
  (STATUS.md/ROADMAP.md/BUGS.md/SPEC.md/RETENTION-NOTES.md/RELEASE-READINESS.md, matching
  `planner-docs`'s real file ownership) with a raw-markdown vs. rendered-HTML preview toggle.
  The rendered-HTML view is a snapshot: it regenerates when a task starts, not live on every page
  open and not only when `planner-docs` writes — see the new Step 0 item 6 in
  `user-level-agents/coder.md`, added right after it writes `Claude/docs/.active-task`.
- New `Claude/hooks/agent-console-flow.html` ("Flow of Flows Console"): the assembly-line conveyor
  pipeline (only the approved "Assembly line" variant — the mockup file held 5 switchable
  concepts, only one shipped), 4 color-coded zones (INTAKE/BUILD/GATE/SHIP) with the kit's real
  per-agent icons/colors (matches the registry in `agent-console.html`: coder alone in BUILD with
  a 🏭 factory + welding sparks, compliance pre-check/MCP place gate/qa-regression/intent-
  reviewer/compliance-reviewer clustered in GATE, planner-docs in SHIP with a sealed-crate ✅), a
  nose-forward truck that travels the belt and pauses at whichever station is active, a Control
  Tower (chief-of-staff hub + token-usage gauge scaled to the max token value recorded so far per
  station, a scrollable per-station status list, decision history), and the Decision
  Log/Model Tiers/Cost of Asking/Gate Outcomes 4-card grid.
- Both new pages linked from the main console's and Stats page's `view-switch` header nav
  (`Console · Stats · Docs · Flow`), and `agent-console-server.py` gained matching `/docs` and
  `/flow` routes alongside the existing `/` and `/stats`.
- Italian-to-English cleanup: `agent-console-stats.html` had leftover Italian UI copy the owner
  flagged ("Nessun codice isola trovato...", "Salva il codice della tua isola...", a tooltip
  reading "Genere assegnato al progetto...", plus the surrounding code comments) — all translated
  to English. Audited `agent-console.html` and both new console files with the same pass; none of
  the kit's intentional status vocabulary (`To do`/`In progress`/`Blocked`/`Done`,
  `CLEAR`/`AMBIGUOUS`) was touched — that's the kit's own tracked convention, not stray text.
- `KIT_VERSION` bumped to v1.77.0.

## v1.76.1 — `second-brain-trainer` verifies findings before they reach the shared vault

Owner asked for a review against best practices for dynamic multi-agent orchestration (fan-out
vs. pipeline, adversarial/claim-level verification before a high-stakes write). Checked the kit's
own parallel-fan-out agent, `second-brain-trainer`, against that: its Step 1-3 fan-out-and-
synthesize (dispatch `second-brain-scout` clones per area in parallel waves, merge duplicates)
already matches the pattern well. The gap was verification — merged findings went straight to
`second-brain-librarian` for writing into the vault with no re-check, and this is a higher-stakes
write than most in the kit: a mistaken pattern here doesn't just cost the current project, every
future project that queries the second brain inherits it.

**What changed:**
- `user-level-agents/second-brain-trainer.md`: new Step 3.5 — every aggregated finding is
  re-opened against its actual file/device and confirmed to (1) genuinely work as described and
  (2) actually be reusable across projects, not secretly dependent on this project's own setup,
  before `second-brain-librarian` ever sees it. Findings that don't hold up are dropped, not
  softened. Step 5's report now also states how many were dropped at this step.
- `codebase-auditor` (v1.75.1) and `second-brain-trainer` now share the same verify-before-write
  discipline — the two places in this kit where an agent's own findings become a permanent
  artifact someone else acts on without re-reading the source.

## v1.76.0 — Skill-design best-practice pass: sharper trigger phrases + a growth "lessons" KB

Owner asked for a review of the kit's skills against published best practices for writing Claude
Skills (description field written for model decision-making with concrete trigger phrases;
gotchas as the highest-value content, continuously updated from real outcomes). Checked every
skill in the kit against those; the "system" skills (`genre`, `uefn-lessons`, `verse-patterns`,
`mcp-tool-contracts`, `discover-retention`) already did this well — hooked to a specific agent
step, already accumulate real lessons. The real gap was the 8 `fortnite-*` growth/marketing
skills: short, generic, human-summary-style descriptions with no concrete trigger phrases, and no
equivalent of `uefn-lessons` capturing what actually worked vs. flopped across real projects.

**What changed:**
- All 8 `fortnite-*` skill descriptions (`analytics-coach`, `competitor-analyzer`,
  `marketing-launch`, `retention-gamedesign`, `social-trailer`, `thumbnail-pro`,
  `title-description`, `update-writer`): rewritten to include concrete phrases an owner would
  actually type ("fammi una copertina," "perché il CTR è basso," "scrivi le patch notes," and
  similar), written for the model's own routing decision rather than as a human-readable summary.
- New `user-level-skills/fortnite-growth-lessons/SKILL.md`: cross-project knowledge base for
  growth/marketing, mirroring `uefn-lessons`'s exact convention but for measured outcomes
  (thumbnail/title/trailer/launch/patch-note approaches that demonstrably over- or under-performed)
  instead of code gotchas — explicitly gated on a real signal (a number, a direct reaction), never
  filed just because an asset was produced.
- `user-level-agents/growth-manager.md`: reads this new skill before routing to any of the 8, and
  now has an explicit "feed outcomes back" step — whenever a real result becomes known during a
  session (owner reports updated metrics, reacts to a launch, comments on a patch note's tone),
  file it as a lesson without waiting to be asked, the same discipline `coder`/`second-brain-
  librarian` already apply on the code side.

## v1.75.1 — `codebase-auditor` now verifies its own findings before handing them off

Owner asked for a best-practice pass over the kit. Reviewed against current guidance on
large/agentic work (delegating audits with evidence verification, in particular) and checked it
against what's actually in this kit's agent files — most of it was already covered (task lists in
ROADMAP.md/STATUS.md, pre-human review gates via intent-reviewer/compliance-reviewer, no
"think step by step"-style redundant prompting anywhere in the kit). One real gap found:
`codebase-auditor` produced findings and hands them straight to `planner-docs` with no re-check
against the actual files — a hallucinated or stale finding could turn into a real ROADMAP task.

**What changed:**
- `user-level-agents/codebase-auditor.md`: new Step 2.5 — every finding gets re-opened against
  its actual file/line/device and rechecked before it's allowed into the report; findings that
  don't hold up on re-check are dropped, not softened. Findings that can't be fully confirmed via
  static analysis alone are now labeled as such (vs. directly-confirmed ones), so `planner-docs`/
  the owner can tell "confirmed" from "worth checking at the next playtest" at a glance. Also
  notes that a large project's audit can be split across parallel passes per category, but the
  verification step always runs against the real files afterward regardless.

## v1.75.0 — Broke the chicken-and-egg loop: UI learning no longer depends on a `coder` task

Owner pointed out the real gap: they design UI screens BY HAND, directly in the project, not via
`coder` — that's precisely why they wanted this skill (`coder` can't design good screens yet
without examples). Every feeding mechanism up to v1.74.3 was tied to `coder` finishing a tracked
task, so hand-authored screens never fed the skill at all — a genuine dead end, since the one
source of real examples (the owner's own hand-drawn work) had no path in.

**What changed:**
- `project-template/CLAUDE.md`'s "UI reference harvest" rule now also runs a per-session **UI
  code drift check**, independent of the task workflow entirely: on every session start, it hashes
  every real UI/widget file found in the project and compares against
  `Claude/docs/.ui-code-ingested.json` (new per-project state file, file path → last-ingested
  hash). Anything new or changed since last time — regardless of who wrote it or whether it was
  ever a tracked task — gets analyzed via `game-ui-designer`'s source-code analysis and filed into
  `code-derived.md`/`manifest.md`/`UI-STYLE-NOTES.md` automatically, then its hash is recorded so
  it isn't re-analyzed until it changes again.
- `user-level-skills/game-ui-designer/SKILL.md`: documents this as mechanism 5, explicitly framed
  as the primary feeding path for hand-authored screens — the `coder`-task-close mechanisms (1-3)
  become the secondary loop once `coder` itself starts generating screens FROM the accumulated
  style guide, closing the full circle (hand-made screens teach the skill → skill lets `coder`
  generate consistent new screens → those get fed back too).

Net effect: the owner can keep designing UI entirely by hand, and every screen still gets learned
automatically the next time the project is opened in Claude Code — no task, no screenshot, no
explicit request.

## v1.74.3 — `coder` self-feeds `game-ui-designer` from every new/edited screen, no screenshot needed

Owner asked the natural follow-up to v1.74.2: while actively working on a project and building or
editing a UI screen, what actually happens automatically? Until now the day-to-day feeding path
(`coder.md` step 8 / `planner-docs.md` step 5) still expected a screenshot as the primary input,
with code-derived analysis only wired in as the one-time bootstrap backfill and an on-demand ask.
That meant ordinary day-to-day UI work wasn't feeding the skill at all unless a screenshot showed
up — inconsistent with the fact that the code itself (the widget file `coder` just wrote) is
always available and doesn't need the owner to do anything.

**What changed:**
- `user-level-agents/coder.md` step 8: after finishing ANY UI screen (new or edited), `coder` now
  runs `game-ui-designer`'s source-code analysis on the file(s) it just wrote as the DEFAULT path
  — always available, no screenshot dependency — and includes the extracted facts in its
  fixed-shape closing report. A screenshot, if one also happens to exist, is added on top, never
  a substitute or a blocker.
- `user-level-agents/planner-docs.md` step 5: files the code-derived facts from `coder`'s report
  into `references/examples/code-derived.md` + `manifest.md` at every task close (falls back to
  extracting them itself if an older-format report didn't include the block). Dropped the
  "pending screenshot marker" fallback since a code-derived entry now always exists regardless of
  whether an image does — a screenshot is purely additive from here on, not something to chase.

Net effect: every UI screen built or modified through this kit from now on automatically becomes
a reference example the moment its task closes — nothing to remember, nothing to attach.

## v1.74.2 — `game-ui-designer` can learn directly from real UI code, not just screenshots

Owner clarified: their existing project has real UMG/Verse widget implementation files for its
UI screens, not exported screenshots — the screenshot-only pipeline from v1.74.0/v1.74.1 had no
path for that.

**What changed:**
- `user-level-skills/game-ui-designer/SKILL.md`: new 4th feeding mechanism, "Direct source-code
  analysis" — reads real widget/UI Verse files directly, extracts concrete facts only (widget
  types/nesting, literal colors, corner-radius/padding, currency asset references, layout
  structure), writes one entry per screen to a new `references/examples/code-derived.md` plus a
  `manifest.md` row sourced to the real file path, and feeds the same per-project
  `Claude/docs/UI-STYLE-NOTES.md` the screenshot path already feeds. Explicitly runs on demand
  when the owner points at real code, not only via the scheduled hooks.
- `user-level-agents/project-bootstrap.md`: the one-time existing-UI backfill (Branch A) now
  checks for real UI code files first — this is the common case for an existing UEFN project —
  falling back to image screenshots only if code isn't found or doesn't apply.

## v1.74.1 — `game-ui-designer` self-feeding made fully automatic (no per-task question)

Owner pushed back on v1.74.0's "ask once whether to save a screenshot" mechanism: same lesson as
the earlier genre-check gap — a step that only fires when manually invoked, or that requires
answering a question every single task, doesn't actually self-maintain. Reworked the whole
feeding pipeline to be automatic in the same three places the rest of this kit already automates
mechanical bookkeeping (task close, every-session check, one-time project bootstrap):

**What changed:**
- `user-level-agents/coder.md` step 8: after finishing a UI screen, stages any available
  screenshot into `Claude/docs/ui-screenshots-pending/` instead of asking whether to keep it —
  purely mechanical, no owner-facing question.
- `user-level-agents/planner-docs.md`: new closing step 5 (renumbering old 5-9 → 6-10, and fixing
  a pre-existing duplicate step-9 numbering along the way) — on closing a UI-related task,
  automatically files any staged screenshot into `~/.claude/skills/game-ui-designer/references/
  examples/<archetype>/`, logs it in that skill's `manifest.md`, and records the concrete style
  choices made into the project's `Claude/docs/UI-STYLE-NOTES.md`; if no screenshot was staged yet,
  leaves a one-line pending marker instead of asking again next session.
- `project-template/CLAUDE.md`: new "UI reference harvest" bullet, same automatic-every-session
  pattern as the genre check — scans `Claude/docs/ui-screenshots-pending/` on every session start
  and files anything a previous task close didn't have an image for yet.
- `user-level-agents/project-bootstrap.md` (Branch A, existing-project analysis): new one-time
  backfill step — scans a pre-existing project for screenshots of UI screens that already exist,
  so projects analyzed for the first time under this skill aren't stuck empty just because they
  predate it.
- `user-level-skills/game-ui-designer/SKILL.md`: self-learning section rewritten to describe the
  3 automatic feeding paths above plus the two things that stay genuinely manual (adding an
  external, non-UEFN inspiration image; periodically reviewing whether `style-guide.md` itself
  needs updating as real examples accumulate).

## v1.74.0 — New skill: `game-ui-designer` (learns the owner's in-game UI style over time)

Owner wanted a way to design new UEFN in-game UI screens (stores, shops, missions/quests,
teleporter, rewards, inventory) that stay visually consistent with examples they've made by
hand, and to be able to feed it images to keep improving — an explicitly self-learning skill,
not a one-shot style dump.

**What was added:**
- `user-level-skills/game-ui-designer/SKILL.md`: new user-level skill (lives at
  `~/.claude/skills/game-ui-designer/`, same convention as `genre/`, `uefn-lessons/`, etc.).
  Covers panel anatomy, item-card recipe, currency display, progress/reward patterns, and what
  NOT to copy directly from reference art (third-party icons/branding).
- `references/style-guide.md`: distilled rules extracted from the owner's first 9 reference
  images (Roblox-sourced, given explicitly as aesthetic reference only, not UEFN screenshots or
  literal assets to reuse).
- `references/examples/<archetype>/*.png` + `manifest.md`: the starting example set, organized
  by UI archetype (store, shop, missions-quests, teleporter, rewards, inventory).
- **Self-learning loop**: the skill instructs itself to (1) save any new reference image the
  owner shares into the matching archetype folder and log it in `manifest.md`; (2) after
  finishing a real screen, ask once whether to save a screenshot of the *finished, owner-approved*
  result back into the examples — this is what gradually shifts the example set from "generic
  Roblox inspiration" to "this owner's own established UEFN style"; (3) periodically re-check
  `style-guide.md` against the accumulated real examples and propose updates if they've drifted.
  Promotion to `mature` follows the same discipline as Genre Skills: 3+ distinct projects with an
  owner-approved finished screenshot each, not just a raw example count.
- `user-level-agents/coder.md`: new step 8 (old step 8→9) — when a task involves building or
  reworking a UI/menu screen, read this skill first (and the project's own
  `Claude/docs/UI-STYLE-NOTES.md` if one already exists, which wins over the generic guide), and
  offer to save a screenshot of the finished result afterward.

## v1.73.3 — Fixed truncated reject-count badge on the last miniflow stage

Owner reported a minor but real display bug in the main Agent Console: the small red "×N" reject
badge on an agent avatar (spotted on `planner-docs`, the rightmost stage in the miniflow rail) was
visually cut off horizontally, unreadable.

**Root cause:** `.mf-reject-badge` is `position:absolute; right:6px` relative to its 96px-wide
`.mf-node`. The rail (`.miniflow-rail`) scrolls horizontally but had no right-side padding, so the
rightmost node sat flush against the rail's own clipped edge — the badge's rendered box extended
past that edge and got cut off. Reproduced with a Playwright script forcing the badge visible on
the last pipeline stage (`planner-docs`) and confirmed visually against the owner's screenshot
before making any change.

**What changed:**
- `agent-console.html`: `.miniflow-rail` now has right-side padding (`padding:6px 14px 2px 0`) so
  the last stage's badge has clearance instead of sitting at the hard scroll edge; `.mf-reject-badge`
  changed from `right:6px` to `right:-2px` (compensates for the node's own edge) with
  `white-space:nowrap` and `z-index:2` added so the badge text never wraps/gets clipped regardless
  of which stage it's on.
- Verified with a Playwright screenshot forcing `×12` on the `planner-docs` badge: fully readable,
  no truncation, no console errors (before/after comparison).

## v1.73.2 — Show the project's assigned genre on the Stats tab (owner spotted the gap)

Owner noticed that the Stats page showed tags and a "Genre Rank" card saying "in Survival", but
never showed the genre actually assigned to the project via `Claude/docs/.genre` — those are two
different sources (one is what the creator chose/confirmed for the project, the other is what
Epic's live API reports for the published island) that usually agree but could in principle
diverge, and the page never surfaced the first one at all.

**What changed:**
- `agent-console-server.py` / `.ps1`: new `/project-genre` endpoint, serving
  `Claude/docs/.genre` verbatim (same plain-text pattern as the existing `/active-task`).
- `agent-console-stats.html`: new green "genre" badge next to the island title, visually distinct
  from the grey tag badges, with a tooltip explaining it's the project-assigned genre — separate
  from whatever genre the Genre Rank card's live API data reports.
- Verified with a mock server returning `survival` from `/project-genre` alongside real tag data:
  Playwright screenshot confirms the badge renders correctly, zero console errors.

## v1.73.1 — Genre check decoupled from project-bootstrap (runs automatically every session)

Fixed a real usability gap the owner hit immediately: the genre-selection step (v1.73.0's Step
0.5) only lived inside `project-bootstrap`, which by design runs ONCE EVER and only on projects
that haven't already been bootstrapped — so it would never fire on any of the owner's existing,
already-analyzed projects, forcing a manual per-project invocation for every one of them.

Moved the trigger to `CLAUDE.md` (project rules), same automatic-every-session pattern already
used for the Agent Console check: as the very first action of any session, check whether
`Claude/docs/.genre` exists — a one-line file check, cheap enough to run every time — and if not,
follow `project-bootstrap.md`'s Step 0.5 procedure directly (that step was already self-contained,
just needed a trigger not gated behind "bootstrap never ran here before"). No permission needed to
run the check itself; the genre choice itself still always stops and asks the owner, same as
before. This means opening any pre-existing project — even ones analyzed long before this feature
existed — now sets its genre and bootstraps its Genre Skill automatically, without the owner
invoking anything by name project by project.

## v1.73.0 — Genre Skills architecture (real code, not just design) + tag badges on Stats

Turns the Genre Skills design discussed with the owner into actual wired-in behavior, plus
closes the loop on official genre/tag data.

**Genre Skills bootstrap and lifecycle, wired into the real agent workflow:**
- `project-bootstrap.md` (Step 0.5, new): the first time a project has no `Claude/docs/.genre`,
  proposes the closed genre list (`~/.claude/skills/genre/fortnite-genres-official.json`), saves
  the owner's choice, and bootstraps an empty `~/.claude/skills/genre/<slug>/SKILL.md` (status
  `draft`) if that genre has no skill yet — deliberately empty, no invented patterns.
- `coder.md` (new step): reads the project's Genre Skill before gameplay/design tasks, one-way
  dependency only (never edits it).
- `planner-docs.md` (new step, on task close): appends a dated observation to the matching
  variant's `evidence.md`, checks the promotion rule (3+ maps with entries and at least one
  pattern — reproducible in 2+, plausible cause, actionable — repeated across them), flips
  `draft` → `mature` and updates `SKILL.md` when it's met, and only then checks 2+ mature
  variants for genuine cross-variant convergence into `references/evidence-shared.md` (staying
  empty is a legitimate outcome, not a gap to force).
- Genre Skills moved to the USER level (`~/.claude/skills/genre/`), matching every other skill in
  this kit (`fortnite-analytics-coach`, `uefn-lessons`, etc.) — shared across every project
  instead of duplicated per-project. Shipped with two prototype genres (Survival, Roguelike),
  each with a first set of variants as empty, honest starting points.

**Official genre + tag lists, now complete from real sources.** The genre list
(`fortnite-genres-official.json`) was previously missing 3 of 13 genres (only 10 were confirmed
via a real `GET /genres` capture). Fetched Epic's own documentation
(dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite) to fill the gap:
Adventure & RPG, Battle Royale, Deathrun & Platformer — their display names are doc-confirmed,
their `slug` values are inferred from the same pattern as the 10 API-confirmed ones and marked
`slugSource: "docs-inferred"` rather than presented as equally certain. Also fetched Epic's Game
Tags documentation (dev.epicgames.com/documentation/fortnite/games-and-game-tags-in-fortnite-creative)
for the full 149-tag official closed list (`fortnite-tags-known.json`) — previously shipped
empty, waiting to be built up tag-by-tag from real captures; now ships pre-populated with Epic's
own list, with a separate `observedOnIslands` array for tracking which tags actually show up on
real islands over time (see below).

**Tag badges on the Stats tab, from real data already being fetched.** `agent-console-server.py`
/ `.ps1`: every `/island-info` call now also updates `~/.claude/skills/genre/fortnite-tags-known.json`'s
`observedOnIslands` with the island's real `tags` field (first/last seen, times observed, which
islands) — best-effort, never breaks the info endpoint on failure. `agent-console-stats.html`:
renders the island's current tags as small badges next to the title, using data already being
fetched for the title itself (no new network calls). Verified with a mock `/island-info` response
carrying 5 tags and a direct call to the tracking function against a real copy of
`fortnite-tags-known.json` — confirmed same-day re-observation doesn't double-count
`timesObserved`, and a Playwright screenshot confirmed the badges render with zero console errors.

## v1.72.0 — Genre Rank card on the Stats tab

Added a "Genre Rank" panel to `agent-console-stats.html`, showing where the island currently
ranks within its genre plus a 7-day rank trend (best/worst/average).

**A winding but honest path to the real endpoint.** The feature was first requested from a
reference screenshot the owner had; it was initially mis-assumed to come from a third-party site
(Fortnite.gg), and a capture prompt was drafted around that premise before the owner corrected
it with a screenshot of the *official* Swagger "Genres" section — missed earlier because that
Swagger page is JS-rendered and unreadable by automated fetch (same limitation noted in v1.71.0).
A first real sample from `GET /genres/{slug}/rankings` didn't match the reference screenshot's
genre or rank range, which turned out to be the wrong endpoint — that one ranks a genre overall,
not one island. The owner then shared the full Swagger endpoint list, which surfaced the actually
relevant one: `GET /islands/{code}/rankings`.

**Confirmed via real capture (2026-09-19).** With no `from`/`to`, the endpoint returns only the
latest single hourly snapshot. With `from`/`to` set to a 7-day window it returns an
HOURLY-granularity series — 167 points observed for the real island tested — each shaped
`{timestamp, genres:[{genreSlug, genre, rank}]}`; `genres` had exactly one element in every real
record (this island carries a single genre tag). Lower rank number = better. A `to` in the future
produces a real `400 Bad Request`, so — same pattern as the metrics endpoint — `to` is always
clamped server-side to "now".

**What changed:**
- `agent-console-server.py` / `.ps1`: new `_get_island_rankings()` / `Get-IslandRankingsJson`,
  same memory+disk cache pattern (5-min TTL) as the metrics endpoint, served at
  `GET /island-rankings`.
- `agent-console-stats.html`: new rank card above the KPI tiles — current rank, best/worst/average
  over the window, and an inverted-axis line chart (lower rank number maps to the smaller y, near
  the top, so "up" reads as "improving" — the opposite convention from every other chart on this
  page, called out explicitly in the code). Best-effort: any error or empty payload just hides the
  card instead of blocking the rest of the page.
- Verified against the owner's own real captured sample: the rendered numbers (#378 current,
  #320 best, #876 worst, #531.5 average) matched the reference screenshot exactly.

## v1.71.1 — Two real chart bugs: silent window compression, wrong date axis

Both found through the owner actually using v1.71.0, not through testing here.

**Bug 1 — a 7-day window rendering as if it were 2 days.** `renderChart()` filtered out `null`
values (days with insufficient traffic — Epic's own floor is 5+ unique players) *before* laying
out the x-axis, so when most days in the window had no data, the few real points got stretched to
fill the whole chart width. Owner report: "in the chart I only see two days even though it says 7,
is that right?". Fixed by keeping every point for layout purposes and grouping only *contiguous*
non-null runs for drawing, so a real gap now shows as a visible break in the line (or a lone dot)
instead of being silently absorbed into the axis.

**Bug 2 (deeper) — the axis itself was wrong.** Even after fixing bug 1, the x-axis still just
spanned however many entries the API happened to return for the window — and it turns out the API
*omits* days with insufficient data from the array entirely rather than padding them with `null`.
A real case (data on only 2 of the last 7 calendar days) rendered those 2 dates as if they were
"the 7-day window", while the actual current date was days later. Owner report (mid-session):
"it's giving me 12/09 and 13/9, today is 18/09". Fixed with a new `padToSevenDayGrid()` that builds a true
7-calendar-day grid ending at the browser's own "today" (UTC-date matched), mapping real points
onto it and leaving an explicit `null` for any day genuinely absent from the API's response — now
the single source of truth for "the window" used by both the KPI tiles and the chart. Verified
against a reproduction of the exact real scenario (data only on 2026-09-12/13, system date
2026-09-18).

## v1.71.0 — Real island stats: a "Stats" tab on the Agent Console, backed by the Fortnite Ecosystem API

New feature, requested after the two v1.70.5 bug fixes: a second page alongside the console,
showing the island's real performance data instead of pipeline/agent activity.

**Layout chosen after a 4-mockup review** (KPI row + a big chart with a metric selector — the
other three explored a small-multiples grid, a sidebar + single chart, and a record-strip +
normalized comparison chart, kept as reference but not built).

**Real API schema, not guessed.** Before writing any of this, `coder` was sent to make a real
call against `api.fortnite.com/ecosystem/v1` and capture the actual response — the public Swagger
page is JS-rendered and unreadable by an automated fetch, so this followed the kit's usual
real-payload-capture discipline instead of inventing field names. Confirmed: the API needs no API
key/OAuth despite `securitySchemes` listing one in its OpenAPI doc (unused by any actual
endpoint); the real path is `GET /islands/{code}/metrics/{interval}` (`day`/`hour`/`minute` as a
path segment, not a query param) with optional `from`/`to` ISO 8601 query params (7-day lookback
needs them passed explicitly — the default window is much shorter); field names are camelCase and
not 1:1 with the human labels (`recommendations`, not `recommends`; `averageMinutesPerPlayer`);
`retention` is a separate array shaped `{d1, d7, timestamp}`, not folded into the other metrics;
values can be `null` on a day with too little traffic (Epic's stated floor: 5+ unique players);
and a documented `429` exists for rate limiting with no published threshold.

**New/changed files:**
- `agent-console-stats.html` — the new page. Same design tokens as `agent-console.html` (this is
  a tab of the same console, not a separate product). Nine KPI tiles (the metric definitions
  above), click a tile to plot it in the chart below, real hover crosshair + tooltip snapping to
  the nearest day, a 7-day max badge per tile, and a friendly empty state when no island code is
  configured yet instead of a blank/broken page.
- `agent-console.html` — added a small Console/Stats view-switch pill in the header (a plain
  `<a href>`, not client-side routing — each view is its own static file on the same local
  server).
- `agent-console-server.py` / `agent-console-server.ps1` — two new endpoints: `/island-metrics`
  (proxies the 7-day daily-granularity call above) and `/island-info` (island title/tags, for the
  page header). Both cache server-side — 5 min for metrics, 1 hour for info, memory + a
  `Claude/logs/fortnite-*-cache.json` fallback file — so a page reload, or a real `429`, still
  shows the last good data instead of an empty page. `/stats` now serves the new HTML file the
  same way `/` serves the console.
- `Claude/docs/.island-code` — new per-project file, same pattern as `.active-task`: a single
  line with the island code (e.g. `1234-5678-9012`), read by both server scripts. Nothing writes
  this automatically yet — set it once per project and the Stats tab picks it up.

Verified with a mock local API server standing in for Epic's endpoint (network to the real one
isn't available from this dev sandbox): metric fetch, the 429-with-stale-cache fallback, and the
missing-island-code case all confirmed server-side; the actual page verified in a real browser via
Playwright against that mock server — KPI tiles, chart, hover tooltip, and switching the plotted
metric by clicking a different tile, zero console/page errors.

## v1.70.5 — Two real Agent Console bugs fixed: stale-entry misattribution, wrong task ID on the miniflow

Both surfaced from real usage after the open-source release, diagnosed locally with the exact log
evidence before any fix was written.

1. **Orphaned queue entries with no expiry corrupted attribution.** When a real `SubagentStop`
   event was lost (session crash/restart, or a phantom orchestrator-poll stop consuming it), the
   matching `start` entry in `agent-console-active.json` sat forever with no expiry. A real log
   capture showed a 7-day-old orphaned `qa-regression` start get "resumed" by the next real stop of
   that type, stamping a week-old description on the just-finished task — and when several such
   stale entries got auto-cleared together on a reload, they all showed the same timestamp, looking
   like a coincidence but actually just one replay tick. Fixed in both the PowerShell and bash hook
   pairs (`agent-console-log.ps1`/`.sh`, `agent-console-stop.ps1`/`.sh`): every queue entry now
   carries its own `ts`, and anything older than 45 minutes (same threshold as the client-side
   `STALE_ACTIVE_MS`) is pruned before a new entry is pushed or matched.

2. **The miniflow header showed the previous task's ID.** `.active-task` (written only by `coder`)
   and the miniflow's active stage (derived live from the `active` stack) are two independent
   sources. A task entering `intent-gate` — which runs before `coder` — advanced the stage
   immediately while the on-disk task-ID label stayed frozen on the previous task until `coder`
   eventually overwrote it, so the header could read e.g. "MINIFLOW — T-050" with `intent-gate`
   active while the real work was already on T-051. Fixed in `agent-console.html`:
   `resetMiniflowCycle()` now clears the task-ID label the instant a new cycle starts, instead of
   leaving the stale id visible until the next poll happens to catch up.

3. **macOS/Linux hook pair brought up to parity.** `agent-console-stop.sh` previously never read
   the `SubagentStop` payload at all — it blindly popped queue index 0, i.e. it still had the
   attribution bug the PowerShell side had already fixed in v1.69, on top of the orphaned-entry bug
   above. Rewritten to match the PowerShell logic (skip phantom/empty `agent_type` events, match the
   oldest queued entry of the same type, prune expired entries, serialize the queue read-modify-write
   with `flock` the way the PowerShell side uses a named Mutex). Verified with a real sandbox
   repro — phantom stop ignored, correct desc attributed with two agent types queued at once, and a
   1-hour-old orphaned entry correctly dropped rather than resumed — before shipping.

## v1.70.4 — Loud warning when launched from the wrong folder (silent hook failures, root cause of the last incident)

Root cause of the "logs stopped, console stopped animating" incident: the session had been
launched from the UEFN project's outer root instead of from inside `Content/`, where this kit's
scaffold actually lives. Every hook in `.claude/settings.json` builds its script path from
`CLAUDE_PROJECT_DIR`, so from the wrong folder every one of them points at a `Claude/hooks/` that
doesn't exist — they fail silently, one at a time, with nothing visibly wrong until you notice the
console is stale. The owner asked for a warning so this is caught immediately instead of
discovered later through cold logs.

**`session-start-reminder.ps1`/`.sh`** (fires on every fresh `claude` launch, matcher `"startup"`)
now checks, before anything else: if `Claude/hooks/agent-console.html` isn't found at
`CLAUDE_PROJECT_DIR` but IS found one level down at `Content/Claude/hooks/agent-console.html`,
that's this exact mistake — emit a loud, explicit `additionalContext` warning telling the owner,
in Claude's very first reply, to close the session and relaunch from inside `Content/`. This can't
silently fail the same way the thing it's warning about does: it only depends on `Test-Path`/
`[ -f ]` file checks, no server, no network call, so it still runs even when every other hook in
this file would be broken by the same wrong-folder mistake it's catching.

Tested directly (bash version): simulated both the wrong-folder case (warning fires, correct
`additionalContext` JSON) and the correct-folder case (no false positive, existing "console
started" message unaffected) — both confirmed via `bash -n` syntax check and running the script
with `CLAUDE_PROJECT_DIR` pointed at each location in turn.

## v1.70.3 — Migration/troubleshooting notes from real-world v1.70 upgrade feedback (root cause corrected)

Docs-only patch, no agent/console logic changed. Three things surfaced testing the v1.70 upgrade on
a real project:

1. **A stale `verse-reviewer` entry surfaced in the console after upgrading — root cause corrected.**
   First suspicion was a leftover `verse-reviewer.md` still installed in `~/.claude/agents/` (this
   kit only ever adds/updates agent files on copy, never deletes retired ones) — but the owner
   confirmed that file was already removed before this happened, so that wasn't it. The actual cause:
   `Claude/logs/agent-console.jsonl` **persists across restarts by design** (see
   `agent-console-server.py`'s own header comment — it's meant to keep activity history, not get
   wiped on every session). A `verse-reviewer` start event logged before the v1.69 rename, with no
   matching stop event, was still sitting in that file; the console's 45-minute stale-cleanup (see
   its own `STALE_ACTIVE_MS` check) surfaced and auto-cleared it exactly as designed — same as it
   would for any genuinely-abandoned entry. Nothing was broken and no fix was needed: it's expected,
   one-time noise from history predating the rename, not a recurring issue. **SETUP-GUIDE.md** Phase
   1 keeps its "delete agent files no longer on the roster before upgrading" step regardless — it's
   still good practice for the general case where an old file WOULD stay invokable — but it wasn't
   what caused this specific incident.
2. **`Content/Claude/docs/` vs `Claude/docs/` confusion.** Confirmed NOT a regression — this kit's
   scaffold has always lived inside the project's `Content/` folder by design (see SETUP-GUIDE
   section 1 and `project-template/CLAUDE.md`), so `Content/Claude/docs/STATUS.md` is the correct,
   intended path. A search from the wrong working directory (project root instead of `Content/`)
   will miss it — worth remembering when troubleshooting, not a path to fix.
3. **Two new troubleshooting entries added to SETUP-GUIDE.md's Agent Console section**: Claude
   Code's own permission prompt pausing before it starts the server / opens the console (this is
   Claude Code's standard tool-permission system reacting to a `Bash` command and/or a browser
   action, not something the kit or the console page itself triggers — approve it, or check
   `.claude/settings.json`'s `permissions` block if it keeps re-prompting every session instead of
   being allow-listed once), and a cosmetic mojibake in MCP log labels (`argumentsâ€¦` instead of
   `arguments…`, a UTF-8/Windows-1252 re-interpretation in `agent-console-mcp.ps1`'s truncation —
   harmless, the underlying event data is intact).

   *(Correction: an earlier draft of this note misattributed the permission prompt to a browser/OS
   security dialog — it's Claude Code's own permission system, corrected above.)*

## v1.70 — Bounded review cycles, fixed report contracts, a durable verdict log, cheaper models on structural-check agents

Follow-through on a "graph engineering" gap audit the owner asked for after sharing an article on
node/edge contracts, bounded cycles, and model tiering. The audit ran as six parallel evaluation
passes over the kit against those principles, then one synthesis pass; six things already matched
the vision (bounded-contract nodes, `.active-task` as a real data-contract edge, structural runtime
routing via CLEAR/AMBIGUOUS and PASS/REJECTED, independent verifiers on the review edges, no
unnecessary node isolation, pipeline-first topology). Seven trivial/low-effort gaps closed:

1. **Bounded REJECTED cycles.** The `intent-reviewer`/`compliance-reviewer` fix-and-resubmit loop
   had no attempt cap, unlike `coder`'s own compile-fix loop (capped at 5). Both reviewers and
   `coder.md` now share the same 5-consecutive-attempt cap: past that, stop, write the unresolved
   items to `Claude/docs/BUGS.md`, and ask the owner — exactly like a stuck compile error.
2. **Fixed report contract for closing a task.** `coder`'s hand-off to `planner-docs` was free
   prose ("a concise summary of what changed"). It's now a fixed shape: Task ID, Files/devices
   touched, both reviewers' verdicts with attempt numbers, second-brain interaction, one-line
   summary.
3. **Fixed output lines for `planner-docs`.** Both of its modes (opening a task, closing a task/
   end-of-session update) now report back in a fixed shape instead of freeform recap prose.
4. **Honesty fix in `compliance-reviewer`.** Two of its checks (naming/Outliner state, DemoDisplay
   stand positions) claimed "if MCP is available, verify live" — but its frontmatter tools are
   `Read, Grep, Glob` only, no MCP access at all. Reworded to check what's actually verifiable from
   files and explicitly say when a claim rests on `coder`'s report rather than independent
   confirmation, instead of implying a live check that can't happen.
5. **`.task-verdicts` (new durable log).** Both reviewers now append one line per verdict
   (`timestamp reviewer task-id verdict attempt-n`) to `Claude/docs/.task-verdicts`, append-only,
   same single-writer/independent-reader pattern as `.active-task`. `planner-docs` cross-checks it
   before marking a task Done, so "both reviewers PASSed" is independently checkable instead of
   resting on `coder`'s prose relay.
6. **Model tiering on structural-check agents.** `intent-gate` and `compliance-reviewer` moved from
   `sonnet` to `haiku` — both are bounded, checklist-shaped checks (ambiguity naming, mechanical
   rule conformance against a fixed list), not open-ended judgment calls, so a cheaper model fits
   the actual cost/latency lever the audit called out as underused. `intent-reviewer` (spec-adherence
   judgment) and `coder` stay on `sonnet`.

Deliberately not done this round, flagged instead for a separate decision: `codebase-auditor`'s
five audit lenses (structural, duplication, performance, maintainability, long-session risk) are a
genuine parallel fan-out/fan-in diamond currently run serially in prose — real opportunity, but
medium effort and an architecture change, proposed rather than applied unprompted. `release-gate`
and `planner-docs` model-tier changes were left alone too — lower-confidence, "pilot only" per the
audit's own caution, worth revisiting only after the two changes above are validated in practice.

No changes to `agent-console.html`'s JS logic — only its `KIT_VERSION` string was bumped to
`"v1.70"` to match; none of the fixes above touch the console's rendering or polling code, so the
full Playwright verification pass wasn't needed this round.

## v1.69 — Structural pipeline hardening: split the review gate, add intent-gate, a single MCP-tool source of truth, and a task-lock file; Agent Console miniflow rail

Follow-through on a flow audit the owner asked for after three separate incidents (v1.65-v1.67)
turned out to share one root cause: an agent judging its own readiness/correctness, or the same
instruction duplicated in prose across multiple files where it could quietly diverge. Four
structural changes, all confirmed by the owner, implemented together:

1. **`intent-gate` (new agent)** — runs BEFORE `coder` writes anything. Independently checks
   whether a task's acceptance criteria (and any owner-supplied base code) are concrete enough to
   implement without guessing, and returns CLEAR or AMBIGUOUS. Moves the "is this actually clear"
   judgment out of `coder`'s own Step 0.5 self-check and into an agent with no stake in getting to
   start the work.
2. **`verse-reviewer` split into `intent-reviewer` + `compliance-reviewer`.** `intent-reviewer`
   checks only spec adherence (the old check 1) and must PASS before `compliance-reviewer` — the
   eight mechanical checks (logger, naming, header, DemoDisplay, deprecated APIs, multiplayer
   authority, state machine, second-brain compliance) — is even invoked. This makes the ordering
   structural instead of a convention inside one agent's single-pass checklist: the incident this
   split responds to was a combined reviewer PASSing a guessed integration because spec adherence
   was one item among nine, not the precondition for the rest.
3. **`~/.claude/skills/mcp-tool-contracts/SKILL.md` (new skill)** — single source of truth for
   "which exact MCP tool does X," starting with the project-identity check
   (`ValkyrieToolset.VerseToolset.ListFiles`, not `AssetTools.find_assets`). `coder.md`,
   `qa-regression.md`, and `project-bootstrap.md` now reference this file by name instead of each
   restating the check in its own words — the exact pattern that let the v1.67 incident happen
   (the same generic instruction, worded slightly differently, in three places at once).
4. **`Claude/docs/.active-task` (new lightweight file)** — `coder` writes the task ID here when it
   flips a task to In progress; `intent-reviewer`/`compliance-reviewer` cross-check the ID `coder`
   reports against this file instead of trusting the report alone.

Agents removed: `verse-reviewer.md`. Agents added: `intent-gate.md`, `intent-reviewer.md`,
`compliance-reviewer.md`. Net: eleven → fourteen agent files installed (two new internal-helper
files were already excluded from that count; the public-facing roster goes from eleven to twelve
directly-invokable agents). Updated for the new gate names/order: `coder.md` (Step 0 writes
`.active-task`, new Step 0.4 invokes `intent-gate`, compliance gate now two sequential PASSes),
`planner-docs.md`, `release-gate.md`, `codebase-auditor.md`, `project-template/CLAUDE.md`,
`user-level-memory/CLAUDE.md` (new rule 13a), `docs-template/ROADMAP.md`, `SETUP-GUIDE.md`.

**Agent Console**: added a miniflow rail (the owner picked "V1" of three mockups presented) above
the orbit — a horizontal row of ring-progress nodes tracking where the CURRENT task sits in
intent-gate → coder → intent-reviewer → compliance-reviewer → planner-docs, derived purely from
the same `/log` event stream already driving the orbit (no new server plumbing required for the
rail itself). A stage shows a live mm:ss timer while active, and a small red "×N" badge if the
task was ever sent backward through it (detected as a regression: an earlier pipeline stage going
active again after a later one was already reached) — the one signal specifically meant to make it
visible, at a glance, when the review gates are actually catching something rather than rubber-
stamping. Added a best-effort `/active-task` endpoint to both `agent-console-server.py` and `.ps1`,
serving `Claude/docs/.active-task`'s content for the rail's task-ID label (the rail still works
fully without it). New node colors `indigo`/`lime` added (all ten previous slots were already
taken); `KIT_VERSION` bumped to v1.69; header text "ten agents"/"ten bots" → "twelve agents"/
"twelve bots". Verified: extracted `<script>` block passes `node --check`; scratch server + seeded
`agent-console.jsonl` + Playwright screenshot confirms the rail renders correctly mid-pipeline
(two stages done, one active with a live timer, task ID shown, zero `pageerror` events) before
cleanup.

## v1.68 — Added `codebase-auditor`: an independent, whole-codebase quality audit

Requested directly: an audit role independent from `coder` itself, styled as a senior developer
who just joined the team — understands architecture/data flow first, then hunts for structural
problems, duplicated code, performance bottlenecks, and maintainability risk, with a specific eye
on what only breaks after a long, uninterrupted play session (a growing collection never cleared,
event bindings stacking up round after round, per-player state never cleaned up on leave) rather
than what a short playtest would catch. Feeds findings to `planner-docs` to queue as ROADMAP
tasks instead of queuing them itself.

Added `user-level-agents/codebase-auditor.md` (model: sonnet). Deliberately distinct from what's
already in the kit: `verse-reviewer` gates one task's compliance right after `coder` finishes;
`qa-regression` hunts regressions from an actual play-session's logs; `project-bootstrap`'s A3
step is a one-time static pass before `SPEC.md` exists. `codebase-auditor` is the repeatable,
whole-codebase second opinion the owner runs on demand at any project stage — never writes code,
never touches devices or documentation files itself.

`planner-docs.md` updated: its task-opening procedure now explicitly covers a batch of findings
handed off from `codebase-auditor` (one ROADMAP task per finding worth tracking, small ones routed
to BUGS.md instead — `planner-docs` makes the final call, `codebase-auditor` only suggests).
`project-template/CLAUDE.md` and SETUP-GUIDE.md updated (ten agents now, install file count
eleven → twelve). Agent Console: new `codebase-auditor` node (🕵️), reusing `red` as a second
regular-node color (added a plain `.node[data-color="red"]` CSS rule alongside the existing
`.node.special[data-color="red"]` used by YOU — every other defined color was already assigned to
a different agent), `KIT_VERSION` bumped to v1.68, header text "nine agents"/"nine bots" → "ten
agents"/"ten bots". Verified with a scratch server + Playwright screenshot: zero `pageerror`
events, 10/10 idle, new node renders correctly on the shared ring.

## v1.67 — New uefn-lessons entry: use ValkyrieToolset.VerseToolset.ListFiles, not AssetTools.find_assets

Root-caused by the owner directly, on a case that had already needed a rollback: `coder.md`
only ever said, generically, "read/list a couple of Verse files or assets through the MCP tools"
for its project-identity safety check — it never named which toolset to use. `coder` picked
`AssetTools.find_assets` on `/Game`, the intuitive choice for "search for assets," without
knowing that in this kit's MCP/UEFN setup that path never surfaces the project's actual custom
content, even with the right project open — it fails silently (empty result, no error), which
reads exactly like "MCP has the wrong project open" and sends debugging in the wrong direction.
The owner verified directly that `ValkyrieToolset.VerseToolset.ListFiles` is the toolset that
actually works.

Added to `~/.claude/skills/uefn-lessons/SKILL.md` under "MCP / tooling quirks" — this is a
property of the MCP/UEFN configuration itself, not this one project, so it belongs in the shared
cross-project lessons file rather than per-project memory (same bar as every other entry there:
"would this help on a different island?"). Also fixed at the source in the three agents that ran
the same generic, toolset-unspecified safety check and would have hit the identical trap:
`coder.md`, `qa-regression.md`, and `project-bootstrap.md` all now name
`ValkyrieToolset.VerseToolset.ListFiles` explicitly and warn against `AssetTools.find_assets` for
this purpose, instead of leaving the toolset choice to intuition.

## v1.66 — No invention: coder must read/restate/ask, verse-reviewer must check the spec was followed

Reported directly, a concrete failure: the owner gave `coder` ready-made base code plus a spec to
integrate with an existing device; `coder` interpreted an unclear point instead of asking,
producing a wrong implementation that needed a rollback — and `verse-reviewer` PASSed it anyway,
because it was only checking rule mechanics (logger, naming, DemoDisplay), never whether the
implementation actually matched what was asked.

**`coder.md`** gains a new mandatory **Step 0.5 — Understand before you touch. Never invent,
never interpret.**: read an unfamiliar device's actual current implementation/config before
touching it (no more guessing from a device's name/type); treat a gap in the task's acceptance
criteria as a blocker to ask about, not a decision to make; when handed ready-made base code,
read it fully and restate the intended integration back to the owner in concrete terms before
editing anything; treat spec ambiguity with the same weight as an unresolvable compile error —
never proceed on a guess "to keep moving."

**`verse-reviewer.md`** gains a new check 1, **Spec adherence — no invention**, checked first,
before every mechanical rule: compares the implementation against the task's acceptance criteria
line by line, and treats a silently-interpreted ambiguity as a REJECTED finding even when the
resulting code is otherwise clean and every other rule passes — compliant code built on a guess
is still wrong. Its "Why this agent exists" section now documents this failure mode directly, and
its description/frontmatter lead with spec adherence instead of burying it among the mechanical
checks.

## v1.65 — Templates physically separated from live project data, safe to bulk-update

Asked directly: "can I overwrite the whole project folder to update everything, without losing
data?" The honest answer before this release was no — `project-template/Claude/docs/` held the
SPEC/STATUS/ROADMAP/BUGS/RETENTION-NOTES/RELEASE-READINESS templates at the *same path* a real
project's live, populated versions of those files live at, so re-copying `project-template/` over
an existing project (to pick up hook/agent fixes from a newer kit version) would have silently
wiped a project's entire tracked history — every task, every log entry, every bug.

Fixed by construction, not by a warning to remember: renamed `project-template/Claude/docs/` to
**`Claude/docs-template/`** (added its own `README.md` explaining it's a seed, never live data).
`Claude/SETUP-INSTRUCTIONS.md` gained step 3b: seed a brand-new project's real `Claude/docs/` from
`docs-template/`, but only if `Claude/docs/` doesn't already exist yet — every step in that file is
now explicitly documented as safe to re-run after an update. `project-template/CLAUDE.md` got a
header comment flagging it as a seed file too (it becomes the project's own live `CLAUDE.md`,
identity and conventions filled in, the first time Phase 2 runs).

Added a new **"Updating an existing project to a new kit version"** section in SETUP-GUIDE.md with
the exact two lists — update-safe (`Claude/hooks/`, `Claude/reference/`,
`Claude/SETUP-INSTRUCTIONS.md`, `Claude/docs-template/`, `.claude/settings.json`) vs. never-bulk-
copy (`Claude/docs/`, project-root `CLAUDE.md`, `Claude/logs/`, per-agent persistent memory) — plus
copy commands (`rsync`/`robocopy`) for the safe subset. This replaces answering "what do I update"
ad hoc after every release with a standing, mechanical procedure.

## v1.64 — Plan-first workflow: no code without a tracked, ID'd task

Requested directly, after a from-scratch project surfaced a bigger structural gap than any single
bug: nothing in the kit stopped `coder` from writing code before specs/status were updated, and
reopening a project after time away didn't make "what's in progress / what's next / what's done"
immediately obvious. This release restructures the documentation flow around one rule
(`~/.claude/CLAUDE.md`, new **rule 13**): every task is a row in `Claude/docs/ROADMAP.md`'s
`Tasks` table (ID, Feature, Status, Acceptance criteria, Priority) before any code gets written
against it, and it's only marked **Done** after `verse-reviewer` PASSes it.

**Orchestrator decision (asked for explicitly, decided against a new agent):** the alternative
considered was a dedicated `orchestrator` subagent enforcing Request → task → code → review →
close. Rejected: a Task-tool subagent is a stateless dispatch, not a supervisor of the main
session's own tool-call sequence — it can't actually intercept "coder is about to start without a
task" from outside. The main Claude Code session already *is* the orchestrator; what it needed
was an unambiguous rule loaded into every session (rule 13) plus `planner-docs` actually enforcing
it as gatekeeper — not one more hand-off hop, which would have worked against this same release's
other goal of cutting down on loops.

**Templates rewritten**: `ROADMAP.md` now has a `Tasks` table plus a "Current MVP / release
target" line `release-gate` reads. `STATUS.md` now opens with a **Current state** block (In
progress / Planned next / Done so far / Recommended next step) that's replaced on every update,
sitting above the existing append-only dated log.

**Agents updated**: `coder` gets a mandatory Step 0 plan-first gate (find the task ID or stop and
ask; flip Status to In progress itself — the one narrow exception to not touching ROADMAP.md — never
Done) and now closes a task by handing off to `planner-docs` after a `verse-reviewer` PASS,
instead of just reporting done. `coder-prep` explicitly never touches these files at all — the
gate and the closing hand-off are `coder`'s job once per wave. `planner-docs` is rewritten as the
two-mode gatekeeper (opening a task / closing one) instead of an end-of-session-only recap agent.
`verse-reviewer` now expects and reports a task ID for traceability. `release-gate` gets an
explicit ROADMAP-completeness criterion (every current-release task Done, and Done tasks
actually backed by a recorded PASS). `project-bootstrap` (both branches) now seeds real `T-<3
digits>` tasks with acceptance criteria instead of a prose "planned features" list or a vague
"next step" line.

**Skills reviewed against the new flow**: all sixteen (`uefn-lessons`, `verse-patterns`,
`uefn-device-gotchas`, `performance-uefn-checklist`, `discover-retention`, `second-brain-query`,
`token-aware-coding`, `brand-collections-uefn`, the eight `fortnite-*`) — none contradicted
plan-first (none of them touch ROADMAP/STATUS or tell an agent to start coding directly), so only
one needed a change: `token-aware-coding` gained a line about grepping one task row instead of
reading the whole ROADMAP.md once it grows across releases. Deliberately did NOT add a padding
entry to `uefn-lessons` just to check a box — this release's gap was process, not a Verse/UEFN/MCP
gotcha, and that skill's own stated bar ("would this help on a different island?") doesn't apply
to something documented directly in rule 13 instead.

`project-template/CLAUDE.md`'s per-project rules list and `SETUP-GUIDE.md` (new section **2b**,
with a full worked example of a feature request end to end) updated to match.

## v1.63 — Added `verse-reviewer`, a compliance gate before a task counts as done

Reported directly by the owner on a from-scratch project: devices shipped without the mandatory
logger, devices with class/configuration problems because the second brain was never consulted,
and reusable patterns that only ever reached a project's own memory instead of the shared vault.
Nothing in the kit caught this — `qa-regression` looks for runtime/gameplay regressions at
playtest, not rule conformance right after a task; `release-gate` looks at whole-project
readiness before a release, not one task right after it's written.

Added `user-level-agents/verse-reviewer.md` (model: sonnet) — the functional-analyst role: never
writes code or touches devices, only checks `coder`'s own output against this kit's mandatory
rules (logger, naming/organization, `DemoDisplay` presence and accuracy, deprecated APIs,
multiplayer authority, state machine) and, when the second brain is configured, cross-checks in
query mode whether a reusable pattern actually reached the vault instead of only living in project
memory. Returns PASS or an itemized REJECTED list; `coder` fixes and resubmits.

`coder.md` updated with a mandatory compliance gate: before reporting any task done, invoke
`verse-reviewer` and only report "done" after a PASS — for a `coder-prep` wave, this runs once for
the whole wave, same reasoning as the existing single-writer second-brain handoff. This keeps the
kit's "one agent owns the task" rule intact: `coder` is still sole owner of implementation and of
deciding when work is finished, it just no longer grades its own compliance.

Also updated: `project-template/CLAUDE.md`'s per-project agent rules list; SETUP-GUIDE.md (agent
count seven→eight→nine across this and the prior two releases, install file count ten→eleven,
section 2's roster); and the Agent Console — new `verse-reviewer` node (🛡️, a new `yellow`
regular-node color variant added to CSS since every other defined color was already assigned),
`KIT_VERSION` bumped to v1.63, header text "eight agents" → "nine agents"/"nine bots". Verified
with a scratch server + Playwright screenshot: zero `pageerror` events, 9/9 idle, new node
renders correctly on the shared ring.

## v1.62 — `fortnite-title-description` rebuilt into a full publishing package

Rebuilt `fortnite-title-description` per direct spec from the owner: it now produces the whole
Discover publishing package in one pass — Title (max 40 characters), Description (max 500
characters), one Main genre proposal, 4 Discover tags, and 3 how-to-play instruction lines (max
150 characters each) — everything in English, with explicit instructions to actually count
characters per field (and show the count, e.g. "37/40") rather than estimate or truncate
mid-sentence to fit. Added a second, distinct deliverable — the **community blog presentation**
(an extended description and a short one), aimed explicitly at getting readers to go play, in
whatever language the owner asks for (the five publishing fields stay English regardless).
Updated `growth-manager.md` and `SETUP-GUIDE.md` section 3e's description of this skill to match
the new scope.

## v1.61 — Agent Console updated for growth-manager

Caught by the owner asking directly ("did you update the console too?") after v1.59 added the
`growth-manager` agent without touching `agent-console.html` — it was still showing the old
seven-agent roster. Added `growth-manager` to the `AGENTS` array (📈, orange — the one color slot
already defined in CSS but unused by any agent), bumped `KIT_VERSION` to v1.61, and updated the
static "seven agents"/"seven bots" header text to eight. Nothing else needed changing: node
layout, angle spacing, and the legend/footer counts all derive from `AGENTS.length` dynamically
(confirmed in code, no hardcoded "7" anywhere else), so the new node slotted in on the shared ring
automatically. Verified with a scratch server + Playwright screenshot against a throwaway copy of
`project-template` — zero `pageerror` events, new node renders correctly at 8/8 idle.

## v1.60 — Confirmed thumbnails now get installed into the project (Resources/ + keyArt)

Requested directly: once a thumbnail from `fortnite-thumbnail-pro` is confirmed, it needs to
land in the project itself, not just be handed over as an image. Added
`references/install-thumbnail.md` to `fortnite-thumbnail-pro` with the exact procedure: create
`Resources/` at the project root if missing (the root is the folder that *contains* `Content/`,
named per `CLAUDE.md`'s "Project identity" — never the current folder, always literally
`Content`), save the confirmed file there, and update the `"keyArt"` key in
`<ProjectName>.uefnproject` (also at the project root) to point at it, e.g.
`"keyArt": "Resources/Thumbnail.png"` — editing only that key, not reformatting the rest of the
JSON. `growth-manager` (v1.59) now owns actually doing this when a thumbnail is confirmed
through it. This is a deliberate, narrow exception to the kit's standing "no agent touches files
outside `Content/`" rule, called out explicitly both in `growth-manager.md` and in
`project-template/CLAUDE.md`'s per-project rules list, scoped to exactly `Resources/` and the
`keyArt` key — nothing else at the project root.

## v1.59 — Added `growth-manager`, a dedicated agent for the eight marketing skills

v1.58 added the eight `fortnite-*` growth/marketing skills but left them relying entirely on
Claude Code's own description-based matching, with no agent owning them — inconsistent with
every other skill-cluster in the kit (`coder` reads `verse-patterns`, `project-bootstrap` reads
`discover-retention`/`brand-collections-uefn`, etc.). Added `user-level-agents/growth-manager.md`
(model: sonnet) as the dedicated owner: a single entry point the owner can talk to in plain
language, which routes to the matching `fortnite-*` skill(s) — one for most requests, several in
sequence for a full launch push — instead of the owner needing to know or name any of the eight
skills. It explicitly stays out of Verse/device work (that's `coder`) and doesn't write
`STATUS.md`/`ROADMAP.md`/`BUGS.md` itself (that's `planner-docs`) — it summarizes for
`planner-docs` instead when something it produced should be recorded there. SETUP-GUIDE.md
updated: agent count (seven → eight agents, section 2), Phase 1 install file count (nine → ten,
section 5), and section 3e rewritten to describe `growth-manager` as the normal way to reach
these skills, with direct skill-matching/naming kept as a fallback.

## v1.58 — Added eight growth/marketing skills (analytics, competitors, launch, retention, trailer, thumbnail, title/description, update writer)

The kit so far only covered building the island (`coder`, `qa-regression`, and the dev-side
`user-level-skills/`). Added eight new skills under `user-level-skills/fortnite-*` covering the
other half of running a map: `fortnite-analytics-coach` (Creator Portal + public-tracker
analysis), `fortnite-competitor-analyzer` (genre/competitor research), `fortnite-marketing-launch`
(launch/growth plans), `fortnite-retention-gamedesign` (session-length/retention game design),
`fortnite-social-trailer` (trailer scripts, TikTok/Shorts hooks), `fortnite-thumbnail-pro`
(high-CTR thumbnail concepts + prompts), `fortnite-title-description` (Discover-optimized
titles/descriptions), and `fortnite-update-writer` (patch notes/announcements).

Unlike the dev-side skills, none of these are read by a fixed step in an agent — there's no
"marketing agent" in this kit to dispatch them from. They rely on Claude Code's own
description-based skill selection instead (same mechanism as `discover-retention` and
`brand-collections-uefn`), so SETUP-GUIDE.md's new section 3e is explicit about how to fall back
to naming the skill directly ("use the fortnite-thumbnail-pro skill") if a request doesn't get
matched automatically. Install step in Phase 1 (section 5) updated to include all eight folders.

## v1.57 — Fixed the footer line disagreeing with the "Agents" legend box

Found immediately after checking the new v1.56 version tag actually worked — it did (confirmed
"v1.56" in the screenshot), but the footer sentence at the bottom of the ring ("1 working, 6
idle...") and the "Agents" legend box at the top ("working 0, broken 1") disagreed about the
exact same agent at the exact same moment.

- **Root cause**: the footer line had its own much older, separate counting logic
  (`activeCount = active.length`) left over from before the broken/waiting distinction existed —
  it only ever knew "in the active stack" vs. "not," with no idea an entry could be flagged
  broken or waiting. The legend box's newer four-state logic was never wired back into it.
- **Fix**: extracted the legend's counting logic into one shared `computeAgentCounts()`, now used
  by both the legend box and the footer line. The footer's wording adapts too — it stays the
  familiar "N working, M idle" when nothing's flagged, and adds "broken"/"waiting" segments only
  when their count is above zero, so it doesn't get more cluttered than it needs to be on a
  normal day.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  20-minute-old `coder` call (well past the 15-minute broken threshold) now shows "0 working, 1
  broken, 6 idle" in BOTH the footer and the legend box.
- `KIT_VERSION` bumped to v1.57.

## v1.56 — Version tag next to the title, to kill a whole class of "did the fix actually apply" confusion

Prompted directly by the last two rounds of troubleshooting in this changelog: a real fix (v1.55)
looked like it hadn't worked, and the actual cause was almost certainly a browser tab left open
from before the file was replaced — this is a single-page app, so a tab doesn't notice its own
HTML file changing on disk until it's reloaded.

- **New `KIT_VERSION` constant** near the top of the page's script, rendered as a small tag right
  after the title (e.g. "v1.56"). Checking it is now the first troubleshooting step: if it still
  shows an old version after replacing the file, the fix is a hard refresh (Ctrl/Cmd+Shift+R), not
  more debugging of the actual feature.
- **This constant must be bumped on every release that touches `agent-console.html`**, matching
  `CHANGELOG.md`'s top heading — said plainly in a comment right above the constant itself as a
  standing reminder, since the whole point only holds if it never drifts out of sync.
- `SETUP-GUIDE.md` updated with a matching troubleshooting note, right at the top of the Agent
  Console section where it'll actually get read before someone goes looking for a phantom bug.
- Verified with the same headless-browser screenshot test as previous releases: confirms the tag
  renders next to the title with no layout shift and no JS errors.

## v1.55 — Auto-clear thresholds were too aggressive for real long-running background work

Found immediately after v1.54, from another live report on the same pre-fix session: the console
showed ALL agents idle while Claude Code's own session view confirmed two real `coder` calls
genuinely still running (9m49s and 25m8s, both climbing) — worse than v1.54's "broken"
misattribution, since now it looked like nothing was happening at all. Root cause: the hard
auto-clear (`STALE_ACTIVE_MS`, 20 minutes) force-removed both entries from tracking entirely, and
the log showed "⚠ auto-cleared 'coder' — no stop event arrived after 20 min" twice at the same
timestamp. Both thresholds were tuned for an older, more conservative assumption about how long a
subagent call normally runs — one this kit's own new parallel-work features (`coder-prep`,
`second-brain-trainer`'s waves, background `coder` calls) have since made outdated:

- **`STALE_ACTIVE_MS` raised from 20 to 45 minutes.** Still a real safety net for a truly
  orphaned entry (a lost `SubagentStop`), just far less likely to fire on legitimate long
  background work.
- **`LED_SOFT_WARN_MS` raised from 6 to 15 minutes**, same reasoning — 6 minutes was flagging
  completely normal memory-heavy reads as "broken" far too eagerly.
- **Real bug fixed in the auto-clear loop itself**: it force-marked a card idle unconditionally,
  without checking whether another concurrent call to the same agent id (see v1.54's "×N" badge)
  was still legitimately active — so clearing one stale sibling could wrongly hide a fresh,
  genuinely-running one. Now uses the same "only if no sibling remains" guard the normal
  stop-event path already used.
- Auto-clear log message updated to say plainly that it does NOT necessarily mean anything broke.
- Verified with the same headless-browser screenshot test as previous releases, this time
  replaying the exact reported timestamps (one `coder` call 25m8s old, one 9m49s old): both now
  correctly show "working ×2" instead of being cleared to idle.

## v1.54 — Fixed a real status-misattribution bug for concurrent same-agent calls, added a "×N" concurrency badge

Found from a live report: the console showed "1 broken" while two real `coder` calls were
running at once (one ~14 minutes old in the background, one fresh) — and the owner couldn't tell
who the second one even was, since the ring only ever showed one `coder` card.

- **Real bug fixed**: `refreshLeds()` and `updateLegendCounts()` both used `Array.find()` to look
  up a named agent's current activity in the `active` stack — which returns the FIRST matching
  entry, i.e. the OLDEST of any concurrent same-id calls. So the card's "broken" (stuck/overdue)
  check was silently keyed off however long the oldest concurrent instance had been running, even
  while a much fresher call to the same agent was the one actually active — exactly what produced
  "1 broken" while the fresh `coder` call was working normally. New `latestEntryFor()` uses the
  MOST RECENT matching entry instead, so the card reflects what's actually current.
- **New "×N" concurrency badge**, via `getConcurrency()`: when 2+ concurrent calls to the same
  named agent share one card (unavoidable — Claude Code gives no per-call id to split them), the
  card now visibly says so instead of the second (or third) instance being entirely invisible.
- **Documented, not fixed (can't be, with the data available)**: which exact stop event pairs
  with which concurrent start is inherently ambiguous without a real call-stack id — the console
  assumes first-started/first-finished (FIFO), a reasonable default, not a guarantee.
  `SETUP-GUIDE.md` now says this plainly, alongside a direct answer to "should broken agents get
  killed": the console is read-only telemetry, it has no way to stop/cancel/kill anything — a
  stuck call has to be handled at the Claude Code session level itself.
- Verified with the same headless-browser screenshot test as previous releases: two synthetic
  concurrent `coder` starts (one 14 minutes old, one fresh) confirm "working 1, broken 0" (was
  "broken 1" before the fix) and the "×2" badge on the shared card.

## v1.53 — Generic "fork" clones now get a "<parent> clone" label and disappear when done

Prompted by the owner spotting a plain "fork" node in the console after `coder` spawned a
background clone, and asking for two things: make it obviously coder's own child, and have it
leave the ring once it's finished instead of sitting there idle forever.

- **New `KNOWN_IDS`/`ephemeralIds` tracking.** The fixed roster (seven bots, Vault, YOU, MCP) is
  captured once at init; anything NOT in it — a generic `subagent_type: "fork"` dispatch being the
  common case — is now treated as ephemeral.
- **`ensureNode()` now takes the parent id** (whoever was on top of the active stack when the
  fork started — the same heuristic `pulseLink()` already used for handoff pulses). An ephemeral
  node gets a 🧬 icon, the parent's own color, a "\<parent name\> clone" label instead of the raw
  `"fork"` string, and its spoke now points at the parent instead of at the hub.
- **New `removeEphemeralNode()`**, called from `setIdle()` instead of the normal idle-in-place
  path whenever the node is ephemeral: removes the DOM node, its spoke, and every tracking
  structure it was registered in (`nodeEls`, `spokeEls`, `counts`, `BLURBS`,
  `SPOKE_TARGET_OVERRIDE`, `ALL_NODES`), then re-runs `recomputeAngles()` so the ring closes the
  gap immediately instead of leaving a dead idle slot.
- Known remaining limitation, unchanged: `subagent_type` is still the only id Claude Code reports
  for a fork, so two genuinely concurrent forks under the same parent still share one node — this
  matters far less now that a single fork (the common case) behaves correctly and cleans up after
  itself.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  `coder` → `fork` start/stop sequence confirms the "coder clone" label, parent-colored spoke, and
  full removal from the ring on stop, with zero JS errors.

## v1.52 — `coder` can now parallelize across independent devices/areas, via a new `coder-prep` helper

Prompted by the owner asking why `coder` stayed one-device-at-a-time even on tasks that obviously
split into unrelated pieces. The real reason: UEFN exposes exactly one MCP server per editor,
serving whichever project is open, and a Verse compile is a whole-project build, not an isolated
per-file one — two concurrent device placements or compiles wouldn't fail safely, they'd race
against that one shared live editor state. That part was never going to be safe to parallelize.
But most of `coder`'s actual time/cost per device is the part BEFORE any MCP call — reading
context, writing the Verse itself — and for genuinely independent areas, that part has nothing
shared to race against:

- **New agent**: `user-level-agents/coder-prep.md` — `model: sonnet` (real implementation work,
  not a lightweight scan, so no model downgrade here unlike `second-brain-scout`). Writes the
  actual Verse for ONE area, following every one of `coder`'s own conventions, but never touches
  MCP and never compiles — it reports back exactly what needs placing/configuring so `coder` can
  apply it afterward.
- **`coder.md`** gained a new "Splitting work across genuinely independent devices/areas" section:
  when a task splits cleanly, dispatch one `coder-prep` per area in parallel (capped ~6-8 per
  wave, same as `second-brain-trainer`), then apply every area's plan yourself, serially — MCP
  placement, `DemoDisplay`, compile-fix loop, one area at a time. Second-brain handoffs from the
  wave get combined into a single `second-brain-librarian` call at the end, same single-writer
  discipline as `second-brain-trainer` already uses. Skip all of this for a task that isn't
  genuinely independent-by-area, or one too small to be worth splitting.
- Nine agent files to install now, not eight — `SETUP-GUIDE.md` updated (install step, agent
  list, and a new explainer paragraph in section 3c). `coder-prep` doesn't get its own Agent
  Console node any more than `second-brain-scout` does — the console's existing fallback-node
  logic for an unrecognized `agent_type` already covers it.

## v1.51 — Documented the community `obsidian-skills` Claude Code plugin as an optional pairing

Not a kit feature — a documentation-only addition, at the owner's request, pointing to a
community Claude Code plugin marketplace worth knowing about if you spend time in the second-brain
vault yourself:

- **`second-brain-template/README.md`**: new step 5 in "Set up the vault (once)" — installing the
  `obsidian-skills` marketplace (by kepano, an Obsidian team member) teaches Claude Code better
  Obsidian-specific conventions (formatting, linking, front matter) on top of whatever
  `second-brain-librarian` already does. Explicitly marked as independent of this kit — not
  shipped or maintained by it, just a good pairing.
- **`SETUP-GUIDE.md`**, Phase 1 step 7 (connect an Obsidian second brain): same note added as a
  final optional bullet, with the same two commands:
  ```
  /plugin marketplace add kepano/obsidian-skills
  /plugin install obsidian@obsidian-skills
  ```

## v1.50 — Project name in the Agents stat box, and a real hub-LED gap fixed

Requested addition plus a real logic gap the owner spotted from a live screenshot (MCP Server node
glowing "working" while the Chief of Staff hub sat grey):

- **Project name in the "Agents" stat box.** A new line, "PROJECT: <name>", now sits above the
  agent-count/legend rows in that box — same project name `pollWhoami()` already fetches for the
  Activity Log panel's header, just also shown here since that box is more prominent.
- **Chief of Staff hub LED gap fixed.** The hub's own LED used to go green ONLY when a subagent
  was in the `active` stack (`active.length > 0`) — so when the main session did something
  directly without delegating to a subagent (e.g. calling the UEFN MCP server itself), the hub
  stayed grey/idle even though it was genuinely working, which is exactly what a live screenshot
  showed (MCP Server node glowing "working", hub LED grey). The hub LED now also turns green
  whenever the main session itself is active, via the same `/session` polling that already drives
  the YOU node's LED (`sessionActive`, kept in sync by `pollSession()`, consumed by
  `refreshLeds()`); `pollSession()` now also calls `refreshLeds()` immediately instead of waiting
  up to a second for the next tick.
- The YOU node's own LED was already correctly session-driven (green while the main session is
  actively working, grey once it's yielded back to you) — audited per the owner's request, no
  change needed there.
- Verified with the same headless-browser screenshot test as previous releases, this time seeding
  a synthetic `agent-console-session.json` with `active:true` and zero running subagents to
  confirm both YOU and the hub go green together in that specific case.

## v1.49 — New `second-brain-scout` helper: cheaper-model clones for second-brain-trainer's parallel analysis

Prompted by a real "Claude usage" report showing 38% of usage coming from unnamed/"fork" subagent
dispatches — almost certainly `second-brain-trainer`'s own parallel analysis clones, which
previously ran as generic unnamed Task dispatches (inheriting the session's default model, e.g.
Sonnet) with no way to configure them more cheaply, since a model override in this kit's design
only applies to a NAMED custom agent (one with its own `model:` frontmatter field), not a
generic/unnamed clone:

- **New agent**: `user-level-agents/second-brain-scout.md` — `model: haiku`. Analyzes exactly one
  project area, read-only, no vault access at all, and reports candidate reusable patterns in the
  same format the old generic clones used. You never invoke it yourself.
- **`second-brain-trainer` Step 2 updated** to dispatch `second-brain-scout` (one per area, per
  wave, still genuinely parallel) instead of a generic/unnamed clone — same behavior and output
  format, cheaper model for a step that's read-only and low-judgment by design.
- Eight agent files to install now, not seven (`SETUP-GUIDE.md` updated) — `second-brain-scout`
  doesn't count toward the kit's "seven agents" branding since it only ever runs as
  `second-brain-trainer`'s own dispatch, never on its own; it doesn't get an Agent Console node of
  its own either — the console's existing fallback-node logic for an unrecognized `agent_type`
  already covers it with no console changes needed.
- Also recommended to the owner, not kit changes: `/compact` mid-task and `/clear` between
  unrelated tasks (65% of usage came from >150k-context sessions), and disabling the `unreal-mcp`
  server when not actively playtesting (39% of usage) — MCP tool results stay in context for the
  rest of the session.

## v1.48 — Reverted the second ring: Obsidian Vault, YOU and MCP Server now share one ring with the bots

The v1.45 "second, further-out ring" for Obsidian Vault/YOU/MCP Server didn't land well visually
— reverted. All ten nodes (seven bots + the three special ones) now orbit on a single shared
ring at one radius, with one dashed guide circle instead of two:

- `OUTER_RING_IDS` and the separate outer-radius/second-guide-circle logic are gone from
  `layoutOrbit()`; every node uses the same `radius` (`halfDim * 0.72`, slightly larger than the
  old inner-ring radius since it's now the only ring).
- `recomputeAngles()` still special-cases Obsidian Vault's own angle — it's placed at the angular
  midpoint between `second-brain-librarian` and `second-brain-trainer` (the v1.47 fix, kept),
  it's just that midpoint is now a slot on the *one* ring instead of a separate outer one. Every
  other node (the six remaining bots, YOU, MCP Server) is spaced evenly around the rest of the
  circle in array order, and the Vault simply slots into the gap between its two second-brain
  neighbors without disturbing anyone else.
- Verified with the same headless-browser screenshot test used for the last few releases —
  confirms all ten nodes on one ring, Vault still between its two second-brain neighbors.

## v1.47 — Obsidian Vault repositioned between its two second-brain agents

Small but requested fix to `recomputeAngles()`: the outer ring used to space Obsidian Vault, YOU,
and MCP Server evenly by array order alone, which happened to land the Vault right next to
`project-bootstrap` — visually unrelated to it. The Vault is now placed at the angular midpoint
between `second-brain-librarian` and `second-brain-trainer` on the inner ring (the two agents it
actually draws spokes to and reacts to), computed via the shortest arc between their two angles;
YOU and MCP Server are then spaced evenly around the rest of the circle relative to that fixed
Vault angle, so nothing else shifts if more inner-ring agents are ever added. Verified with the
same headless-browser screenshot test used for the last two releases.

## v1.46 — Agent Console header/layout compaction: merged title row, new agent status legend, matched panel heights

Requested space-saving pass on `agent-console.html`'s header and layout, live-tested with the same
headless-browser + synthetic-event pattern used for v1.45 before packaging:

- **Merged header row.** The tagline ("seven agents. one chief of staff...") and the connection
  status line used to sit stacked below the title as two extra rows; they now sit to the right of
  the title on the same row (`.termlines` is a single flex row, `.termlines-side` stacks them
  right-aligned) — recovers two lines of vertical space.
- **Title changed to all-caps**: "DREAM BOT TEAM AGENT CONSOLE FOR UEFN" (title bar and `<title>`
  tag both updated; the blinking `_` cursor is kept).
- **Removed the decorative `.termbar`** (the three macOS-style red/yellow/green window-chrome
  dots) — recovers a third line. Those exact three colors aren't wasted: they're reused as the
  semantic colors in the new legend below (plus grey for idle).
- **Tokens stat box narrowed** (`.stat.compact`, `flex:0.65`) — it's a single number, it didn't
  need as much room as the other stat boxes.
- **New "Agents" stat box.** Shows the total agent count (7) plus a live idle/working/broken/
  waiting breakdown with a colored-dot legend (grey=idle, green=working, red=broken,
  yellow=waiting), computed by a new `updateLegendCounts()` call inside `refreshLeds()` so the
  numbers and the individual node LEDs can never disagree.
- **Four-state LED model.** The node LED heuristic used to have three states (idle / active /
  waiting, with "waiting" rendered red for both "blocked on a delegated child" and "stuck /
  running suspiciously long"). Those two very different meanings are now split: **yellow** =
  blocked waiting on a delegated child (not top of the active stack), **red** = the top-of-stack
  entry itself has been running past `LED_SOFT_WARN_MS` (likely stuck/erroring — "broken"). Green
  (working) and grey (idle) are unchanged.
- **Activity Log panel height now matches the orbit-ring panel.** `.main-grid` switched from
  `align-items:start` to `align-items:stretch`, and `.orbit-wrap` centers its ring vertically in
  whatever extra room that leaves — previously the two side-by-side panels could end up visibly
  different heights.

## v1.45 — Agent Console visual pass: second ring, vault "contested" effect, bot rays, regression missiles, fountains, project name

A full set of requested visual additions to `agent-console.html`, live-tested with a headless
browser (screenshots + a synthetic event stream) before packaging:

- **Second virtual ring.** Obsidian Vault, YOU, and MCP Server now orbit on a further-out ring
  (`OUTER_RING_IDS`), visually separate from the seven working-bot agents on the inner ring — a
  faint dashed guide circle marks each ring. `recomputeAngles()` now spaces the two rings
  independently so a node added to one never crowds the other.
- **Obsidian Vault "connected to both brains."** The vault now draws two spokes — one to
  `second-brain-librarian` (purple, existing), one to `second-brain-trainer` (new, teal) — and
  pulses (`vaultPulse`) whenever either is active, with a stronger oscillating "tug" animation
  (`.contested`, `vaultContested`) when BOTH are active at once, as if pulled from two directions.
  A floating "💭 Thinking" indicator with an animated ellipsis shows above it while active.
- **Bot ray bursts.** Every inner-ring agent gets a small, colored ripple-ring burst around its
  own icon while active (`.node-ray`) — the same idea as the hub's own ripple, scaled down and
  colored per-agent, so a working bot visibly radiates too, just far less dramatically.
- **Regression missiles.** When a `qa-regression` stop event's own description matches
  `/regression/i` (optionally with a count, e.g. "3 regressions" → up to 4 staggered launches), a
  small 🚀 flies from `qa-regression` to `coder` along an arced path and ends in a mini particle
  explosion (`spawnExplosion`) on arrival.
- **Fountains.** Obsidian Vault spawns a small stream of 💎 while active; `planner-docs` spawns a
  small stream of 📄 while active — both plain arc-and-fade particles (`spawnFountainParticle`),
  keyed by node id so start/stop is idempotent.
- **Project name in the activity log panel.** The right-hand panel's title now shows "📁
  <project folder name>" (from `/whoami`'s `project` field, already polled for the Session-running
  timer) so it's obvious at a glance which project's console you're looking at.
- Footer explanation text rewritten to document all of the above.

## v1.44 — Fixed "Session running for" showing hours/days right after a genuine server restart

Real bug, found from a live report ("the server isn't being restarted... it's been up 5 hours!!")
that turned out to be a display problem, not a restart problem — the v1.40 kill+restart mechanism
was working correctly, but the console's own "Session running for" stat made it look otherwise:

- **Root cause**: that stat was computed client-side from the OLDEST line in
  `Claude/logs/agent-console.jsonl`. That file deliberately persists across server
  restarts/sessions (it's the activity history — "delete it for a clean slate" is documented,
  intentional behavior). So once you'd used the kit across a few sessions, the stat kept showing
  hours/days of elapsed time no matter how recently the server had actually restarted — it was
  reading accumulated history, not server uptime.
- **Fix**: `agent-console-server.ps1`/`.py` now record their own real process-start time at
  launch and serve it from `/whoami` as a new `started_at` field (alongside the existing
  `project` field from v1.40). The console page polls `/whoami` every 5 seconds and prefers that
  real start time for "Session running for" — it now genuinely resets to zero the moment the
  server restarts, and also self-corrects mid-session if the server underneath the open tab gets
  restarted (project switch, kit update). Falls back to the old earliest-log-line behavior only
  against a server build that predates the `started_at` field, so an old server + new page combo
  degrades gracefully instead of showing nothing.
- `agent-console.jsonl`'s own persistence is untouched — this only changes what feeds the timer
  stat, not the activity log/history.
- SETUP-GUIDE.md's "Session timer" paragraph rewritten, plus a new troubleshooting entry for
  exactly this symptom.

## v1.43 — Console auto-opens in the browser; new brand-collections-uefn skill; console diagnostics confirmed clean

Three things landed together, per the owner's request to batch them into one update after two
rounds of diagnostics:

- **Console diagnostics: no code bugs found, only documentation gaps.** A live payload capture
  confirmed the console's "fork" background-agent dispatch (`● fork(...)` in the transcript) was
  already correctly tracked all along — it's the same `Agent`/`Task` tool the console already
  listens for, just with `subagent_type: "fork"`, not a different tool name needing a matcher
  fix. The only real finding: every fork shares one generic fallback node (🤖) instead of one per
  task, because the fallback keys off `subagent_type`, identical for every fork regardless of what
  each one does — a deliberate limitation of the generic-node mechanism, not a bug. Documented in
  SETUP-GUIDE.md's troubleshooting section instead of leaving it implying a matcher fix was
  needed. Likewise, the v1.40 stale-cross-project-server fix was independently re-confirmed
  working exactly as designed (kill+restart via `/whoami` happens automatically, before Claude's
  first reply) — the only gap was that nothing opened a browser tab, which is the next item.
- **The console now opens itself in your default browser, automatically, every session** — an
  explicit owner preference (previously the hook only started the server and mentioned the URL,
  leaving opening the tab up to you). `session-start-reminder.ps1` uses `Start-Process`; `.sh`
  tries `open` (macOS) then `xdg-open` (Linux), doing nothing on a headless box rather than
  failing the hook. `CLAUDE.md`'s fallback section and `.claude/settings.json`'s comment updated
  to match.
- **New optional skill: `brand-collections-uefn`.** Recognizes which official Fortnite Game
  Collection (brand island — TMNT, LEGO, Fall Guys, Star Wars, KPop Demon Hunters, Squid Game,
  The Walking Dead Universe, Rocket Racing) a project is built on, from real Content Browser
  folder names, device classes, and template names — not guesswork. Ships with a marker table
  researched directly from Epic's own Game Collections documentation: strong, confirmed technical
  markers for TMNT/LEGO/Fall Guys; name-only "weak" entries for the other five, since Epic's
  public pages for those don't publish folder/class-level detail. Includes a capture procedure
  for upgrading a "weak" entry (or adding a brand missing entirely) straight from a real project —
  writes to the skill's own reference file (works immediately, no vault needed) and, if the
  second brain is configured, to a `type: pattern` article via `second-brain-librarian` for
  cross-machine reuse; large projects can lean on `second-brain-trainer`'s parallel-analysis
  pattern for the capture pass itself. Wired into `project-bootstrap`'s A1 step and as a new rule
  12 in `user-level-memory/CLAUDE.md`. Install step 5 now copies seven skill folders instead of
  six.

## v1.42 — Agent Console: added the second-brain-trainer node

The console's `AGENTS` list still only had six entries after v1.41 added the seventh agent — it
now has its own node, so a training-sweep run is actually visible instead of falling back to a
generic/unknown node:

- New node for `second-brain-trainer` (🐝, a new `teal` color — every other slot in the existing
  8-color palette was already taken by another node) added to `agent-console.html`'s `AGENTS`
  array, with matching CSS rules (blob border/glow, name color, pill color) for the new `teal`
  `data-color`.
- The header tagline ("six agents. one chief of staff...") updated to "seven agents." The
  "N idle" footer counter was already computed dynamically from `AGENTS.length`, so it picks up
  the new total automatically — no fix needed there.
- No hook/server changes needed for this: `second-brain-trainer` dispatches its own parallel
  analysis clones and its one `second-brain-librarian` handoff exactly like any other agent-to-
  agent invocation the console already tracks (start/stop, FIFO attribution, comet/pulse) — this
  update only adds the node it lights up on the ring.

## v1.41 — New optional agent: second-brain-trainer (parallelized vault training pass)

New seventh agent, `second-brain-trainer`, for owners who want to backfill the Obsidian second
brain from a large or unfamiliar project faster than the normal one-thing-at-a-time flow:

- Splits the current project into areas (owner-given, or inferred from `Claude/docs/SPEC.md`'s
  project-structure section and the Outliner's own grouping) and dispatches one read-only
  analysis clone per area **in parallel** (batched in waves of ~6-8 if there are more areas than
  that) — genuinely concurrent subagents, visible as multiple simultaneous nodes if the Agent
  Console is open.
- Keeps the vault's single-writer rule intact: the parallel clones never touch the vault
  themselves, only gather findings; `second-brain-trainer` aggregates every clone's results and
  hands them to `second-brain-librarian` in exactly ONE call at the end. The vault is plain
  markdown with no locking, so this avoids the corrupted/lost-content risk of two writers
  touching it around the same time — parallelizing the reading is safe, the writing stays
  strictly single-threaded either way.
- Only useful when `second-brain-librarian` (and its vault) is already configured; skips itself
  with a clear message if it isn't. Owner-invoked only — not something the other agents call on
  their own.
- `user-level-agents/second-brain-trainer.md` added (Phase 1 install step 5 now copies seven
  agent files instead of six). SETUP-GUIDE.md updated: section 2's agent list, section 3c's
  second-brain writeup, and the intro's feature list and agent count.

## v1.40 — Agent Console: deterministic, per-project auto-start (no more asking, no more stale cross-project server)

Fixes a real bug the owner hit switching UEFN maps/projects, plus the matching feature request —
start the console with the very first command of a session, not after a round of asking:

- **Bug fixed: stale cross-project server.** Every project used the same fixed port (8765), and
  the old `SessionStart` hook only checked "is *something* listening on 8765" before deciding
  whether to start a new one — so switching to a different UEFN project while a previous
  project's server was still bound left you looking at the *wrong* project's console, since it
  looked "already running" from the outside. Fixed by giving every server instance a new
  `/whoami` route reporting which project folder it's actually serving; the session-start hook
  now compares that against the current project before deciding anything.
- **No more asking.** `session-start-reminder.ps1`/`.sh` no longer prompts Claude to ask whether
  you want the console open. It now deterministically: (1) checks `/whoami` on port 8765; (2) if
  it's already serving THIS project, leaves it alone; (3) otherwise kills whatever's bound to the
  port — only if it looks like one of this kit's own server processes (powershell/pwsh/python),
  never an unrelated program — and starts a fresh one scoped to the current project, in the
  background. Claude just mentions the URL in its first reply; there's nothing to answer.
- `agent-console-server.ps1` and `.py` both gained the `/whoami` route (`{"project": "<this
  project's folder>"}`), computed once at server startup from the script's own location — this is
  the mechanism the fix above relies on.
- `CLAUDE.md`'s fallback "Rules for this project's agents" section rewritten to match: describes
  the same deterministic check-and-replace behavior instead of "ask, then start if nothing's
  listening," for the rare case the hook's own context note doesn't reach an older Claude Code
  build.
- `.claude/settings.json`'s `SessionStart` block comment updated to describe the new behavior.
- SETUP-GUIDE.md section 5b rewritten (the "how it starts" paragraph and the troubleshooting
  entry) to match — including a new note for the specific symptom "it's showing a different
  project's data."
- No change needed for the very-first-ever-bootstrap case the owner also asked about:
  `Claude/hooks/agent-console.html` already ships as part of this kit's project template, so it's
  present from the very first session on a project regardless of whether `project-bootstrap` has
  ever been run — the deterministic auto-start above already covers it with no special-casing.

## v1.39 — Agent Console: new MCP Server node, YOU session-active LED

Two feature requests, implemented and live-tested by the owner's own Claude Code session (with
synthetic events for the MCP node, to avoid actually touching the UEFN editor during testing),
then backported into the kit source (including authoring the missing `.sh`/`.py` equivalents for
parity, since only the `.ps1` versions were provided):

- **New "MCP Server" node** (🛰️, orange), fed by a new pair of hooks,
  `agent-console-mcp.ps1`/`.sh`, wired on both `PreToolUse` and `PostToolUse` for the
  `mcp__unreal-mcp__call_tool` matcher (added as a second, independent command alongside
  `after-playtest.ps1`/`.sh` on that same matcher — not a replacement). It writes to its own log,
  `Claude/logs/agent-console-mcp.jsonl`, served from a new `/mcp` route. The node lights up (LED,
  "working" pill, call counter, tooltip with a best-effort label of what was called) while a call
  is in flight, and returns to idle on stop. When a bot made the call, a pulse animates from that
  bot's node to the MCP node so you can see *who's* talking to the editor; a direct call from the
  main session just shows the node connected to the hub.
- **YOU node now shows a session-active LED**: green while the main Claude Code session is
  actively working, grey once it's yielded back and is waiting on your next message — independent
  of the existing red "approval required" alert (still tied to `release-gate`, unchanged). Fed by
  `agent-console-tokens.ps1`/`.sh` (already firing on every tool call — now also writes
  `Claude/logs/agent-console-session.json` with `active:true`) and a new
  `agent-console-session-stop.ps1`/`.sh`, added as a second command on the existing `Stop` hook,
  which writes `active:false` at the exact moment the main session yields back to you. Served
  from a new `/session` route.
- Fixed a bug caught during testing: the MCP Server node's pill showed "undefined" instead of
  "idle" on first load (a special node with no `pillOff` defined had no fallback).
- `agent-console-server.ps1` gained the two new routes (already done upstream); backported the
  same `/mcp` and `/session` routes into `agent-console-server.py` for parity, since the uploaded
  copy was still the three-route version.
- `.claude/settings.json` updated: new `PreToolUse` block for `agent-console-mcp.ps1`, a second
  `PostToolUse` command on the existing `mcp__unreal-mcp__call_tool` block, and a second `Stop`
  command for `agent-console-session-stop.ps1`.
- New SETUP-GUIDE.md paragraphs documenting both features under section 5b.

## v1.38 — Agent Console: per-agent + hub status LEDs, comet moved fully outside the ring

The owner's own Claude Code session made further live-tested improvements directly to
`agent-console.html` (verified both with overlapping real subagents and by injecting synthetic
states into the page to check the logic deterministically, since real timings were too fast to
screenshot at the right millisecond):

- **Dynamic status LED on every agent card**, replacing the old fixed-green "online" dot:
  - grey = idle
  - green (pulsing) = genuinely working right now (top of the active-invocation stack)
  - red (blinking) = either waiting on a delegated task to finish (it's active but not on top of
    the stack — e.g. `coder` that just handed off to `second-brain-librarian`), or has been
    running longer than 6 minutes with no stop, a likely-stuck signal distinct from (and earlier
    than) the 20-minute hard auto-clear added in v1.36.
  Verified with 3 overlapping invocations: only the most-recently-started one shows green, the
  rest show red — the intended parent/child-delegation reading.
- **Chief of Staff hub** now has its own status LED too (green while supervising at least one
  active agent, grey when everything's idle), correctly positioned on the hub's own edge.
- **Comet orbit radius increased** from ~30px (effectively glued to the 32px blob edge) to ~46px,
  so it now clearly orbits outside the icon instead of riding along its border glow. Also added a
  real fading tail — a gradient arc trailing the comet's head — instead of just a glowing dot.
- Confirmed no "unknown" card remains in the current log history from the v1.37 fix; if one
  reappears after a hard refresh on `http://127.0.0.1:8765/`, it's worth a fresh capture with the
  same method used for the v1.37 diagnosis rather than assuming it's the same already-fixed bug.

## v1.37 — Agent Console: the real "unknown"/stuck-card root cause, found and fixed

The owner ran the diagnostic prompt from v1.36 in their own Claude Code session against a live
capture of `SubagentStop` payloads (2 real subagents dispatched overlapping) and found the actual
bug — the v1.36 auto-clear safety net was masking the symptom, not fixing it. Two real,
independent findings, backported into `agent-console-log.ps1`/`.sh` and
`agent-console-stop.ps1`/`.sh`:

- **`SubagentStop` fires for more than just a real subagent finishing.** Of 5 captured events,
  only 2 were real completions (a populated `agent_type` whose `agent_id` matched a prior
  dispatch); the other 3 were internal orchestrator-session events with `agent_type:""` and an
  `agent_id` never seen in any start event (one even carried the session's own scheduled-wakeup
  id). The old script treated every SubagentStop as a real stop and always popped the FIFO
  queue's oldest entry — so a ghost event would consume a real agent's queue entry, permanently
  desyncing every attribution after it. That's what actually produced the "unknown" cards and
  real cards (e.g. `coder`) staying stuck on WORKING — not a simple ordering race.
  `agent-console-stop.ps1`/`.sh` now reads the payload's own `agent_type` directly; if it's
  empty, the script exits immediately without touching the queue or logging anything. The queue
  is now used only to recover the matching `desc`, by searching for the oldest entry whose
  `agent` matches the real `agent_type` — not by blindly popping index 0 — which also fixes
  attribution when two different agent types are active at once and finish out of order.
- **A PowerShell 5.1 parsing gotcha**, found once the above was fixed and `desc` was still coming
  back empty: `@(Get-Content -Raw | ConvertFrom-Json)` — the outer `@(...)` around the pipe —
  double-nests the result once the queue has more than one element (`Object[1]{ Object[N]{ ... }
  }` instead of a flat `Object[N]`), silently breaking the agent-match search. Queue parsing in
  both `.ps1` scripts now normalizes explicitly ($null / already-an-array / single-object) with
  no outer `@(pipe)` wrap. The `.sh` scripts use `jq` and were never subject to this specific
  gotcha, but got the `agent_type`-based ghost-event fix ported over regardless, since that part
  is about hook payload behavior, not the shell.
- Confirmed end-to-end with `coder` + `qa-regression` dispatched overlapping and finishing in
  reversed order: correct `desc` on both, no `unknown`, and the queue back to `[]` clean.
- v1.36's 20-minute auto-clear safety net stays in place as a front-end fallback (still worth
  having in case a future Claude Code version changes these field names again — see the updated
  SETUP-GUIDE troubleshooting entry), but is no longer expected to be the thing doing the actual
  work here.
- Rewrote the SETUP-GUIDE.md troubleshooting entry for stuck/misattributed/"unknown" cards to
  describe the real mechanism instead of the earlier (incorrect) FIFO-ordering theory.

## v1.36 — Agent Console: fixed stuck animations, ring overlap, hub icon, vault connector

Direct feedback from a live run that surfaced a real "unknown" card in the console (see the new
SETUP-GUIDE troubleshooting entry) plus three follow-on asks:

- **Comet/pulse animations no longer run forever.** Root cause of the underlying symptom (a
  card's comet/pulse staying "active" after the real work finished): a `stop` event can get
  misattributed to a phantom `"unknown"` agent when the FIFO attribution queue
  (`agent-console-active.json`) is popped while already empty, which "eats" a stop that belonged
  to a real, still-active card. As a front-end safety net (independent of fixing the hook-side
  race, which needs a live capture to pin down per-setup), a card with no matching stop event
  after 20 minutes is now auto-cleared — its comet/pulse/glow turn off and the activity log gets
  an explicit "⚠ auto-cleared" note explaining why, instead of spinning indefinitely.
- **Ring layout no longer overlaps when a new node appears at runtime.** A dynamically-added
  fallback node (e.g. that same `"unknown"` card) used to keep the *original* even-spacing angle
  math from before it existed, so it could land right on top of an existing node instead of the
  ring re-spacing itself. All node angles are now recomputed whenever a new node is added.
- **Chief of Staff hub icon**: replaced the abstract coral starburst mark (read as "a little
  flower") with the same 🤖 robot glyph used for an unrecognized/fallback agent card, per direct
  feedback — same visual language, not a separate abstract mark.
- **Obsidian Vault's connector** now points at `second-brain-librarian` instead of at the hub —
  it isn't a bot the Chief of Staff talks to directly, it's the storage that
  `second-brain-librarian` actually writes into, so the line now reflects that relationship
  instead of implying a direct hub connection.
- Added a matching SETUP-GUIDE.md troubleshooting entry for the "unknown" node specifically,
  since it's a distinct enough symptom from the older generic stuck-card entry to deserve its own
  explanation and remedy.

## v1.35 — Agent Console: vivid colors, gem icon for Obsidian Vault, Claude-style hub mark

Follow-up to v1.34's redesign, based on direct feedback that the first pass looked too washed
out compared to the reference image (bright neon rings on a dark background, not muted glass):

- Removed the `grayscale`/`opacity` filter that was desaturating every idle node's ring and
  icon — that was the actual cause of the "muted" look, since it was graying out the
  already-correct per-agent border color. Every node's colored ring, glow, and label now render
  at full saturation all the time; only the glow intensity and a scale bump change between
  idle and active.
- Node shape switched from the organic "blob" to a clean circle with a thicker (3px) glowing
  ring, closer to the reference's neon-circle look; each node also got a small pulsing green
  "online" dot in the corner, and its name label is now colored to match its own ring instead of
  plain gray.
- **Obsidian Vault** now uses a gem icon (💎) instead of a folder, echoing the amethyst-crystal
  icon in the reference image.
- **Chief of Staff hub**: replaced the placeholder text glyph with a small custom inline-SVG
  mark (three overlapping coral-orange rounded bars radiating from a center dot) instead of a
  generic icon — a distinct, Claude-toned identity for the hub specifically, not the same icon
  reused for every other node. The hub's ring, glow, and ripple rings were retinted to match
  (coral / amber / magenta instead of blue / purple / cyan).

## v1.34 — Agent Console visual redesign: "Dream Bot Team AGENT CONSOLE_"

Cosmetic/UX redesign of `agent-console.html` only — no changes to the hooks, the FIFO queue, the
server, or the token/timer logic behind it. Two design passes in a row, both from live reference
images the owner supplied:

- Renamed the console's title to **"Dream Bot Team AGENT CONSOLE_"** (matches the existing
  blinking-cursor convention already used elsewhere in the file).
- Replaced the old two-column hex layout with a radial layout: a central **"chief of staff"** hub
  (a Claude-style glyph in a circular core) with three staggered expanding ripple rings
  (`@keyframes ripple`) so it reads as "alive" even at rest.
  Six agent nodes plus two new special nodes are arranged evenly around it and slowly orbit
  (~0.9°/s, one lap roughly every 6.5 minutes) via a `requestAnimationFrame` loop that recomputes
  each node's position, its SVG spoke back to the hub, and any in-flight pulse dot every frame.
- Distinct color per agent, reinforced (same six-color palette as before, now driving glow color,
  border color, and the new comet color together).
- Agent icons are now glassmorphic "blobs" — `backdrop-filter: blur()`, translucent gradient
  fill, an organic asymmetric `border-radius` loosely inspired by the Fortnite sprite gallery the
  owner referenced (not a literal copy — a from-scratch shape in that spirit, since the request
  left the exact execution up to me).
- Spokes now carry a **continuous traveling pulse** while an agent is active (not just on
  handoff) — a small dot flowing along the spoke toward the hub, in the agent's own color, so
  "this agent is working" is visible at a glance without reading the pill text.
- Added a small **comet**: a half-circle dot that orbits an agent's icon (`@keyframes
  spinComet`), shown only while that agent is `.active`, colored to match the agent.
- Added two new special, non-subagent nodes on the same ring:
  - **Obsidian Vault** ("shared memory") — lights up whenever `second-brain-librarian` is active,
    since that's the real agent that writes to the vault.
  - **YOU** ("approvals only") — turns red and pulses whenever `release-gate` is active. This is
    a **heuristic proxy**, called out explicitly in the footer: there's no dedicated
    "approval requested" hook in this kit yet, so `release-gate` running is used as the closest
    available signal that a real decision is waiting on a human. A matching red "⚠ approval
    required" stat card lights up in the top stats row at the same time, and the hub itself gets a
    red glow.
- Moved the activity/terminal log to the right-hand column (`.main-grid`, a two-column grid that
  collapses to one column under 960px) instead of full-width below the layout.
- `SETUP-GUIDE.md` section 5b's screenshots/description of the console's look are now stale and
  should be refreshed to match, next time that section is touched — not done in this pass since it
  was purely visual and no behavior changed.

## v1.33 — two more real bugs found testing the token/timer update, both fixed

The owner tested v1.32 live (guided by a diagnostic prompt) and found two genuine bugs, not
hypothetical ones:

- **Stale server process**: the running `agent-console-server.ps1` had been started before the
  updated files were copied in — it had already loaded the old `agent-console.html` and doesn't
  re-read routes/files after startup, so `/tokens` looked broken when the real cause was an old
  process still serving old content. Not a code bug, but common enough to call out explicitly:
  `SETUP-GUIDE.md` section 5b now has a dedicated note to restart the server after updating any
  `agent-console-*` file.
- **Real race condition**: `agent-console-log.ps1` and `agent-console-stop.ps1` both
  read-modify-write `Claude/logs/agent-console-active.json` (the FIFO attribution queue), and
  overlapping subagent invocations can run both at the same instant. Confirmed via a live test:
  concurrent unsynchronized writes corrupted a queue entry (a field serialized as a 2-element
  array instead of a plain string), which then threw uncaught inside `agent-console.html`'s
  render loop before `lastCount` advanced past the bad entry — permanently wedging the
  connection indicator on "🔴 DISCONNECTED" every poll thereafter, plus a stuck "WORKING" card
  and a stray ghost card, despite the server and network being completely fine. Fixed two ways:
  a named Mutex (`Local\AgentConsoleQueueMutex`, shared between both scripts) now serializes the
  read-modify-write section so the queue file can't be corrupted in the first place, and
  `agent-console.html`'s `processEntries()` now defensively skips any log entry whose
  `agent`/`desc` fields aren't plain strings instead of throwing — so even a future corrupted
  entry from some other cause degrades to "one skipped row," not a permanently broken console.

## v1.32 — session timer and approximate token counter in the Agent Console

- **Session timer**: a "Session running for" readout, ticking live every second, computed
  client-side from the earliest event already loaded — no new hook needed. Each active agent
  card also now shows its own live elapsed time (`⏱ 1:24`) while it's working.
- **Tokens this session (experimental/best-effort)**: a new stat showing a rough running total
  of token activity, summed from the session transcript Claude Code writes to disk. New hook
  `Claude/hooks/agent-console-tokens.ps1`/`.sh`, wired as a `PostToolUse` hook with no matcher
  (fires on every tool call, not just subagent ones), reads the transcript incrementally
  (tracked byte offset, so it stays cheap on a long session) and writes a cumulative snapshot to
  `Claude/logs/agent-console-tokens.json`. `agent-console-server.ps1`/`.py` gained a `/tokens`
  endpoint serving that file; the page polls it alongside `/log`.
- Explicitly documented as approximate: the total sums `input + output + cache_read +
  cache_creation` tokens across every assistant turn — a proxy for activity, not a billing
  figure, since prompt-caching pricing and per-turn full-context `input_tokens` aren't adjusted
  for. There's no documented API for this — it's inferred from the transcript's on-disk shape,
  which could change between Claude Code versions; `SETUP-GUIDE.md` section 5b has a
  troubleshooting entry (and a debug-capture switch in the script) for when it doesn't.
- `.claude/settings.json` updated with the new no-matcher `PostToolUse` block.

## v1.31 — fixed premature "finished" on backgrounded subagents

Found live: the owner dispatched `coder` to fix three bugs at once, Claude Code ran it in the
background ("Waiting for 1 background agent to finish"), and the console showed "finished" two
seconds after "started" while the agent was still genuinely working.

- **Root cause**: "stop" was logged from `PostToolUse` on the subagent-dispatch tool
  (`Task`/`Agent`) — but for a backgrounded dispatch, that tool call returns (firing
  `PostToolUse`) the instant the work is handed off, not when it's actually done. Foreground
  dispatches happened to look right by coincidence; background ones didn't.
- **Fix**: "stop" now comes from the `SubagentStop` hook instead — the hook Claude Code fires on
  a subagent's real completion, foreground or background. `agent-console-log.ps1`/`.sh` now only
  logs "start" (on `PreToolUse`, unchanged); a new `agent-console-stop.ps1`/`.sh` handles "stop"
  on the new `SubagentStop` hook.
- Since `SubagentStop`'s payload doesn't reliably say which agent just finished,
  attribution goes through a new small FIFO queue file, `Claude/logs/agent-console-active.json`:
  the start hook pushes an entry, the stop hook pops the oldest one and uses its
  agent/description. Best-effort (documented as such), correct for the common case.
  `.claude/settings.json` updated: removed the old stop-logging `PostToolUse` "Task|Agent"
  block, added a `SubagentStop` block.
- `SETUP-GUIDE.md` section 5b rewritten to describe the new two-hook/queue mechanism, plus a new
  troubleshooting entry for a card stuck on "WORKING" or a wrong attribution (delete
  `agent-console-active.json` to reset).

## v1.30 — real root cause found: the subagent tool isn't always named "Task"

The owner diagnosed this live (guided debug: uncommented the raw-payload capture, temporarily
widened the hook matcher to `.*`, invoked `coder` explicitly, inspected the captured payload).
Confirmed cause of the console staying at 0/IDLE even with a correct `.claude/settings.json`:
on this build, Claude Code's internal subagent-dispatch tool is named `"Agent"`, not `"Task"` —
every event was being filtered out before it ever reached the log. All other field names
(`hook_event_name`, `tool_input.subagent_type`, `tool_input.description`) were already correct.

- `agent-console-log.ps1`/`.sh` now accept **both** `"Task"` and `"Agent"` as the tool name,
  since it's been observed to vary by Claude Code build/version — future-proofs the console
  against needing this same diagnosis again on a different setup.
- `.claude/settings.json`'s two matchers changed from `"Task"` to the regex `"Task|Agent"`.
- `SETUP-GUIDE.md` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly, and the
  troubleshooting section now says explicitly what to do if a future version renames the tool to
  something else again (add it to both the script check and the matcher, same pattern).

## v1.29 — fixes from a real test of the Agent Console automation

Two problems found live-testing v1.28: the automatic session-start question never fired, and the
console stayed at 0/IDLE even after opening it manually.

- **Root cause of the silent prompt**: `session-start-reminder.ps1`/`.sh` printed plain text to
  stdout, which isn't reliably read as an instruction by Claude Code. Rewrote both to emit
  proper hook-output JSON (`hookSpecificOutput.additionalContext`), the documented way to inject
  context Claude actually sees at session start.
- **Guaranteed fallback added**: the same reminder now also lives as plain prose in
  `project-template/CLAUDE.md`'s "Rules for this project's agents" section — CLAUDE.md always
  loads regardless of any hook-output quirk in a given Claude Code version, so the console
  question surfaces even if the hook JSON approach doesn't land on some setup.
- **Clarified why cards can stay at 0/IDLE**: the console only reacts to a genuine `Task` tool
  dispatch to a named subagent — general conversation or an inline edit Claude does without
  delegating doesn't produce one, and isn't a bug. `SETUP-GUIDE.md` section 5b now says this
  explicitly, plus an expanded troubleshooting checklist covering the most likely real cause:
  `.claude/settings.json` needs to be fully replaced on an existing project, not just the new
  hook script files copied in.

## v1.28 — Agent Console asks to open itself, automatically

- New `Claude/hooks/session-start-reminder.ps1`/`.sh`, wired into `.claude/settings.json` as a
  `SessionStart` hook (matcher `startup`, so it fires when you launch `claude` fresh, not on
  every `/clear`/`/compact`). If the project has the Agent Console installed, it reminds Claude
  at the very start of the session to ask the owner whether they want it open — if yes, Claude
  checks port 8765 and, if nothing's listening, starts `agent-console-server.ps1`/`.py` itself
  in the background (detached, doesn't block the session) and tells the owner to open
  `http://127.0.0.1:8765/`. Says no once, doesn't ask again that session.
- `SETUP-GUIDE.md` section 5b and `Claude/SETUP-INSTRUCTIONS.md` step 9 updated to describe the
  automatic prompt as the default way to open the console, with manual startup kept as an
  alternative for anyone who'd rather run it in their own terminal.

## v1.27 — real-time Agent Console

A local, arcade-style dashboard that shows the team of agents actually working in real time —
which one is active, on what, and when one hands off to another — instead of only seeing the
finished output in `STATUS.md`/`BUGS.md`.

- New `Claude/hooks/agent-console.html`: a self-contained page with a card per agent (glows in
  that agent's own color and shows the current task while active), a scrolling activity log, and
  an animated pulse between two cards when one agent invokes another mid-task.
- New `Claude/hooks/agent-console-log.ps1`/`.sh`: wired into `.claude/settings.json` as
  `PreToolUse`/`PostToolUse` hooks matched on the `Task` tool (what Claude Code uses internally
  for every subagent invocation) — appends a start/stop line to
  `Claude/logs/agent-console.jsonl` per event, already configured in the scaffold, nothing to
  set up per project.
- New `Claude/hooks/agent-console-server.ps1` (PowerShell, no dependencies) and
  `agent-console-server.py` (Python, cross-platform): a small local web server serving the page
  and the live log — run manually, in its own terminal, kept open while working; not started
  automatically.
- `.claude/settings.json` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly;
  `SETUP-GUIDE.md` gets a new section 5b documenting setup, usage, and troubleshooting (same
  debug-payload pattern as the existing post-playtest hook).
- Entirely optional and safe to ignore/remove — nothing else in the kit depends on it.

## v1.26 — token-consumption reduction: six progressive-disclosure skills

Based on a set of recommendations the owner got analyzing the kit's token usage (same
adapt-don't-paste-verbatim approach as prior externally-sourced proposals):

- **Six new skills**, all following the progressive-disclosure shape (short `description`,
  dense body, `references/` loaded only on demand): `verse-patterns` (reusable Verse code
  idioms — multiplayer authority, state machines, logging/timers, item pool/round progression),
  `uefn-device-gotchas` (device-TYPE-specific quirks — DemoDisplay sizing/orientation,
  Elimination Manager/Item Granter timing, Storm Controller/Player Spawner position-critical
  behavior), `performance-uefn-checklist` (the static red-flag checklist), `discover-retention`
  (Discover signal facts plus a growing validated-proposal log, superseding `uefn-lessons`'
  "Discover / retention signals" category), `second-brain-query` (rules for asking the second
  brain narrowly), and `token-aware-coding` (general token-efficient habits — targeted search
  over full reads, precise `@file` mentions, periodic summarization).
- **`~/.claude/CLAUDE.md` rule 7 (DemoDisplay) trimmed**: the detailed sizing/orientation math
  and the `get_actor_bounds` gotcha moved to `uefn-device-gotchas/references/
  demodisplay-sizing.md`; CLAUDE.md now keeps only the always-needed core rule (one stand per
  Verse device, function-grouped) and the safety-critical gameplay-position exception, with a
  pointer to the skill for the rest — this file loads in every session, on every project, so
  trimming it has the largest leverage of any change in this pass.
- **`uefn-lessons/SKILL.md` de-duplicated**: its "Discover / retention signals" category now
  points to `discover-retention` instead of repeating the same facts; its "Device behavior
  surprises" category now points to `uefn-device-gotchas` for device-specific quirks, keeping
  the two skills' scopes non-overlapping (uefn-lessons = generic Verse/UEFN/MCP tooling,
  uefn-device-gotchas = per-device-type behavior).
- **Agent files wired to the new skills** rather than duplicating their content inline:
  `coder.md`'s pre-work checklist now points to `verse-patterns`/`uefn-device-gotchas`/
  `second-brain-query` at the relevant steps, and its DemoDisplay bullet points to the sizing
  reference instead of restating the math; `project-bootstrap.md`'s A3 now reads
  `performance-uefn-checklist` instead of inlining the checklist, and A4 reads
  `discover-retention` instead of `uefn-lessons`' (now-removed) Discover category;
  `qa-regression.md` references `performance-uefn-checklist` for what to watch at playtest.
- `SETUP-GUIDE.md` Phase 1 step 5 now lists all six new skill folders for installation, and a
  new section 3d explains what each one covers and why the progressive-disclosure shape matters
  for token usage.

## v1.25 — synthesis behavior applied consistently across every sync, not just `evolve`

Follow-up refinement (second round of feedback the owner got on v1.24, adapted rather than
applied verbatim):

- **Sync mode now checks for lateral synthesis too**: after `coder`/`project-bootstrap` hand off
  something to capture, `second-brain-librarian` checks related articles for a newly-surfaced
  connection (Level 1: update their "Connessioni e potenziali" directly) and adds a
  `wiki/meta/frontiere-conoscenza.md` entry when the sync reinforces or creates a genuinely
  interesting combination (Level 1 for a note, Level 2 to propose a new synthesis article) — so
  every ordinary sync feeds the KB's evolution, not only an explicit `evolve` run. Its report now
  says explicitly whether it touched other articles' connections or the frontier file.
- **"Connessioni e potenziali" got a concrete four-line template** (formalized links, latent
  links, synthesis candidates, open questions) instead of being described only abstractly —
  makes it actually consistent across articles and checkable by `audit`.
- `type: synthesis` articles now list their component concepts as a scannable inline
  `componenti: [[...]]` line under "Componenti combinati," for quick Dataview/graph use.
- **Query now prefers citing a synthesis article over its isolated components**, when one exists
  — the actual value-add of a second brain over flat search — applying whether the query comes
  from the owner or from `coder`/`project-bootstrap` asking before their own work.
- Release-notes sync (mode 3) now also updates a tracked device/mechanic article's "Connessioni e
  potenziali" (or adds a frontier entry) when a release note affects it, instead of leaving the
  conflict only inside the release-notes article itself.
- Step 0's near-miss-filename handling now gives the exact rename command, not just the
  diagnosis.
- Index-update steps now also remind to update any `moc-*.md` for a touched wiki, if one exists.
- Added an optional `wiki/meta/log-sessioni-sintesi.md` (a lightweight running tally of `evolve`
  runs), created only once `evolve` has actually run a few times, distinct from the narrative
  `evoluzione-kb.md`.
- The `second-brain-librarian.md` ↔ vault `CLAUDE.md` cross-reference on proactive-synthesis
  behavior is now stated as a direct instruction ("apply Level 1 immediately, propose Level 2")
  rather than just pointing at the other file.

Deliberately NOT added, per the owner's own judgment on the proposal: autonomous `evolve`
triggering, automatic versioning of the vault's `CLAUDE.md` itself, automatic Canvas/diagram
generation, or additional mandatory frontmatter fields — all flagged as premature/out of scope
for now.

## v1.24 — emergent synthesis and evolution for the second brain

Significant rewrite of `second-brain-template/CLAUDE.md`, incorporating and adapting a set of
proposals the owner got from another AI assistant, integrated to fit the existing architecture
rather than pasted verbatim:

- New **"Emergent synthesis and evolution"** section: `second-brain-librarian` now actively
  looks for connections between articles it wasn't explicitly asked to find — during `compile`,
  a query, or `audit` — not just when told to. Three levels of autonomy: apply directly (update
  an article, add a missing wikilink), propose-then-confirm (new synthesis article, merge, new
  wiki), and a dedicated Level 3 pass only on explicit command. Five named reasoning moves
  (structural analogy, generalization, composition, inversion, cross-domain transfer) to use
  when actively looking for a connection, with the "why" documented in 1-2 dense sentences.
- New **`evolve`/`sintetizza [topic]`** workflow (Level 3): a deliberate whole-KB (or scoped)
  synthesis pass — finds under-connected clusters, drafts 3-7 emergent ideas in
  `output/sintesi-YYYY-MM-DD.md`, and presents them for review. Never applies anything
  unconfirmed, same rule as `audit`.
- New `wiki/meta/` living files, created on demand (not pre-created empty):
  `frontiere-conoscenza.md` (open questions, untested hypotheses, patterns seen on 2+ projects
  without an article yet), `evoluzione-kb.md` (dated log of significant syntheses/reorganizations),
  `principi-design-second-brain.md` (observations about how this KB itself is working — a wiki
  article for the owner to read, explicitly NOT a mechanism for the agent to rewrite its own
  `CLAUDE.md` autonomously; structural changes to this file stay the owner's call).
- Richer, Dataview/graph-friendly frontmatter (`aliases`, `status`, `type`, `visto_su`,
  `versione_implementazione` — all optional, added where they genuinely apply), a new required
  `## Connessioni e potenziali` section on most articles, and a dedicated four-section structure
  for `type: synthesis` articles.
- `audit` gained four categories: under-synthesized clusters, weak connections, dormant ideas,
  stagnant evolution (a device/mechanic-specific case of staleness, called out because it
  directly hurts reuse value).
- `compile` gained a step 9 (synthesis side effect) and `query` a closing self-check, both
  tying back into the same "notice connections proactively" behavior.

`second-brain-librarian.md` updated to recognize `evolve`/`sintetizza` as a fourth direct
command alongside `compile`/query/`audit`, and to note the proactive-connection behavior applies
during ordinary work too, not only when `evolve` is explicitly invoked.

## v1.23 — "How I Want Claude to Help Me" section in the vault's CLAUDE.md

Added a new section to `second-brain-template/CLAUDE.md`: connect ideas between notes the owner
may have missed — while compiling, writing, or answering a query, `second-brain-librarian`
should actively look for related-but-unlinked existing articles (even across different thematic
wikis) and surface the connection (add the `[[wiki link]]`, mention it in the summary/answer),
not just handle the immediate task and move on.

## v1.22 — fixed two real bugs in the release-notes sync script

Found on a real Windows test run of `weekly-release-notes-sync.ps1`:

1. **Permission error reading the vault's `CLAUDE.md`.** The script never `cd`'d into the vault
   before calling `claude -p`; non-interactive/print mode can't prompt for confirmation, so it
   refused to touch anything outside its working directory. Fixed by `Set-Location` into the
   vault plus passing `--add-dir` as a belt-and-suspenders measure. Applied the same fix to the
   `.sh` version for consistency, even though bash's quoting doesn't hit the next bug.
2. **Prompt silently truncated mid-sentence.** The prompt had embedded double quotes (`"UEFN
   release-notes sync"`); when PowerShell hands a string like that to an external `.exe`,
   Windows' native argument parsing treats the embedded quote as closing the argument early —
   this is exactly what happened, the agent received the prompt cut off right before the quoted
   phrase. Fixed by removing all embedded double quotes from the prompt text.

`second-brain-template/README.md` now documents both gotchas and recommends testing the script
by hand once before wiring it into Task Scheduler/cron.

## v1.21 — weekly UEFN release-notes sync

`second-brain-librarian` gets a fourth mode, "UEFN release-notes sync" (added `WebFetch` to its
tool list): fetches
[Epic's "What's new in UEFN" page](https://dev.epicgames.com/documentation/fortnite/whats-new-in-unreal-editor-for-fortnite)
and keeps `wiki/note-di-rilascio-uefn/` current — one article per release. First run ever
backfills every entry found on the page; every run after that diffs against what's already
indexed and adds only newly published entries, never re-creating or duplicating one already
captured. Flags anything that looks like it deprecates something already noted elsewhere in the
KB (an `uefn-lessons` entry, a project's `BUGS.md`, an existing device article's snippet).

Added `second-brain-template/weekly-release-notes-sync.ps1` and `.sh` to actually run this on a
schedule, plus README instructions for wiring either into Windows Task Scheduler (`schtasks`,
Thursdays) or cron (macOS/Linux) — Claude Code itself has no built-in weekly scheduler, so this
is standard OS automation, the same pattern as the kit's own post-playtest hook. Can also be run
once by hand by asking any session to "use second-brain-librarian to sync UEFN release notes."

`note-di-rilascio-uefn/` added to the vault's suggested starting wikis in
`second-brain-template/CLAUDE.md`; setup guide's section 3c documents the new mode and the
automation setup.

## v1.20 — Windows hidden-extension gotcha on the vault's CLAUDE.md

Found on a real setup: saving/renaming `CLAUDE.md` through Windows File Explorer with
extensions hidden (the default) can silently produce `CLAUDE.MD.md` instead of `CLAUDE.md` —
Explorer hides the trailing `.md` because it's a "known" extension, so the wrong filename looks
identical to the correct one in the file list, and `second-brain-librarian` correctly reported
the vault as unconfigured (it reads the real filesystem, not Explorer's display) while the owner
saw what looked like the right file.

Fixes:
- `second-brain-template/README.md` and `SETUP-GUIDE.md` (Phase 1 step 7) now tell you to verify
  the vault's `CLAUDE.md` from a terminal (`dir CLAUDE*` / `ls CLAUDE*`) instead of trusting
  Explorer's file list, with the exact rename if it's wrong.
- `second-brain-librarian` now names the exact wrong filename (or missing folder) it actually
  found on disk when the vault looks misconfigured, instead of a generic "not configured" — so a
  five-second rename doesn't get reported the same way as an actually broken setup.

## v1.19 — second brain becomes read-write, not just write-only

Until now `coder` and `project-bootstrap` only fed the Obsidian second brain, never consulted
it — a project could reimplement something already catalogued from scratch without ever
checking. Fixed:

- **`coder`** (new step 5) queries `second-brain-librarian` before implementing a common
  device/mechanic pattern (respawn, item pool, round progression, elimination handling, and
  similar) from scratch, and adapts the existing snippet instead of reinventing it when a
  current implementation is already catalogued. Not mandatory on every task — only when the
  pattern is common enough to plausibly already exist.
- **`project-bootstrap`**'s A4 (retention proposals) now also queries the second brain for
  proposals already tried on other projects and their actual outcome, preferring a
  track-recorded proposal over a purely theoretical one when both apply.
- `second-brain-librarian`'s "direct vault commands" section now explicitly covers being queried
  by `coder`/`project-bootstrap` this way, not just by the owner.

Documented in `~/.claude/CLAUDE.md` rule 11, the setup guide's section 3c, and item 7 of "What
this kit does."

## v1.18 — second brain path set to `C:\SecondBrainOssidian`

`~/.claude/CLAUDE.md` rule 11's "Second brain path" now defaults to `C:\SecondBrainOssidian`
instead of the `<SECOND_BRAIN_PATH>` placeholder, so `second-brain-librarian` picks it up
automatically — no manual edit needed on this machine. Also updated as the worked example in the
setup guide's Phase 1 step 7 and in `second-brain-template/README.md`. Reusing this kit on a
different machine or vault location: replace the path with your own, or with the literal
`<SECOND_BRAIN_PATH>` placeholder to turn the feature off.

## v1.17 — dedicated second-brain-librarian agent

Added a sixth agent, `second-brain-librarian` — the only agent in this kit whose work happens
outside the current UEFN project's folder. It's now the sole owner of reads/writes to the
Obsidian second brain vault added in v1.16:

- `coder` and `project-bootstrap` no longer write to the vault themselves. When they identify a
  reusable device/mechanic worth capturing, they hand off to `second-brain-librarian` with a
  short brief (device/mechanic, what changed, project name, date) instead — keeping the vault's
  actual conventions in one place rather than duplicated (and potentially drifting) across every
  agent that might touch it.
- `second-brain-librarian` also runs the vault's own `compile` (ingest `raw/` material the owner
  drops in directly), query, and `audit`/`lint` workflows when invoked directly, exactly as
  defined in the vault's own `CLAUDE.md`.
- It always reads `<SECOND_BRAIN_PATH>/CLAUDE.md` before acting, since the vault's conventions
  are the authority and may be customized by the owner over time — nothing about the vault's
  structure is hardcoded into this agent beyond finding it and the handoff format.
- Never blocks UEFN work: if the vault is unreachable or unconfigured, it reports that and
  stops; `coder`/`project-bootstrap` treat a handoff exactly like a missing `uefn-lessons` file.

`~/.claude/CLAUDE.md` rule 11, the setup guide (Phase 1 step 7, section 2's agent list, section
3c), and `second-brain-template/README.md` all updated to describe the handoff model instead of
direct writes.

## v1.16 — optional Obsidian second brain for reusable mechanics

Added `second-brain-template/` (`CLAUDE.md` + `README.md`) — a separate, optional Obsidian vault
(not inside any UEFN project) that accumulates game-mechanic and Verse device implementations
across every project, kept current per device/mechanic rather than as a pile of snapshots, so a
working pattern can be reused by copying an up-to-date wiki snippet instead of rebuilding it.

New `~/.claude/CLAUDE.md` rule 11 ("Second brain (Obsidian) integration — optional") holds the
vault's path (`<SECOND_BRAIN_PATH>` placeholder, filled in once per machine, off by default) and
the writing rules: `coder` writes/updates an article after implementing a reusable device/
mechanic pattern; `project-bootstrap` does the same as a new closing step (A6) after its initial
analysis of an existing project. Both read the vault's own `CLAUDE.md` for its current
conventions before writing (it may be customized over time) rather than hardcoding assumptions
here. Never blocks a UEFN task: skipped silently if the path is unset or unreachable.

Setup guide: new optional Phase 1 step 7 (vault creation + path configuration), new section 3c
explaining the feature and how it differs from `uefn-lessons` (short tooling gotchas vs. full
wiki articles on reusable implementations), "What this kit does" item 7, and base-rules summary
item 9. Phase 1's later steps (register/verify) shifted from 7-9 to 8-10; a numbering gap
introduced in v1.13 (step 7 missing between 6 and 8) is also fixed by this renumbering.

## v1.15 — self-heal MCP registration on a new machine

Fixed a real gap: MCP server registration lives in `~/.claude.json`, per machine — it never
travels with the project (Git, cloud sync, a new computer), so a project already fully set up on
one machine showed no MCP tools the first time it was opened on another, with nothing telling
`coder`/`qa-regression`/`project-bootstrap` this was expected rather than a broken project.

All three MCP-using agents now check for this explicitly, before their existing identity-match
safety check: if `claude mcp list` doesn't show `unreal-mcp` but `CLAUDE.md`'s "Project identity"
is already filled in (proof this project was set up with MCP before), they treat it as a
new-machine first run — not a project problem — and register the server themselves (same
auto-find-and-register routine `Claude/SETUP-INSTRUCTIONS.md` step 2 already used for first-time
setup: check port 8000, then `claude mcp add ... --scope user` if missing). No manual step or
re-run of `Claude/SETUP-INSTRUCTIONS.md` needed on the new machine for this specifically.

Documented in the setup guide under "Why the MCP server is set up this way," with a reminder
that Phase 1's UEFN-side setup (`.mcp.json`, *Auto Start Server*, the kit's user-level files, the
Unreal Engine skills plugin) still needs to be done once on the new machine — this self-heal only
covers the Claude Code registration step, not UEFN's own server config.

## v1.14 — deprecated-API detection, a three-track roadmap, and Discover-grounded retention proposals

`project-bootstrap`'s A3 quality check now produces three separate, priority-ordered tracks in
`Claude/docs/BUGS.md` instead of one undifferentiated bug list:
- **Bugs**, ordered by severity (as before).
- **Deprecated functions**: calls to deprecated/soon-to-be-removed Verse/UEFN APIs or device
  features, each with its replacement if known from Epic's official docs. `coder` (rule 4 in
  `~/.claude/CLAUDE.md`) doesn't introduce new calls to something already flagged, and migrates
  one opportunistically when already touching that code. `qa-regression` flags any it comes
  across too.
- **Performance issues** (static review, added in v1.12), now explicitly its own track with its
  own impact-ordered roadmap rather than mixed into the bug list.

A4 (retention proposals) is now grounded in how Fortnite's **Discover** surfacing actually
measures engagement — average playtime, bounce rate (the concrete reason a 5-minute session
threshold matters for visibility, not just player experience), player retention, and Qualified
Play-Through Rate — sourced from
[Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite)
and added as a new curated "Discover / retention signals" category in
`user-level-skills/uefn-lessons/SKILL.md`, so proposals can name which specific signal they
target instead of offering generic playtime advice.

## v1.13 — Unreal Engine skills plugin is now required, with its Git prerequisite

Phase 1's plugin install step is no longer optional: `/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official` is now a required part of
environment setup (renumbered to step 6, shifting the later registration steps to 8-10). Added
its prerequisite: Git must be installed first ([Git for Windows](https://gitforwindows.org/) on
Windows), plus a Windows-specific gotcha — if Claude Code is already running in a PowerShell
session when Git gets installed, that session won't see the new `git` command until it's closed
and reopened (PowerShell only reads `PATH` at startup), which otherwise looks like a failed Git
install even though it succeeded.

## v1.12 — static performance review during bug identification

`project-bootstrap`'s A3 quality check (existing-project bug identification) now also does a
static performance review of the code, flagging patterns likely to cost FPS at runtime: per-tick
work that could run less often or on events instead, unbounded/growing loops or collections,
expensive calls (spawns, MCP/device queries, distance/trace checks) inside a loop or per-tick
path instead of throttled/cached, per-player work that scales badly with player count, and heavy
logic left running after it's no longer needed. Each finding becomes its own `BUGS.md` entry,
marked as a static finding for `qa-regression` to confirm at actual playtest — this doesn't
replace `qa-regression`'s existing runtime performance checks (rule 4 in `~/.claude/CLAUDE.md`),
it catches likely issues earlier, before the first playtest even happens.

## v1.11

Phase 1, step 5 of the setup guide now mentions, as an optional extra, installing Anthropic's
official Unreal Engine skills plugin (`/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official`) alongside this kit's own
user-level files — a separate plugin with its own Unreal Engine/Verse skills, complementary to
this kit rather than a replacement for it.

## v1.10 — DemoDisplay rule refined with real placement/sizing details

Replaced the v1.9 DemoDisplay/support-device rules (`~/.claude/CLAUDE.md` rules 7-8, `coder.md`,
`project-bootstrap.md`) with a much more precise version, based on hands-on testing on a real
project:
- **Grouping by function**: one `DemoDisplay` stand per Verse device, containing every device
  that Verse device configures — not one stand per connected device.
- **Sizing**: resize via the `DemoDisplay`'s own `width`/`depth`/`height` properties (through
  `ObjectTools`), never actor Scale (stays `1,1,1`). Documented the actual numeric relationships
  (`width=6/depth=5/height=4` defaults ≈ 500×633uu; `+1 width` ≈ `+100uu` on Y; `width=8-10`
  typically fits 5-6 grouped devices).
- **Orientation**: yaw=0 → front=+X, right=+Y, with a note to always check yaw before assuming
  an axis — a real attempt got this backwards.
- **`get_actor_bounds` gotcha**: asymmetric components (e.g. a spotlight cone) can skew the
  bounding box on one side; compute the real footprint from the set `width`/`depth`/`height`
  instead, and only use `get_actor_bounds` to check the side expected to be symmetric.
- **Placement on the stand**: devices go inside the stand's X/Y footprint at the same Z as its
  base — no Z stacking, no fixed-spacing rows, freely grouped within the footprint.
- **Gameplay-critical-position exception**: devices whose position IS functional gameplay data
  (Storm Controller/Beacon = storm circle center, Player Spawner = spawn point, etc.) are never
  physically moved onto a stand — they stay in place and are only referenced by name in the
  `DemoDisplay`'s description. `coder` and `project-bootstrap` now both check this before moving
  or flagging any device for relocation.

Also seeded two real entries into `user-level-skills/uefn-lessons/SKILL.md` ("Device behavior
surprises" and "MCP / tooling quirks") with the width/Scale and `get_actor_bounds` gotchas above,
replacing two of the placeholder examples.

## v1.9

Added two new base rules (`~/.claude/CLAUDE.md`, rules 7-8; older rule 7 shifted to 9, rule 8
to 10 — check cross-references if you customized the file):
- **DemoDisplay for every Verse device**: every custom Verse device gets a dedicated
  `DemoDisplay` device documenting what it does and what it's connected to, created or updated
  on every touch, not just at creation. `coder` maintains it going forward; `project-bootstrap`
  flags existing devices with a missing or stale one as a non-blocking BUGS.md entry.
- **Support devices outside the play area**: logic/support devices (Item Granter, Timer,
  Elimination Manager, `DemoDisplay`, etc.) must be placed outside the playable area so players
  never see or reach them — devices players are meant to encounter (Player Spawner, a central
  display case) are the explicit exception. `project-bootstrap` flags misplaced support devices
  it finds on existing projects rather than moving them itself.

## v1.8

Removed the packaging-warning notes ("verify `Claude/` and `.claude/` don't end up in the
released experience") from `CLAUDE.md`, `SETUP-GUIDE.md`, and `Claude/SETUP-INSTRUCTIONS.md`
(step 7bis). It's intentional that they ship with the release — the whole point of installing
the scaffold inside `Content/` is that it rides along as a backup, covered by UEFN's own
save/cloud-sync, not something to strip out before release.

## v1.7 — cross-project learning

Added `user-level-skills/uefn-lessons/SKILL.md`, a shared knowledge base installed once
(Phase 1) that persists across every project, unlike `coder`/`qa-regression`'s existing
per-project memory which resets on every new island. `coder` and `qa-regression` now read it
before starting work and add a short entry to it — instead of to their per-project memory —
whenever they hit a lesson that's about Verse/UEFN/MCP itself rather than something specific to
the current project's own devices or design. This is the mechanism for actually getting better
at UEFN development the more projects use this kit, instead of every new island starting from
the same blind spots. Documented in the setup guide as new section 3b, and in
`~/.claude/CLAUDE.md` rule 8 alongside the existing per-project memory rule.

## v1.6

Added Outliner (Scene Graph) organization and device naming to the naming/organization base
rule — previously it only covered the Content Browser's folders and files:
- Devices should be grouped in the Outliner into folders matching the experience's actual
  areas/systems (e.g. `Lobby`, `Game Area 1`, `Devices`), not left flat.
- Devices should be renamed `<DeviceType>_<Function>` (e.g. `teleport_lobby`) instead of kept
  at their default auto-generated name, so what a device does is clear without opening it.
- `coder` follows this when placing/configuring devices going forward.
- `project-bootstrap` now also reviews existing projects' Outliner organization during its
  quality check and, if it's disorganized, proposes a reorganization plan (folders + a
  current-name → suggested-name list) in `SPEC.md` for the owner to review — it doesn't rename
  devices on its own, since a blind rename can break Verse references bound to a device's name.

## v1.5

`Claude/SETUP-INSTRUCTIONS.md` step 2e now covers the most common false alarm: if the owner
just enabled *Python Editor Scripting* / *UEFN MCP Toolsets* while the project was already open
in UEFN, those settings don't take effect until the project is reloaded. The instructions now
tell the owner to close and reopen the project in UEFN (not necessarily quit UEFN) before
re-checking, instead of leaving them to guess why a setting they just enabled still isn't
working.

## v1.4

`Claude/SETUP-INSTRUCTIONS.md` step 2 now finds and registers the MCP server on its own instead
of just checking whether Phase 1 already did it: it probes port 8000 directly (`netstat`/
`lsof`), and if the server is up but not yet registered in Claude Code, registers it
automatically at user scope — no manual `claude mcp add` required from the owner. This makes
per-project setup self-sufficient: whichever project you set up first also does the one-time
registration, and every later project just finds it already there. Phase 1 in the setup guide
now marks its own registration steps (6-8) as optional — useful as an early sanity check, but
no longer required before setting up your first project.

## v1.3

Added an "About the author" section at the top of the setup guide (Mimmo_the_root — creator
code ROOT, Discord, socials) and a note on why some setup steps are left manual on purpose
(transparency: see and understand what's installed, rather than hide it behind a one-click
installer).

## v1.2 — Two-phase setup restructure

Fixed a real ordering/confusion problem, verified against Epic's official UEFN MCP docs and
against a real working setup tested on multiple projects:

- Setup is now explicitly split into **Phase 1 (environment setup, once per machine)** and
  **Phase 2 (per-project setup, repeated for every project)** — with a table up front spelling
  out the two different folders you launch `claude` from in each phase, since that was the
  actual source of confusion.
- Phase 1 now correctly sequences: create `.mcp.json` inside the **UEFN installation folder**
  → (re)start UEFN → enable *Auto Start Server* → verify the port is listening (`netstat`/
  `lsof`) → install the kit's user-level agents/CLAUDE.md → launch `claude` from that same
  installation folder → register the server once at Claude Code user scope → verify. Previously
  these steps were scattered across a "prerequisites checklist" and two later sections, in an
  order that didn't match how it actually needs to be done.
- Per-project `Claude/SETUP-INSTRUCTIONS.md` step 2 is now a lightweight double-check (assumes
  Phase 1 already ran) instead of repeating full registration instructions.
- Note: Epic's own documentation describes a different, per-project `.mcp.json` approach
  (created in each project's root folder). This kit deliberately uses the machine-level
  approach in Phase 1 instead — tested and working across multiple real projects — and says so
  explicitly in the guide's sources section, so readers comparing against Epic's page aren't
  thrown off by the difference.

## v1.1

Clarified the MCP server prerequisites, which were previously conflated into a single
per-project checklist: split *Auto Start Server* (once per machine) from *Python Editor
Scripting* / *UEFN MCP Toolsets* (once per project), and added a port-listening check
(`netstat`/`lsof`) as the first diagnostic step. Superseded by the fuller restructure in v1.2
above.

## v1.0 — Community edition (English)

First public release. Five user-scope Claude Code subagents (project-bootstrap, coder,
qa-regression, planner-docs, release-gate) plus a per-project scaffold for developing UEFN
projects at scale without mixing them up. Key design decisions baked into this release:

- The scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) is installed **inside** each project's
  `Content/` folder on purpose, so it's covered by UEFN's own save/cloud-sync. Since `Content`
  is named identically in every project, the project's identity is read from the parent folder
  name once during setup and stored in `CLAUDE.md`, never recomputed from the current folder.
- The MCP server is registered once at Claude Code **user scope**, so every project on the
  machine sees it automatically — no per-project `.mcp.json`.
- The `unreal-mcp` server exposes a single generic dispatcher tool for all actions; the
  post-playtest hook filters on the call's JSON payload rather than the tool name.
- `Claude/reference/logger-template.verse.txt` uses a `.verse.txt` extension on purpose — UEFN
  compiles every `.verse` file under `Content/`, and this template isn't a valid standalone
  Verse module.
