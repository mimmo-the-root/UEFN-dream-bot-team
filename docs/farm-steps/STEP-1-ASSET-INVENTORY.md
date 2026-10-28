# Step 1 of 8: inventory of the farm assets (nothing is built in this step)

You are working on the map of this project (Chicken Roundup, a farm). This step only LOOKS and WRITES A LIST. Nothing is placed.

## What this step is for
Before building a farm we need to know what the editor really offers: buildings, trees and plants, ground surfaces, paths, fences, props, and the devices that spawn chickens. A search by exact asset name misses most of it (in the first run `find_assets` with names like Barn, Tree, Fence returned nothing and the farm was built with 12 pieces). Browse by folder and by short word, not by guessed full names.

## Rules (read them first)
- Use the MCP for everything. You work only through the MCP tools. You cannot see or click the UEFN window, so do NOT ask the owner to open panels, and do NOT try to drive the UI. If the MCP cannot reach something, write it in the section "Not reachable via MCP" and move on. The owner's assistant (Claude) looks at the editor itself and tells you the gaps (see "Gap pass").
- Read-only: do NOT place, move, delete or edit anything in the level. Do NOT call StartSession, StartGame, PushChanges, BuildAll.
- Never call `find_assets` without a filter (it can return 100 MB). Always pass `folder_path`, or `name` (a short word, substring), or `asset_type`. `list_folders` with `recursive: false`.
- At most about 30 MCP calls in this step (the Gap pass has its own budget of 15). One query at a time, and read each answer before the next.
- Write nothing outside `Claude/docs/map/ASSETS.md` (create the folder if needed). Do not touch ROADMAP.md, PLAN.md or the timer.
- Never delete files: if something must go, move it to `_to_delete`.

## Method
1. Ping: read the current level (`get_current_level`) and say which project you are in.
2. Survey the roots: `list_folders` (recursive false) on the project root and on the content roots you already saw working in this project (for example `/CR_Legacy`, `/CR_Legacy/Playsets`, `/CR_Legacy/Creative/Maps/Prefabs`, the creative devices roots). Note the folder names that look like props, prefabs, vegetation, buildings, materials.
3. For each category below, run short substring searches (`name`) inside the most likely folders (`folder_path`). Try at least 3 different words per category before you write "not found". Use these words as a start:
   - Buildings and structures: barn, farm, house, cabin, shed, silo, stable, coop, windmill, tower, shack, ranch, cottage
   - Trees: tree, oak, pine, birch, palm, trunk, log, stump
   - Plants: fern, bush, shrub, grass, flower, plant, hedge, bramble, crop, corn, wheat, pumpkin, vegetable, field
   - Ground and paths: dirt, gravel, grass, mud, path, road, sand, soil, ground, floor, terrain, decal, material
   - Fences and gates: fence, gate, picket, rail, wire, wall
   - Farm props: hay, haystack, bale, tractor, trough, barrel, crate, well, cart, wagon, scarecrow, ladder
   - Water and rocks: pond, stream, rock, boulder, cliff
   - Chickens and animals: use `ListDeviceAssets` with `nameFilter`: wildlife, animal, chicken, creature, spawner. Write the exact device names and say which animal each one can spawn (if the asset name or description says it; otherwise write "unknown").
   - Light and sky: look for a day-sequence or sky device (`ListDeviceAssets` with sky, sun, time, light, weather).
4. For every useful result write ONE row: category, the full asset path exactly as returned, a short note (what it looks like by its name, whether it is a prefab, a prop or a device). Do not guess sizes: they are measured in step 2 with a sample.
5. Mark `allowed in a playable island: unknown` for everything. It is only known when a session validates it (step 5). Prefer assets from the same folders as the pieces that were already placed in this map without a validation error.

## The file to write: `Claude/docs/map/ASSETS.md`
Start with 3 lines: date, how many MCP calls you made, which roots you browsed. Then one table per category with the columns `Asset path | What it is | Note`. Then two sections:
- `Not found`: per category, every word you tried (at least 3) and the folder, so it is visible that you looked.
- `Not reachable via MCP`: anything you wanted but the MCP tools cannot list or open (say which tool failed and what it answered). Do not invent rows.

Minimum to call the first pass done (if you cannot reach a line, say so in the file and why):
- at least 4 different buildings or structures,
- at least 3 kinds of trees and 3 kinds of plants or crops,
- at least 2 ground surfaces or materials for grass, dirt and a path,
- at least 2 kinds of fences and one gate or opening,
- at least 4 farm props,
- every device that can spawn animals, with what it spawns.

## When the first pass ends
Reply in 8 lines at most: rows per category, which minimums you reached, which not and why, the number of MCP calls. Then say: "Step 1 first pass done. Waiting for the gap list." and STOP.

## Gap pass
The gap pass is the file `Claude/docs/STEP-1B-GALLERY-PASS.md` (the owner's gallery method: gallery first, asset inside the gallery, then the rest by asset name going back to its gallery). Follow it when the owner says so. It also writes the lessons and ends the step.

## Lessons (every step ends with this; nothing is learned silently)
Right after the gap pass, before you stop, write `Claude/docs/map/LESSONS-STEP-1.md` with ONLY facts from this step:
- **Expected / happened**: what you expected a search or folder to return, and what it really returned (exact tool, filter, answer).
- **What worked**: the folders, words and filters that found the most assets; which words found nothing.
- **What the MCP could not reach** (from the section above) and what Claude found in the editor that you missed (from the gap list).
- **Rules**: at most 3 lines, each general (no map name, no asset paths, no task IDs): WHEN it applies, WHAT to do, WHY it matters.

Then, in this order, and each one only if it is available (a one-line note if not, never an error):
1. Call the `skill-reflector` agent with `LESSONS-STEP-1.md` as evidence. It only QUEUES proposals; the owner approves them on the Skills page. Do not edit any skill yourself.
2. If the second brain is configured, call `second-brain-librarian` in sync mode with the asset findings that are reusable across projects (which folders hold buildings, vegetation, fences, animal spawners, and the search words that worked). If it is not configured, say so in one line.

## Owner checkpoint
The owner reads `ASSETS.md` (and the summary) and answers ONE of: `approved`, or a precise list such as "missing: barns". The owner does not need to open UEFN for this step. Only after `approved` is step 2 started.
