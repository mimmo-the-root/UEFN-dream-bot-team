# Step 2C: replace, do not stack (one object per place)

The owner looked at the viewport after step 2B. The farm is now right (big grass area, house with roof, barn, small trees, yard). One error remains, and it is a rule for everything you place from now on: you laid new pieces ON TOP of pieces that were already in that place. You must REPLACE them. The owner saw grass squares and grass-to-dirt edge pieces lying over the dirt and gravel yard (two tiles in the same spot, one visibly above the other, with the dirt showing through at one side), and the earlier note in `PLACED.md` says the dirt and gravel tiles were "stacked on the grass at z 12" on purpose. That is the wrong method.

## The rule (for this step and all next steps)
When a new object takes a place where another object already is, the old one goes away first. Which old one:
- Objects YOU placed in this farm (everything in `Farm/Ground`, `Farm/Buildings`, `Farm/Props`, `Farm/Trees`, and your own samples): delete the replaced one with the delete tool of `SceneTools`, after logging it (name, asset, transform, reason) in `PLACED.md`. This is the only case where you delete.
- Objects that were in the level before you (the items in `Farm_Old_v1`, and the devices): never delete. If one is in the way, move it with `set_actor_transform` out of the farm area or hide it with `set_actor_hidden`, and log it.
- Two pieces may overlap only when stacked by design (a roof on a wall, a haybale on a crate). Ground is never stacked: one tile per cell.

## What to do
1. Audit the ground. In ONE script (do not return raw actor lists, only the findings), read the bounds of every actor in `Farm/Ground` and group them by cell (x, y of the tile center). List the cells that hold more than one tile and, for each, which tiles and their z.
2. Fix the ground. For each cell with more than one tile keep only the intended one: dirt in the yard cells, gravel on the lane, a grass-to-dirt edge piece (`_Straight`, `_InnerCorner`, `_Outer`) on the yard border, grass everywhere else. Delete the rest (they are yours). Put the kept tiles at the same z as their neighbours, so the surface is flat and no tile sticks above another. Do the same for the grass squares laid over the yard in the area in front of the barn.
3. Audit the props. In one script, read the bounds of everything in `Farm/Props`, `Farm/Trees`, `Farm/Buildings` and of the old items in `Farm_Old_v1`, and list every pair whose boxes intersect (return only the pairs, with the overlap size in cm). For a pair where a new object lies over an old or another one: remove the replaced one by the rule above. For a pair of different things that merely touch (a shrub against a wall), move the new one away.
4. Check the result with a count: cells with more than one tile = 0; overlapping pairs not stacked by design = 0.
5. Look at it: `CaptureViewport` from above of the whole farm, and a low close view of the yard in front of the barn (the place with the tractor and the dirt). Save the captures in `Claude/docs/map/shots/` as `step2c-top.png` and `step2c-yard.png`, open them, and write one line each on what you see. If a capture fails, write the exact error: do not claim you looked.
6. Update `PLACED.md` with a block `Step 2C`: tiles deleted, objects moved, objects hidden, the two counts of point 4.

## Lessons
Add to `Claude/docs/map/LESSONS-STEP-2.md` a section `Replace, do not stack`: the rule above in one line each for ground, props and old items, and how you found the stacked cells (the audit by cell). General rules only (no map names or paths): when it applies, what to do, why. Then call `skill-reflector` with that file as evidence (it only queues proposals) and, if the second brain is configured, `second-brain-librarian` in sync mode.

## Finish
Reply in 6 lines: cells fixed, objects removed, objects moved, final counts. Say "Step 2C done. Owner: please look at the yard again." and STOP. Do not start step 3.
