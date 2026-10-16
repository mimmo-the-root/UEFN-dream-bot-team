# MCP area: ui-widgets (UMGToolSet, MVVMToolset, WidgetAnimationToolset, VerseFieldsToolset)

Date: 2026-10-15. UEFN version: 42.40 (taken from previous-findings.md, same editor; not re-queried). Lab: `/root_ai_lab`, task T-001. 53 tools in the area, 53 tried.

Format notes valid for the whole area: call through `call_tool {toolset_name, tool_name, arguments}`; answers are `{"returnValue": ...}`; object references are `{"refPath": "..."}` (a plain string also works for most); the widget parts are addressed as `<blueprint refPath>:WidgetTree.<Name>`.

## 0. Lab setup trap (read first)

The editor only accepts asset paths under the project mount `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/...`. `/root_ai_lab/...` is rejected by the editor (`FolderPath "/root_ai_lab/UI_T001" is outside this project's valid asset roots (/09e4e8d3-83f9-4ee0-9777-072ed3984380/, /ArmASR/, ...`). The lab guard compares against LAB_ROOT, so LAB_ROOT must be set to the full mount path `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab` (the open level already lives under it) for the lab to allow real asset paths. With LAB_ROOT=`/root_ai_lab` the lab refuses the real path ("refused even in the laboratory, path outside /root_ai_lab"). In Git Bash a leading `/` is rewritten by MSYS: set the variables from PowerShell.

## 1. What the area is for, and the tools

Build and edit Widget Blueprints (UI screens) without opening the designer: tree, text, named slots, Verse fields, MVVM bindings, animations.
Toolset names: `UMGToolSet.UMGToolSet`, `MVVMToolset.MVVMToolset`, `WidgetAnimationToolset.WidgetAnimationToolset`, `VerseFieldsToolset.VerseFieldsToolset`.

| Tool | R/W | Tried |
|---|---|---|
| UMG/CreateWidgetBlueprint | W | yes ok |
| UMG/ListWidgetBlueprints | R | yes ok |
| UMG/ListWidgetClasses | R | yes ok (21 classes here) |
| UMG/GetWidgetClassInfo | R | yes ok |
| UMG/GetWidgets | R | yes ok |
| UMG/GetWidgetTreeDepth | R | yes ok (root only = 0) |
| UMG/GetWidgetDescription | R | yes ok (text dump, shows Text:) |
| UMG/GetNamedSlots | R | yes ok |
| UMG/AddWidget | W | yes ok |
| UMG/RenameWidget | W | yes ok |
| UMG/MoveWidget | W | yes ok |
| UMG/RemoveWidget | W | yes ok |
| UMG/WrapWidgets | W | yes ok |
| UMG/ReplaceWidgetWithTemplate | W | yes ok (this is how text widgets are created) |
| UMG/ReplaceWidgetWithChild | W | yes ok |
| UMG/ReplaceWidgetWithNamedSlot | W | yes ok (namedSlot is a plain string) |
| UMG/SetNamedSlotContent | W | yes ok (only on a child blueprint or with hostWidget) |
| UMG/CompileWidgetBlueprint | W | yes ok |
| UMG/AddUIComponent | W | yes, refused by project (3 tries) |
| UMG/MoveUIComponent | W | yes, error (no component can exist) |
| UMG/RemoveUIComponent | W | yes, error (no component can exist) |
| MVVM/ListViewModels | R | yes ok |
| MVVM/ListWidgetViewModels | R | yes ok |
| MVVM/AddViewModelToWidget | W | yes ok (returns null) |
| MVVM/AddViewModelProperty | W | yes, blocked (needs a Blueprint view model, none creatable) |
| MVVM/ListWidgetViewBindings | R | yes ok |
| MVVM/ListWidgetViewEvents | R | yes ok |
| MVVM/ListConversionFunctions | R | yes ok |
| MVVM/ListBindableWidgetProperties | R | yes ok |
| MVVM/CreateViewBinding | W | yes ok (returns binding GUID) |
| MVVM/SetBindingMode | W | yes ok |
| MVVM/RemoveWidgetViewBinding | W | yes ok |
| MVVM/CreateViewEventBinding | W | yes ok (returns event refPath; no remove tool) |
| MVVM/GetWidgetViewConfig | R | yes ok (returns only true) |
| MVVM/SetWidgetViewConfig | W | yes ok |
| MVVM/FixupMVVMData | W | yes ok (returns null) |
| Anim/CreateWidgetAnimation | W | yes ok |
| Anim/ListWidgetAnimations | R | yes ok |
| Anim/FindWidgetAnimation | R | yes ok |
| Anim/AddWidgetToAnimation | W | yes ok |
| Anim/GetWidgetAnimationBindings | R | yes ok |
| Anim/RemoveWidgetBinding | W | yes ok |
| Anim/SetWidgetAnimationLength | W | yes ok |
| Anim/SetWidgetAnimationDisplayLabel | W | yes ok |
| Anim/RenameWidgetAnimation | W | yes ok |
| Anim/RemoveWidgetAnimation | W | yes ok |
| VerseFields/GetSupportedVerseFieldTypes | R | yes ok |
| VerseFields/AddVerseField | W | yes ok |
| VerseFields/ListVerseFields | R | yes ok |
| VerseFields/EditVerseField | W | yes ok |
| VerseFields/DuplicateVerseField | W | yes ok |
| VerseFields/RemoveVerseField | W | yes ok |
| VerseFields/BindWidgetPropertyToVerseField | W | yes ok (returns binding GUID) |

