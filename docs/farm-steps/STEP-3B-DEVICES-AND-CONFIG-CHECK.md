# Step 3B: devices in folders, real names, messages, Island Settings, and a configuration check

The owner opened the level after step 3. Four rules were not respected, and the configuration was not checked. Fix them and then prove it with a check. Replace-not-stack applies (no duplicates), nothing from before you is deleted (move or relabel), no StartGame, no Verse in this step. After a timeout on a change, read the state first. Log every change in `PLACED.md` (block `Step 3B`).

## What went wrong (the owner's list)
1. **No Outliner folders for the devices.** The devices stand loose in the Outliner. Every device must live in a folder by role.
2. **The devices were not renamed.** The owner cannot tell them apart in the configuration pickers (a device list full of default names). Every device needs a clear label.
3. **Messages.** In the configuration the owner does not know which message to use (the HUD message, the score and timer texts). The text and the message fields must be set by you, or given to the owner as an exact text to paste.
4. **Island Settings.** It is not known if they were configured, and it is not known whether the other configuration problems were solved.

## Part 1: folders (SceneTools `set_actor_folder`)
List every device in the level (`find_actors`, filter by class or label, in small groups; never one huge read). Put each one in a folder:
- `Devices/Chickens`: `PenSpawner`, `ChickenSpawner_1..6`, and the old wildlife spawner (ambience) if it is kept.
- `Devices/Pen`: the capture area of the pen and the carried-item spawners (4).
- `Devices/Gameplay`: the Verse manager when it exists, the timer device, the score manager.
- `Devices/Display`: the HUD message devices and anything that only shows text (outside the play area, as the plan says).
- `Devices/Environment`: sky, light, day sequence devices.
Anything else: a folder named for its role, never the root of the Outliner. Read back with `get_actors_in_folder` that every folder holds what you listed, and that no device is left at the root.

## Part 2: names (`ActorTools/set_label`)
Every device gets the label `Role_Index` with letters, digits and underscore only (for example `ChickenSpawner_1`, `PenSpawner`, `PenCaptureArea`, `ChickenItem_1..4`, `RoundTimer`, `ScoreManager`, `HudStart`, `HudFinal`, `Sky_Main`). No default names (`PID_..._UAID_...`) may remain on any device. Two devices never share a label. Read every label back and write the table `Claude/docs/map/DEVICE-NAMES.md`: label, class, folder, position.

## Part 3: messages and texts
Find every device that has a message or text field (HUD message devices, timer, score manager, any billboard or text). For each: read the field with `ObjectTools.get_properties` (or the device tools), set the text yourself with `set_properties` when the MCP accepts it, and read it back. Texts to use: start "Round up the chickens! Bring them back to the pen.", final "Round over! Chickens delivered: {score}" (use the device's own placeholder if it has one; if not, a plain text without a placeholder), score label "Chickens". If a field cannot be set (a localized message asset the MCP cannot create), do NOT leave it empty: write in `OWNER-TODO.md` the exact text and the exact field, with the editor steps. Write what you set in `WIRING.md` (section `Messages`): device, field, text, set by MCP or owner.

## Part 4: Island Settings
Take the table `Island settings` from `Claude/docs/PLAN.md` (max players, min players, teams, round, respawn, join in progress). Look in `Claude/hooks/mcp-known-tools.json` for any tool that reads or writes island, project or game-mode settings. For each setting: read it (or say "not readable"), set it if a tool allows it, read back. Whatever the MCP cannot read or set goes to `OWNER-TODO.md` with the exact path in the editor (where to click) and the value. Do not claim a setting is configured unless you read it back.

## Part 5: the configuration check (`Claude/docs/map/CONFIG-CHECK.md`)
Build a table, one row per device and per setting, columns `Item | Setting | Expected | Read back | OK`. It must contain at least: every device's folder and label; the spawners' animal (chicken), `spawnCount` and the game limit of AI; the capture area (what it counts, team, the pen position inside the fence); the carried-item spawners (item, position inside the farm, not inside a building or fence); timer and score manager settings against the plan; the messages of Part 3; the Island Settings of Part 4; the Verse manager references (assigned or not: today not assigned, mark it as waiting for step 6, do not mark OK). Also run the validation messages again: read the message log or the session answer for WARNINGS (not only errors) and list each warning with the device or asset it names and what you did. A row is OK only if you read the value back; otherwise `not checked` or `owner`. At the end: counts OK / owner / not checked / failed.

## Lessons
Write `Claude/docs/map/LESSONS-STEP-3B.md`: what you missed in step 3 and why (the rules were in the plan and in the kit, the check was missing), and at most 3 general rules (no map names or paths) such as: "when a device is placed, give it a role label and a role folder in the same call, before reading anything else". Then call `skill-reflector` with it as evidence (it only queues proposals) and, if the second brain is configured, `second-brain-librarian` in sync mode (device folders and labels, messages, the configuration check table).

## Finish
Reply in 8 lines: devices moved to folders, devices renamed, messages set, Island Settings set and read back, rows OK / owner / not checked / failed, warnings found. Say "Step 3B done. Owner: look at the Outliner and at OWNER-TODO.md." and STOP. Do not start step 6.
