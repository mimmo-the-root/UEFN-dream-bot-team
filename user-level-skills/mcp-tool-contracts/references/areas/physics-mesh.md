# MCP area: physics-mesh (StaticMeshTools, SkeletalMeshTools, PhysicsAssetToolset, PrimitiveTools, + TextureTools adjacent)

Date: 2026-10-16 (T-014 pass A update: mesh creation re-attempted, still impossible, trap 12). UEFN version: 42.40 (from previous-findings.md, same editor; not re-queried). Lab `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`, task T-010. 63 tools in the area, 32 tried ok, 31 refused or rejected (see parts 3, 4, 6). Scratch scripts: `Claude/logs/_explore/p0.py`..`p17.py`.

Toolsets (exact names, from MAP.md): `editor_toolset.toolsets.static_mesh.StaticMeshTools` (16), `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools` (22), `PhysicsToolsets.PhysicsAssetToolset` (17), `editor_toolset.toolsets.primitive.PrimitiveTools` (4), `editor_toolset.toolsets.texture.TextureTools` (4, adjacent: no other task covers it). Helpers: `AssetTools/find_assets`, `SceneTools` (add_to_scene_from_asset, remove_from_scene, find_actors), `ActorTools`, `ObjectTools` (get/set/reset_properties).

Call form: `call_tool {toolset_name, tool_name, arguments}` -> `{"returnValue": ...}`. Object refs `{"refPath":"..."}`. Run from PowerShell with `LAB_AGGRESSIVE=1`, `LAB_ROOT=/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`.

KEY FACT: the lab root holds NO mesh, skeletal mesh or physics asset (find_assets on StaticMesh/SkeletalMesh/PhysicsAsset/Skeleton/Texture2D under the lab root = 0 each) and none can be created (traps 1-3). So every mesh/physics WRITE tool is untestable here; all reads work on engine/plugin assets; the collision/physics setting write works on the COMPONENT of a lab-spawned actor via ObjectTools.

## 1. What the area is for, and the tools

Read mesh facts (bounds, LODs, materials, bones, sockets, physics bodies/constraints), edit mesh assets (Nanite, collision, LODs, sockets, materials) and physics assets (bodies, shapes, constraints), and add primitive shape components to an actor.

| Tool (StaticMeshTools) | R/W | Tried |
|---|---|---|
| get_bounds {mesh} | R | yes ok |
| get_lod_count {mesh} | R | yes ok (0 for every static mesh tried, see trap 5) |
| get_lod_thresholds {mesh} | R | yes ok |
| get_material_slots {mesh} | R | yes ok |
| get_material {mesh, slot_name} | R | yes, error with a wrong slot name only (trap 6) |
| is_nanite_enabled {mesh} | R | yes ok |
| get_vertex_count / get_triangle_count {mesh, lod_index} | R | yes, error `LOD index 0 is out of range. Mesh has 0 LODs.` (trap 5) |
| set_nanite_enabled, remove_collisions, generate_convex_collisions, generate_lods, remove_lods, set_lod_thresholds, set_material | W | refused by the lab guard on a plugin mesh (trap 2); not run on /Engine meshes on purpose |
| import_file {folder_path, asset_name, source_file, ...} | W | refused (trap 3) |

| Tool (SkeletalMeshTools) | R/W | Tried |
|---|---|---|
| get_bounds, get_lod_count, get_material_slots, get_material {mesh, slot_name}, get_skeleton, get_bone_names, get_bone_parent {mesh, bone_name}, get_bone_children {mesh, bone_name}, get_socket_names, get_morph_target_names, get_vertex_count, get_section_count {mesh, lod_index} | R | yes ok |
| get_physics_asset {mesh} | R | yes ok (mesh with a physics asset); error text on one without |
| get_socket_transform / get_socket_bone {mesh, socket_name} | R | yes ok on SKM_ZenMaster (socket FX_Start_Petal); error on unknown socket |
| add_socket, remove_socket, rename_socket, set_socket_transform, set_material, assign_physics_asset | W | refused by the guard (trap 2) |
| import_file | W | refused (trap 3) |

