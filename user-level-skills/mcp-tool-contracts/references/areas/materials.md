# MCP area: materials (MaterialTools, MaterialInstanceTools)

Date: 2026-10-15 (T-014 update 2026-10-16: leftovers cleaned). UEFN version: 42.40 (from previous-findings.md, same editor; not re-queried). Lab `/root_ai_lab`, task T-008. 39 tools in the area, 39 tried, all ok. Scratch scripts: `Claude/logs/_explore/m0.py`..`m12.py`.

Toolsets (from the MCP map MAP.md): `editor_toolset.toolsets.material.MaterialTools` (25 tools), `editor_toolset.toolsets.material_instance.MaterialInstanceTools` (14 tools). Related, used only to APPLY materials: `StaticMeshTools` (set_material/get_material/get_material_slots), `ObjectTools` (set_properties/get_properties on expressions and components), `SceneTools` (add_to_scene_from_asset/remove_from_scene), `AssetTools` (save_assets/delete/find_assets). `PrimitiveTools` and `TextureTools` not used here (other tasks).

Call form: `call_tool {toolset_name, tool_name, arguments}`; answers `{"returnValue": ...}`. Object arguments are `{"refPath": "..."}`. A material refPath is `<pkg>.<Name>`; an expression is `<material refPath>:MaterialExpression<Class>_<n>`. Lab mount must be `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (not `/root_ai_lab`). Run from PowerShell: Git Bash path-converts the env value and the lab refuses it.

## 1. What the area is for, and the tools

Create Material / MaterialFunction / MaterialParameterCollection assets, build and wire expression graphs, create instances and read/set their parameters, measure shader cost, and apply a material to a mesh/actor.

| Tool (MaterialTools) | R/W | Tried |
|---|---|---|
| create_material {folder_path, asset_name} | W | yes ok |
| create_function {folder_path, asset_name} | W | yes ok |
| create_parameter_collection {folder_path, asset_name} | W | yes ok (asset only; no tool edits MPC entries) |
| list_expression_classes {material_or_function} | R | yes ok (26 KB, refPaths of every expression class) |
| add_expression {material_or_function, expression_class, x, y} | W | yes ok |
| delete_expression {material_or_function, expression} | W | yes ok |
| delete_unused_expressions {material} | W | yes ok |
| get_expressions {material_or_function} | R | yes ok |
| get_expression_input_names {expression} | R | yes ok |
| get_expression_output_names {expression} | R | yes ok |
| get_expression_inputs {material_or_function, expression} | R | yes ok |
| connect_expressions {from_expression, from_output_name, to_expression, to_input_name} | W | yes ok (returns null) |
| disconnect_expressions {to_expression, to_input_name} | W | yes ok |
| connect_to_output {expression, output_name, material_property} | W | yes ok |
| disconnect_from_output {material, material_property} | W | yes ok |
| get_property_input {material, material_property} | R | yes ok |
| layout_expressions {material_or_function} | W | yes ok |
| list_parameter_groups {material_or_function} | R | yes ok |
| rename_parameter_group {material_or_function, old_name, new_name} | W | yes ok |
| delete_parameter_group {material_or_function, group_name} | W | yes ok |
| recompile {material_or_function} | W | yes ok |
| get_statistics {material} | R | yes ok (264 B; Material and Instance) |
| diff_material {old_asset_path, new_asset_path} | R | yes ok (package paths without .Name; 6.4 KB for two small materials) |
| diff_function {old_asset_path, new_asset_path} | R | yes ok |
| get_referencing_materials {material_function} | R | yes ok (see trap 5) |

| Tool (MaterialInstanceTools) | R/W | Tried |
|---|---|---|
| create {folder_path, asset_name, parent} | W | yes ok |
| list_parameters {material} | R | yes ok (Material or Instance; items {type,name}) |
| get_scalar_parameter / set_scalar_parameter {instance, name, value} | R / W | yes ok |
| get_vector_parameter / set_vector_parameter {instance, name, value {r,g,b,a}} | R / W | yes ok |
| get_static_switch_parameter / set_static_switch_parameter {instance, name, value} | R / W | yes ok |
| get_texture_parameter / set_texture_parameter {instance, name, value {refPath}} | R / W | yes ok (engine texture accepted) |
| set_parameter_override {instance, name, override} | W | yes ok |
| clear_parameters {instance} | W | yes ok |
| set_parent {instance, parent} | W | yes ok |
| diff {old_asset_path, new_asset_path} | R | yes ok (identical assets only: returns "") |

## 2. Verified recipes (exact args; each has ok rows in explore-ledger.jsonl)

R1 Material from nothing, with parameters, wired to outputs:
1. `MaterialTools/create_material {"folder_path":"<mount>/Mat_X","asset_name":"M_X"}` returns `{"returnValue":{"refPath":"<mount>/Mat_X/M_X.M_X"}}`.
2. `MaterialTools/add_expression {"material_or_function":{"refPath":"<M>"},"expression_class":{"refPath":"/Script/Engine.MaterialExpressionVectorParameter"},"x":-400,"y":0}` returns refPath `<M>:MaterialExpressionVectorParameter_0` (same with `ScalarParameter`, `StaticSwitchParameter`, `TextureSampleParameter2D`, `Multiply`, `Constant`, `MaterialFunctionCall`).
3. Name and default: `ObjectTools/set_properties {"instance":{"refPath":"<expr>"},"values":"{\"parameterName\":\"TintColor\",\"defaultValue\":{\"r\":1,\"g\":0.2,\"b\":0.1,\"a\":1},\"group\":\"GrpA\"}"}` returns true (`values` is JSON TEXT; a scalar default is a plain number).
4. `MaterialTools/connect_to_output {"expression":{"refPath":"<expr>"},"output_name":"","material_property":"MP_BaseColor"}` returns null; read back `get_property_input {"material":{"refPath":"<M>"},"material_property":"MP_BaseColor"}` returns `{"output_name":"RGB","expression":{...},"input_name":""}`.
5. `MaterialTools/recompile {"material_or_function":{"refPath":"<M>"}}` then `get_statistics {"material":{"refPath":"<M>"}}` returns instruction counts (e.g. num_pixel_shader_instructions 187).

R2 Instance: read parameter, set, re-read (the task's core check):
1. `MaterialInstanceTools/create {"folder_path":"<mount>/Mat_X","asset_name":"MI_X","parent":{"refPath":"<M>"}}`.
2. `get_scalar_parameter {"instance":{"refPath":"<MI>"},"name":"Rough"}` returns 0.5 (parent default).
3. `set_scalar_parameter {"instance":...,"name":"Rough","value":0.9}` returns null; re-read returns 0.8999999761581421 (float32).
4. Vector: `set_vector_parameter {"instance":...,"name":"TintColor","value":{"r":0.1,"g":0.8,"b":0.3,"a":1}}`; re-read returns the same within float32.
5. Static switch: `set_static_switch_parameter {...,"name":"UseX","value":true}` re-reads true. Texture: `set_texture_parameter {...,"name":"TexA","value":{"refPath":"/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"}}` re-reads that refPath (default was DefaultTexture).

R3 Wire through a Multiply and undo: `get_expression_input_names` returns ["A","B"]; `connect_expressions {"from_expression":{"refPath":"<vec>"},"from_output_name":"","to_expression":{"refPath":"<mul>"},"to_input_name":"A"}`; `get_expression_inputs {"material_or_function":...,"expression":...}` shows the wiring; `disconnect_expressions {"to_expression":...,"to_input_name":"B"}`; `disconnect_from_output {"material":...,"material_property":"MP_EmissiveColor"}` then `get_property_input` returns `expression: null`.

R4 Parameter groups: set `group` via set_properties; `list_parameter_groups` returns ["GrpA","GrpB"]; `rename_parameter_group {old_name:"GrpB",new_name:"GrpC"}`; `delete_parameter_group {group_name:"GrpC"}` (ungroups; parameters stay).

R5 Reparent an instance: `set_parent {"instance":...,"parent":{"refPath":"<M2>"}}` then `list_parameters {"material":{"refPath":"<MI>"}}` shows only M2's parameters; set back and the original list returns.

R6 Apply a material to an actor (ONE process): `SceneTools/add_to_scene_from_asset {"asset_path":"/Engine/BasicShapes/Cube","name":"X","xform":{"location":{"x":0,"y":0,"z":5000},"rotation":{"pitch":0,"yaw":0,"roll":0},"scale":{"x":1,"y":1,"z":1}}}` returns a FortStaticMeshActor; component path is `<actor>.StaticMeshComponent0`; `ObjectTools/set_properties {"instance":{"refPath":"<comp>"},"values":"{\"overrideMaterials\":[{\"refPath\":\"<MI>\"}]}"}` returns true; `ObjectTools/get_properties {"instance":...,"properties":["overrideMaterials"]}` returns it; reset with `[]`; `SceneTools/remove_from_scene {"actor":{"refPath":"<actor>"}}` returns true.

R7 Compare: `diff_material {"old_asset_path":"<pkg A>","new_asset_path":"<pkg B>"}` returns a unified diff of a JSON dump (expressions with class, inputs, properties).

Previous findings re-run here (area-relevant):
- `ObjectTools/set_properties` with `values` as JSON text: riconfermata (true on expression and component; objects inside the text work for LinearColor and refPath arrays).
- `ObjectTools/get_properties`: diversa from "rejects guessed shape": the required args are `instance` and `properties` (array of names); works, returns JSON text.
- `AssetTools/save_assets {asset_paths:[pkg]}` true: riconfermata. `AssetTools/delete {path}` true: riconfermata (also from a later process). `find_assets {folder_path,name}`: riconfermata.
- `AssetTools/duplicate` with an engine path as source: diversa for this case: `FolderPath "/Engine/BasicShapes/Cube" is outside this project's valid asset roots`.

