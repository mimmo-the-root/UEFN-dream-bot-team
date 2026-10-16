# MCP area: vfx-niagara (NiagaraToolsets: System, Assets, Component, Info)

Date: 2026-10-16 (task T-009 + T-014 pass A). UEFN version: 42.40. Lab `/root_ai_lab`. 48 tools in the area; T-014 (2026-10-16) CLOSED the write gap: CreateNiagaraSystem from the engine template now works, all 17 Add/Remove/Set tools and the 4 component tools were run with read-back and restore (ApplyStackIssueFix with a caveat, trap 17). Scratch scripts: `Claude/logs/_explore/v0.py`..`v11.py`, `g5.py`..`g25.py`.

Toolsets (exact names, from the MCP map): `NiagaraToolsets.NiagaraToolset_System` (40 tools), `NiagaraToolsets.NiagaraToolset_Assets` (3), `NiagaraToolsets.NiagaraToolset_Component` (4), `NiagaraToolsets.NiagaraToolset_Info` (1). Helper tool used: `editor_toolset.toolsets.asset.AssetTools/find_assets`.

Call form: `call_tool {toolset_name, tool_name, arguments}`; answers `{"returnValue": ...}`. Object references are `{"refPath": "..."}`. Run from PowerShell with `LAB_AGGRESSIVE=1` and `LAB_ROOT=/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`.

STATE AT CLOSE (T-014 pass A): all 48 tools tried; every write has an ok ledger row (ApplyStackIssueFix: effect verified, reply is an error, trap 17). Everything created (`<LAB_ROOT>/Fx` with NS_T014 and NS_T014B, 4 NiagaraActors) was deleted again; `find_assets` under Fx returns [].

Run with `LAB_ROOT=/root_ai_lab` (no guid) from PowerShell since the guard widening (see materials.md trap 11).

## 1. What the area is for, and the tools

Read and edit Niagara systems: system, emitters, script stacks (spawn/update), modules and their inputs, renderers, user variables, and the NiagaraComponent on an actor.

Reference object used by almost every System tool (`NiagaraExt_StackItemReference`, all six fields required): `{"system":{"refPath":"<NS>"},"emitterName":"","scriptName":"","moduleName":"","rendererIndex":-1,"inputNameStack":[]}`. Fill only what you point at: emitter = `emitterName`; script stack = plus `scriptName` (`EmitterSpawnScript`, `EmitterUpdateScript`, `ParticleSpawnScript`, `ParticleUpdateScript`); module = plus `moduleName`; input = plus `inputNameStack:["Spawn Count"]`; renderer = `emitterName` + `rendererIndex`.

| Tool (NiagaraToolset_System) | R/W | Tried |
|---|---|---|
| GetSystemSummary {system} | R | yes ok (576 B) |
| GetUserVariables {system} | R | yes ok |
| GetSystemData {system} | R | yes ok (propertyValues JSON text) |
| GetSystemSchema {} | R | yes ok (25 KB) |
| GetSystemCompileState {system} | R | yes ok |
| GetSystemDependencies {system} | R | yes ok |
| GetStackIssues {system} | R | yes ok (4.8 KB, info issues only) |
| GetEmitterSummary {emitterRef} | R | yes ok |
| GetEmitterData {emitterRef} | R | yes ok |
| GetEmitterSchema {} | R | yes ok (12 KB) |
| GetEmitterTopology {emitterRef} | R | yes ok (56 KB) |
| GetEmitterInputValues {emitterRef} | R | yes ok (48 KB) |
| GetScriptStackTopology {scriptRef} | R | yes ok (6.8 KB) |
| GetScriptStackInputValues {scriptRef} | R | yes ok (5 KB) |
| GetModuleTopology {moduleRef} | R | yes ok |
| GetModuleInputValues {moduleRef} | R | yes ok |
| GetModuleSchema {moduleReference} | R | yes ok (10 KB) |
| GetModuleSchemaFromAsset {moduleAsset} | R | yes ok (9 KB) |
| GetStackInputTopology {stackInputRef} | R | yes ok |
| GetStackInputSchema {inputReference} | R | yes ok |
| GetStackInputData {stackInputRef} | R | yes ok |
| GetRendererData {rendererRef} | R | yes ok (10 KB) |
| GetRendererSchema {rendererClass} | R | yes ok (19 KB) |
| GetDataInterfaceSchema {dataInterfaceClass} | R | yes ok |
| GetDynamicInputChain {stackInputRef} | R | yes, error on a non-dynamic input (trap 4) |
| GetDynamicInputSchema {dynamicInputReference} | R | yes, connection reset: editor lost (trap 2) |
| GetDynamicInputSchemaFromAsset {dynamicInputAsset} | R | yes ok (pass 2, R5) |
| GetAvailableDynamicInputs {type} | R | yes ok (pass 2, R5; pass 1 connection reset) |
| CreateNiagaraSystem {assetName, assetPath, templateSystem} | W | yes ok (T-014, R6; pass 1-2 refused, trap 1 is history) |
| AddEmitter, RemoveEmitter, AddModule, RemoveModule, AddRenderer, RemoveRenderer, AddSetParametersModule, AddSetParameterEntry, RemoveSetParameterEntry, AddUserVariables, RemoveUserVariables, SetSystemData, SetEmitterData, SetRendererData, SetStackInputData, SetModuleEnabled | W | yes ok (T-014, R7, R8) |
| ApplyStackIssueFix {system, issueId, fixId} | W | yes, effect applied, reply is an error (trap 17, R8) |

