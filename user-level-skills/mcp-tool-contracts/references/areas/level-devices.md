# MCP area: level-devices (ActorTools, SceneTools, EntityToolset, DeviceToolset)

Date: 2026-10-15. UEFN version: 42.40 (from previous-findings.md, same editor; not re-queried). Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (LAB_ROOT = GUID mount, set from PowerShell, scripts run from `Content`), task T-004. 69 tools in the area, 67 tried (ok or error recorded), 2 deliberately not tried (create_level, load_level). Scratch scripts: `Claude/logs/_explore/d0.py`..`d15.py`, `h.py`.

Full toolset names: `editor_toolset.toolsets.actor.ActorTools`, `editor_toolset.toolsets.scene.SceneTools`, `ValkyrieToolset.EntityToolset`, `ValkyrieToolset.DeviceToolset`. Answers `{"returnValue": ...}`. References are `{"refPath": "..."}`; actors are the `actorPath` of `find_actors` / the `refPath` returned by the add tools. Transforms: `{location{x,y,z}, rotation{pitch,yaw,roll}, scale{x,y,z}}` (plain XYZ, degrees).

LAB_LEVEL=1 is NOT needed and NOT used: in lab mode (`LAB_AGGRESSIVE=1`) the header of `mcp_lab.py` says LAB_LEVEL only matters in NORMAL mode; level writes inside LAB_ROOT are allowed in lab mode. The real limit is the path guard (section 3, trap 1).

## 1. What the area is for, tools

Place and move actors, label them, tag them, file them in outliner folders, add components (ActorTools + SceneTools); place catalog devices, read and set their settings, wire events (DeviceToolset); Verse entities and components (EntityToolset).

| Tool | R/W | Tried |
|---|---|---|
| Actor/get_label, get_tags, has_tag, get_actor_transform, get_actor_bounds, get_components, get_root_component, get_parent_component, get_component_actor, diff | R | yes ok |
| Actor/set_label, add_tag, remove_tag, set_actor_transform, look_at, add_component, remove_component, set_parent_component | W | yes ok (actor created in same process) |
| Scene/get_current_level, get_folders, get_data_layers, get_collision_channels, find_actors, get_actors_in_folder, get_actors_in_data_layer, get_actor_asset_path, is_actor_hidden, trace_world | R | yes ok |
| Scene/diff | R | yes: error `level (World) diff is not yet supported` |
| Scene/add_to_scene_from_class, add_to_scene_from_asset | W | yes ok |
| Scene/set_actor_folder, rename_folder, delete_folder, set_actor_hidden, save_actor, remove_from_scene, replace_actors_with_asset | W | yes ok |
| Scene/create_data_layer_asset, add_actors_to_data_layer, remove_actors_from_data_layer, load_actors, unload_actors | W | yes ok |
| Scene/replace_actors_with_class | W | yes: error `Failed to replace 1 actor(s) with 'StaticMeshActor'` (TargetPoint -> StaticMeshActor) |
| Scene/create_level, load_level | W | NO (see section 6) |
| Device/ListDeviceAssets, GetBindingOptions, ListEventBindings | R | yes ok |
| Device/ListDeviceProperties, GetDeviceProperties, SetDeviceProperty | R/R/W | yes: errors (section 3) |
| Device/PlaceDevice | W | yes: refused by lab guard x2, `Failed to place device` x1 |
| Device/AddEventBinding, RemoveEventBinding | W | yes: error (no event on bare ScriptDevice) and refused by guard (real pads) |
| Entity/FindEntities, ListEntityClasses, ListComponentClasses | R | yes ok |
| Entity/CreateEntity | W | yes: refused by guard x2, `abstract` x1 |
| Entity/GetComponents, GetEntityTransform, ListComponentProperties, GetComponentProperty | R | yes: error (arg is not an entity/component) |
| Entity/SetEntityTransform, AddComponent, RemoveComponent, DeleteEntity, SetComponentProperty | W | yes: refused by guard (no entity could be created) |

## 2. Verified recipes (all also in `recipes.json`)

All run in ONE Python process (see trap 1). `S`=SceneTools, `A`=ActorTools. `XF = {"location":{"x":0,"y":0,"z":200},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":1,"z":1}}`.

