# Step 2 of 8: build the farm: ground first, then buildings, props and trees (sample first, then batches)

This is the real test of the kit: you build the environment with the MCP, the owner looks at the result. Source of the assets: `Claude/docs/map/ASSETS.md` (section Picks). Use only names from it, with their full paths. Placement tools you already used: `SceneTools/add_to_scene_from_asset`, `set_actor_transform`, `get_actor_bounds`, `set_actor_folder`, `get_actor_transform`, `find_actors`.

## Rules
- MCP only, through the kit's lab guard (as in `mcp-level`). First call: `get_current_level`; if it is not this lab project, stop.
- No StartSession, StartGame, PushChanges. Verse is not touched in this step. Never `find_assets` without a filter.
- Delete nothing. The old farm pieces already in the level are moved with `set_actor_folder` into a folder `Farm_Old_v1` (do not hide or remove them). Everything new goes in the folder `Farm` (subfolders `Ground`, `Buildings`, `Props`, `Trees`). Fences and chickens are step 3.
- After a timeout or a lost answer on a placement, never repeat it blindly: read the editor state (`find_actors` in the folder) first, then decide.
- No random retries: if a call fails, write the exact error and the arguments in `Claude/docs/map/PLACED.md` and continue with the next item; report the failures at the end.

## Reference: how the published tutorial did it (an Epic community tutorial on a farm built with the MCP)
The author worked in small prompts, in this order, and you follow the same order of ideas: (1) inventory only, nothing built; (2) the first layout in farm style: barn, house, silo, stable, shed, field; (3) a review of that layout, fixing distances, and a SAMPLE of the trees before filling the level with vegetation; (4) grass and dirt on the ground, paths, fences and chicken spawners; (5) save the work. The review is done by looking at the viewport, from above and from the player's eye level. Not all of the author's prompts are public, so do not hunt for them: the steps below already contain the method.

## You can see the level
`EditorAppToolset/CaptureViewport`, `GetCameraTransform`, `SetCameraTransform` and `SetViewportViewMode` exist. Use them to look at your own work: a top view (camera high, looking down) and a view at eye level (about 170 cm high, looking along the yard toward the barn and toward the pen). Save each capture in `Claude/docs/map/shots/` (`step2-a-ground-top.png`, `step2-b-layout-top.png`, `step2-b-layout-eye.png`, ...), open the images and look at them. Write one line per image on what you see: is the ground grass or the grid, are buildings closed and facing the yard, does anything float, sink or overlap, is the pen empty. If a capture fails, write the exact error and say so: do not claim you looked.

## Pass 0: the ground (landscape and grass). It was never built: do it first
Today the level is a flat grid floor with no grass at all. A farm needs real ground before anything is placed on it. Work in this order and stop at the first that works:
1. Look: `find_actors` for any `Landscape` actor in the level and list the MCP toolsets (the known-tools list in `Claude/hooks/mcp-known-tools.json`): is there any landscape, terrain or foliage tool? Write what you found (yes/no, tool names) at the top of `SIZES.md`.
2. If there is a landscape tool: create the landscape for the play area (about 100 m by 100 m is enough for the farm), with a grass material. Read back its bounds, then capture a top view and an eye-level view.
3. If there is none (the likely case): cover the play area with ground tiles. Use the ground picks from `ASSETS.md` (the grass-to-dirt tiles `PPID_CR_Legacy_BP_Grass_Temp_Dirt_*` with their `_Straight`, `_InnerCorner`, `_Outer` edge pieces, the solid dirt and gravel tiles). In the sample pass, place one tile of each type and measure it. Then tile the whole area with grass, with a dirt yard in front of the barn and a dirt lane from the yard to the pen; the edge pieces go on the borders. The old flat floor is not deleted: move it with `set_actor_folder` to `Farm_Old_v1`, or leave it under the tiles, and say which and why. Watch the z height of the tiles against the floor (no flicker, no gaps).
4. If the MCP cannot make grass in any way, do NOT fake it: write in `LAYOUT.md` section `Owner ground steps` the exact editor steps for the owner (Landscape mode, create, grass material layer, size), and continue with the buildings on the flat floor, marking the step as "ground waits for the owner".
After the ground is placed, capture a top view and look: is it grass with a dirt yard and lane, with no grid showing through? Fix before going on. Ground counts in "Done means": the ground must cover the whole farm area, with a visible grass and a visible dirt yard.