| Tool (NiagaraToolset_Assets) | R/W | Tried |
|---|---|---|
| GetAssetDiscoveryInfo {} | R | yes ok (`[]` in this project) |
| FindNiagaraScripts {folderPath, name, usages, visibilities, supportedUsages, bRecursive, bIncludeDeprecated} | R | yes ok (see trap 5) |
| GetNiagaraScriptDigest {objectPath} | R | yes ok (pass 2, R5) |

| Tool (NiagaraToolset_Component) | R/W | Tried |
|---|---|---|
| GetUserVariables {component}, GetVariable {component, var}, SetVariable {component, variable}, SetSystem {niagaraComponent, system, bResetExistingOverrideParameters} | R, R, W, W | yes ok (T-014, R9) |

| Tool (NiagaraToolset_Info) | R/W | Tried |
|---|---|---|
| UEnum_Info {enum} | R | yes ok |

## 2. Verified recipes (exact args; each has ok rows in explore-ledger.jsonl; all in `recipes.json`)

Prerequisite for every recipe: a Niagara system refPath. This project mounts Epic's content: `AssetTools/find_assets {"folder_path":"","name":"","asset_type":{"refPath":"/Script/Niagara.NiagaraSystem"}}` returned 15141 systems (1.7 MB, see trap 3) and 129 emitters (`/Script/Niagara.NiagaraEmitter`, 11 KB). Template systems: `/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion.SimpleExplosion` (also MinimalLightweight, FountainLightweight, RadialBurst, DirectionalBurst, `/Niagara/DefaultAssets/DefaultSystem.DefaultSystem`). No system exists under the lab root.

R1 Read a system: `GetSystemSummary {"system":{"refPath":"<NS>"}}` returns `{systemName, userVariables, emitters:[{emitterName, bEnabled, simTarget, rendererClasses}]}` (SimpleExplosion: OmnidirectionalBurst, UpwardMeshBurst, SimpleSpriteBurst). Then `GetSystemCompileState` returns `aggregateStatus "UpToDate"` plus one entry per script; `GetSystemDependencies` returns usedRenderers / usedDataInterfaces / usedModules / usedDynamicInputs; `GetStackIssues` returns `{numErrors, numWarnings, numInfos, issues[]}`.