R1 Place an actor, rename `<Type>_<Function>`, tag, move, file in a folder, read back:
1. `S/add_to_scene_from_class {"actor_type":{"refPath":"/Script/Engine.TargetPoint"},"name":"T004_A","xform":XF}` returns `{"returnValue":{"refPath":"<level>:PersistentLevel.TargetPoint_UAID_..."}}` (the `name` becomes the LABEL; the object name gets a UAID suffix).
2. `A/set_label {"actor":{"refPath":"<a>"},"label":"TargetPoint_Spawn"}` true; `A/get_label` returns it.
3. `A/add_tag {"actor":..., "tag":"t004"}` (returns null); `A/get_tags` `["t004"]`; `A/has_tag` true; `S/find_actors {"collision_channels":[],"tag":"t004"}` finds it; `A/remove_tag` null.
4. `A/set_actor_transform {"actor":...,"xform":{...},"worldspace":true}` true; `A/get_actor_transform` reads it (yaw 90 came back 89.99999999999999). `A/look_at {"actor":...,"target":{"x":400,"y":0,"z":200}}` null, yaw became -9.46.
5. `S/set_actor_folder {"actor":...,"folder_path":"T004/Points"}` null, creates the folder; `S/get_folders` `["T004","T004/Points"]`; `S/get_actors_in_folder {"folder_path":"T004","recursive":true}` lists it; `S/rename_folder {"old_path":"T004/Points","new_path":"T004/Spawns"}` returns 2.
6. Cleanup `S/remove_from_scene {"actor":...}` true.

R2 Components: `A/add_component {"owner":{"refPath":"<a>"},"component_type":{"refPath":"/Script/Engine.PointLightComponent"},"name":"T004Light"}` returns the component refPath `<a>.T004Light`; `A/get_components` lists it (plus an auto BillboardComponent_0); `A/get_component_actor {"component":...}` returns the owner; `A/get_parent_component` returns `<a>.SceneComp`; `A/set_parent_component {"component":..., "parent":{"refPath":"<a>.SceneComp"}}` true; `A/remove_component {"component":...}` true.

R3 Place from an asset: `S/add_to_scene_from_asset {"asset_path":"/Engine/BasicShapes/Cube","name":"T004_Cube","xform":XF}` returns a `FortStaticMeshActor_UAID_...`; `S/replace_actors_with_asset {"actors":[{"refPath":"<a>"}],"asset_path":"/Engine/BasicShapes/Sphere"}` returns the new actor refPaths.

R4 Data layer: `S/create_data_layer_asset {"asset_path":"{lab_mount}/T004_DL"}` returns `{lab_mount}/T004_DL.T004_DL`; `S/add_actors_to_data_layer {"actors":[...],"asset_path":"{lab_mount}/T004_DL"}` null; `S/get_data_layers` then lists an instance; `S/get_actors_in_data_layer` lists the actor; `S/remove_actors_from_data_layer` null. Delete the asset with `AssetTools/delete {"path":"{lab_mount}/T004_DL"}` true.

R5 Level reads: `S/find_actors {"collision_channels":[],"name":"Brush"}` (a plain `{}` fails, see trap 2) returns descriptors {guid, class, label, bounds, actorPath, folderPath, dataLayerAssets}; `S/get_current_level` returns `/09e4e8d3-.../root_ai_lab`.

R6 Read a real device's wiring: take `actorPath` of a placed classic device from `find_actors` (e.g. label `Player 1 Spawn Pad`, class `BP_Creative_Player_Spawner_Prop_C`), then `Device/GetBindingOptions {"devicePath":{"refPath":"<path>"}}` returned `{"sourceEvents":["On Player Spawned","OnSpawnFailed"],"targetFunctions":["Enable","Disable","SpawnPlayer"]}`; `Device/ListEventBindings` returned `[]`. Use these event names exactly (with spaces) for AddEventBinding.

R7 Catalog: `Device/ListDeviceAssets {"nameFilter":"button"}` returns 3 devices with `assetPath.refPath` (`/CreativeCoreDevices/SetupAssets/PID_Device_Button.PID_Device_Button`) and `bIsVerseDevice`. Unfiltered: 383 items.

R8 Entities: `Entity/FindEntities {}` returned `[]` (no entities in this level); `ListEntityClasses {"nameFilter":"entity"}` 1508 unfiltered (1445 EntityItems), `ListComponentClasses {"nameFilter":"mesh"}` 178 unfiltered.