Also used from other toolsets: `editor_toolset.toolsets.object.ObjectTools` (`list_properties`, `get_properties`, `set_properties`, `search_subclasses`), `editor_toolset.toolsets.asset.AssetTools` (`save_assets`, `duplicate`, `is_dirty`, `find_assets`), `editor_toolset.toolsets.programmatic.ProgrammaticToolset/execute_tool_script`.

## 2. Verified recipes (exact arguments; `{bp}` = `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/UI_T001/WBP_T001.WBP_T001`)

R1. Create a widget and its tree.
1. `UMGToolSet/CreateWidgetBlueprint {"folderPath":"/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/UI_T001","assetName":"WBP_T001","parentClass":{"refPath":"/Script/UMG.UserWidget"}}` returns `{"refPath": "<bp>"}`.
2. `AddWidget {"widgetBlueprint":{"refPath":"{bp}"},"widgetClass":{"refPath":"/Script/UMG.Overlay"},"widgetDisplayName":"Root","parentWidget":null}` (first widget becomes root; an Image as root was also accepted).
3. `AddWidget {... "widgetClass":{"refPath":"/Script/UMG.StackBox"},"widgetDisplayName":"Stack","parentWidget":{"refPath":"{bp}:WidgetTree.Root"}}`.
4. `CompileWidgetBlueprint {"widgetBlueprint":{"refPath":"{bp}"}}` returns true; then `AssetTools/save_assets {"asset_paths":["/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/UI_T001/WBP_T001"]}` returns true and `is_dirty` false.

R2. TEXT: set and read back (the T-001 criterion).
1. Add any widget (an Image) under a panel, then `ReplaceWidgetWithTemplate {"widgetBlueprint":{"refPath":"{bp}"},"widgetToReplace":{"refPath":"{bp}:WidgetTree.Img"},"templateClass":{"refPath":"/Game/Valkyrie/UMG/UEFN_TextBlock.UEFN_TextBlock_C"}}` returns `bSuccess:true` plus a long list of unmatched properties (harmless). The widget keeps its name.
2. `ObjectTools/set_properties {"instance":{"refPath":"{bp}:WidgetTree.Txt"},"values":"{\"text\":\"Ciao Lab\"}"}` returns true (`values` is a JSON TEXT string, camelCase names).
3. `ObjectTools/get_properties {"instance":"{bp}:WidgetTree.Txt","properties":["text"]}` returns `"{\"text\":\"Ciao Lab\"}"`; `GetWidgetDescription` also shows `Text:Ciao Lab`.

