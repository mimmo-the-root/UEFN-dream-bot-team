# Tool reference

388 tools, 369 with a proven recipe.

Every tool of the UEFN MCP that the kit has met, grouped by toolset, with the parameters its tested recipe uses. The last column says how far the kit trusts the recipe: proven (used in real work or replayed), tool-ok (answered in a test), unverified, avoid (known trap, do not call). This page is generated; the full live description of each tool stays on your computer: run `mcp_map.py --find <word>` to see it.

## ActorTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_component | owner (asset ref), component_type (asset ref), name (text) | yes | proven |
| add_tag | actor (asset ref), tag (text) | yes | proven |
| diff | old_actor (asset ref), new_actor (asset ref) | no | proven |
| get_actor_bounds | actor (asset ref) | no | proven |
| get_actor_transform | actor (asset ref) | no | proven |
| get_component_actor | component (asset ref) | no | proven |
| get_components | actor (asset ref) | no | proven |
| get_label | actor (asset ref) | no | proven |
| get_parent_component | component (asset ref) | no | proven |
| get_root_component | actor (asset ref) | no | proven |
| get_tags | actor (asset ref) | no | proven |
| has_tag | actor (asset ref), tag (text) | no | proven |
| look_at | actor (asset ref), target (object) | yes | proven |
| remove_component | component (asset ref) | yes | proven |
| remove_tag | actor (asset ref), tag (text) | yes | proven |
| set_actor_transform | actor (asset ref), xform (object), worldspace (true/false) | yes | proven |
| set_label | actor (asset ref), label (text) | yes | proven |
| set_parent_component | component (asset ref), parent (asset ref) | yes | proven |

## AssetTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| create_folder | path (text) | yes | proven |
| delete | path (text) | yes | proven |
| duplicate | path (text), new_path (text) | yes | proven |
| exists | path (text) | no | proven |
| find_assets | folder_path (text), asset_type (asset ref), recursive (true/false) | no | proven |
| get_asset_class | asset_path (text) | no | proven |
| get_asset_tags | asset_path (text) | no | proven |
| get_dependencies | asset_path (text) | no | proven |
| get_metadata_tags | asset_path (text) | no | proven |
| get_referencers | asset_path (text) | no | proven |
| is_dirty | asset_path (text) | no | proven |
| list_folders | root_path (text), recursive (true/false) | no | proven |
| load_asset | asset_path (text) | no | proven |
| move | path (text), new_path (text) | yes | proven |
| reload_asset | asset_path (text) | yes | proven |
| save_assets | asset_paths (list) | yes | proven |
| update_metadata_tags | asset_path (text), set_tags (object) | yes | proven |

## CurveTableTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_key | curve_table (asset ref), row_name (text), key (object) | yes | proven |
| add_row | curve_table (asset ref), row_name (text), default_value (number) | yes | proven |
| create | folder_path (text), asset_name (text) | yes | proven |
| diff | old_asset_path (text), new_asset_path (text) | no | proven |
| get_keys | curve_table (asset ref), row_name (text) | no | proven |
| import_file | folder_path (text), asset_name (text), source_file (text), interp_mode (text) | yes | proven |
| list_rows | curve_table (asset ref) | no | proven |
| remove_row | curve_table (asset ref), row_name (text) | yes | proven |
| rename_row | curve_table (asset ref), row_name (text), new_row_name (text) | yes | proven |
| set_keys | curve_table (asset ref), row_name (text), keys (list) | yes | proven |

## DataTableTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_rows | data_table (asset ref), row_names (list) | yes | proven |
| create | folder_path (text), asset_name (text), schema (asset ref) | yes | proven |
| diff | old_asset_path (text), new_asset_path (text) | no | proven |
| get_rows | data_table (asset ref), row_names (list) | no | proven |
| get_schema | data_table (asset ref) | no | proven |
| import_file | folder_path (text), asset_name (text), source_file (text), schema (asset ref) | yes | proven |
| list_rows | data_table (asset ref) | no | proven |
| remove_rows | data_table (asset ref), row_names (list) | yes | proven |
| rename_rows | data_table (asset ref), renames (object) | yes | proven |
| search_row_structs | struct_name (text) | no | proven |
| set_rows | data_table (asset ref), values (text) | yes | proven |

## DeviceToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddEventBinding | sourceDevicePath (asset ref), sourceEvent (text), targetDevicePath (asset ref), targetFunction (text) | yes | proven |
| GetBindingOptions | devicePath (asset ref) | no | proven |
| GetDeviceProperties | see mcp_map.py --find | ? | no recipe |
| ListDeviceAssets | nameFilter (text) | no | proven |
| ListDeviceProperties | see mcp_map.py --find | ? | no recipe |
| ListEventBindings | devicePath (asset ref) | no | proven |
| PlaceDevice | assetPath (asset ref), transform (object) | yes | proven |
| RemoveEventBinding | sourceDevicePath (asset ref), sourceEvent (text), targetDevicePath (asset ref), targetFunction (text) | yes | proven |
| SetDeviceProperty | see mcp_map.py --find | ? | no recipe |

## EditorAppToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddAssetsToCollection | collection (object), assetPaths (list) | yes | proven |
| CaptureAssetImage | assetPath (text) | no | proven |
| CaptureEditorImage | none | no | proven |
| CaptureViewport | none | no | proven |
| CreateCollection | collectionName (text), shareType (text) | yes | proven |
| DestroyCollection | collection (object) | yes | proven |
| FocusOnActors | actors (list) | yes | proven |
| GetActiveEditorModes | none | no | proven |
| GetAssetThumbnails | assetPaths (list) | no | proven |
| GetCVarValue | name (text) | no | proven |
| GetCameraTransform | none | no | proven |
| GetCollectionAssets | collection (object) | no | proven |
| GetContentBrowserPath | none | no | proven |
| GetOpenAssets | none | no | proven |
| GetSelectedActors | none | no | proven |
| GetSelectedAssets | none | no | proven |
| GetSelectedOutlinerFolders | none | no | proven |
| GetShowFlag | flagName (text) | no | proven |
| GetVisibleActors | none | no | proven |
| ListCollections | none | no | proven |
| ListEditorModes | none | no | proven |
| ListShowFlags | none | no | proven |
| OpenEditorForAsset | assetPath (text) | yes | proven |
| RemoveAssetsFromCollection | collection (object), assetPaths (list) | yes | proven |
| ScreenCoordsToWorld | coords (object) | no | proven |
| SearchCVars | name (text) | no | proven |
| SelectActors | actors (list) | yes | proven |
| SelectAssets | assetPaths (list) | yes | unverified |
| SelectOutlinerFolders | see mcp_map.py --find | ? | no recipe |
| SetCVarValue | name (text), value (text) | yes | proven |
| SetCameraTransform | transform (text) | yes | proven |
| SetContentBrowserPath | path (text) | yes | proven |
| SetEditorMode | modeId (text) | yes | proven |
| SetShowFlag | flagName (text), bEnabled (true/false) | yes | proven |
| SetViewportViewMode | viewMode (text) | yes | proven |
| ShowNotification | message (text) | no | proven |
| WorldPosToScreenCoords | position (object) | no | proven |

## EntityToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddComponent | see mcp_map.py --find | ? | no recipe |
| CreateEntity | entityClass (asset ref), transform (object) | yes | proven |
| DeleteEntity | entity (asset ref) | yes | proven |
| FindEntities | nameFilter (text) | no | proven |
| GetComponentProperty | component (asset ref), propertyName (text) | no | proven |
| GetComponents | entity (asset ref) | no | proven |
| GetEntityTransform | entity (asset ref) | no | proven |
| ListComponentClasses | nameFilter (text) | no | proven |
| ListComponentProperties | component (asset ref) | no | proven |
| ListEntityClasses | nameFilter (text) | no | proven |
| RemoveComponent | see mcp_map.py --find | ? | no recipe |
| SetComponentProperty | component (asset ref), propertyName (text), value (text) | yes | proven |
| SetEntityTransform | entity (asset ref), transform (object) | yes | proven |

## GameplayTagsToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| FindReferencersByTag | tagName (text) | no | proven |
| GetTagInfo | tagName (text) | no | proven |
| ListTags | parentTag (text) | no | proven |
| ListTagsInSource | tagSource (text) | no | proven |

## LogsToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| GetLogCategories | see mcp_map.py --find | ? | no recipe |
| GetLogEntries | category (text), pattern (text), maxEntries (number) | no | proven |
| GetVerbosity | category (text) | no | proven |
| SetVerbosity | category (text), verbosity (text) | yes | proven |

## MVVMToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddViewModelProperty | see mcp_map.py --find | ? | no recipe |
| AddViewModelToWidget | widgetBlueprint (asset ref), viewModelClass (asset ref) | yes | proven |
| CreateViewBinding | widgetBlueprint (asset ref), sourceContext (optional), sourcePropertyPath (text), destinationContext (asset ref), destinationPropertyPath (text), conversionName (text) | yes | proven |
| CreateViewEventBinding | widgetBlueprint (asset ref), eventContext (optional), eventPropertyPath (text), destinationContext (asset ref), destinationPropertyPath (text) | yes | proven |
| FixupMVVMData | widgetBlueprint (asset ref) | yes | proven |
| GetWidgetViewConfig | widgetBlueprint (asset ref), outConfiguration (object) | no | proven |
| ListBindableWidgetProperties | widgetBlueprint (asset ref), widget (asset ref) | no | proven |
| ListConversionFunctions | widgetBlueprint (asset ref) | no | proven |
| ListViewModels | searchPath (text) | no | proven |
| ListWidgetViewBindings | widgetBlueprint (asset ref) | no | proven |
| ListWidgetViewEvents | widgetBlueprint (asset ref) | no | proven |
| ListWidgetViewModels | widgetBlueprint (asset ref) | no | proven |
| RemoveWidgetViewBinding | widgetBlueprint (asset ref), bindingId (text) | yes | proven |
| SetBindingMode | widgetBlueprint (asset ref), bindingId (text), mode (text) | yes | proven |
| SetWidgetViewConfig | widgetBlueprint (asset ref), configuration (object) | yes | proven |

## MaterialInstanceTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| clear_parameters | instance (asset ref) | yes | proven |
| create | folder_path (text), asset_name (text), parent (asset ref) | yes | proven |
| diff | old_asset_path (text), new_asset_path (text) | no | proven |
| get_scalar_parameter | instance (asset ref), name (text) | no | proven |
| get_static_switch_parameter | instance (asset ref), name (text) | no | proven |
| get_texture_parameter | instance (asset ref), name (text) | no | proven |
| get_vector_parameter | instance (asset ref), name (text) | no | proven |
| list_parameters | material (asset ref) | no | proven |
| set_parameter_override | instance (asset ref), name (text), override (true/false) | yes | proven |
| set_parent | instance (asset ref), parent (asset ref) | yes | proven |
| set_scalar_parameter | instance (asset ref), name (text), value (number) | yes | proven |
| set_static_switch_parameter | instance (asset ref), name (text), value (true/false) | yes | proven |
| set_texture_parameter | instance (asset ref), name (text), value (asset ref) | yes | proven |
| set_vector_parameter | instance (asset ref), name (text), value (object) | yes | proven |

## MaterialTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_expression | material_or_function (asset ref), expression_class (asset ref), x (number), y (number) | yes | proven |
| connect_expressions | from_expression (asset ref), from_output_name (text), to_expression (asset ref), to_input_name (text) | yes | proven |
| connect_to_output | expression (asset ref), output_name (text), material_property (text) | yes | proven |
| create_function | folder_path (text), asset_name (text) | yes | proven |
| create_material | folder_path (text), asset_name (text) | yes | proven |
| create_parameter_collection | folder_path (text), asset_name (text) | yes | proven |
| delete_expression | material_or_function (asset ref), expression (asset ref) | yes | proven |
| delete_parameter_group | material_or_function (asset ref), group_name (text) | yes | proven |
| delete_unused_expressions | material (asset ref) | yes | proven |
| diff_function | old_asset_path (text), new_asset_path (text) | no | proven |
| diff_material | old_asset_path (text), new_asset_path (text) | no | proven |
| disconnect_expressions | to_expression (asset ref), to_input_name (text) | yes | proven |
| disconnect_from_output | material (asset ref), material_property (text) | yes | proven |
| get_expression_input_names | expression (asset ref) | no | proven |
| get_expression_inputs | material_or_function (asset ref), expression (asset ref) | no | proven |
| get_expression_output_names | expression (asset ref) | no | proven |
| get_expressions | material_or_function (asset ref) | no | proven |
| get_property_input | material (asset ref), material_property (text) | no | proven |
| get_referencing_materials | material_function (asset ref) | no | proven |
| get_statistics | material (asset ref) | no | proven |
| layout_expressions | material_or_function (asset ref) | yes | proven |
| list_expression_classes | material_or_function (asset ref) | no | proven |
| list_parameter_groups | material_or_function (asset ref) | no | proven |
| recompile | material_or_function (asset ref) | yes | proven |
| rename_parameter_group | material_or_function (asset ref), old_name (text), new_name (text) | yes | proven |