Previous findings re-run: `get_actor_bounds` after `GetSelectedActors` chain: **riconfermata** (actor path from find_actors works the same); "`get_component_actor` wants a component, not an actor": **riconfermata** (returns the owner actor of a component); "no get_actor_label": **diversa**: ActorTools has `get_label` / `set_label`; `find_actors`, `get_current_level`, `get_folders`, `get_data_layers`, `get_collision_channels` no-arg reads: **diversa**: `find_actors` needs `collision_channels` (error below), it did not answer with no arguments; `ListDeviceAssets` / `FindEntities` / `ListEntityClasses` / `ListComponentClasses`: **riconfermata** (heavy when unfiltered).

## 3. Traps (exact messages)

1. **Lab guard path rule (the big one).** In a write call every string starting with `/` must be an object created BY THE LAB IN THE SAME PYTHON PROCESS (`created` set), a class under `/Script/` or `/Engine/`, or start with `<LAB_ROOT>/`. Actor paths look like `/09e4.../root_ai_lab.root_ai_lab:PersistentLevel.X` (a `.` after the root, not `/`) so any actor that already existed, or that this lab created in an earlier process, is refused: `refused even in the laboratory, path outside /09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab: /09e4e8d3-.../root_ai_lab.root_ai_lab:PersistentLevel.Ta...` (set_label, add_tag, set_actor_transform, set_actor_folder, AddEventBinding, SetEntityTransform ...). Not circumvented. Do place + all writes + cleanup in ONE script. Reads on any actor path are fine.
2. `find_actors` with no `collision_channels`: `Function "find_actors", input param "collision_channels" is required by the function input schema Json, but is missing`. Pass `[]`.
3. `PlaceDevice` with a catalog path: `refused even in the laboratory, path outside /09e4.../root_ai_lab: /CreativeCoreDevices/SetupAssets/PID_Device_Button.PID_Device_Button` (also `/CR_Legacy/Playsets/PID_CP_Devices_Trigger...`, `/VerseDevices/_Verse/VNI/VerseDevices.Devices_creative_device`). Every catalog device lives outside the lab root, and the project has no device assets of its own (383 listed, only Verse ones are `/VerseDevices`, `/VerseInternalTesting`). So no catalog device can be placed in this lab. `PlaceDevice` with `/Script/FortniteGame.BuildingActor`: `Failed to place device '/Script/FortniteGame.BuildingActor'.`
4. `CreateEntity` with project/engine entity class: refused by the guard (`/09e4.../_Verse/Assets...`, `/EntityFramework/_Verse/VNI/Component.mesh_component`); with `/Script/Entity.BaseEntity`: `The entity class '/Script/Entity.BaseEntity' is abstract.` Only entity classes under `/Script/` pass the guard and BaseEntity is the only one, so no entity can be created here: all entity write tools were only reached as refusals.
5. Device property tools on a bare actor: `ListDeviceProperties/GetDeviceProperties/SetDeviceProperty`: `Parameter error: <actor> is not valid ScriptDevice for property 'Device'` (TargetPoint or classic BP device such as the spawn pad / IslandSettings) and, on a `/Script/VerseDevices.ScriptDevice` spawned with `add_to_scene_from_class`: `Verse device '<path>' has no resolved Script subobject (build Verse first?).` These tools need a placed device of a BUILT Verse class (see the `verse-build` area); classic devices are read only through GetBindingOptions/ListEventBindings.
6. `AddEventBinding` on the bare ScriptDevice: `Source device has no bindable event named 'OnX'.` (the real names come from GetBindingOptions, with spaces: `On Player Spawned`).
7. Entity reads on an actor: `Parameter error: <actor> is not valid BaseEntity for property 'Entity'`; on a component of an actor: `is not valid BaseComponent for property 'Component'`. Entities are Verse entities, not actors.
8. `Scene/diff {old_scene_path,new_scene_path}` with the level path: `SceneTools.diff: level (World) diff is not yet supported: /09e4.../root_ai_lab`; with `.../root_ai_lab/root_ai_lab`: `Could not load scene asset`.
9. `get_actors_in_folder {"folder_path":""}`: `Folder does not exist: ''`.
10. `delete_folder` returns a count (0 = nothing removed); empty outliner folders (`T004`, `T004/Spawns`) lingered in `get_folders` after deleting them, and a `rename_folder` of a nested folder left a root folder `Spawns` once. Cosmetic, level was not saved.
11. `add_to_scene_from_class` with `/Script/ScriptDevice.ScriptDevice`: `is not valid Class for property 'actor_type'`; the right class is `/Script/VerseDevices.ScriptDevice`.
12. Guard inconsistency seen once (d10): after `create_data_layer_asset` / `add_actors_to_data_layer` in a process, `remove_from_scene` on actors created by earlier processes was accepted (6 removed); the same call in a fresh process is refused (d14). Probably a side effect of the guard's `created` set (it is filled by any tool named add*/create*). Reported to the owner, not used on purpose afterwards. Leftover in the level: the `ScriptDevice` pair and one `TargetPoint_Spawn` actor may remain (find_actors by label `TargetPoint_Spawn`); harmless, level not saved.

