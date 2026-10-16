# MCP lab: final coverage of the 388 tools (T-011)

Date: 2026-10-16. UEFN 42.40, lab `root_ai_lab`. Inputs: `Claude/logs/explore-ledger.jsonl` (2983 rows, 20:37 to 01:11), `coverage.json` + `COVERAGE.md` (queue engine, run 1), `recipes.json` (225 keys), the 10 area files, `soak.json`, `session-loop.json`.

## 1. Result

388 tools in the catalog. **388 tried (none without a ledger row), 357 ok (92%)** (`Claude/logs/_explore/cov.py`, run 2026-10-16). Recipe-only: 2. Refused by the guard (all rows refused): 7. Rejected (error, no ok row): 21. No answer: 1. Never tried: 0.

Previous figure in this file (332 ok, 86%) came from an earlier tally and is superseded.

| Area | Tools | ok | verified-by-recipe only | refused-by-guard | rejected | no answer | never tried | ok share | tools with a recipe |
|---|---|---|---|---|---|---|---|---|---|
| ui-widgets (UMG, MVVM, WidgetAnimation, VerseFields) | 53 | 49 | 0 | 0 | 4 | 0 | 0 | 92% | not recounted |
| assets (AssetTools, DataTable, CurveTable, GameplayTags, ObjectTools) | 48 | 43 | 0 | 0 | 5 | 0 | 0 | 89% | not recounted |
| editor-logs (EditorAppToolset, LogsToolset) | 41 | 40 | 0 | 0 | 1 | 0 | 0 | 97% | not recounted |
| level-devices (Actor, Scene, Entity, Device) | 68 | 64 | 0 | 0 | 4 | 0 | 0 | 94% | not recounted |
| verse-build (VerseToolset) | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 100% | not recounted |
| session-regression (SessionToolset) | 8 | 7 | 1 | 0 | 0 | 0 | 0 | 87% | not recounted |
| scripting-batch (Programmatic, ValkyriePython) | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 100% | not recounted |
| materials (MaterialTools, MaterialInstanceTools) | 39 | 39 | 0 | 0 | 0 | 0 | 0 | 100% | not recounted |
| vfx-niagara (4 Niagara toolsets) | 54 | 51 | 1 | 0 | 1 | 1 | 0 | 94% | not recounted |
| physics-mesh (StaticMesh, SkeletalMesh, PhysicsAsset, Primitive, Texture) | 63 | 50 | 0 | 7 | 6 | 0 | 0 | 79% | not recounted |
| **Total** | **388** | **357** | **2** | **7** | **21** | **1** | **0** | **92%** | **not recounted** |

(The "ok share" column is ok only, rounded down; recipe-only tools are not added. The per-area "tools with a recipe" counts of the earlier table were not recomputed.)

Recipes: `recipes.json` now has 246 keys, each with a `status` field (`verified` 230, `unverified` 16, `guard-refused` 0) set by `Claude/logs/_explore/apply_recipe_status.py` from the ledger; backup `Claude/logs/_explore/recipes.before-T011.json`.

Columns: ok = at least one ledger row `ok` (answered without error); verified-by-recipe only = no ok row but a hand recipe in recipes.json documents the behaviour; refused-by-guard = every row refused by `mcp_lab.py`; rejected = answered with an error about arguments or state, no ok row; no answer = connection dropped; never tried = no ledger row.

Area totals follow the toolset mapping above. The area files count a little differently (T-010 says 63 physics-mesh tools; T-009/T-014 say 48 Niagara while the catalog has 54 with the Component/Assets/Info toolsets; T-004 says 69 level-devices vs 68 here). Differences are 1 to 6 tools and come from which toolsets each file counted, not from different tools.

## 2. Method and discrepancies

Method (script, reproducible): for each of the 388 keys of `coverage.json`, collect all ledger rows with the same `toolset/tool`; class = ok if any row `r=ok`; else recipe if the key (before `#`) is in recipes.json; else refused if all rows are `refused`; else rejected if any row `rejected`; else no answer; else never. Ledger `ok` means "the call returned a value", not "the result was meaningful" (some ok rows are read-backs of null).

