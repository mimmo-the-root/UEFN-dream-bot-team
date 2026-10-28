# Gap list for step 1 (written by Claude from the Content Drawer, plus the owner's method)

## Why the first pass missed things
The first pass searched ASSET NAMES inside `/CR_Legacy/Playsets/PlaysetProps`. The owner's method is the opposite and finds much more: search the FOLDER names for the keyword, then browse INSIDE the matching folders. The assets in there usually do NOT contain the keyword in their own name (for example a barn asset inside "Frenzy Farm Barn & Shed Gallery" is not called "barn").

## Folders seen in the Content Drawer (search "farm", FortniteGame, All)
- Fortnite / Galleries / Building / `Farm Building Gallery`
- Fortnite / Galleries / Building / `Frenzy Farm Barn & Shed Gallery`
- Fortnite / Galleries / Building / `Frenzy Farm House Gallery`
- Fortnite / Galleries / Props / `Farm Parts Gallery`
- Fortnite / Galleries / Props / `Frenzy Farm Prop Gallery`
- Fortnite / Galleries / Props / `Plumpton Farm Gallery`
- Fortnite / Prefabs / `Frenzy Farm`
- Fortnite / Props / `Frenzy Farm`

## What to do (budget 15 calls)
1. Find the real mount path of these folders with `list_folders` (`root_path`, recursive false): start at the content root that holds `Fortnite` (try `/Fortnite`, then its subfolder `Galleries`, then `Building` and `Props`; also `Prefabs` and `Props` under `Fortnite`). Report the exact path you got. If the Fortnite root is not reachable, write it under `Not reachable via MCP` with the answer.
2. For each of the 8 folders above, list what is inside (`find_assets` with that exact `folder_path`, and `asset_type` if the answer is large). Never unfiltered. Add the useful assets to `ASSETS.md` (buildings, barn and shed parts, house parts, props), with the full path as returned.
3. Do the same folder-first search with these other keywords on the folder names under `/Fortnite` (Galleries, Prefabs, Props): `tree`, `nature`, `vegetation`, `foliage`, `plant`, `fence`, `wall`, `ground`, `terrain`, `path`, `road`, `rock`, `water`, `pond`, `crop`, `garden`. List the matching folders first (one `list_folders` per level), then look inside the 2 or 3 most promising ones.
4. Add a column or note "found in folder X" so the owner sees which folder held it.

## Lesson to record in LESSONS-STEP-1.md
Searching asset names finds almost nothing when the assets are organized in gallery folders: search folder names for the keyword first, then list the content of the matching folders.