## NiagaraToolset_Assets

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| FindNiagaraScripts | folderPath (text), name (text), usages (list), visibilities (list), supportedUsages (list), bRecursive (true/false), bIncludeDeprecated (true/false) | no | proven |
| GetAssetDiscoveryInfo | none | no | proven |
| GetNiagaraScriptDigest | objectPath (text) | no | proven |

## NiagaraToolset_Component

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| GetUserVariables | component (asset ref) | no | proven |
| GetVariable | component (asset ref), var (object) | no | proven |
| SetSystem | niagaraComponent (asset ref), system (asset ref), bResetExistingOverrideParameters (true/false) | yes | proven |
| SetVariable | component (asset ref), variable (object) | yes | proven |

## NiagaraToolset_Info

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| UEnum_Info | enum (asset ref) | no | proven |

## NiagaraToolset_System

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddEmitter | system (asset ref), templateEmitter (asset ref), emitterName (text) | yes | proven |
| AddModule | moduleLocationRef (object), moduleAsset (asset ref) | yes | proven |
| AddRenderer | newRendererLocation (object), rendererClass (asset ref) | yes | proven |
| AddSetParameterEntry | moduleRef (object), entry (object) | yes | proven |
| AddSetParametersModule | moduleLocationRef (object), parameters (list) | yes | proven |
| AddUserVariables | system (asset ref), variablesToAdd (list) | yes | proven |
| ApplyStackIssueFix | system (asset ref), issueId (text), fixId (text) | yes | unverified |
| CreateNiagaraSystem | assetName (text), assetPath (text), templateSystem (asset ref) | yes | proven |
| GetAvailableDynamicInputs | type (object) | no | proven |
| GetDataInterfaceSchema | dataInterfaceClass (asset ref) | no | proven |
| GetDynamicInputChain | stackInputRef (object) | no | proven |
| GetDynamicInputSchema | dynamicInputReference (object) | no | proven |
| GetDynamicInputSchemaFromAsset | dynamicInputAsset (asset ref) | no | proven |
| GetEmitterData | emitterRef (object) | no | proven |
| GetEmitterInputValues | emitterRef (object) | no | proven |
| GetEmitterSchema | none | no | proven |
| GetEmitterSummary | emitterRef (object) | no | proven |
| GetEmitterTopology | emitterRef (object) | no | proven |
| GetModuleInputValues | moduleRef (object) | no | proven |
| GetModuleSchema | moduleReference (object) | no | proven |
| GetModuleSchemaFromAsset | moduleAsset (asset ref) | no | proven |
| GetModuleTopology | moduleRef (object) | no | proven |
| GetRendererData | rendererRef (object) | no | proven |
| GetRendererSchema | rendererClass (asset ref) | no | proven |
| GetScriptStackInputValues | scriptRef (object) | no | proven |
| GetScriptStackTopology | scriptRef (object) | no | proven |
| GetStackInputData | stackInputRef (object) | no | proven |
| GetStackInputSchema | inputReference (object) | no | proven |
| GetStackInputTopology | stackInputRef (object) | no | proven |
| GetStackIssues | system (asset ref) | no | proven |
| GetSystemCompileState | system (asset ref) | no | proven |
| GetSystemData | system (asset ref) | no | proven |
| GetSystemDependencies | system (asset ref) | no | proven |
| GetSystemSchema | none | no | proven |
| GetSystemSummary | system (asset ref) | no | proven |
| GetUserVariables | system (asset ref) | no | proven |
| RemoveEmitter | emitterToRemove (object) | yes | proven |
| RemoveModule | moduleToRemove (object) | yes | proven |
| RemoveRenderer | rendererToRemove (object) | yes | proven |
| RemoveSetParameterEntry | moduleRef (object), parameterName (text) | yes | proven |
| RemoveUserVariables | system (asset ref), variablesToRemove (list) | yes | proven |
| SetEmitterData | emitter (object), emitterData (object) | yes | proven |
| SetModuleEnabled | moduleRef (object), bEnabled (true/false) | yes | proven |
| SetRendererData | renderer (object), rendererData (object) | yes | proven |
| SetStackInputData | stackInputRef (object), inputData (object) | yes | proven |
| SetSystemData | system (asset ref), systemData (object) | yes | proven |

## ObjectTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| get_class | instance (asset ref) | no | proven |
| get_properties | instance (text), properties (list) | no | proven |
| list_properties | instance (asset ref) | no | proven |
| reset_properties | instance (asset ref), properties (list) | yes | proven |
| search_subclasses | base_class (asset ref) | no | proven |
| set_properties | instance (asset ref), values (text) | yes | proven |

## PhysicsAssetToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddBody | physicsAsset (asset ref), boneName (text) | yes | proven |
| AddConstraint | physicsAsset (asset ref), bone1Name (text), bone2Name (text) | yes | proven |
| CreateFromMesh | meshPath (text), bAssignToMesh (true/false) | yes | proven |
| GetBodyMassScale | physicsAsset (asset ref), boneName (text) | no | proven |
| GetBodyNames | physicsAsset (asset ref) | no | proven |
| GetBodyPhysicsMode | physicsAsset (asset ref), boneName (text) | no | proven |
| GetBodyShapes | physicsAsset (asset ref), boneName (text) | no | proven |
| GetConstraints | physicsAsset (asset ref) | no | proven |
| RemoveBody | physicsAsset (asset ref), boneName (text) | yes | proven |
| RemoveConstraint | physicsAsset (asset ref), bone1Name (text), bone2Name (text) | yes | proven |
| RemoveShape | physicsAsset (asset ref), boneName (text), shapeName (text) | yes | proven |
| SetBodyMassScale | physicsAsset (asset ref), boneName (text), massScale (number) | yes | proven |
| SetBodyPhysicsMode | physicsAsset (asset ref), boneName (text), mode (text) | yes | proven |
| SetBox | physicsAsset (asset ref), boneName (text), shapeName (text), center (object), rotation (object), extentX (number), extentY (number), extentZ (number) | yes | proven |
| SetCapsule | physicsAsset (asset ref), boneName (text), shapeName (text), center (object), rotation (object), radius (number), length (number) | yes | proven |
| SetConstraintLimits | physicsAsset (asset ref), info (object) | yes | proven |
| SetSphere | physicsAsset (asset ref), boneName (text), shapeName (text), center (object), radius (number) | yes | proven |

## PrimitiveTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_cone | actor (asset ref), name (text), radius (number), height (number) | yes | proven |
| add_cube | actor (asset ref), name (text), dimensions (object) | yes | proven |
| add_cylinder | actor (asset ref), name (text), radius (number), height (number) | yes | proven |
| add_sphere | actor (asset ref), name (text), radius (number) | yes | proven |

## ProgrammaticToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| execute_tool_script | see mcp_map.py --find | ? | no recipe |
| get_execution_environment | none | no | proven |

## SceneTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_actors_to_data_layer | actors (list), asset_path (text) | yes | proven |
| add_to_scene_from_asset | asset_path (text), name (text), xform (object) | yes | proven |
| add_to_scene_from_class | actor_type (asset ref), name (text), xform (object) | yes | proven |
| create_data_layer_asset | asset_path (text) | yes | proven |
| create_level | see mcp_map.py --find | ? | no recipe |
| delete_folder | folder_path (text) | yes | proven |
| diff | see mcp_map.py --find | ? | no recipe |
| find_actors | collision_channels (list), name (text) | no | proven |
| get_actor_asset_path | actor (asset ref) | no | proven |
| get_actors_in_data_layer | asset_path (text) | no | proven |
| get_actors_in_folder | folder_path (text), recursive (true/false) | no | proven |
| get_collision_channels | none | no | proven |
| get_current_level | none | no | proven |
| get_data_layers | none | no | proven |
| get_folders | none | no | proven |
| is_actor_hidden | actor (asset ref) | no | proven |
| load_actors | actors (list) | yes | proven |
| load_level | see mcp_map.py --find | ? | no recipe |
| remove_actors_from_data_layer | actors (list), asset_path (text) | yes | proven |
| remove_from_scene | actor (asset ref) | yes | proven |
| rename_folder | old_path (text), new_path (text) | yes | proven |
| replace_actors_with_asset | actors (list), asset_path (text) | yes | proven |
| replace_actors_with_class | actors (list), actor_type (asset ref) | yes | proven |
| save_actor | actor (asset ref) | yes | proven |
| set_actor_folder | actor (asset ref), folder_path (text) | yes | proven |
| set_actor_hidden | actor (asset ref), hidden (true/false) | yes | proven |
| trace_world | start (object), end (object) | no | proven |
| unload_actors | actors (list) | yes | proven |

## SessionToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| GetClientLogEntries | pattern (text), maxResults (number), startLine (number) | no | unverified |
| GetGameState | none | no | proven |
| GetSessionStatus | none | no | proven |
| PushChanges | bVerseOnly (true/false) | yes | proven |
| StartGame | none | yes | proven |
| StartSession | none | yes | proven |
| StopGame | none | yes | proven |
| StopSession | none | yes | proven |

## SkeletalMeshTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| add_socket | mesh (asset ref), socket_name (text), bone_name (text) | yes | proven |
| assign_physics_asset | mesh (asset ref), physics_asset (asset ref) | yes | proven |
| get_bone_children | mesh (asset ref), bone_name (text) | no | proven |
| get_bone_names | mesh (asset ref) | no | proven |
| get_bone_parent | mesh (asset ref), bone_name (text) | no | proven |
| get_bounds | mesh (asset ref) | no | proven |
| get_lod_count | mesh (asset ref) | no | proven |
| get_material | mesh (asset ref), slot_name (text) | no | proven |
| get_material_slots | mesh (asset ref) | no | proven |
| get_morph_target_names | mesh (asset ref) | no | proven |
| get_physics_asset | mesh (asset ref) | no | proven |
| get_section_count | mesh (asset ref), lod_index (number) | no | proven |
| get_skeleton | mesh (asset ref) | no | proven |
| get_socket_bone | mesh (asset ref), socket_name (text) | no | proven |
| get_socket_names | mesh (asset ref) | no | proven |
| get_socket_transform | mesh (asset ref), socket_name (text) | no | proven |
| get_vertex_count | mesh (asset ref), lod_index (number) | no | proven |
| import_file | folder_path (text), asset_name (text), source_file (text) | yes | proven |
| remove_socket | mesh (asset ref), socket_name (text) | yes | proven |
| rename_socket | mesh (asset ref), old_name (text), new_name (text) | yes | proven |
| set_material | mesh (asset ref), slot_name (text), material (asset ref) | yes | proven |
| set_socket_transform | mesh (asset ref), socket_name (text), transform (object) | yes | proven |

## StaticMeshTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| generate_convex_collisions | mesh (asset ref), hull_count (number), max_hull_verts (number), hull_precision (number) | yes | proven |
| generate_lods | mesh (asset ref), triangle_percents (list) | yes | proven |
| get_bounds | mesh (asset ref) | no | proven |
| get_lod_count | mesh (asset ref) | no | avoid |
| get_lod_thresholds | mesh (asset ref) | no | proven |
| get_material | mesh (asset ref), slot_name (text) | no | proven |
| get_material_slots | mesh (asset ref) | no | proven |
| get_triangle_count | mesh (asset ref) | no | proven |
| get_vertex_count | mesh (asset ref) | no | proven |
| import_file | folder_path (text), asset_name (text), source_file (text), import_materials (true/false), import_textures (true/false), combine_meshes (true/false) | yes | proven |
| is_nanite_enabled | mesh (asset ref) | no | proven |
| remove_collisions | mesh (asset ref) | yes | proven |
| remove_lods | mesh (asset ref) | yes | proven |
| set_lod_thresholds | mesh (asset ref), thresholds (list) | yes | proven |
| set_material | mesh (asset ref), slot_name (text), material (asset ref) | yes | proven |
| set_nanite_enabled | mesh (asset ref), enabled (true/false) | yes | proven |

## TextureTools

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| export_png | texture (asset ref), file_path (text) | yes | proven |
| get_size | texture (asset ref) | no | proven |
| import_file | folder_path (text), asset_name (text), source_file (text) | yes | proven |
| read_texture | texture (asset ref) | no | proven |