## 3. Traps

1. `set_properties` needs `values` as a JSON text string, not an object.
2. Output pin name: `connect_*` take `""` for the default output; `get_property_input` reports `"RGB"` for a VectorParameter and `""` for Multiply. `get_expression_output_names` lists them (Vector/TextureSample: RGB,R,G,B,A,RGBA).
3. Float readback: 0.9 reads back as 0.8999999761581421; compare with tolerance.
4. `StaticMeshTools/get_material {mesh, slot_name:"None"}` returns `Material slot "None" not found on Cube.` Use the name from `get_material_slots` (`WorldGridMaterial`). `set_material` was not run on the engine mesh.
5. `get_referencing_materials` returned `[]` right after setting `materialFunction` on a MaterialFunctionCall; after `save_assets` + `recompile` it returned `[{}]` (one empty object, no path), and it stayed `[{}]` after the call node was deleted until the next recompile.
6. `set_parameter_override {override:false}` then re-enable returns the PARENT value, not the old override (as the tool doc says).
7. `ObjectTools/list_properties` on a StaticMeshComponent is 55 KB: use `get_properties` with the one name.
8. (Fixed 2026-10-16, guard widened; was:) a scene actor created by an earlier Python process cannot be changed or removed later: `refused even in the laboratory, path outside <mount>/root_ai_lab: ...root_ai_lab.root_ai_lab:PersistentLevel.Fo...`. Create, use and remove actors in ONE script. Assets created earlier can be deleted from a later process.
9. Each new Material adds shader compile time (tool doc): prefer instances of an existing material.
10. Git Bash converts `LAB_ROOT=/09e4...` into a Windows path; use PowerShell.
11. After the guard widening (2026-10-16) `LAB_ROOT` must be `/root_ai_lab` (no guid): the guard strips the guid from every path before comparing, so with the guid-form root every write is refused with `path outside /<guid>/root_ai_lab`. Tool arguments still use the guid form.
12. `AssetTools/exists` right after `delete` can still answer true for a path given without `.Name` or for a just-deleted loaded asset (MI_T008, NS_T014 stayed true while `find_assets` returned []); use `find_assets` or `exists` with the `.Name` form (MI_T008.MI_T008 gave false).

