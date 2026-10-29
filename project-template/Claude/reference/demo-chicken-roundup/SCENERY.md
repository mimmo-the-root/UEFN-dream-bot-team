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
| The chickens | `Device_WildlifeSpawner_V2` (6 spread over the field, 1 on the pen) | Never assume the animal: read it and set it (the default was a wolf). Keep spawn counts low. Not an Item Spawner and not a trigger |
| Delivery zone | `Volume` (14 x 14 m) and `Device_CaptureArea_V2` | the pen detects delivery |
| Round | `Device_Timer_V2`, `Device_ScoreManager_V2`, two `Device_HUDMessage_V2`, `Device_VFXSpawner`, one Audio Player | referenced by the Verse manager |
| Players | `BP_Creative_Player_Spawner_Prop`, one per player | 4 pads at least 300 cm apart, not overlapping |
| Island | `Device_ExperienceSettings_V2_UEFN` | owner step: max players 4, one team, 1 round, 3 minutes |
Classic devices accept the object property tools only with a text value. Device references of the Verse manager may be refused by the MCP: list them for the owner.

## Order that worked
1. One sample of each piece, far apart in an empty corner (folder `Farm_Sample`); measure the bounds and write them down.
2. Ground tiles over the play area. 3. The barn as one playset, then the house pieces. 4. The pen fence with a gate (leave a 5 m gap if the gate piece is closed). 5. Props and trees. 6. Devices. 7. Read back every step and capture the viewport from above and at eye level.