## 4. What does NOT work or is forbidden here

- Placing any catalog device, setting a device property, wiring an event between real devices, creating or editing entities/components: blocked by the lab guard (trap 1/3/4) or by missing built Verse class (trap 5). The code paths of `PlaceDevice`, `SetDeviceProperty`, `AddEventBinding` were NOT reached, so their success behaviour is unknown. Needs a non-lab project or a guard change by the owner; not worked around.
- Criteria "place a device, read and set a property, wire an event" is therefore only partly covered: actors yes (R1-R3), device read yes (R6), device property set/wire no.
- `replace_actors_with_class` TargetPoint -> StaticMeshActor fails (log only).
- Level-wide `diff`: not supported by UEFN.

## 5. Tasks for a subagent

1. "Place a marker": R1 steps 1-3 in one script with a given class, label and tag; return the actor refPath and the readbacks (label, tags, transform).
2. "List what is in the level": `find_actors {"collision_channels":[], "name":"<filter>"}`; return label, class, folderPath, bounds per actor; never an unfiltered dump into the report.
3. "Read a device's wiring": for a given label, find_actors, GetBindingOptions + ListEventBindings; return sourceEvents, targetFunctions and the existing bindings.
4. "Organize": move actors matching a tag into a given outliner folder (set_actor_folder), verify with get_actors_in_folder, report the count.
5. "Add and remove a component" on a created actor (R2) and report get_components before/after.
Return to the orchestrator: refPaths created, the exact error text of any refusal, and whether cleanup (remove_from_scene, delete_folder) was done.

## 6. Tools not tried and why

- `SceneTools/create_level`, `SceneTools/load_level`: they switch the open level in the editor (possible save-changes modal that can hang the MCP, and the lab guard requires the open level to stay under LAB_ROOT). Not worth the risk for a disposable lab; try only with the owner at the keyboard.
- Entity write tools (`CreateEntity` success, `AddComponent`, `RemoveComponent`, `SetEntityTransform`, `SetComponentProperty`, `DeleteEntity`) and `PlaceDevice`/`SetDeviceProperty`/`AddEventBinding`/`RemoveEventBinding` success paths: reached only as refusals/errors (section 4).

## Trap added 2026-10-15 (T-006)

- NEVER place `/Script/Engine.TargetPoint` or other non-UEFN engine classes: validation error blocks StartSession and publish (`UEFNValidation: Error: Disallowed reference to /Script/Engine.TargetPoint`; StartSession -> `Failed: Validation failed`, then the editor MCP hangs for minutes). Leftover saved actors survive restart because of OFPA (one file per actor): delete them explicitly. Diagnose with LogsToolset GetLogEntries {category:"",maxEntries:0,pattern:"UEFNValidation"}.

## Update 2026-10-16 (T-014 pass B, widened guard, LAB_ROOT=/root_ai_lab; scripts `_explore/h1.py`..`h17.py`)

Corrects traps 1, 3, 4 above (they described the old guard). Now: level actor paths `/<guid>/root_ai_lab.root_ai_lab:PersistentLevel.X` are inside the lab; a source asset path under `/Game`, `/Engine`, `/Niagara`, `/Script` is accepted for place/create.