| Tool (PhysicsAssetToolset) | R/W | Tried |
|---|---|---|
| GetBodyNames, GetConstraints {physicsAsset}; GetBodyShapes, GetBodyPhysicsMode, GetBodyMassScale {physicsAsset, boneName} | R | yes ok |
| CreateFromMesh {meshPath, bAssignToMesh}, AddBody, RemoveBody, AddConstraint, RemoveConstraint, SetBodyPhysicsMode, SetBodyMassScale, SetConstraintLimits, SetSphere, SetBox, SetCapsule, RemoveShape | W | refused by the guard (trap 2) |

| Tool (PrimitiveTools) | R/W | Tried |
|---|---|---|
| add_cube {actor, name, dimensions}, add_sphere {actor, name, radius}, add_cone / add_cylinder {actor, name, radius, height} | W | yes ok (one script, trap 7) |

| Tool (TextureTools) | R/W | Tried |
|---|---|---|
| get_size {texture} | R | yes ok `{"x":32,"y":32}` |
| read_texture {texture} | R | yes ok on `/Engine/EngineResources/DefaultTexture` (returns a `urn:toolresult:...` pointer, not pixels); error `Failed to export texture` on WhiteSquareTexture |
| export_png {texture, file_path}, import_file | W | refused: disk path (trap 3) |

## 2. Verified recipes (exact args; ok rows in explore-ledger.jsonl; all in `recipes.json`)

Inputs found by `AssetTools/find_assets {"folder_path":"","name":"<substr>","asset_type":{"refPath":"/Script/Engine.<Class>"}}` (always give `name`): StaticMesh `/Engine/BasicShapes/Cube.Cube` (also Sphere, Cube1), `/AnimToTexture/Characters/Mannequin/SM_Mannequin_VertexAnimation.SM_Mannequin_VertexAnimation`; SkeletalMesh `/AnimToTexture/Characters/Mannequin/Meshes/SKM_Mannequin.SKM_Mannequin` (name filter "SK_" returns 1252, "SKM_" 1791: always narrow); PhysicsAsset `/FigureCosmetics/Props/Emote/YuzuCrank_Pita/SkeletalMesh/PA_YuzuCrank_Pita.PA_YuzuCrank_Pita` (6 bodies, 5 constraints; name "PA_" returns 1388).

R1 Static mesh facts: `StaticMeshTools/get_bounds {"mesh":{"refPath":"/Engine/BasicShapes/Cube.Cube"}}` -> `{min:{x:-50,y:-50,z:-50}, max:{50,50,50}, isValid:true}`; `get_material_slots` -> `["WorldGridMaterial"]`; `is_nanite_enabled` -> false; `get_lod_thresholds` -> `[2]`.

R2 Skeletal mesh facts: on SKM_Mannequin `get_bounds` -> `{origin, boxExtent, sphereRadius}`; `get_lod_count` 2; `get_vertex_count {mesh}` 23309; `get_section_count` 2; `get_material_slots` `["M_Body","M_ChestLogo"]`; `get_material {mesh, slot_name:"M_Body"}` -> `{refPath: .../M_Body.M_Body}`; `get_skeleton` -> `{refPath: .../SK_Mannequin.SK_Mannequin}`; `get_bone_names` (root, pelvis, spine_01...); `get_bone_parent {mesh, bone_name:"hand_l"}` -> "lowerarm_l"; `get_bone_children {bone_name:"pelvis"}` -> ["spine_01","thigh_l","thigh_r"]. Sockets: SKM_ZenMaster (`/FigureCosmetics/...`, found with find_assets name "SKM_") `get_socket_names` -> ["FX_Start_Petal"], `get_socket_transform {mesh, socket_name}` -> `{location, rotation, scale}`, `get_socket_bone` -> "JNT_Sword".