| Source | ok | Note |
|---|---|---|
| coverage.json / COVERAGE.md (queue engine, 1 run, 348 s) | 68 | rejected 77, unresolved 224, refused 19, never 0 |
| explore-ledger.jsonl (hand scripts T-001..T-014 + queue) | 332 | 1437 ok rows of 2983; 1352 rejected, 186 refused, 8 no answer |
| recipes.json | 219 tools | 225 keys; 6 are `#` variants or named procedures, not separate tools |

Discrepancies:
- The queue engine resolved 68; the hand scripts resolved 332. Of the engine's `unresolved` (224) and `rejected` (77), 245 are ok in the ledger (183 + 62): the engine cannot build the objects (widget blueprints, Niagara systems, entities) that the hand recipes create inside one process. "Unresolved 224" is a limit of the engine, not of the MCP.
- The engine counted 19 refused; the ledger's final refused count is 24 (all physics-mesh writes): the guard was widened after the queue ran (the level-devices refusals became ok in T-014) and the physics-mesh rows were re-tried with real arguments.
- The ledger has 389 distinct names: 2 are wrong-name probes (`UMGToolSet/ListWidgetViewBindings`, `SessionToolset.SessionToolset/GetSessionStatus`), not catalog tools.
- The area files and this table agree on ok counts for ui-widgets 49, materials 39, verse-build 10, scripting-batch 4, physics-mesh 32.
- `ApplyStackIssueFix` is "recipe only": the call answers an error while the fix is applied (vfx-niagara trap 17).

## 3. Tools without an ok row (31) and why

Counted by `Claude/logs/_explore/cov.py` from the ledger (2026-10-16): 7 refused by the guard, 21 rejected, 1 no answer, 2 recipe-only. Sections 3.1 to 3.3 list them; 3.2 and 3.3 predate pass E and may still name tools that now have an ok row (the PhysicsAssetToolset and SkeletalMeshTools writes): the ledger is authoritative.

Type: block = precondition not satisfiable in this lab; destructive = deliberately not run; crash suspect; needs asset; needs recipe.

### 3.1 Refused by the lab guard, 7 (every ledger row refused)
Reason: no StaticMesh can be created or copied into the lab (engine meshes rejected by the editor "outside valid asset roots", plugin meshes refused by the guard as sources), so the StaticMesh writes never reach the tool. PhysicsAssetToolset and SkeletalMeshTools writes are NOT in this list: they have ok rows since pass E (50 of 63 physics-mesh tools ok).
- StaticMeshTools (6): generate_convex_collisions, generate_lods, set_lod_thresholds, set_nanite_enabled, remove_collisions, remove_lods.
- TextureTools (1): export_png (disk path write, refused by design).