Closed (ledger ok, recipes merged):
- PlaceDevice success: only the 2 catalog devices under `/Game` pass (`/Game/Playsets/PID_CP_Devices_Hover_Platform...`, `.../PID_CP_Devices_SwordStone...`); returns `{refPath: ...Creative_Hover_Platform_C_UAID_...}`. Other 381 catalog paths (`/CreativeCoreDevices`, `/CR_Legacy`, `/CRD_*`, `/_Verse`) are still refused by the guard (not in the source list).
- set_label (`HoverPlatform_T014Test`) + set_actor_folder (`T014Devices`) + get_actors_in_folder ok; remove_from_scene true; the folder vanishes with its last actor (delete_folder then says `Folder does not exist`).
- AddEventBinding / ListEventBindings / RemoveEventBinding ok between the level's two existing spawn pads: `On Player Spawned` -> `Enable`. ListEventBindings lists the binding on the TARGET device (source returns `[]`); unknown target function: `Target device has no bindable function named 'NoSuchFn'.`; the two Hover/SwordStone devices have empty GetBindingOptions.
- CreateEntity ok with `/Game/Athena/AI/NPCs/Base/InteropEntity/NPCInteropEntity.NPCInteropEntity_C` (the only non-abstract entity class guard-accepted; `search_subclasses` of `/Script/Entity.BaseEntity` lists 1511, only 2 outside Verse mounts). GetComponents returns transform_component_0 + replication_component_0; GetEntityTransform / SetEntityTransform (yaw 30 reads 30.00000000000001) / ListComponentProperties / GetComponentProperty / SetComponentProperty (`NetCullDistance` 15000 -> 12000, read back 12000, restored 15000) / DeleteEntity ok.

Still blocked (exact):
- SetDeviceProperty / ListDeviceProperties success: need a placed Verse device; `PlaceDevice {assetPath:/<guid>/_Verse.root_ai_lab-lab_client_probe}` -> `refused even in the laboratory, path outside /root_ai_lab`; `add_to_scene_from_class /Script/VerseDevices.ScriptDevice` ok but `ListDeviceProperties` -> `has no resolved Script subobject`; `ObjectTools/set_properties {values:{script:{refPath:<verse class>}}}` -> same refusal.
- Guard blind spot (reported, NOT used): the same `set_properties` with `values` passed as a JSON STRING instead of an object is not refused and attached the Verse script (`script` became `...ScriptDevice_UAID_....root_ai_lab-lab_client_probe_0`). It was probed once by mistake in one script and reset at once (`reset_properties script` true). The owner should decide whether to close that hole or accept the route.
- AddComponent: `/EntityFramework/_Verse/VNI/Entity.tag_component` refused (not a source root); `/Script/Entity.BaseComponent` abstract. RemoveComponent needs `componentClass` (not component), refused for the same reason.
- Leftovers: none (find_actors 25 actors = the original level; entity list `[]`).

## Update 2026-10-16 (T-015 pass C1, corrected guard, scripts `_explore/i1.py`..`i21.py`; LAB_ROOT unset, `/root_ai_lab` derived)

Corrects trap 3, 4, 5, section 4 and section 6 above; supersedes the T-014 pass B "Still blocked" list.