R3 Physics asset read: `PhysicsAssetToolset/GetBodyNames {"physicsAsset":{"refPath":"<PA>"}}` -> bone names; `GetBodyShapes {physicsAsset, boneName:"root"}` -> `[{shapeName:"root_capsule", shapeType:"Capsule", center, rotation, radius, length, extentX, extentY, extentZ}]`; `GetBodyPhysicsMode` -> "Default"; `GetBodyMassScale` -> 1; `GetConstraints` -> `[{bone1Name, bone2Name, swing1Motion:"Limited", swing1LimitDegrees:45, swing2Motion, swing2LimitDegrees, twistMotion, twistLimitDegrees}]`. Chain: `SkeletalMeshTools/get_physics_asset {mesh}` returns the PA refPath (SKM_ZenCrash -> PA_ZenCrash, 1 body "root", 0 constraints).

R4 Collision/physics setting set, re-read, reverted equal (task criterion; ONE script, lab-spawned actor):
1. `SceneTools/add_to_scene_from_asset {"asset_path":"/Engine/BasicShapes/Cube","name":"T010_Cube2","xform":{"location":{"x":0,"y":0,"z":5100},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":1,"z":1}}}` -> FortStaticMeshActor refPath `A`; component `A.StaticMeshComponent0`.
2. `ObjectTools/get_properties {"instance":{"refPath":"<comp>"},"properties":["bGenerateOverlapEvents","bodyInstance"]}` -> JSON text: bGenerateOverlapEvents false, bodyInstance.collisionEnabled "QueryOnly", collisionProfileName "FortStaticMesh", bSimulatePhysics false, bEnableGravity true.
3. `ObjectTools/set_properties {"instance":...,"values":"{\"bGenerateOverlapEvents\":true,\"bodyInstance\":{\"collisionEnabled\":\"QueryAndPhysics\",\"bEnableGravity\":false}}"}` -> true; re-read shows the new values (nested bodyInstance partial update works, other fields kept).
4. Revert with the ORIGINAL values explicitly: same call with false / "QueryOnly" / true -> true; re-read equals step 2 (EQUAL). `collisionProfileName` set to "BlockAll" and back to "FortStaticMesh" also re-reads equal.
5. `SceneTools/remove_from_scene {"actor":{"refPath":"A"}}` -> true; `find_actors {"collision_channels":[],"name":"T010"}` -> [].

R5 Primitive components: on the same lab actor `PrimitiveTools/add_cube {"actor":{"refPath":"A"},"name":"P_add_cube","dimensions":{"x":50,"y":50,"z":50}}`, `add_sphere {actor,name,radius:40}`, `add_cone {actor,name,radius:30,height:60}`, `add_cylinder {actor,name,radius:30,height:60}` each return the new component refPath `A.P_add_cube`; `ActorTools/get_components {actor}` then lists 4 more components. Removing the actor removes them.

Previous findings re-run (area-relevant): `ObjectTools/set_properties` with `values` as JSON TEXT and camelCase names: riconfermata (R4). `ObjectTools/get_properties`: riconfermata with `{instance, properties:[...]}` (returns JSON text). `get_actor_bounds {actor}`: riconfermata on the lab actor (`{min:{-50,-50,5050}, max:{50,50,5150}}`). `AssetTools/find_assets` needs `name`: riconfermata (folder alone is not enough; `asset_type` needed). `AssetTools/duplicate` of an engine asset: riconfermata as refused (editor error, trap 1). Placement-class restrictions: not exercised here.

## 3. Traps (exact messages)