R2 Walk down to one value, read only: emitter name from R1; `GetEmitterTopology {"emitterRef":{"system":{"refPath":"<NS>"},"emitterName":"OmnidirectionalBurst","scriptName":"","moduleName":"","rendererIndex":-1,"inputNameStack":[]}}` returns the four stacks (`emitterSpawnScript`, `emitterUpdateScript`, `particleSpawnScript`, `particleUpdateScript`, each `{scriptName, modules[]}`) and `renderers[]`. In OmnidirectionalBurst the update stack holds EmitterState and SpawnBurst_Instantaneous. Then `GetModuleInputValues {"moduleRef":{...,"scriptName":"EmitterUpdateScript","moduleName":"SpawnBurst_Instantaneous"}}` returns inputs; "Spawn Count" = `{"struct":{"refPath":"/Script/Niagara.NiagaraInt32"},"value":{"value":100}}`. One input directly: `GetStackInputData {"stackInputRef":{...,"moduleName":"SpawnBurst_Instantaneous","inputNameStack":["Spawn Count"]}}` returns `{"struct":{"refPath":"/Script/Niagara.NiagaraInt32"},"value":{"value":100}}`. `GetStackInputTopology` and `GetStackInputSchema` take the same reference (`inputReference` for the schema).

R3 Renderer and data interface: `GetRendererData {"rendererRef":{...,"emitterName":"OmnidirectionalBurst","rendererIndex":0}}` returns `{propertyValues: "<JSON text>"}` (Material `/Niagara/DefaultAssets/DefaultSpriteMaterial.DefaultSpriteMaterial`, Alignment, SortMode...). Schemas (no system needed): `GetRendererSchema {"rendererClass":{"refPath":"/Script/Niagara.NiagaraSpriteRendererProperties"}}` (19 KB), `GetDataInterfaceSchema {"dataInterfaceClass":{"refPath":"/Script/Niagara.NiagaraDataInterfaceCurve"}}`, `GetSystemSchema {}`, `GetEmitterSchema {}`, `GetModuleSchemaFromAsset {"moduleAsset":{"refPath":"/Niagara/Modules/Emitter/SpawnBurst_Instantaneous.SpawnBurst_Instantaneous"}}`.

R4 Find module scripts: `NiagaraToolset_Assets/FindNiagaraScripts {"folderPath":"","name":"Initialize","usages":["Module"],"visibilities":[],"supportedUsages":[],"bRecursive":true,"bIncludeDeprecated":false}` (all seven params required) returned a list of 14 items, every item an empty object `{}` (trap 5). `NiagaraToolset_Info/UEnum_Info {"enum":{"refPath":"/Script/Niagara.ENiagaraScriptUsage"}}` returns the enum values as JSON text (valid `usages` strings).

R6 (T-014) Create a lab system: `CreateNiagaraSystem {"assetName":"NS_T014","assetPath":"<mount>/Fx","templateSystem":{"refPath":"/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight"}}` returns `{"returnValue":{"refPath":"<mount>/Fx/NS_T014.NS_T014"}}`; `find_assets {folder_path:"<mount>/Fx",name:""}` lists it; `GetSystemSummary` shows one empty emitter `Minimal` (no modules, no renderers). A second system NS_T014B the same way.

R7 (T-014) Structure edits, each re-read through `GetSystemSummary` / `GetEmitterTopology` (modules carry `enabled`, not `bEnabled`):
- `AddEmitter {system, templateEmitter:{refPath:"/Niagara/DefaultAssets/Templates/Emitters/SimpleSpriteBurst.SimpleSpriteBurst"}, emitterName:"EmitA"}` returns the topology (EmitterState, SpawnBurst_Instantaneous, InitializeParticle, ParticleState, ScaleColor, SolveForcesAndVelocity, 1 sprite renderer); `RemoveEmitter {emitterToRemove:<ref with emitterName>}` returns null.
- `AddModule {moduleLocationRef:<ref emitterName + scriptName "EmitterUpdateScript">, moduleAsset:{refPath:"/Niagara/Modules/Emitter/SpawnRate.SpawnRate"}}` returns the module topology (moduleName SpawnRate); `RemoveModule {moduleToRemove:<ref ... moduleName "SpawnRate">}` null; the list is back to two modules.
- `AddRenderer {newRendererLocation:<ref emitterName>, rendererClass:{refPath:"/Script/Niagara.NiagaraRibbonRendererProperties"}}` returns `{rendererIndex:1, rendererClass}`; `RemoveRenderer {rendererToRemove:<ref emitterName, rendererIndex 1>}` null.
- `SetModuleEnabled {moduleRef:<ref ParticleUpdateScript/ScaleColor>, bEnabled:false}` null; topology shows `enabled:false`; true restores.
- `AddSetParametersModule {moduleLocationRef:<ref ParticleSpawnScript>, parameters:[{variable:{name:"Particles.T014A", type:{classStructOrEnum:{refPath:"/Script/Niagara.NiagaraFloat"}}}, defaultValue:{struct:{refPath:NiagaraFloat}, value:{value:1.0}}}]}` returns a module named `SetVariables_<guid>` with `bIsSetParametersModule:true`; `AddSetParameterEntry {moduleRef, entry:<same shape>}` returns the module with 2 inputs; `RemoveSetParameterEntry {moduleRef, parameterName}` null (1 input); `RemoveModule` removes the module.
- `AddUserVariables {system, variablesToAdd:[{name:"User.T014Float", description, type:{classStructOrEnum:{refPath}}, defaultValue:{struct, value:{value:2.5}}}]}` null; `GetUserVariables` shows it; `RemoveUserVariables {system, variablesToRemove:[{name, type}]}` null.

