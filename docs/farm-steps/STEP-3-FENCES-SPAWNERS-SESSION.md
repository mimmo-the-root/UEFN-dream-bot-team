# Step 3 (combined, one run): replace-not-stack fix, pen and fences, chicken spawners, save point, validation

Run these parts in order, in one go, and stop only at the end or at a stop rule. The owner is asleep: do not ask anything, make the most reasonable choice, write it down, and continue. Never use `find_assets` without a filter. Delete only what the replace rule allows. After a timeout on a change, read the state first, never repeat blindly. Log everything in `Claude/docs/map/PLACED.md` (block per part).

## Part A: do `Claude/docs/STEP-2C-REPLACE-NOT-STACK.md` first, completely
(One object per place; replace your own pieces, never delete the old ones from before you, move or hide them; audit by cell; captures.) When it is done, go on.

## Part B: the pen, fences and gate (the tutorial's terrain-prompt follow-up)
1. The pen is the empty rectangle reserved in `LAYOUT.md`. Fence it with ONE fence family from `ASSETS.md` Picks (Frenzy Farm picket `PPID_CR_Legacy_Apollo_Picket_Fence` and `_Doorway_A` for the gate, or `Apollo_Wooden_Fence_*`). Measure the fence piece (bounds) from the sample you already have, compute the piece count and the corners from the pen size, place them without gaps or overlaps (replace rule), with ONE gate opening facing the lane from the yard, wide enough for a player (at least 2.5 m). Read the bounds back.
2. A clean dirt path (packed dirt, not the bright gravel if it looks snowy in a capture) from the yard to the gate, and a short path from the house to the yard if missing. Replace tiles, never stack.
3. Put the old devices (wildlife spawner, capture item spawners, the blue circle) where they make sense or leave them, and say which. Do not delete them.
4. Capture a top view and an eye-level view toward the pen; look; fix once.

## Part C: the chicken spawners (check the animal, do not assume)
1. Place a wildlife spawner device inside the pen, named `PenSpawner`, and six more named `ChickenSpawner_1` to `ChickenSpawner_6` around the farm (outside the pen, in open grass and yard, not inside buildings or on the lane). Use `PID_Device_WildlifeSpawnerV2` (it exists in the level already once).
2. Read the device properties (`ListDeviceProperties` / `GetDeviceProperties`) and set the animal type to CHICKEN on every one of them with `SetDeviceProperty`, then read it back. If the animal list has no chicken, or the property cannot be set, write the exact error and the list of values it offers and continue (this goes to the owner list below).
3. Write `Claude/docs/map/WIRING.md` section `Chicken spawners`: device name, location, animal read back (chicken or the exact value), and whether it is assigned to a Verse device (not yet: the Verse device does not exist in this step).

## Part D: save point (the tutorial saves before the first playtest)
Look in `Claude/hooks/mcp-known-tools.json` for a save tool and for a Lore or revision-control tool. Save all with the tool if it exists and read the saved state back. For Lore check-in: if a tool exists use it with the message "Farm environment: ground, buildings, props, trees, pen, spawners" and read the state back; if none exists, write in the owner list: "Save the level and check in to Lore from the editor". Do not claim a save you cannot confirm.

## Part E: validation (Start Session) and the walk-in preparation
1. `SessionToolset/StartSession` (about 90 s; do not call it twice while one is running). Do NOT call `StartGame` in this step: a game without a player proves nothing.
2. If the session fails validation, read the real validation errors (message log / the tool answer), not a summary. Typical cause (tutorial): vegetation or assets not allowed in a playable island. Replace each disallowed asset with an allowed one of the same style IN THE SAME PLACE (replace rule: delete yours, place the new one at the same transform), list each substitution, then try again. At most 3 attempts. If the editor offers an auto-fix, do not use it: fix the errors yourself.
3. When the session is up (editing mode is fine), stop. Write the result in `PLACED.md`: attempts, errors read, substitutions.
4. If after 3 attempts it still fails: stop and write the exact errors; this is a finding, not a failure to hide.

## Lessons (one file for the whole run)
Write `Claude/docs/map/LESSONS-STEP-3.md`: what each tool did, what the validation said, how the replace rule played out, what the captures showed, and at most 3 general rules per part (no map names, paths or task IDs): when it applies, what to do, why. Then call `skill-reflector` with it as evidence (it only queues proposals) and, if the second brain is configured, `second-brain-librarian` in sync mode (pen and fence recipe, wildlife spawner chicken setting, validation substitution). If something is not available, one line, no error.

## The owner list (write it at the end as `Claude/docs/map/OWNER-TODO.md`)
Only what you could not do with the MCP: the chicken animal setting if it failed, Lore check-in if no tool, anything validation left. For each item: exact editor steps (where to click, what to set), why, and how Claude will check it afterward. Then the next owner action: "Press play in Fortnite, walk the farm, enter the pen, look for live chickens; tell Claude what you see (expected / observed)."

## Finish
Reply in 8 lines: parts done, counts, validation result, owner list size. Say "Step 3 done. Owner: walk the farm in the session." and STOP. Do not write Verse, do not start the game, do not start the next step.