1. Duplicating an engine mesh into the lab fails in the EDITOR, not in the guard: `AssetTools/duplicate {path:"/Engine/BasicShapes/Cube", new_path:"<LAB_ROOT>/Phys_T010/SM_CubeT010"}` and with `.Cube` -> `FolderPath "/Engine/BasicShapes/Cube" is outside this project's valid asset roots (/09e4e8d3-83f9-4ee0-9777-072ed3984380/, /ArmASR/, /AudioGameplay/, ...`. Not worked around.
2. Every write on an asset outside LAB_ROOT: `refused even in the laboratory, path outside /09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab: /AnimToTexture/Characters/Mannequin/Meshes/SKM_Mannequin.SKM_Mannequin` (same text with the PA path). This includes `duplicate` of a plugin mesh and `CreateFromMesh {meshPath, bAssignToMesh:false}` (meshPath is a plain string and is checked too).
3. Disk imports/exports: `refused: a path on the disk outside the project` (guard refuses any drive-letter path for a write tool, even one inside the project folder). Affects StaticMeshTools/SkeletalMeshTools/TextureTools `import_file` and `TextureTools/export_png`.
4. `ObjectTools/reset_properties {instance, properties:["bGenerateOverlapEvents","bodyInstance"]}` returns true but does NOT restore the actor's original values: it goes to the class default (overlap true, collisionProfileName "BlockAll", seen on a FortStaticMeshActor). To revert, set the originals explicitly (R4).
5. `get_lod_count` returns 0 on every static mesh tried (Cube, SM_Mannequin_VertexAnimation, two BRCosmetics props) while `get_lod_thresholds` returns a list (`[2]`, `[2,0.18,0.18]`); `get_vertex_count`/`get_triangle_count` then fail for any lod_index (also with it omitted): `LOD index 0 is out of range. Mesh has 0 LODs.` No working vertex count read for static meshes was found. SkeletalMeshTools get_vertex_count works (23309).
6. `StaticMeshTools/get_material {mesh, slot_name:"None"}` -> `Material slot "None" not found on Cube.` Slot names come from get_material_slots.
7. Scene actor guard (as in T-008): an actor can be written or removed only by the SAME Python process that created it: do create, set, re-read, add primitives and `remove_from_scene` in one script with try/finally.
8. `SkeletalMeshTools/get_physics_asset` on a mesh with none: `<Object '...SKM_Mannequin' ...> has no physics asset assigned.` (an error, not null). `get_socket_transform`/`get_socket_bone` on a missing socket: `Socket "nosuch" not found on SKM_Mannequin.`
9. `TextureTools/read_texture` -> `Failed to export texture: <path>` on `/ChaosClothAsset/Textures/WhiteSquareTexture` and `/Engine/EngineResources/WhiteSquareTexture`; works on `/Engine/EngineResources/DefaultTexture` and returns only a `urn:toolresult:...` pointer string.
10. `SceneTools/find_actors {"name":"T008"}` fails without `collision_channels` (`input param "collision_channels" is required`); pass `[]`.
11. Size: `find_assets` with name "SK_"/"SKM_"/"PA_" returns 1252/1791/1388 paths: narrow the name or folder.

12. (T-014 pass A, 2026-10-16) Creating a lab mesh was retried with the widened guard, every source the guard accepts. Results (all `AssetTools/duplicate {path, new_path:"<mount>/Phys_T014/<name>"}`):
   - `/Engine/BasicShapes/Cube.Cube`, `/Engine/EngineMeshes/Sphere.Sphere`, `/Engine/EngineMeshes/SkeletalCube.SkeletalCube`: guard passes, EDITOR rejects: `FolderPath "<src>" is outside this project's valid asset roots (/09e4e8d3-.../, /ArmASR/, /AudioGameplay/, ...`.
   - `/Game/Creative/Devices/Generic/Meshes/Sm_Devices_FakeGlowAndLighting` (StaticMesh), `/Game/Characters/Player/Male/Male_Avg_Base/Fortnite_M_Avg_Player_Physics` (PhysicsAsset): same editor rejection (`/Game` is listed by find_assets: 18960 StaticMesh, 1086 SkeletalMesh, 891 PhysicsAsset, but is not a valid root for duplicate).
   - `/Niagara/DefaultAssets/S_Arrow.S_Arrow` (one of 2 StaticMeshes under /Niagara; the only valid-root source the guard accepts): editor `FolderPath "/Niagara/DefaultAssets/S_Arrow.S_Arrow" is not writable in this project.` then `UserRaisedError in Default__AssetTools.duplicate` (the tool wants the source path writable).
   - Plugin-mount meshes (`/AnimToTexture/...`, `/FigureCosmetics/...`) are valid roots for the editor but the guard refuses them as sources (`refused even in the laboratory, path outside /root_ai_lab`); they are not in the widened source list (Niagara, Engine, Game, Script, FortniteGame, Fortnite, NiagaraAdditions). Not circumvented.
   - No tool creates a mesh from nothing (map search: merge, convert, bake, proxy, factory, new asset, clone: none). `PhysicsAssetToolset/CreateFromMesh` writes next to the SOURCE mesh (`<mesh folder>/<name>_PhysicsAsset`), so it needs a lab skeletal mesh first. `PrimitiveTools/add_*` add components, not assets.
   - `find_assets` with asset_type StaticMesh, SkeletalMesh, PhysicsAsset, Skeleton under the whole project root `/09e4e8d3-...` = 0 each.
   Needed to unblock (decision for the owner or a guard change, not done by agents): add the plugin mounts that hold small meshes (for example `/AnimToTexture`, `/FigureCosmetics`) to SRC_ROOTS in `Claude/hooks/mcp_lab.py`, then `duplicate` a StaticMesh, a SkeletalMesh and its PhysicsAsset into `<mount>/Phys_T014`.