## Pass 1: the sample (about 10 calls)
Goal: measure the real size of each piece type instead of guessing.
1. Place ONE piece of each type, far apart in an empty corner of the level, in folder `Farm_Sample`: a barn wall, a barn roof, a rural house wall, a haybale, a crate, a tractor, a tree (large), a shrub, one ground tile of each type, and the whole-barn playset `PID_CP_FrenzyFarm_L_Barn_a` (try it as one building).
2. For each, read back with `get_actor_bounds`. Write the table `Claude/docs/map/SIZES.md`: asset, placed OK (yes/no and the error), bounds (x, y, z in cm), origin note (is the pivot at the base or the center?).
3. Decide, and write it in `SIZES.md`: build the barn as ONE playset or from pieces. If the whole playset placed and its bounds look like a barn (roughly 7 by 9 by 7 tiles), use it and say so. If any asset is rejected, do not use it again.
4. Delete nothing: move the sample to the folder `Farm_Sample` and leave it; it is cleaned in the last step.

## Pass 2: the layout (no MCP calls, write a file)
Write `Claude/docs/map/LAYOUT.md` BEFORE placing anything: a top view as a small text grid and a list with the position (x, y, yaw) of every object, computed from the measured sizes. Rules for the layout:
- Compose a farm, not a scatter: the barn at one side with its door facing the yard; the house beside it; a central open yard; a large pen (an open rectangle left empty on purpose, step 3 puts the fence and the chickens there); haybales along the barn wall and some in the field; crates, tractor, scarecrow, tank cart and wheelbarrow near the barn; trees along the edges and a few in the yard; shrubs and hedges by the buildings; the weathervane on the barn if the roof allows.
- Keep clear: the pen, a 4 m wide lane from the yard to the pen, and the player start area. Nothing may overlap (check with the bounds: no two bounding boxes intersect except stacked pieces by design).
- Minimums to call this pass done: the ground covers the whole farm area (grass plus a dirt yard and lane); 1 barn (whole or from at least 12 pieces), 1 house (at least 8 pieces), 4 haybales, 6 crates or barrels, 4 farm props, 10 trees (3 kinds), 8 shrubs or hedges. About 120 to 200 actors in total is normal.

## Pass 3: build in batches
- Place in batches of 15 to 25 objects per call or script (the kit rule: 5 or more reads in ONE script). Folder per group: `Farm/Ground` (first), `Farm/Buildings`, `Farm/Props`, `Farm/Trees`.
- After each batch: read back the folder with `find_actors`, compare the count with the batch, and check 2 random objects with `get_actor_transform` against LAYOUT.md. Append every placed object to `Claude/docs/map/PLACED.md` (asset, folder, final transform, ok or error).
- If a piece floats or sinks (the pivot is not at the base), fix the z once from the measured bounds and write the correction in `SIZES.md` as a rule for the next steps.

## Pass 3b: review, then fix (the tutorial's second prompt)
After the batches: capture the top view and two eye-level views (yard toward the barn, yard toward the pen). Compare with `LAYOUT.md`. Fix what you see with `set_actor_transform` (distances too small or too large, buildings facing the wrong way, floating or sunk pieces, props inside walls), then capture again. Do at most 2 review rounds. Write in `PLACED.md` what each round changed. Only then the owner checkpoint.

## Done means (objective, not "looks built")
Write at the top of `PLACED.md`: counts per group versus the minimums above, the number of failures with their errors, and the number of actors in `Farm` found by `find_actors`. The step is done only if all minimums are met and every object has a read-back.

## Lessons (end of the step)
Write `Claude/docs/map/LESSONS-STEP-2.md`: expected / happened (what each tool did, what failed, how long a batch takes), what the sizes were against the guesses, what the layout missed once built, and at most 3 general rules (no map names or paths): when it applies, what to do, why. Then call `skill-reflector` with that file as evidence (it only queues proposals for the owner) and, if the second brain is configured, `second-brain-librarian` in sync mode (placement recipe: sample, measure, layout file, batches, read-back). If something is not available, one line, no error.

## Finish
Reply in 8 lines: counts per group, failures, actors in `Farm`, MCP calls. Say "Step 2 done. The farm is placed: owner, please look at the viewport." and STOP. Never start step 3 on your own.

## Owner checkpoint
The owner looks at the viewport and at your captures in `Claude/docs/map/shots/` and answers `approved` or a precise list: "the barn door faces the wall", "too many trees", "tractor inside the barn". Cod fixes only what is listed, with `set_actor_transform`, then stops again.