## UMGToolSet

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddUIComponent | see mcp_map.py --find | ? | no recipe |
| AddWidget | widgetBlueprint (asset ref), widgetClass (asset ref), widgetDisplayName (text), parentWidget (optional) | yes | proven |
| CompileWidgetBlueprint | widgetBlueprint (asset ref) | yes | proven |
| CreateWidgetBlueprint | folderPath (text), assetName (text), parentClass (asset ref) | yes | proven |
| GetNamedSlots | widgetBlueprint (asset ref) | no | proven |
| GetWidgetClassInfo | widgetClass (asset ref) | no | proven |
| GetWidgetDescription | widgetBlueprint (text) | no | proven |
| GetWidgetTreeDepth | widgetBlueprint (asset ref) | no | proven |
| GetWidgets | widgetBlueprint (asset ref) | no | proven |
| ListWidgetBlueprints | folderPath (text) | no | proven |
| ListWidgetClasses | filter (text) | no | proven |
| MoveUIComponent | see mcp_map.py --find | ? | no recipe |
| MoveWidget | widgetBlueprint (asset ref), widget (asset ref), newParent (asset ref), childIndex (number) | yes | proven |
| RemoveUIComponent | see mcp_map.py --find | ? | no recipe |
| RemoveWidget | widgetBlueprint (asset ref), widget (asset ref) | yes | proven |
| RenameWidget | widgetBlueprint (asset ref), widget (asset ref), newDisplayName (text) | yes | proven |
| ReplaceWidgetWithChild | widgetBlueprint (asset ref), widgetToReplace (asset ref) | yes | proven |
| ReplaceWidgetWithNamedSlot | widgetBlueprint (asset ref), widgetToReplace (asset ref), namedSlot (text) | yes | proven |
| ReplaceWidgetWithTemplate | widgetBlueprint (asset ref), widgetToReplace (asset ref), templateClass (asset ref) | yes | proven |
| SetNamedSlotContent | widgetBlueprint (asset ref), slotName (text), widgetClass (asset ref), widgetName (text), hostWidget (optional) | yes | proven |
| WrapWidgets | widgetBlueprint (asset ref), widgets (list), wrapperClass (asset ref) | yes | proven |

## ValkyriePythonToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| EnablePythonInUEFN | none | yes | proven |
| IsPythonEnabledInUEFN | none | no | proven |

## VerseFieldsToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddVerseField | widgetBlueprint (asset ref), fieldName (text), spec (object) | yes | proven |
| BindWidgetPropertyToVerseField | widgetBlueprint (asset ref), verseFieldName (text), targetWidget (asset ref), widgetPropertyPath (text) | yes | proven |
| DuplicateVerseField | widgetBlueprint (asset ref), fieldName (text), newName (text) | yes | proven |
| EditVerseField | widgetBlueprint (asset ref), fieldName (text), spec (object), newName (text) | yes | proven |
| GetSupportedVerseFieldTypes | none | no | proven |
| ListVerseFields | widgetBlueprint (asset ref) | no | proven |
| RemoveVerseField | widgetBlueprint (asset ref), fieldName (text) | yes | proven |

## VerseToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| BuildAll | none | yes | proven |
| Copy | sourcePath (text), destPath (text), bRecursive (true/false) | yes | proven |
| CreateDirectory | path (text) | yes | proven |
| Delete | path (text), bRecursive (true/false) | yes | proven |
| Grep | pattern (text), pathGlob (text) | no | proven |
| ListFiles | path (text), bRecursive (true/false) | no | proven |
| Move | sourcePath (text), destPath (text) | yes | proven |
| ReadFile | path (text), span (object) | no | proven |
| Replace | path (text), oldString (text), newString (text) | yes | proven |
| WriteFile | path (text), content (text), bCreateIfMissing (true/false) | yes | proven |

## WidgetAnimationToolset

| Tool | Parameters | Writes | Status |
|---|---|---|---|
| AddWidgetToAnimation | widgetBlueprint (asset ref), animation (asset ref), objectToBind (asset ref) | yes | proven |
| CreateWidgetAnimation | widgetBlueprint (asset ref), animationName (text), lengthSeconds (number) | yes | proven |
| FindWidgetAnimation | widgetBlueprint (asset ref), animationName (text) | no | proven |
| GetWidgetAnimationBindings | animation (asset ref) | no | proven |
| ListWidgetAnimations | widgetBlueprint (asset ref) | no | proven |
| RemoveWidgetAnimation | widgetBlueprint (asset ref), animation (asset ref) | yes | proven |
| RemoveWidgetBinding | animation (asset ref), bindingGuid (text) | yes | proven |
| RenameWidgetAnimation | widgetBlueprint (asset ref), animation (asset ref), newName (text) | yes | proven |
| SetWidgetAnimationDisplayLabel | animation (asset ref), displayLabel (text) | yes | proven |
| SetWidgetAnimationLength | animation (asset ref), lengthSeconds (number) | yes | proven |