R8 (T-014) Values: set, re-read equal, restore (every set returned null; re-read after each):
- `SetSystemData {system, systemData:{propertyValues:"{\"TranslucencySortPriority\":3}"}}`; `GetSystemData` then shows 3; restore 0.
- `SetEmitterData {emitter:<ref>, emitterData:{propertyValues:"{\"RandomSeed\":7}"}}`; restore 0.
- `SetRendererData {renderer:<ref emitterName + rendererIndex 0>, rendererData:{propertyValues:"{\"MacroUVRadius\":2}"}}`; restore 0.
- `SetStackInputData {stackInputRef:<ref SpawnBurst_Instantaneous, inputNameStack ["Spawn Count"]>, inputData:{struct:{refPath:NiagaraInt32}, value:{value:123}}}` returns the stored value; `GetStackInputData` returns 123; sending back the first read (1) restores it.
- `ApplyStackIssueFix {system, issueId, fixId}`: induce an Error with `RemoveModule EmitterState` (issue "The module has unmet dependencies", fix "Add new dependency module EmitterState", style Fix), wait about 9 s, `GetStackIssues`, then the call. Reply: error `Cannot collect stack issues while a compile is in flight` but the module is back and numErrors is 0 (trap 17).

R9 (T-014) Component tools, ONE script, try/finally: `SceneTools/add_to_scene_from_asset {asset_path:"<lab NS>", name:"T014_Fx", xform}` returns a `NiagaraActor` refPath A (class /Script/Niagara.NiagaraActor; the editor accepts it, StartSession was not run); component = `A.NiagaraComponent0`. `GetUserVariables {component}` lists `T014Float` (no `User.` prefix); `GetVariable {component, var:{name:"T014Float", type:{classStructOrEnum:{refPath:NiagaraFloat}}}}` returns 2.5; `SetVariable {component, variable:{name:"T014Float", type:{...}, value:{struct:{refPath:NiagaraFloat}, value:{value:7.0}}}}` null, re-read 7; set 2.5 back, re-read 2.5. `SetSystem {niagaraComponent, system:<other lab NS>, bResetExistingOverrideParameters:true}` null; `ObjectTools/get_properties {instance:<comp>, properties:["asset"]}` shows the new system; set back. `remove_from_scene {actor:A}` true; `find_actors {actor_type:{refPath:"/Script/Niagara.NiagaraActor"}, collision_channels:[]}` returns [].

Previous findings re-run: the previous-findings file has no Niagara recipe; nothing to mark here. Its general rules were riconfermata where used: reference as `{"refPath":...}`, big lists need a filter (`find_assets` needs `asset_type` here; folder alone is not enough).

## 3. Traps (exact messages)