## 4. What does not work or is forbidden

- Mesh and physics-asset writes: no mesh/PA exists in the lab and none can be copied in (traps 1-3), so 12 PhysicsAssetToolset, 7 StaticMeshTools, 6 SkeletalMeshTools writes are guard-refused with real arguments (ledger rows `refused`). They were NOT run on `/Engine/BasicShapes/Cube`: the guard lets a path under `/Engine/` through and it would change an engine asset in memory, which the lab rules forbid.
- Removing the T-008 leftover actor `T008_Cube` from a new process was refused (T-010); fixed by the guard widening: removed in T-014 (materials.md R8).
- Placing physics-simulating actors or starting a session was not done (T-006 lesson).

## 5. Tasks for a subagent (physics-mesh)

1. "Describe static mesh M": `get_bounds`, `get_material_slots`, `get_lod_thresholds`, `is_nanite_enabled`; return bounds size, slot names, thresholds, nanite flag.
2. "Describe skeletal mesh M": `get_bounds`, `get_lod_count`, `get_bone_names` (count + first 10), `get_material_slots`, `get_socket_names`, `get_physics_asset`; return them (catch the "no physics asset" error as null).
3. "Describe physics asset PA": `GetBodyNames`, then `GetBodyShapes` and `GetBodyPhysicsMode` per bone, `GetConstraints`; return a table bone | shapes | mode, plus the constraint list. Trim inside one `execute_tool_script`.
4. "Read collision settings of actor A": `ActorTools/get_components`, `ObjectTools/get_properties` with `["bGenerateOverlapEvents","bodyInstance"]` on its StaticMeshComponent0; return collisionEnabled, collisionProfileName, bSimulatePhysics, bEnableGravity.
5. "Set collision of a lab actor and revert": R4 in one script; return before / changed / reverted tuples and whether equal.
6. "Find meshes by name N": `find_assets` with `asset_type` StaticMesh or SkeletalMesh and `name`; return at most 30 refPaths.

## 6. Never-tried tools and why

Not tried successfully (31 of 63), all because a lab-owned mesh / physics asset cannot exist (no copy path, traps 1-3): StaticMeshTools set_nanite_enabled, remove_collisions, generate_convex_collisions, generate_lods, remove_lods, set_lod_thresholds, set_material, import_file, and get_vertex_count/get_triangle_count (no static mesh with LODs per get_lod_count; trap 5); SkeletalMeshTools add_socket, remove_socket, rename_socket, set_socket_transform, set_material, assign_physics_asset, import_file; PhysicsAssetToolset CreateFromMesh, AddBody, RemoveBody, AddConstraint, RemoveConstraint, SetBodyPhysicsMode, SetBodyMassScale, SetConstraintLimits, SetSphere, SetBox, SetCapsule, RemoveShape; TextureTools export_png, import_file. Unblock: the owner copies a StaticMesh and a SkeletalMesh with a physics asset into `/root_ai_lab/...` by hand (or allows disk imports from inside the project); a pass 2 then runs the writes. Each refused call has a `refused`/`rejected` ledger row with the exact message.

T-014 pass A (2026-10-16): still not tried successfully, same 31 tools. 8 `duplicate` attempts with 8 distinct sources logged (trap 12), 0 new ok. The cause moved from the lab guard (T-010) to the editor and to the guard's source list; see the unblock line in trap 12.