## 4. What does not work or is forbidden

- No tool edits MaterialParameterCollection entries: `create_parameter_collection` yields an empty asset.
- No dedicated tool for blend mode / shading model / two-sided (would be `ObjectTools/set_properties` on the material; not tried).
- Duplicating engine meshes into the project is refused (outside valid asset roots).
- Leftover from this task (CLOSED 2026-10-16, T-014): `T008_Cube` and `Mat_T008` were removed, see recipe R8.

R8 Clean up a leftover actor and its material (T-014, 2026-10-16, ok rows in the ledger):
1. `SceneTools/find_actors {"name":"T008","collision_channels":[]}` returns the descriptor; its `actorPath` is `/<guid>/root_ai_lab.root_ai_lab:PersistentLevel.FortStaticMeshActor_UAID_...`.
2. `SceneTools/remove_from_scene {"actor":{"refPath":"<actorPath>"}}` returns true (works from a LATER process once the guard has the widened rule); `find_actors` again returns [].
3. `AssetTools/delete {"path":"<mount>/Mat_T008"}` returns true (deletes the folder and both assets); `find_assets {"folder_path":"<mount>/Mat_T008","name":""}` returns [].
4. Run with `LAB_ROOT=/root_ai_lab` (no guid): with the guid form the widened guard compares the stripped path against a guid root and refuses everything (trap 11).