1. Write tools refuse templates outside the lab: `CreateNiagaraSystem {assetName:"NS_T009", assetPath:"<LAB_ROOT>/VFX_T009", templateSystem:{refPath:"/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight"}}` gave `refused even in the laboratory, path outside /09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab: /Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight`. The guard allows only `/Script/`, `/Engine/` and lab-root paths, and every Niagara template lives in `/Niagara/...` or a plugin mount. Not worked around.
2. `GetDynamicInputSchema {dynamicInputReference: <input ref of Spawn Count, a plain Int32 input, not a dynamic input>}` ended in `ConnectionResetError`; the next calls gave `ConnectionResetError`, then `could not read the open level to confirm the laboratory: URLError`; port 8000 stopped listening and no editor process remained (only `CrashReportClientEditor`). Probable cause: this call on a non-dynamic input crashes the editor (one observation, not re-tested). Do not call `GetDynamicInputSchema` on an input that is not in Dynamic mode; use `GetDynamicInputSchemaFromAsset` for assets (verified pass 2, R5).
3. Size: `find_assets` with `asset_type NiagaraSystem` and empty folder returns 1.7 MB (15141 paths). Filter by `name` or `folder_path`+`name`. `GetEmitterTopology` 56 KB and `GetEmitterInputValues` 48 KB per emitter: use `GetScriptStackTopology` (7 KB) or `GetModuleInputValues` (1 KB) instead.
4. `GetDynamicInputChain` on a plain input: `GetDynamicInputChain: the starting input's value mode is not Dynamic. Only Dynamic-mode inputs have a chain to walk. Static-switch / conditional sub-inputs are flattened into their parent module's Inp...`. Not a crash; it needs an input whose value is a dynamic input.
5. `FindNiagaraScripts` without `usages` fails: `Function "FindNiagaraScripts", input param "usages" is required by the function input schema Json, but is missing`. All of usages, visibilities, supportedUsages, bRecursive, bIncludeDeprecated, folderPath, name are required. The 14 results were all `{}` (no path or name came back): use `GetNiagaraScriptDigest` (verified pass 2, R5) or `find_assets` with `/Script/Niagara.NiagaraScript` to get names.
6. Result values are wrapped: a module input is `{"struct":{refPath of the value type},"value":{"value":N}}` (double `value`). Enums come as `{"enum":{refPath},"enumName":"...::NewEnumerator0","displayName":"System"}`. GetSystemData/GetEmitterData/GetRendererData return their properties as a JSON TEXT string in `propertyValues`.
7. Script names in refs are the short names (`EmitterUpdateScript`), while `GetSystemCompileState` prints them as `ENiagaraScriptUsage::ParticleUpdateScript`.
8. Reads on engine templates (`/Niagara/...`) pass the lab guard because they are read tools; do not try writes on them.

9. Pass 2: `AssetTools/duplicate {path:"/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight", new_path:"<LAB_ROOT>/NS_T009_Copy"}` -> `refused even in the laboratory, path outside <LAB_ROOT>: /Niagara/DefaultAssets/...`; `exists` then false. Not worked around.
10. `CreateNiagaraSystem` with `templateSystem:{refPath:""}` -> `Parameter error: None is not valid value for property 'TemplateSystem'.` (the template is mandatory and must resolve).
11. `GetDynamicInputSchemaFromAsset` wants a NiagaraScript that is a dynamic input: `/Niagara/DynamicInputs/Constant.Constant` -> `is not valid NiagaraScript for property 'DynamicInputAsset'` (no such asset); use a path from `find_assets {folder_path:"/Niagara/DynamicInputs", name:"Random", asset_type:{refPath:"/Script/Niagara.NiagaraScript"}}`.
12. `GetAvailableDynamicInputs {type:{refPath}}` -> `'classStructOrEnum.refPath' is missing`: the type is wrapped, `{"type":{"classStructOrEnum":{"refPath":"/Script/Niagara.NiagaraInt32"}}}`.
13. Component tools take a `NiagaraComponent` object ref; a nonexistent one gives `Parameter error: <path> is not valid NiagaraComponent for property 'Component'` (no crash). GetDynamicInputSchema stays DO NOT CALL on non-dynamic inputs (pass 2 did not call it).
14. Shell: from Git Bash set `MSYS_NO_PATHCONV=1` or LAB_ROOT gets rewritten to a Windows path and the lab refuses to start.