## Update 2026-10-16 (T-015 pass C1, corrected guard, scripts `_explore/i15.py`..`i18.py`)

Corrects trap 12 (its "unblock" line) and parts 4 and 6 above. Result: the 31 mesh/physics write tools are STILL untested, now for a reason that is neither the guard nor a missing decision: **the editor itself will not copy a plugin or engine asset into the project, and nothing else can make a mesh.**

Exact attempts (all `AssetTools/duplicate {path, new_path:"<mount>/Meshes/<name>"}`, guard passed each, ledger rows `rejected`):
- `/AnimToTexture/Characters/Mannequin/SM_Mannequin_VertexAnimation.SM_Mannequin_VertexAnimation` (StaticMesh): `FolderPath "<path>" is not writable in this project.` then `UserRaisedError in Default__AssetTools.duplicate`.
- `/AnimToTexture/Characters/Mannequin/Meshes/SKM_Mannequin.SKM_Mannequin` and `/FigureCosmetics/Props/Emote/ZenCrash/SkeletalMesh/SKM_ZenCrash.SKM_ZenCrash` (SkeletalMesh): same two messages. (PhysicsAsset `PA_YuzuCrank_Pita`: same editor check, not repeated: it lives under the same non-writable mount.)
- `/Engine/BasicShapes/Cube.Cube`: `FolderPath "/Engine/BasicShapes/Cube.Cube" is outside this project's valid asset roots (/09e4e8d3-.../, /ArmASR/, /AudioGameplay/, ...` (the editor message is cut at about 200 characters).
So `duplicate` needs a source that is both a valid root AND writable: only the project's own folder qualifies, and it holds 0 StaticMesh / SkeletalMesh / PhysicsAsset / Skeleton (find_assets under `/<guid>` re-run, 0 each; project root folders: `Claude`, `Collections`, `Developers`, `__ExternalActors__`, `__ExternalObjects__`, `root_ai_lab/UI_T001`).
- Making a mesh from nothing: no tool (map search `create`, `copy`, `clone`, `convert`, `bake`: only PhysicsAsset `CreateFromMesh`, which needs a skeletal mesh and writes next to its source, i.e. into the plugin mount; not called).
- `StaticMeshTools/import_file {folder_path:"<lab>/Meshes", asset_name:"SM_LabCube", source_file:"C:\UEFN_Progetti\root_ai_lab\Content\Claude\logs\_explore\LabCube.obj"}` (a small OBJ cube written by the lab inside the project folder): `import_file refused: a path on the disk outside the project`. The path IS inside the project, so the message reads as unjust: the guard rule `DISK_PATH` refuses every drive-letter path for a write tool (command and message also in lab-progress.md). Not circumvented; the owner can decide to allow project-folder paths for `import_file`.

Therefore the lab folder `<lab>/Meshes` was never created and there is nothing to delete.

### Tools of this area still untried, with the real reason (31 of 63)
| Tool(s) | Real reason |
|---|---|
| StaticMeshTools set_nanite_enabled, remove_collisions, generate_convex_collisions, generate_lods, remove_lods, set_lod_thresholds, set_material | no StaticMesh asset exists in the project and `duplicate` of any plugin/engine mesh is rejected by the editor (not writable / outside valid roots) |
| StaticMeshTools get_vertex_count, get_triangle_count | every readable static mesh reports 0 LODs (trap 5), no mesh with LODs to read; also needs the copy above for a mesh with LODs |
| StaticMeshTools / SkeletalMeshTools import_file, TextureTools import_file, export_png | disk path rule of the guard refuses even a path inside the project (see above) |
| SkeletalMeshTools add_socket, remove_socket, rename_socket, set_socket_transform, set_material, assign_physics_asset | no SkeletalMesh in the project; same duplicate rejection |
| PhysicsAssetToolset AddBody, RemoveBody, AddConstraint, RemoveConstraint, SetBodyPhysicsMode, SetBodyMassScale, SetConstraintLimits, SetSphere, SetBox, SetCapsule, RemoveShape | no PhysicsAsset in the project; same duplicate rejection; writing the plugin asset in place is forbidden |
| PhysicsAssetToolset CreateFromMesh | needs a lab SkeletalMesh; with a plugin mesh it would write the new asset into the plugin mount |