### 3.2 Rejected, 21 (answered with an error)
| Tool(s) | Reason | Type |
|---|---|---|
| DataTableTools/import_file, CurveTableTools/import_file, StaticMeshTools/import_file, SkeletalMeshTools/import_file, TextureTools/import_file | disk path source; the guard refuses drive paths for write tools, so the tool itself was never reached | block (guard by design) |
| PhysicsAssetToolset/CreateFromMesh | needs a lab skeletal mesh (writes next to the source mesh) | needs asset |
| StaticMeshTools/set_material | needs a lab static mesh | needs asset |
| StaticMeshTools/get_vertex_count, get_triangle_count | `LOD index out of range`: every static mesh tried reports 0 LODs | needs asset (a mesh with LODs) |
| GameplayTagsToolset/FindReferencersByTag, GetTagInfo, ListTagsInSource | probes used tags/sources that do not exist; no tool creates a gameplay tag | needs recipe (use a tag returned by the list tool; hypothesis) |
| EditorAppToolset/CaptureAssetImage | works on meshes, materials, textures; a widget blueprint was refused | needs asset (a material or mesh in the lab) |
| EditorAppToolset/SelectOutlinerFolders | needs an existing outliner folder (folders vanish with their last actor) | needs recipe: create actor in folder, select, remove, in ONE script (hypothesis) |
| DeviceToolset/ListDeviceProperties, GetDeviceProperties, SetDeviceProperty | need a PLACED Verse device; the built class `/<guid>/_Verse.root_ai_lab-lab_client_probe` is refused by the guard as PlaceDevice source | block (owner decision) |
| EntityToolset/AddComponent, RemoveComponent | `/Script/Entity.BaseComponent` is abstract; concrete component classes live under `/EntityFramework/_Verse`, not a source root | block (guard SRC_ROOTS) |
| SceneTools/create_level, load_level | called only with an empty path: a real call would switch the open level | destructive |
| SceneTools/diff | level (World) diff is not supported by UEFN; scene-asset diff needs a scene asset | block (UEFN limit) |
| SceneTools/replace_actors_with_class | TargetPoint to StaticMeshActor fails (log only); other class pairs untried | needs recipe |
| MVVMToolset/AddViewModelProperty | needs a ViewModel Blueprint asset; no tool creates one | needs asset |
| UMGToolSet/AddUIComponent, MoveUIComponent, RemoveUIComponent | all four component classes tried are "not permitted in this project"; Move/Remove need an existing component | block (project policy) |
| NiagaraToolset_System/GetDynamicInputChain | needs an input whose value mode is Dynamic | needs recipe (set a dynamic input first; hypothesis) |

### 3.3 Other (4)
| Tool | State | Reason / type |
|---|---|---|
| ObjectTools/get_class | never tried | the queue engine could not build its argument and no hand script called it; probably a one-line read (hypothesis). Needs recipe |
| SessionToolset/GetClientLogEntries | recipe only, answers only an error | `No client log was found` in 7+ attempts; needs a live play-in-client plus a placed device that prints; the probe device cannot be placed (guard). Block |
| NiagaraToolset_System/GetDynamicInputSchema | no answer | CRASH SUSPECT: called on a non-dynamic input, ConnectionResetError, editor port closed once (T-009); not called again in T-014. Only ever call it on a Dynamic-mode input |
| NiagaraToolset_System/ApplyStackIssueFix | recipe only | replies an error ("compile in flight") but the fix is applied; verify by re-reading |

## 4. Soak (`soak.json`)

100 iterations of a 6-step loop (CreateWidgetBlueprint, AddWidget, CompileWidgetBlueprint, save_assets, delete, GetCameraTransform), 3.5 min, `failed_steps` 400.

| Step | first 10 (s) | last 10 (s) | slower |
|---|---|---|---|
| CreateWidgetBlueprint | 0.334 | 0.334 | no |
| AddWidget | 0.333 | 0.333 | no |
| CompileWidgetBlueprint | 0.333 | 0.333 | no |
| save_assets | 0.435 | 0.440 | no |
| delete | 0.231 | 0.227 | no |
| GetCameraTransform | 0.332 | 0.333 | no |

Reading: the "no drift" result is valid for the rejection path and for plain reads, not for real creation. The ledger shows every soak CreateWidgetBlueprint (429 rows, 00:40-00:49) rejected in 0.33 s with `FolderPath "/root_ai_lab/Cover" is outside this project's valid asset roots`: the soak passed the LAB_ROOT form `/root_ai_lab` as an ASSET path, which the editor refuses (assets need the GUID mount `/09e4e8d3-.../root_ai_lab`). The 400 failed steps are the 4 widget-dependent steps of the 100 iterations; the constant 0.333 s is the round trip of an error. What does hold: about 600 calls in 3.5 min with no drop, no hang and no latency growth (0.33 s for a refused call, 0.23 s delete, 0.44 s save_assets, 0.333 s GetCameraTransform). Not measured: drift of real create/compile/delete cycles (hypothesis: slower, since a widget compile takes seconds in T-001). Recommendation: re-run the soak with the GUID mount as asset path (cheap).

