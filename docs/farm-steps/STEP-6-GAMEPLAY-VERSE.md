# Step 6: the Chicken Roundup gameplay in Verse (digest first, wiring list second, nothing started)

Prerequisite: step 3 is done (farm, pen, spawners `PenSpawner` and `ChickenSpawner_1..6` with the chicken animal, session validated) and the owner has walked the farm. Read `Claude/docs/map/OWNER-TODO.md` and the owner's notes first; if the owner reported a problem with the farm or the live chickens, fix that before writing Verse.

## What the game is (the tutorial's gameplay prompt, in our words)
The chickens have escaped from the coop. The player collects them by running up to them: when the player overlaps a chicken it tames and FOLLOWS the player. Bringing a chicken back into the pen stops it following and gives the player ONE point. The points are shown on screen starting from zero. A celebration effect plays at every delivery. Base version: one player. Keep the code structured per player (score kept per agent) so the kit's 4-player co-op can be added later without rewriting.

## Rules
- Use the MCP and the kit's guard. No StartGame and no StartSession in this step (the owner starts the game after linking). `BuildAll` yes. Never invent a Verse API: every device, event and function you use must be found in the Verse digest files of this project.
- Never silently replace a requested mechanic. If the following mechanic is not possible, you stop and write it in `OWNER-TODO.md` under `Decision needed`, with the options and what each changes; you do not switch to carried items on your own.
- Write only Verse files in the project's Verse folder, `Claude/docs/map/VERSE-DIGEST.md`, `WIRING.md`, `OWNER-TODO.md`, `LESSONS-STEP-6.md`.

## Part 1: the digest check (write `VERSE-DIGEST.md` BEFORE any code)
Search the Verse digests (`VerseToolset` ListFiles / Grep / ReadFile on the digest files) and answer each with the exact identifier you found, or "not found":
1. The wildlife spawner device: its events (spawned, tamed, eliminated, whatever exists) and functions (spawn, despawn, tame, follow, set target) and how to get the spawned creature as an object.
2. How a creature can FOLLOW an agent: a built-in follow or tame behavior of the device, or a navigation or movement API usable from Verse (move to, follow target, navigation target). Say which one you will use.
3. How to detect delivery: a volume or zone device over the pen (an overlap event), or checking each chicken's position against the pen bounds. Say which.
4. The score on screen: the score manager or HUD device, or a UI widget; how to start at zero and how to show per-player points.
5. The celebration: the effects or VFX device, its enable or play function, and the sound.
6. Tags: whether devices can be found by tag from Verse (`GetCreativeObjectsWithTag` and the tag class) and whether the MCP can set a tag on a placed device (look in `mcp-known-tools.json`).
Write for each: found / not found, the identifier, the file it was in. This file is the ground truth for the code.

## Part 2: the design, in `WIRING.md` (the wiring manifest)
Before the code, write the list of every reference the Verse device will need: `Field | Type | Count | Points to | Name in the level | Who sets it (MCP or owner)`. Target (the tutorial's version, adjust to the digest): six chicken spawners (`ChickenSpawner_1..6`), the pen spawner (`PenSpawner`), the delivery zone, the score or HUD device, two celebration effects. Test, with ONE harmless read and ONE write on the first placed instance, whether the MCP can assign an object reference to a Verse device field (`SetDeviceProperty` was rejected for references in the first run). Write the verdict. Everything the MCP cannot set goes to the owner list. If the tag lookup works (digest and MCP both), build a tiny separate probe device first (finds the six spawners by one tag and logs the count) and report; if it works the final device uses tags and the owner has nothing to link. Do this as an experiment, not as the only path: keep editable fields as the fallback.

## Part 3: the code
1. A Verse device `chicken_roundup` (file `chicken_roundup.verse`): per-player score, the follow behavior chosen in Part 1, the delivery detection, the score on screen from zero, the celebration. When a chicken is delivered it stops following and cannot score again. A tamed chicken that was not delivered never scores (this was the tutorial's bug: two tamed and one delivered counted two).
2. Self-check in `OnBegin`: log one line `[WIRING] chicken_spawners=<n>/<expected> pen=<yes|no> zone=<yes|no> hud=<yes|no> vfx=<n>/<expected>` and, if anything is missing, one line per missing item. The kit reads these lines after the game starts.
3. Place the device in the level (name `ChickenRoundup`, folder `Farm/Gameplay`), with the references the MCP could set. `BuildAll` until it is clean. Read back the properties of the placed device and write how many references are set.
4. Do not start the session or the game.

## Part 4: the owner list, field by field
Rewrite `OWNER-TODO.md`, in order, only what the MCP could not set. Each item: the editor steps (select `ChickenRoundup` in the Outliner, Details panel, section name, field name), which level device goes in which entry (for arrays: "add six entries, ChickenSpawner_1 to _6 one per entry"), the warning "PenSpawner is not one of the six", and how Claude will check it. End with: "When done, tell Claude: I linked <list>. Claude reads the references, builds, and only then starts the session." Then the test the owner does in the game: score starts at zero; walking up to a chicken tames it and makes it follow without a point; delivering gives one point and the celebration; two tamed and one delivered gives ONE.

## The wiring gate (fixed order, never skip)
build, then the owner links, then Claude reads back the references and the build is clean, then StartSession, then StartGame with the owner in the game, then Claude reads the `[WIRING]` log line and reports "n/n assigned" before anything is called working. A game started before the references are read back is a false start.

## Lessons
Write `Claude/docs/map/LESSONS-STEP-6.md`: expected / happened (digest findings, what the MCP could and could not set, tags result), and at most 3 general rules (no map names or paths): when it applies, what to do, why. Then call `skill-reflector` with it as evidence (it only queues proposals) and, if the second brain is configured, `second-brain-librarian` in sync mode (the wildlife follow/tame recipe, the wiring manifest, the self-check log).

## Finish
Reply in 8 lines: digest verdicts, references set by the MCP and by the owner, tag experiment result, build status. Say "Step 6 ready. Owner: link the fields in OWNER-TODO.md." and STOP.