Unblock options (owner decisions, not agent work): (1) import a mesh through the editor UI into `/root_ai_lab` once (then these 31 tools run on it); or (2) allow `import_file` with a path inside the project folder in `mcp_lab.py` (then the lab writes its own OBJ/FBX). Everything else in the area is covered.

## Update 2026-10-16 (T-015 pass D: the owner's drone, scripts `_explore/j0.py`..`j14.py`)

The owner imported a drone (FBX) in the editor. It lives in a NEW project mount `/09e4e8d3-83f9-4ee0-9777-072ed3984380/mech-drone/` (folders `textures/`, `source/`), NOT under `/root_ai_lab`. Level has 28 actors (25 + 3 drone actors).

Assets (all project-owned by the GUID mount, all outside LAB_ROOT): SkeletalMesh `mech-drone/textures/Drone.Drone` (28 bones, 6308 vertices LOD0, 1 LOD, 2 sections, slots Fire + Robot, 0 sockets, 0 morph targets, NO physics asset, bounds extent 179x68x101); Skeleton `Drone_Skeleton`; AnimSequence `Drone_Anim` (4.667 s, 141 keys, rateScale 1); MaterialInstanceConstant `Robot`, `Fire` (parent `/InterchangeAssets/Materials/FBXLegacyPhongSurfaceMaterial`; Robot: Shininess 32, DiffuseColor/AmbientColor 0.588, SpecularColor 0.45); 16 Texture2D (`Drone_*`, `Fire_*`, twice, in `textures/` and `source/`). 0 StaticMesh, 0 PhysicsAsset.

Actors: `Drone Anim` and `Drone Skeleton` play `Drone_Anim` (AnimationSingleNode, looping, playing); `Drone` has animToPlay null (static pose). Component is `<actor>.SkeletalMeshComponent0` (class SkeletalMeshComponent); the earlier failure was a bad property name (`animToPlay` lives inside `animationData`; one unknown name fails the whole get_properties call).

