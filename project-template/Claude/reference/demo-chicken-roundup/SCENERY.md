# Farm scenery and devices: the recipe that worked

Proven in a real build of this pilot (an editor session with the MCP, read back after every step). Use these names and rules; do not guess. If a name does not resolve, say so and stop: a cube is never "built".

## Finding assets (read before any search)
- Props live in `/CR_Legacy/Playsets/PlaysetProps`. A full path is `/CR_Legacy/Playsets/PlaysetProps/<name>.<name>`.
- NEVER call `find_assets` without filters (about 120 MB, the MCP connection closes). Always `folder_path` plus `name`. Do not call `ListDeviceAssets` without need: it returns about 77,000 characters; look for one device class by name instead (Verse digest or a filtered search).
- Prove one name with `find_assets {folder_path, name}` before placing a series. Some names exist only with a hash suffix (see the barn archway and the house pieces below): use the name exactly as the search returns it.
- If the search fails, report the exact error and stop on red. Do not replace the farm with engine cubes and mark the row "built".

## Picks, one family per role (Frenzy Farm style)
| Role | Assets (prefix `PPID_CR_Legacy_` unless noted) |
|---|---|
| Whole barn (one playset, 141 to 303 child actors) | `/CR_Legacy/Playsets/PID_CP_FrenzyFarm_L_Barn_a` |
| Barn pieces | `Apollo_Barn_Wall_C`, `Apollo_Barn_Roof_A`, `Apollo_Barn_Roof_A_Cap`, `Apollo_Barn_Door_Large_Base`, `Apollo_Barn_Steeple_A` |
| House | `Apollo_Rural_Wall_A_0303c232`, `Apollo_Rural_Doorway_A_2862ce3b`, `Apollo_Rural_Window_B_A_10879558` |
| Ground | `BP_Grass_Temp_Solid` (grass), `BP_Dirt_Temp_Solid`, `BP_Gravel_Solid`, edges `BP_Grass_Temp_Dirt_Straight_SM`, `_InnerCorner`, `_Outer` |
| Fence and gate | `Fence_Picket01`, `Fence_Picket01_Doorway1`, `Fence_Rural`, `Apollo_Picket_Fence`, `Apollo_Picket_Fence_Doorway_A` |
| Haybales | `Haybale_01`, `_02`, `_04`, `_05` |
| Props | `Apollo_Wood_Crate_02`, `Apollo_Farm_Tractor_01`, `Apollo_Farm_Scarecrow_01`, `Apollo_Farm_WheelBarrow_01`, `Apollo_Farm_ChickenCoop_01` |
| Trees and plants | `Athena_Tree_Large_2`, `Athena_Tree_Pine_3`, `Athena_Tree_Medium_01_`, `Athena_Prop_Plant_Shrub_01`, `CP_Farm_Cabbage_01`, `Hedge_High_Rectangle` |

## Sizes and placement rules (measured, cm)
- A ground tile is 512 x 512 x 12 (grass top at z 4); x centred, y starts at the tile origin. Scaled (4,4,1) it is 2048 x 2048. Dirt and gravel tiles go on z 12 over the grass.
- Walls and props sit on z 0. A haybale is centred and sinks 13 cm: place it at z 13. Barn wall 513 x 46 x 387. Fence piece about 512 wide.
- A large tree reports its whole canopy (about 2800 wide): scale it (Large_2 x0.3, Pine_3 x0.7, Medium_01 x0.7 give 8 to 10 m trees).
- `set_actor_transform` with only `scale` sends the actor to the origin: always send location, rotation and scale together (read, change, set).
- A whole playset places as a root plus many children, without folders: search a box larger than the footprint, count the children, then put them in a folder by script.