R3. Verse field bound to a widget property (full MVVM binding, one call).
1. `VerseFieldsToolset/AddVerseField {"widgetBlueprint":{"refPath":"{bp}"},"fieldName":"Op","spec":{"type":"float","defaultValue":"0.5"}}` returns true.
2. `BindWidgetPropertyToVerseField {"widgetBlueprint":{"refPath":"{bp}"},"verseFieldName":"Op","targetWidget":{"refPath":"{bp}:WidgetTree.Txt"},"widgetPropertyPath":"RenderOpacity"}` returns the binding GUID.
3. `MVVMToolset/ListWidgetViewBindings {"widgetBlueprint":{"refPath":"{bp}"}}` shows source memberName `Op` (SelfContext) to destination `RenderOpacity` on widget `Txt`, bindingType OneWayToDestination.

R4. General MVVM binding with explicit mode.
`MVVMToolset/CreateViewBinding {"widgetBlueprint":{"refPath":"{bp}"},"sourceContext":null,"sourcePropertyPath":"Label","destinationContext":{"refPath":"{bp}:WidgetTree.Txt"},"destinationPropertyPath":"Text","conversionName":""}` returns GUID; `SetBindingMode {"widgetBlueprint":{"refPath":"{bp}"},"bindingId":"<guid>","mode":"TwoWay"}` returns true (ListWidgetViewBindings then shows `TwoWay`); `RemoveWidgetViewBinding {widgetBlueprint, bindingId}` returns true. `sourceContext:null` = the blueprint itself (its Verse fields).

R5. Animation create, bind, read, edit, remove.
`WidgetAnimationToolset/CreateWidgetAnimation {"widgetBlueprint":{"refPath":"{bp}"},"animationName":"FadeIn","lengthSeconds":2.0}` returns `animation.refPath = {bp}:FadeIn`; `AddWidgetToAnimation {"widgetBlueprint":..., "animation":{"refPath":"{bp}:FadeIn"},"objectToBind":{"refPath":"{bp}:WidgetTree.Txt"}}` returns bindingId; `GetWidgetAnimationBindings {"animation":{"refPath":"{bp}:FadeIn"}}` lists it; `SetWidgetAnimationLength {"animation":..., "lengthSeconds":3.5}` then `ListWidgetAnimations` shows `lengthSeconds 3.500016689300537` (frame rounding); `RemoveWidgetBinding {"animation":..., "bindingGuid":"<guid>"}`; `RemoveWidgetAnimation {widgetBlueprint, animation}`.

R6. Named slot on a child blueprint.
`CreateWidgetBlueprint {... "assetName":"WBP_Child","parentClass":{"refPath":"<folder>/WBP_T001.WBP_T001_C"}}` (parent has a NamedSlot widget "Slot1"); `GetNamedSlots` on the child returns `[{"slotName":"Slot1","hostWidget":null,"contentWidget":null}]`; `SetNamedSlotContent {"widgetBlueprint":child,"slotName":"Slot1","widgetClass":{"refPath":"/Script/UMG.Overlay"},"widgetName":"InSlot","hostWidget":null}` fills it. For a widget instance inside another blueprint pass `hostWidget` = the instance refPath; then `ReplaceWidgetWithNamedSlot {"widgetBlueprint":h,"widgetToReplace":{"refPath":"<instance>"},"namedSlot":"Slot1"}` (plain string) returns true.

R7. Batch read in one call: `ProgrammaticToolset/execute_tool_script` with a script defining `run()` and calling `execute_tool("UMGToolSet.UMGToolSet.GetWidgets", json.dumps({...}))["returnValue"]` for 5 tools (UMG, Verse fields, animations, MVVM) returned one dict.