### The 6 parts, for this update
1. What it is for: the first project-owned skeletal mesh in the lab, read and animated through the level actors.
2. Verified (ok rows in the ledger): all SkeletalMeshTools reads on Drone (see `recipe/describe_project_skeletal_mesh_outside_lab`); ObjectTools reads of the component and of the AnimSequence/MI; owner actors moved, scaled (8-step script), `globalAnimRateScale` 1 -> 2 -> 1, `bPauseAnims` true -> false, all re-read and restored; lab MI (parent `/Engine/EngineMaterials/DefaultMaterial`) applied to `overrideMaterials` of the Drone component and reverted to `[]`, MI folder deleted.
3. Traps: (a) writes on the level actors of the owner are allowed by the guard (they live under the level root), but ANY write whose arguments name an asset under `mech-drone` is refused: `set_properties` with `animToPlay` = Drone_Anim -> `refused even in the laboratory, path outside /root_ai_lab: /09e4e8d3-.../mech-drone/textures/Drone_Anim.Drone_Anim`; (b) `duplicate` of Drone, Drone_Skeleton, Drone_Anim, Robot, Fire into `<lab>/Meshes` -> same message (source list does not include the project's other mounts); (c) `SkeletalMeshTools/add_socket`, `PhysicsAssetToolset/CreateFromMesh`, `SceneTools/add_to_scene_from_asset {asset_path:'.../Drone'}` -> same message; (d) scale applied but rotation of 360 deg reads as 0 (normal).
4. Forbidden/not circumvented: widening LAB_ROOT to the GUID or to `/mech-drone`, or writing the owner's mesh in place. These refusals look unjust (the assets are project-owned) and are logged in lab-progress.md.
5. Tasks for a subagent: "describe skeletal mesh actor" (components -> asset -> bones/materials/anim), "animate and restore an actor" (script above).
6. Still untried (31 of 63), real reason now: the guard accepts writes only under `/root_ai_lab` and sources only from its list; the only project-owned meshes are under `/mech-drone`. Unblock: owner copies Drone.Drone, Drone_Skeleton and Robot/Fire into `/root_ai_lab/Meshes` by hand in the editor (or adds `/mech-drone` to the guard's allowed roots in `mcp_lab.py`); then the 6 SkeletalMeshTools writes (add/remove/rename socket, set_socket_transform, set_material, assign_physics_asset), CreateFromMesh and the 11 other PhysicsAsset writes run on the copy. StaticMeshTools writes (7+2) still need a StaticMesh: none exists. import_file/export_png: disk rule unchanged.

## Update 2026-10-16 (T-015 pass E: write tools run on lab COPIES of the drone, scripts `_explore/k0.py`..`k8.py`)

### The 6 parts, for this update
1. What it is for: closing the untried mesh/physics write tools on copies of the owner's drone, never on the originals.
2. Verified (ok rows in the ledger, set / re-read equal / revert where reversible): `AssetTools/duplicate` of `mech-drone/textures/Drone`, `Drone_Skeleton`, `Drone_Anim` into `<lab>/Meshes` (works since the guard honours `extra-root: /mech-drone`). SkeletalMeshTools add_socket, set_socket_transform (re-read equal, reverted equal), rename_socket, remove_socket, set_material (Robot slot -> DefaultMaterial and back, equal), assign_physics_asset (get_physics_asset equal). PhysicsAssetToolset CreateFromMesh (28 bones -> 25 bodies, 0 constraints), SetBodyMassScale (1 -> 2.5 -> 1), SetBodyPhysicsMode (Default -> Kinematic -> Default), SetSphere, SetBox, SetCapsule, RemoveShape (shape list equal after removal), AddConstraint, SetConstraintLimits (reverted equal), RemoveConstraint, RemoveBody, AddBody (+ SetSphere on it). 18 new tools: 50 of 63 ok. Recipes: `recipe/duplicate_project_skeletal_mesh_into_lab`, `skeletal_mesh_sockets_add_rename_transform_remove`, `skeletal_mesh_set_material_and_revert`, `physics_asset_create_from_skeletal_mesh`, `physics_asset_body_mass_mode_shapes_constraints`.
3. Traps: (a) `CreateFromMesh {meshPath}` takes the PACKAGE path: `<lab>/Meshes/Drone` works, `<lab>/Meshes/Drone.Drone` fails `Failed to create package at '<...>/Drone.Drone_PhysicsAsset'`; (b) the copy of the mesh keeps the ORIGINAL skeleton and the original MIs (get_skeleton points to mech-drone); (c) CreateFromMesh creates no constraints, so AddConstraint comes first (defaults Free / 45 deg); (d) SetConstraintLimits needs all 8 fields of `info`; (e) most physics writes return `null`, not true; (f) the shape of a CreateFromMesh body is named "None"; (g) `AssetTools/delete {path:'<lab>/Meshes'}` removes the folder with its assets in one call.
4. Forbidden/not circumvented: none new. Originals untouched (verified: Drone still 0 sockets, Robot slot still `mech-drone/textures/Robot`, /mech-drone still 21 assets, 3 drone actors in the level).
5. Tasks for a subagent: "make a physics asset for skeletal mesh M in the lab": duplicate, CreateFromMesh (package path), assign, edit bodies, delete folder.
6. Still untried (13 of 63), real reasons: StaticMeshTools set_nanite_enabled, remove_collisions, generate_convex_collisions, generate_lods, remove_lods, set_lod_thresholds, set_material, get_vertex_count, get_triangle_count: the project holds 0 StaticMesh (find_assets), `duplicate` of any engine/plugin StaticMesh is rejected by the EDITOR (`FolderPath "/Engine/BasicShapes/Cube" is outside this project's valid asset roots`, re-run now) and no tool makes a StaticMesh from a skeletal one (map search: none). StaticMeshTools/SkeletalMeshTools/TextureTools import_file and TextureTools export_png: the guard rule `DISK_PATH` still refuses any drive-letter path for a write tool (guard unchanged, so not re-run); the file would be inside the project. Unblock: the owner imports or copies one StaticMesh into `/root_ai_lab` or `/mech-drone` by hand, or allows project-folder paths for import_file.