## Devices that worked (place with `PlaceDevice`, then `set_label` and `set_actor_folder` at once)
| Role | Class | Notes |
|---|---|---|
| The chickens | `Device_WildlifeSpawner_V2` (6 spread over the field, none in the pen; `spawnCount` 1, type index 0 = chicken, `values` of `set_properties` is a JSON string) | Never assume the animal: read it and set it (the default was a wolf). Keep spawn counts low. Not an Item Spawner and not a trigger |
| Scoring object | the egg prop `PPID_CR_Legacy_CP_Prop_Egg_Bottom` + `PID_Device_DamageVolume_V2` | see the section The egg: no Capture Area, no Volume, no spawner in the pen |
| Round | `Device_Timer_V2`, `Device_ScoreManager_V2`, two `Device_HUDMessage_V2`, `Device_VFXSpawner`, one Audio Player | referenced by the Verse manager |
| Players | `BP_Creative_Player_Spawner_Prop`, one per player | a new map already has `Player 1 Spawn Pad` and `Player 2 Spawn Pad` near x -378..0, y -157..-128: find them (`find_actors`, name `Spawn Pad`) and DELETE them with `remove_from_scene` FIRST, then place `PID_Device_PlayerSpawnPad` x4 (labels `PlayerSpawner_1..4`, folder `Devices/Players`, y 1500, x -1500 -1100 -700 -300, z 20) and read back that only those 4 remain |
| Island | `Device_ExperienceSettings_V2_UEFN` | owner step: max players 4, one team, 1 round, 3 minutes |
Classic devices accept the object property tools only with a text value. Device references of the Verse manager may be refused by the MCP: list them for the owner.

## Order that worked
1. One sample of each piece, far apart in an empty corner (folder `Farm_Sample`); measure the bounds and write them down.
2. Ground tiles over the play area. 3. The barn as one playset, then the house pieces. 4. The pen fence with a gate (leave a 5 m gap if the gate piece is closed). 5. Props and trees. 6. Devices. 7. Read back every step and capture the viewport from above and at eye level.

## Placement check (after every device and prop: MOVE, do not just report)
- After placing, read the location of every device and compare it with the zones that matter: the egg and its damage volume, the spawn area, the play boundary.
- A device that is in the wrong place is MOVED (read, change the location, set, read back) in the same step. Writing "it is inside the pen" in the notes without moving it is a failure. A chicken spawner at the egg, a pad inside a fence or a prop inside a spawn pad are all moved, then checked again.
- Existing devices of the template map are reused first (list the actors before placing anything): move them to the right place, rename them, and add only what is missing.

## The egg (owner decision, replaces the capture area: simple on purpose)
- Put `PPID_CR_Legacy_CP_Prop_Egg_Bottom` (label `PenEgg`, folder `Devices/Pen`) in the middle of the pen at x 980, y 2984, z 16, scale 2 (about 104 x 104 x 72 cm). On it put `PID_Device_DamageVolume_V2` (`/CRD_VolumetricRegion/SetupAssets/TID/DamageVolume/`, label `PenDamageVolume`, folder `Devices/Pen`) at x 980, y 2984, z 26, actor scale 0.6, `zone Shape` Cylinder, `zoneHeight`/`zoneWidth`/`zoneDepth` 0.3 (a cylinder hugging the egg, about 94 cm wide).
- Damage configuration: `affectsCreatures` true, `affectsPlayers` false, `affectsVehicles` false, `affectsGuards` false, `damage` 500; leave `enabledOnPhase` at Gameplay Only (`bEnabled` reads false in the editor and cannot be set: that is normal). Read it back and write it in `map/DEVICES.md`.
- Behind the egg put `PPID_CR_Legacy_WildWest_Scarecrow_01` (label `PenScarecrow`, folder `Environment/Props`) at x 1008, y 3172, z 16, yaw 180 as the landmark.
- Score: a chicken that goes into the egg is eliminated and the `EliminatedEvent` of the six chicken spawners gives one point in the Verse manager (each spawner makes one chicken, so each counts once). No `capture_area_device`: it fires for agents and a chicken is not one.
- Support devices (timer 180, Score Manager, two HUD Message, the Verse manager) go on the DemoDisplay stand at y -3000 to -3300, never in the field. Island settings the MCP can set: `roundTimeLimit_Override` true, `roundTimeLimit` 3; teams and environment damage are owner steps.
- A mechanic is `Done` only after a log line proves it (`[SIGNAL] chicken in egg N`) in a real play by the owner; before that it is `built, not played`.

## What the owner placed by hand (read first, keep, remember)
- Before building, list the actors and the folders. Anything the owner placed or configured himself (assets, the egg, the damage volume and its settings) is NOT moved, deleted or rebuilt. Read its transform and settings and write them in `map/DEVICES.md` under "Placed by the owner", so a later step or a new session reuses them instead of guessing.
- If the owner changes the mechanic, the spec (`GAME-SPEC.md` Assumptions), the plan, the roadmap, the Verse and the playtest list are updated in the same pass, and the old device is removed from the map.
