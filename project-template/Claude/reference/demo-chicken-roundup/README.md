# Pilot demo: Chicken Roundup ("Raduno di polli")

A real, complete example of the kit's flow from zero, based on the Epic farm example. It is here so you can see what each step produces, and to try the whole path in a disposable project.

| File | Step that makes it | What it shows |
|---|---|---|
| GAME-SPEC.md | `/spec` | idea, 5-line loop, 2 stories with independent tests, success criteria, assumptions, sources consulted, technical risks, score and approval |
| CONSTITUTION.md | `/game-plan` | principles with reason and source, forbidden words, budget, the Self-healing block |
| PLAN.md | `/game-plan` | per story: devices (recipe / skill / explore), Verse files, assets inventory, manual steps; build order in two passes; risks to tasks |
| ROADMAP.md | `/task-list` | 6 tasks with story, risk, dependencies and a test you can do in play |
| PLAYTEST.md | `/environment --playtest` | expected / observed per story and a box per success criterion |

Run it again: `/demo` copies these files to `Claude/docs/demo-chicken-roundup/` (nothing of yours is touched). `/demo --load` puts them in `Claude/docs/` of a NEW EMPTY test project, so the Docs page shows the Idea, Spec and Plan tabs filled and you can follow the steps. It never overwrites an existing file.

Do not load it in your real map. Create a test project first: in UEFN make a new empty project (Fortnite > Create), open Claude Code in its folder and run the kit setup (`/kit-update`). When you want to start the demo again, discard that test project, make a new one and run `/demo --load`.