## 5. Session loop (`session-loop.json`)

5 loops of StartSession, GetSessionStatus, StartGame, GetGameState, GetClientLogEntries, StopGame, StopSession. `clean_loops` 0 of 5.

| Step | Result in all 5 loops | Time |
|---|---|---|
| StartSession | Completed | 15.6 to 16.7 s (manual runs in T-006: 67-79 s) |
| GetSessionStatus | Connected at once | 0 s wait |
| StartGame | `The Start Game command is not currently available.` | 0.01-0.02 s |
| GetGameState | `CanStart` | 0.00-0.02 s |
| GetClientLogEntries | `No client log was found; start a play-in-client session first.` | 0.01-0.02 s |
| StopGame | `No match is running to stop.` | 0.01-0.02 s |
| StopSession | ok (null) | 0.01-0.02 s |

Reading: the loop is stable and deterministic (identical outcome 5 of 5, no flakiness, StopSession always cleans up, no hang) but never reached Running. In T-006 StartGame worked after StartSession and gave `Running`. Difference: the loop called StartGame immediately after `Connected` at 16 s. Hypothesis (unverified): StartSession answers Completed before the client is ready, so GetGameState should be polled (about 60 s) and StartGame retried. The loop is also "not clean" by construction because GetClientLogEntries counts as a failure until a live client log exists. Failure detection by the build step (code 3509) was verified separately in session-regression R4 and does not depend on this loop.

## 6. Recipes count

225 keys in recipes.json, 219 tools covered; per area: ui-widgets 14, assets 38, editor-logs 19, level-devices 54, verse-build 10, session-regression 8, scripting-batch 4, materials 17, vfx-niagara 37, physics-mesh 18 (the T-011 criterion "at least 3 per area" is met everywhere). Two keys are procedures, not tools: `collision_set_and_revert`, `recipe/apply_material_instance_to_actor`.

## 7. Aperto

- **GetClientLogEntries** (SessionToolset): still answers `No client log was found`; the working route is `EditorToolset.LogsToolset/GetLogEntries`. Status in recipes.json: `unverified`.
- **Soak and session loop not run**: 100 cycles of the soak and 5 full session cycles were not executed; they slide to **T-017**. Single probe: StartSession about 88 s, StartGame 0.28 s after `Connected`.
- **Tools without ok, outside physics-mesh (3)**:
  - SelectOutlinerFolders: needs an outliner already open.
  - SceneTools/replace_actors_with_class: only the TargetPoint to StaticMeshActor pair was tried; other class pairs not tried.
  - NiagaraToolset_System/GetDynamicInputChain: rejected; needs an input in Dynamic mode first.
  - ObjectTools/get_class: NOT in this list any more, it has ok rows in the ledger.
- **Physics-mesh, 13 tools without ok** (cov.py): 10 StaticMesh (generate_convex_collisions, generate_lods, set_lod_thresholds, set_nanite_enabled, remove_collisions, remove_lods refused by the guard; import_file, set_material, get_vertex_count, get_triangle_count rejected), 1 SkeletalMesh import_file, 2 Texture (export_png refused, import_file rejected). Cause: no StaticMesh in the project and `import_file` refused for disk paths (project path rule). None of the 13 has been tried against a real mesh.
- **Inconsistency to resolve**: section 3.1 lists 11 PhysicsAssetToolset tools as refused-by-guard, but the ledger has ok rows for them (AddBody, RemoveBody, SetSphere, ...). cov.py counts them ok. Section 3.1 is not corrected here; the ok rows need a check before the list is rewritten.
- The recipe `status` is a key-subset match (an ok row whose args contain every top-level arg key of the recipe); values are not compared. `MaterialInstanceTools/set_parent#drone_skeletal_fix` is `unverified` because its key has no toolset prefix and does not match the ledger name.