## 5. Tasks for a subagent (materials)

1. "List the parameters of material X": `list_parameters`; return [{type,name}] plus `get_statistics` numbers.
2. "Create an instance of X named Y and set parameters P=v": create, set_*_parameter, re-read each; return the values read back.
3. "Report the shader cost of material X": `recompile` then `get_statistics`; return the 8 integers.
4. "Compare materials A and B": `diff_material`; return the diff trimmed to changed expressions.
5. "Which parameter groups does X have; rename G1 to G2": list, rename, list; return both lists.
6. "Put instance Y on a cube in one script and remove it": R6 in one process; return the `overrideMaterials` read back and the remove result.

## 6. Never-tried tools and why

All 39 tools were tried. Partial: `MaterialInstanceTools/diff` only on identical assets (returns ""); `StaticMeshTools/set_material` not run (only an engine mesh was available and it must not be changed); `get_referencing_materials` returns `[{}]` without a path (trap 5).

## Drone fix log (2026-10-16, scripts `_explore/dr0.py`..`dr10.py`)

Diagnosis (mech-drone, mesh `/<guid>/mech-drone/textures/Drone.Drone`, slots `Fire`, `Robot`):
- `Fire` and `Robot` are MaterialInstanceConstant, parent `/InterchangeAssets/Materials/FBXLegacyPhongSurfaceMaterial` (FBX importer default). `textureParameterValues` was `[]` on both (no texture ever assigned) and every `*MapWeight` scalar read 0, so no texture could show; DiffuseColor 0.588 grey. Blend Opaque, DefaultLit, not two-sided.
- Editor log: `LogMaterial: Warning: Material .../Robot.Robot missing usage flag SkeletalMesh! Default Material will be used in game.` (same for Fire) and `LogSkeletalMesh: Warning: Material with missing usage flag was applied to skeletal mesh .../Drone.Drone`: the material fell back to the default material.
- Textures fine: all Texture2D, loaded; Drone_normal TC_Normalmap BC5 sRGB False; diff/gloss/spec/ao/emissive sRGB True DXT1; Fire_Alpha has no alpha channel (RGB jpeg, use R). Only warning: folder name `mech-drone` has an invalid character `-` (AssetCheck), not material related.
Original values (for revert): Robot: parent Interchange phong, Shininess 32, DiffuseColor/AmbientColor (0.588,0.588,0.588,1), SpecularColor (0.45,0.45,0.45,1). Fire: same parent, Shininess 2, Diffuse/Ambient 0.588 grey, SpecularColor (0,0,0,1). Backups: `/<guid>/root_ai_lab/DroneBackup/Robot`, `.../Fire` (duplicates, made before the change).
Changes: new `/root_ai_lab/Drone_Fix/M_Drone` (BaseColorTex Drone_diff, NormalTex Drone_normal, GlossTex Drone_gloss -> OneMinus -> Roughness, AOTex Drone_ao R -> AO, EmissiveTex Drone_emissive * EmissiveStrength 2, Metallic 0.6; bUsedWithSkeletalMesh true) and `M_DroneFire` (Translucent, Unlit, two-sided, Fire_Dif*3 -> Emissive, Fire_Alpha R -> Opacity; bUsedWithSkeletalMesh true). `set_parent` of `mech-drone/textures/Robot` -> M_Drone and `Fire` -> M_DroneFire, save_assets true. Revert: set_parent back to the Interchange phong parent (values above were not touched).
Verification: both materials recompile, statistics 217 / 158 pixel instructions, 5 / 2 texture samples; `get_material_slots` Fire, Robot and each `get_material` returns the instance; bUsedWithSkeletalMesh reads true. Not verified visually (no viewport shot) and no fresh in-game log line after the fix.
Trap: property name is `bUsedWithSkeletalMesh`; one bad key in the values JSON fails the whole set.
