# Read-only UEFN MCP tools proven on UEFN 42.40 (deep test, 2026-10-15)

All called through `call_tool` with `toolset_name`, `tool_name` (short name) and `arguments`. Answers come as text JSON: `{"returnValue": ...}`. Errors come as `isError` text. Facts below are from a real run; nothing is guessed.

## Answer straight away, no arguments needed

| Toolset | Tools |
|---|---|
| EditorToolset.EditorAppToolset | GetActiveEditorModes, GetCameraTransform, GetContentBrowserPath, GetSelectedActors, GetSelectedAssets, GetSelectedOutlinerFolders, GetVisibleActors, ListCollections, ListEditorModes, ListShowFlags, SearchCVars |
| EditorToolset.LogsToolset | GetLogCategories |
| UMGToolSet.UMGToolSet | ListWidgetBlueprints, ListWidgetClasses |
| MVVMToolset.MVVMToolset | ListViewModels |
| ValkyrieToolset.EntityToolset | FindEntities, ListComponentClasses, ListEntityClasses |
| ValkyrieToolset.DeviceToolset | ListDeviceAssets |
| ValkyrieToolset.SessionToolset | GetGameState ("Unconnected" when no play session), GetSessionStatus ("Disconnected") |
| VerseFieldsToolset.VerseFieldsToolset | GetSupportedVerseFieldTypes |
| editor_toolset.toolsets.scene.SceneTools | find_actors, get_current_level, get_folders, get_data_layers, get_collision_channels |
| editor_toolset.toolsets.asset.AssetTools | find_assets, is_dirty, list_folders |

## Too big to call without a filter

`find_assets` (about 120 MB with no filter), `GetLogCategories` (about 125 KB), `ListEntityClasses` (about 250 KB), `ListDeviceAssets` (about 80 KB), `ListTags` (about 2.8 MB), `list_folders` (about 2 MB). Always pass a filter or a folder. Epic's page warns that heavy MCP calls can make the editor hitch or hang.

## Need a real object, not a made-up one

About 130 read tools answered "None is not valid value for property ..." to made-up arguments. They are alive and need a real reference (a widget blueprint, an actor, a material, a mesh). Get the reference first from a listing tool, then pass its `refPath`. Examples: `ListWidgetBlueprints` then `GetWidgets`; `GetSelectedActors` then `get_actor_bounds`.

## Known from Epic's page (https://dev.epicgames.com/documentation/fortnite/uefn-mcp)

- Python toolsets use plain XYZ, not UEFN's Left-Up-Forward. Convert carefully when mixing with Verse positions.
- The server starts and stops only when the editor is closed and reopened. The port is changed in Editor Preferences (Server Port Number).
- Verse file operations are sandboxed to the creator's project.

## Chains that worked on a real run (2026-10-15)

Object references are passed as a plain path string (`"widgetBlueprint": "/Project/Widgets/UW_X.UW_X"`), no `{"refPath": ...}` needed. Lists return `{"refPath": ...}` items: reuse that path.

- Widgets: `GetContentBrowserPath` (folder) then `ListWidgetBlueprints {folderPath}` (recursive, needs the folder) then `GetWidgets`, `GetWidgetTreeDepth`, `GetWidgetDescription`, `ListWidgetViewBindings`, `ListWidgetViewModels`, `ListWidgetViewEvents` with `{widgetBlueprint}`. `GetWidgets` returns `info` (widgetCount, rootWidgetClass) and `widgets[]` (widget, parent, slot, widgetName, bIsVariable, uIComponents).
- One named widget: `ListBindableWidgetProperties {widgetBlueprint, widget}` where `widget` is the `{"refPath": ...}` object taken from a `GetWidgets` item.
- Actors: `GetSelectedActors` then `get_actor_bounds {actor}`. `get_component_actor` wants a component, not an actor. There is no `get_actor_label`.

## Batch several calls in one: ProgrammaticToolset

`call_tool` with `toolset_name` `editor_toolset.toolsets.programmatic.ProgrammaticToolset`, `tool_name` `execute_tool_script`, `arguments {"script": "<python>"}`. The script defines `run()` returning a dict and calls tools with `execute_tool("<Toolset>.<Tool>", json.dumps(args))["returnValue"]` (full dotted name). Allowed imports: json, math, datetime, copy, re, time. `get_execution_environment` returns these instructions. Proven: one script did content-browser path, blueprint list, tree depth and widget count (4 reads) in a single call. Use it for any sequence of 3 or more calls: fewer round trips, less editor load. Output schemas are not in the tool list: read the reply of each tool once before parsing it in a script.

