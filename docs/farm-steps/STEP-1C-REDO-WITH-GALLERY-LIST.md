# Step 1C: redo the inventory with the real gallery list (read-only, MCP only)

New fact from the editor. The gallery `Fortnite / Props / Frenzy Farm` (254 assets) is not a separate place: its assets are playset props in `/CR_Legacy/Playsets/PlaysetProps`, the folder you already searched. The Content Drawer shows a short Display Name (for example "Rural Doorway A"); the real asset name is the long one (`PPID_CR_Legacy_Apollo_Rural_Doorway_A_2862ce3b`). Searching the display name finds nothing; searching the real name, or its prefix, works. The exact list copied from the editor is in `Claude/docs/map/GALLERY-props-frenzy-farm.txt` (one line per asset, the path is inside the quotes). Read that file: it is the ground truth for this gallery. Do not search for names that are in it, take them from it.

## Rules
- MCP only. Read-only: do not place, move, delete or edit anything in the level. No StartSession, StartGame, PushChanges, BuildAll. Never `find_assets` without a filter. Budget: about 25 MCP calls.
- Write only `Claude/docs/map/ASSETS.md` (rewrite its `Picks` and `By gallery` sections) and `Claude/docs/map/LESSONS-STEP-1.md`.

## What to do
1. Read `GALLERY-props-frenzy-farm.txt`. Group its assets by role, with the full asset path: barn and shed pieces, rural house walls, doorways and windows, roofs, fences and gates, haybales, crates, farm props (tractor, scarecrow, tank cart, wheelbarrow, water wheel, weathervane, pulleys), plants. Count the pieces per group. Note which variants share the same base name (they differ by a hash suffix: they are the same piece with different colors or settings; list the base name once and say how many variants).
2. Compare with the first pass. List what the first pass missed that this gallery contains (for example haybales, the Rural house set, crates), and what the first pass found that is NOT in this gallery (another style: say which).
3. Choose ONE style family for each role, preferring this gallery (the "Frenzy Farm" family) so styles do not mix: barn, house, fence and gate, haybales, crates and props. For the roles this gallery does not cover (trees, ground and paths, hedges, rocks) keep the first-pass picks but say they come from another family, and which.
4. The `By gallery` table now has one row for this gallery with the real path, the count, and the roles it covers.
5. The other galleries (Farm Building, Barn & Shed, House, Farm Parts, Plumpton Farm, Prefabs/Frenzy Farm, the Nature and Tree galleries) are not listed yet. Do not guess their content. If a `GALLERY-*.txt` file for one of them exists in `Claude/docs/map/`, use it the same way; otherwise write in `Not found` that the list is still to be copied from the editor.
6. Verify two things with the MCP, one call each: that two assets you pick from the list (a Rural wall and a Haybale) exist (`find_assets` with `folder_path` `/CR_Legacy/Playsets/PlaysetProps` and `name` = a distinctive part of the real name), and what the answer looks like (path, type). Write it down.

## Lessons
Write `Claude/docs/map/LESSONS-STEP-1.md` (replace the earlier one, keep its good lines): expected / happened, why the first pass missed things (display name vs asset name, gallery grouping), and at most 3 general rules (no map names, no paths): when it applies, what to do, why. Then call `skill-reflector` with that file as evidence (it only queues proposals for the owner) and, if the second brain is configured, `second-brain-librarian` in sync mode (the gallery trick: display name differs from asset name, copy the asset list from the editor with Ctrl+A, Ctrl+C). If something is not available, one line, no error.

## Finish
Reply in 8 lines: groups and counts, what the first pass missed, the style family chosen per role, the two verification calls, MCP calls used. Say "Step 1 done. ASSETS.md is ready for your review." and STOP. Never start step 2 on your own.