15. (T-014) `AddUserVariables` items are FLAT: `{name, description, type, defaultValue}`. A nested `{variable:{name,type}, defaultValue}` is accepted (null) but creates a variable named `User.None` with a null type; `RemoveUserVariables` of it fails `'classStructOrEnum.refPath' is missing or does not resolve`. It only goes away with the asset.
16. (T-014) `SetVariable` on a component without `type` in `variable` returns null and changes nothing (and a null-typed duplicate `T014Float` appears in `GetUserVariables`). Give `{name, type, value}`. A bare number as `value.value` gives `Missing 'value' object for Property 'Value'`.
17. (T-014) `ApplyStackIssueFix` answers `Cannot collect stack issues while a compile is in flight. Wait for compilation to complete (UNiagaraSystem::OnSystemCompiled) before calling.` even after a 9 s wait, yet the fix IS applied (EmitterState re-added, numErrors 0, seen twice). Verify by re-reading; the ledger rows are `rejected`, not ok.
18. (T-014) A system created from MinimalLightweight has one emitter `Minimal` with no modules and no renderer; use `AddEmitter` with a real emitter template to get something to edit.
19. (T-014) `SetSystem` with the system the component already has: `New Niagara System is the same as the existing System.`
20. (T-014) `SceneTools`/`AssetTools/list_folders` of the project root still lists deleted `NiagaraActor_UAID_...` objects of `PersistentLevel`; `find_actors` (the truth) returns none.

## 4. What does not work or is forbidden

- Nothing is blocked any more (T-014). Still do not: call `GetDynamicInputSchema` on a non-dynamic input (crashed the editor once); write to `/Niagara/...` templates (source only); leave a NiagaraActor in the level (delete it in the same script).
- `GetDynamicInputSchema` was NOT called in T-014 either.

R5 (pass 2) Script digest and dynamic inputs, read only: `NiagaraToolset_Assets/GetNiagaraScriptDigest {"objectPath":"/Niagara/Modules/Emitter/SpawnBurst_Instantaneous.SpawnBurst_Instantaneous"}` returns `{usage, libraryVisibility, supportedUsages, category, description, bDeprecated, bSuggested}`. `System/GetAvailableDynamicInputs {"type":{"classStructOrEnum":{"refPath":"/Script/Niagara.NiagaraInt32"}}}` returns a list of `{refPath}` of dynamic inputs for that type (Add_Integer, ModuloInt...). `System/GetDynamicInputSchemaFromAsset {"dynamicInputAsset":{"refPath":"/Niagara/DynamicInputs/Random/RandomInt.RandomInt"}}` returns `{asset, inputs:[{name, type, metaData...}]}` (large).

## 5. Tasks for a subagent (vfx-niagara)

1. "Describe Niagara system S": `GetSystemSummary` + `GetSystemCompileState`; return systemName, emitters (name, simTarget, renderer classes), aggregateStatus.
2. "Read input I of module M in emitter E of system S": `GetStackInputData` with the six-field reference; return the type refPath and value.
3. "List the modules of emitter E per stack": `GetEmitterTopology`, keep only `scriptName` and `moduleName` lists (the full answer is 56 KB: trim inside a batch script).
4. "Does system S have issues": `GetStackIssues`; return numErrors, numWarnings and issue shortDescriptions.
5. "Which Niagara systems does folder F or name N have": `find_assets` with `asset_type` `/Script/Niagara.NiagaraSystem` and `name`; return at most 50 refPaths.
6. "Set input I to V and re-read, then restore": create a lab system (R6) and an emitter (R7), `SetStackInputData`, `GetStackInputData`, restore (R8); return both values; delete the system folder at the end (verified in T-014).

## 6. Never-tried tools and why

T-014 pass A: 48 of 48 tried. Exceptions: `GetDynamicInputSchema` (on purpose, crash risk, only works on a Dynamic-mode input) and `GetDynamicInputChain` (needs an input in Dynamic mode; `SetStackInputData` with a dynamic input value was not attempted). ApplyStackIssueFix works but its reply is an error (trap 17). Criteria of T-009 met: system created, parameter read, set, re-read equal, restored; lab-placed NiagaraActor created and deleted in one script.