## Writes proven on UEFN 42.40 (test widget in its own folder, 2026-10-15)

All through `call_tool`. Reference parameters take `{"refPath": "..."}`.

- `UMGToolSet/CreateWidgetBlueprint {folderPath, assetName, parentClass {refPath: "/Script/UMG.UserWidget"}}` creates the asset (the file appears on disk at once; the folder is created too).
- `UMGToolSet/AddWidget {widgetBlueprint, widgetClass, widgetDisplayName, parentWidget}`: `parentWidget` is optional but MUST be passed explicitly: `null` makes the new widget the root (only when the tree is empty), otherwise the call fails. The first widget must be a panel (Overlay worked). Returns the widget's `refPath` (`<blueprint>:WidgetTree.<name>`).
- `CompileWidgetBlueprint {widgetBlueprint}` returns true. `AssetTools/save_assets {asset_paths: ["/Folder/WBP_X"]}` (package path, no `.Name` suffix) returns true; `is_dirty` turns false.
- `AssetTools/duplicate {path, new_path}` returns true; the copy compiles.
- `ProgrammaticToolset/execute_tool_script` can write too: one script added a widget and read the count back.
- Not every widget class is allowed. This project listed (`ListWidgetClasses`): CanvasPanel, GridPanel, Image, NamedSlot, Overlay, SafeZone, ScaleBox, ScrollBox, SizeBox, StackBox, UniformGridPanel, WidgetSwitcher, WrapBox, plus Epic's `UEFN_TextBlock_C`, `UEFN_Slider_C` and the Verse UI Kit widgets (`UW_Button_Basic_C`, ...). Proven with `AddWidget` (explicit `parentWidget`): StackBox, SizeBox, ScaleBox, Image inside SizeBox, and the Verse UI Kit button `/root_pillars/VerseUIKit/Widgets/Buttons/BasicButton/UW_Button_Basic.UW_Button_Basic_C`. Refused: plain `TextBlock` ("not permitted in this project") and `UEFN_TextBlock_C` ("unsupported class") through `AddWidget`; text is probably placed through a template (`ReplaceWidgetWithTemplate`, as Epic's guide says): not tested yet.
- Also proven: `MoveWidget {widgetBlueprint, widget, parent, index}`, `RenameWidget {widgetBlueprint, widget, newDisplayName}`, `RemoveWidget {widgetBlueprint, widget}` (true), all on a test widget; five Verse fields on one widget in one script (bool, int, string, event) all returned true and `ListVerseFields` shows them.
- `ObjectTools/set_properties {instance, values}`: `values` is a JSON TEXT string, not an object, and property names are camelCase as `list_properties` prints them (`toolTipText`). An object value is accepted but returns false.
- `VerseFieldsToolset/AddVerseField {widgetBlueprint, fieldName, spec {type, eventParameterTypes, defaultValue, visibility, writeAccess, bIsVar}}`: `spec.type` must be one of bool, int, float, string, message, color, color_alpha, texture, material, event.
- `AssetTools/find_assets {folder_path}` alone does NOT limit the answer to the folder (it returned engine paths): always add `name`.
- `ObjectTools/set_properties` with the JSON text form returned true. `get_properties` rejects the guessed argument shape (not solved; use `list_properties` to read).
- `AssetTools/duplicate` returns false when the target already exists.

## When the editor's MCP stops answering (lab, 2026-10-15)

- `SessionToolset/StartSession` came back `Failed: Validation failed` and from then on every MCP call timed out (90 s) and later refused the connection, while the editor process and port 8000 looked fine. The cause was UEFN's **Revision Control** having disconnected. Reconnecting it was enough: no editor restart. Check Revision Control first, before restarting anything or blaming the project.
- An agent that sees this must stop, say so, and ask the owner to look at the UEFN window (dialogs, Revision Control, a leftover play client). It must not retry in a loop, and it never closes or kills a running editor. Only after a crash (no editor process, crash evidence) and only with the owner's opt-in (`auto-recover: yes` in Claude/LAB-PROJECT.txt), `python Claude/hooks/uefn_session.py recover` may start it again (max 2 attempts in 30 min).