## 3. Traps (exact messages)

- Asset path: `FolderPath "/root_ai_lab/UI_T001" is outside this project's valid asset roots (/09e4e8d3-.../, /ArmASR/, ...)`. Use the GUID mount path.
- `AddWidget: 'Widget can't have children.'.` appears when the parent is not a panel (Image, text) and also when `parentWidget` is null on a non-empty tree.
- `AddWidget: WidgetClass 'TextBlock' is not permitted in this project.` and `AddWidget: 'Can't construct a widget using the passed class because it is unsupported.'.` for `UEFN_TextBlock_C`: text only through `ReplaceWidgetWithTemplate`.
- `MoveWidget` parameters are `newParent` and `childIndex` (not parent/index as in older notes; -1 appends).
- `ReplaceWidgetWithChild`: `Panel widget must have exactly one child.` (an empty panel or a panel with 2+ children fails).
- `ReplaceWidgetWithNamedSlot`: `NamedSlot must not be None.` when `namedSlot` is passed as an object; pass the slot name string.
- `SetNamedSlotContent: named slot 'Slot1' does not exist on the widget blueprint.` on the blueprint that OWNS the NamedSlot widget; it works on a child blueprint (parent class = the owner's `_C`) or with `hostWidget`. A NamedSlot widget is not reported by `GetNamedSlots` on its own blueprint (returns `[]`).
- `AddVerseField failed: Unsupported WriteAccess 'public'. Use "" to inherit Visibility, or one of "<public>", "<internal>", "<protected>", "<private>", "<scoped>".` `visibility` takes `public`; `writeAccess` takes `<public>` or "".
- `EditVerseField` needs `newName` (same name to keep); `EditVerseField failed: Field 'Score' not found for update.` / `DuplicateVerseField failed: Field 'Score' not found.` / `RemoveVerseField failed: Field 'Score2' not found.` when the field does not exist (the first AddVerseField had failed).
- `CompileWidgetBlueprint: Compilation failed. Event 'Txt.On All Font Faces Finish Loading => Self.Set Visibility()': The property path 'WBP_T001.SetVisibility' is invalid.` CreateViewEventBinding accepts a bad destination and returns an event refPath, the compile then fails, while `save_assets` still returns true. Fix: ObjectTools `set_properties {"instance":"<blueprint>:MVVMWidgetBlueprintExtension_View_0.MVVMBlueprintView_0.MVVMBlueprintViewEvent_N","values":"{\"bCompile\":false,\"bEnabled\":false}"}` then compile returns true. There is no list or remove tool for event bindings (`RemoveWidgetViewBinding` takes the GUID of property bindings; event refPath carries no GUID, `get_properties` of bindingId errors).
- `GetWidgetViewConfig` returns only `true`; the `outConfiguration` input is not echoed back (no way found to read the values).
- `RenameWidgetAnimation` resets `displayLabel` to the new name (set the label after renaming).
- `AddViewModelProperty: Parameter error: /Script/SimpleVotingOptionRuntime.VotingOptionViewModel is not valid Blueprint for property 'ViewModel'.` It needs a ViewModel Blueprint asset; none of the lab's toolsets creates one.
- `AddUIComponent: ComponentClass 'MouseHoverComponent' is not permitted in this project.` (same for SizeBoxComponent, NavigationUIComponent, LiteImageDownloadComponent); `MoveUIComponent/RemoveUIComponent: No UI components found on this widget blueprint.`
- `ListViewModels` with the lab folder as `searchPath` returned 10 engine view models (no lab ones exist) (`/Script/FortniteUI.HUDEquippedItemViewModel`, ...).
- `ListWidgetClasses` is about 5 KB with descriptions; fine. `ListWidgetBlueprints` is recursive on the folder.

## 4. What does not work or is forbidden

- Plain `TextBlock`, `UEFN_TextBlock_C` through AddWidget, UI components (all four classes tried), creating or extending view model Blueprints, removing event bindings by tool.
- Playing an animation: the area has no play tool (needs a game session; not tried here, T-006). Animation "play/read" was verified as create, bind, read, edit, remove.
- Reading back the MVVM view config values.
- Verse UI Kit widgets (`UW_Button_Basic_C`) are NOT in `ListWidgetClasses` of this lab (project has no VerseUIKit folder).

## 5. Tasks for a subagent (and what to return)

1. "Build a widget screen": create `WBP_<Name>` in a given folder with Overlay root, StackBox, N text blocks via ReplaceWidgetWithTemplate, set each text. Return the blueprint refPath, the list of `{widgetName, refPath}` and the compile result (true/false + message).
2. "Dump a widget": for a given blueprint refPath run the batch script (GetWidgets, GetWidgetDescription, ListVerseFields, ListWidgetAnimations, ListWidgetViewBindings). Return a compact tree, fields, animations, binding list.
3. "Bind a Verse field": add Verse fields (type, default) and bind each to a widget property (e.g. `Text`, `RenderOpacity`); return the GUIDs and the ListWidgetViewBindings summary (source, destination, mode).
4. "Add an animation": create an animation with length N, bind named widgets, return refPath, bindingIds and lengthSeconds read back.
5. "Fix a broken compile": read the exact `CompileWidgetBlueprint` error, disable offending event bindings with ObjectTools (bCompile/bEnabled false), recompile; return before/after messages.

## 6. Tools never tried

None: all 53 were called at least once. Blocked after real tries: AddViewModelProperty (no ViewModel Blueprint), AddUIComponent (project refuses the classes), MoveUIComponent, RemoveUIComponent (consequence).

## 7. Previous findings re-run (previous-findings.md, UI part)

- Read-only answers (ListWidgetBlueprints, ListWidgetClasses, ListViewModels, GetSupportedVerseFieldTypes): riconfermata. `ListWidgetClasses`: diversa: 21 classes, no Verse UI Kit widgets (`UW_Button_Basic_C` absent).
- Widget chain ListWidgetBlueprints -> GetWidgets/GetWidgetTreeDepth/GetWidgetDescription/ListWidgetViewBindings/ListWidgetViewModels/ListWidgetViewEvents: riconfermata (all with `{widgetBlueprint}`).
- ListBindableWidgetProperties {widgetBlueprint, widget}: riconfermata (tried on a text widget, returns property names).
- CreateWidgetBlueprint, CompileWidgetBlueprint, save_assets (package path), is_dirty, duplicate (true; false when target exists): riconfermata.
- AddWidget: "parentWidget null makes root only when tree is empty": riconfermata. "First widget must be a panel (Overlay)": diversa: an Image was accepted as root. Non-empty tree with null parent: diversa: error text is `Widget can't have children.`.
- Allowed classes: StackBox, SizeBox (via WrapWidgets), Image, NamedSlot, Overlay accepted: riconfermata; plain TextBlock refused: riconfermata; UEFN_TextBlock_C refused by AddWidget: riconfermata, and the "probably ReplaceWidgetWithTemplate" guess is now confirmed (see R2).
- MoveWidget {widget, parent, index}: diversa: the parameters are `newParent` and `childIndex`. RenameWidget, RemoveWidget: riconfermata.
- Verse fields: five fields in one script: riconfermata for bool/string/float/int/event types here (int needs `writeAccess` `<public>` or ""); spec.type list: riconfermata.
- `ObjectTools/set_properties` with a JSON text `values`, camelCase: riconfermata; object value returns false: riconfermata. `get_properties` "rejects the guessed argument shape": diversa: it works with `{"instance": ref, "properties": ["text"]}` and returns a JSON text.
- `find_assets {folder_path}` alone not limited to the folder: diversa: here it returned only the assets of the folder (5 WBP). Keep adding `name` to be safe.
- `execute_tool_script` batch with the full dotted tool name: riconfermata (5 reads in one call, also across toolsets).
