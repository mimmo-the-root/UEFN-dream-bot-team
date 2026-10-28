# STEP 3C - Island Settings: read, set, read back, report

Do NOT change anything else. Work with the MCP only (ObjectTools get_properties / set_properties on the Island Settings device; find it with find_actors / the Outliner name "island settings").

## 1. Read
List every property of the Island Settings device with its exact name and current value. Save the full list in `Claude/docs/map/ISLAND-SETTINGS-READ.md`.

## 2. Set (only options that exist as properties; write the exact property name you used)
| Group | Option | Value |
|---|---|---|
| Structure | Max Players | 4 |
| Structure | Teams | Cooperative (no teams) |
| Matchmaking | Minimum Players | 1 |
| Round | Total Rounds | 1 |
| Round | Time Limit | 3 minutes |
| Spawning | Respawn Type | On |
| Spawning | Join in Progress | On |
| Player > Equipment | Pickaxe Destruction | None |
| Player > Equipment | Environment Damage | Off |
| Player > Equipment | Pickaxe Damage | Off (unless a mechanic needs it) |
| Player > Equipment | Start with Pickaxe | No (unless a mechanic needs it) |
| Player > Equipment | Disable Harvest Slot | True |
| Player > Build Mode | Building Can Destroy Environment | No |
| Player > Build Mode | Allowed to Edit | Default |
| Player > Build Mode | any "Allow Building" / building-enabled option, if present | None / Off |

## 3. Read back
Read every property again. Write `Claude/docs/CONFIG-CHECK.md` with one row per option: property name, wanted, read back, status (SET / NOT FOUND / READ-ONLY / DIFFERENT). Never write "configured" for a value you did not read back.

## 4. Owner list
Every option marked NOT FOUND, READ-ONLY or DIFFERENT goes into `Claude/docs/OWNER-TODO.md` with: where to click (Outliner > "island settings" > Details > group > option), the value to set, and why (barn must not be destroyed by the pickaxe, no building).

## 5. Lessons
Write `Claude/docs/LESSONS-STEP-3C.md`: what the MCP could and could not set, exact property names, what the kit must say in /environment and /demo about Island Settings.

## Owner checkpoint (do not do it yourself)
Press Play, hit the barn with the pickaxe, try to build. Report expected/observed.
