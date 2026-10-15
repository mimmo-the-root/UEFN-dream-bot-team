# MCP toolsets seen on 2026-10-15 (UEFN 42.40) beyond the first contracts

Source: the first `/mcp-snapshot` on a real project: 28 toolsets, 388 tools. Names can change with UEFN updates: re-run `/mcp-snapshot` and `describe_toolset` before relying on one. Reading is always allowed in `live` mode; anything that writes, saves, builds or starts a session needs the owner's yes unless the task is exactly that change.

| Toolset | Tools | What it is for |
|---|---|---|
| `UMGToolSet` | 21 | Reading and editing widget trees (for example `GetWidgets`, `ReplaceWidgetWithTemplate`). |
| `VerseFieldsToolset` | 7 | Verse fields on widgets (`ListVerseFields`; `AddVerseField` and `DuplicateVerseField` write). |
| `MVVMToolset` | 15 | View bindings (`ListWidgetViewBindings`). |
| `WidgetAnimationToolset` | 10 | Widget animations. |
| `VerseToolset` | n/a | Verse files: listing, writing, `BuildAll`. |
| `SessionToolset` | 8 | `StartSession`, `PushChanges`, client logs. |
| `DeviceToolset` | n/a | Placing devices, setting properties, bindings (also holds the read tools in the main contract). |
| `EntityToolset` | 13 | Scene graph entities. |
| `EditorAppToolset`, `LogsToolset`, `ProgrammaticToolset` | n/a | Viewport capture, logs, batch calls. |
| Assets | n/a | Material, Niagara, Physics, DataTable, CurveTable, Texture, Mesh toolsets. |

All 12 tool names that Epic's Verse UI Kit guide mentions exist under the same names: `GetWidgets`, `ListVerseFields`, `ListWidgetViewBindings`, `get_referencers`, `list_properties`, `set_properties`, `save_assets`, `BuildAll`, `AddVerseField`, `DuplicateVerseField`, `ReplaceWidgetWithTemplate`, `AssetTools.find_assets`.

Checked by reading (first run): `GetWidgets` on a kit button returns its widget tree; `ListVerseFields` returns its fields (a button has one event, `OnButtonClicked`). Writing (Verse fields, bindings, widget replacement, compile, save) is exposed but not tried yet; when it is, record here what worked.

Write rules: pass `save_assets` only the paths you changed (an empty list saves everything, including other people's work); read property names with `list_properties` before `set_properties`.