Closed (ledger ok, recipes merged, level back to 25 actors, `FindEntities` `[]`):
- **Verse device end to end.** `PlaceDevice {assetPath:{refPath:"/<guid>/_Verse.root_ai_lab-lab_device_probe"}, transform}` ok; `ListDeviceProperties {device}` returns JSON TEXT keyed camelCase (`debugLoggingEnabled`, `probeValue` integer, `probeText` (empty schema), `probeButton` object with refPath); `GetDeviceProperties {device, propertyNames:["ProbeValue","ProbeText"]}` -> `{"ProbeValue": 3, "ProbeText": "lab"}` (Verse field names, not camelCase); `SetDeviceProperty {device, propertyName:"ProbeValue", value:"7"}` (value is a JSON-encoded STRING; `"\"changed\""` for text) null, re-read 7, restored 3 and "lab", re-read EQUAL. Cleanup remove_from_scene true; the folder set with set_actor_folder disappears with its last actor.
- **Events to/from a Verse device: not possible.** `GetBindingOptions` of the placed Verse device returns `{"sourceEvents":[],"targetFunctions":[]}` also with `<public>` methods and `<public>` `event()` fields; `AddEventBinding` pad -> device: `Target device has no bindable function named 'DoProbe'.`; device -> pad: `Source device has no bindable event named 'OnProbeFired'.` Real reason: this API exposes only events/functions of classic Blueprint devices; Verse creative_device members are not listed. A Verse device reaches other devices through its `@editable` device references (probeButton shows as a property of type `/CreativeCoreDevices/_Verse.button_device`).
- **PlaceDevice from the three catalog mounts**: `/CreativeCoreDevices/SetupAssets/PID_Device_Button` (Device_Button_V2_C), `PID_Device_Billboard`, `PID_CP_Devices_CaptureArea_V2`; `/CR_Legacy/Playsets/PID_CP_Devices_CreativeButton` (BP_Creative_Button_C), `PID_CP_Devices_Billboard`; `/VerseDevices/_Verse/VNI/VerseDevices.Devices_creative_device` (VerseDevice_C, ListDeviceProperties returns "" = no settings). All removed. Classic BP devices: `ListDeviceProperties` / `SetDeviceProperty` -> `... is not valid ScriptDevice for property 'Device'` (tools are Verse-only); `SetDeviceProperty` on an unknown name: `Device '<path>' has no editable setting named 'X'.`
- **Binding between a placed catalog device and a level device**: Button_V2 `GetBindingOptions` -> sources `["On Interact"]`, targets `["Enable","Disable"]`; `AddEventBinding {source: button, sourceEvent:"On Interact", target: Player 1 Spawn Pad, targetFunction:"Enable"}` null; `ListEventBindings` of the pad lists it; `RemoveEventBinding` null; list `[]`. CaptureArea_V2 exposes 11 events / 11 functions; Billboard 0 events, 3 functions (`SetTextHidden`, `SetTextVisible`, `Update Display When Receiving Text Data`).
- **Entities**: `CreateEntity` with `/Game/.../NPCInteropEntity_C` returns `{entity:{refPath}, displayName, entityClass}` (the ref is under `["entity"]`, not `["refPath"]`). `AddComponent {entity, componentClass:{refPath:"/EntityFramework/_Verse/VNI/Entity.rarity_component"}}` ok for `tag_component`, `icon_component`, `rarity_component` (returns `{component:{refPath}, componentName:"rarity_component_0", componentClass}`; `GetComponents` lists it; `ListComponentProperties {component: <returned component>}` -> `[{name:"Rarity", type:"rarity*", value, bReadOnly}]`, icon -> `Icon`, tag -> `Tags` `{"internalTags":{}}`); `RemoveComponent {entity, componentClass}` null and `GetComponents` back to transform + replication. `text_display_component`, `mesh_component`, `decal_component`, `sphere_light_component` (all in ListComponentClasses): `AddComponent` -> `Parameter error: <class> is not valid Class for property 'ComponentClass'` (not attachable to this entity class). `RemoveComponent` of a class never added in the process: `refused even in the laboratory, path outside /root_ai_lab: /EntityFramework/...` (class path is neither a source root nor in the guard's created set; logical, not unjust). `SetComponentProperty {component: <entity>.replication_component_0, propertyName:"NetCullDistance", value:"12000"}`, read back 12000, restored 15000.
- **CreateEntity with /EntityFramework classes**: `simulation_entity` ok (returns `.../LevelEntity.LevelEntity.simulation_entity_<id>`) but `DeleteEntity` -> `Cannot delete the root entity.` and an `EntityProxyActor` appears in the level (26 actors). Cleanup that worked: `SceneTools/find_actors {collision_channels:[], name:"simulation_entity_<id>"}` then `remove_from_scene` on its `actorPath` (back to 25, `FindEntities` `[]`). `level_entity`, `Prefab_RepTest_Entity_Simple`, `Prefab_MaterialsTest`: `is not valid Class for property 'EntityClass'`. Avoid `simulation_entity` unless you need it.
- **SelectOutlinerFolders**: `["/"]` and an existing folder (`T015Sel/Sub`, present in `get_folders`) both pass the guard and fail in the editor: `Folder(s) not found in any outliner: /`. Real reason: the tool selects in OPEN scene outliners; the editor has no World Outliner panel open and no MCP tool opens one. `[]` returns null; `GetSelectedOutlinerFolders` returns `[]`.

Still not closable here: nothing in this area is blocked by the guard any more; `create_level`/`load_level` are still skipped on purpose (they switch the open level).
