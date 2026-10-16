# MCP area: assets (AssetTools, DataTableTools, CurveTableTools)

Date: 2026-10-15. UEFN version: 42.40 (from previous-findings.md, same editor; not re-queried). Lab `/root_ai_lab`, task T-002. 38 tools in the area, 38 tried (36 ok, 2 refused by the lab guard). Scratch scripts: `Claude/logs/_explore/a0.py`..`a9.py`.

Full toolset names: `editor_toolset.toolsets.asset.AssetTools`, `editor_toolset.toolsets.data_table.DataTableTools`, `editor_toolset.toolsets.curve_table.CurveTableTools`. Call via `call_tool {toolset_name, tool_name, arguments}`; answers `{"returnValue": ...}`. Paths use the GUID mount `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab/...` (LAB_ROOT must be that, see ui-widgets.md section 0). Asset tools take the package path (no `.Name`); DataTable/CurveTable tools take `{"refPath": "<pkg>.<Name>"}`; `diff` takes plain package strings.

## 1. What the area is for, and the tools

Find, copy, move, delete, save assets and read/write their metadata (AssetTools); create and edit DataTables (rows with typed columns) and CurveTables (rows of time/value keys) without the editor UI.

| Tool | R/W | Tried |
|---|---|---|
| Asset/find_assets | R | yes ok (folder, name, asset_type, tags filters) |
| Asset/exists | R | yes ok |
| Asset/list_folders | R | yes ok |
| Asset/get_asset_class | R | yes ok |
| Asset/get_asset_tags | R | yes ok |
| Asset/get_metadata_tags | R | yes ok |
| Asset/is_dirty | R | yes ok |
| Asset/get_dependencies | R | yes ok (empty for a fresh table) |
| Asset/get_referencers | R | yes ok (empty) |
| Asset/load_asset | W (loads) | yes ok |
| Asset/reload_asset | W (discards unsaved) | yes ok |
| Asset/save_assets | W | yes ok |
| Asset/update_metadata_tags | W | partly: set_tags ok, remove_tags rejected (3 tries) |
| Asset/create_folder | W | yes ok |
| Asset/duplicate | W | yes ok |
| Asset/move | W | yes ok |
| Asset/delete | W | yes ok (asset and folder) |
| DataTable/search_row_structs | R | yes ok (579 structs with `*`, 38 KB) |
| DataTable/create | W | yes ok |
| DataTable/get_schema | R | yes ok |
| DataTable/add_rows | W | yes ok |
| DataTable/set_rows | W | yes ok |
| DataTable/get_rows | R | yes ok |
| DataTable/list_rows | R | yes ok |
| DataTable/rename_rows | W | yes ok |
| DataTable/remove_rows | W | yes ok |
| DataTable/diff | R | yes ok |
| DataTable/import_file | W | refused by lab (disk path) |
| CurveTable/create | W | yes ok |
| CurveTable/add_row | W | yes ok |
| CurveTable/add_key | W | yes ok |
| CurveTable/set_keys | W | yes ok |
| CurveTable/get_keys | R | yes ok |
| CurveTable/list_rows | R | yes ok |
| CurveTable/rename_row | W | yes ok |
| CurveTable/remove_row | W | yes ok |
| CurveTable/diff | R | yes ok |
| CurveTable/import_file | W | refused by lab (disk path) |

## 2. Verified recipes (exact arguments; `{L}` = `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`)

All also in `recipes.json`. Each was run in this lab with an ok entry in the ledger.

R1. Folder and DataTable round trip (row write re-read equal):
1. `AssetTools/create_folder {"path":"{L}/Assets_T002"}` -> true
2. `DataTableTools/create {"folder_path":"{L}/Assets_T002","asset_name":"DT_T002","schema":{"refPath":"/Script/GameplayTags.GameplayTagTableRow"}}` -> `{refPath: "{L}/Assets_T002/DT_T002.DT_T002"}`
3. `DataTableTools/get_schema {"data_table":{"refPath":"<that refPath>"}}` -> JSON text `{"tag":{...},"devComment":{...}}`
4. `DataTableTools/add_rows {"data_table":{...},"row_names":["RowA","RowB"]}` -> null; `list_rows` -> `["RowA","RowB"]`
5. `DataTableTools/set_rows {"data_table":{...},"values":"{\"RowA\": {\"devComment\": \"hello T002\"}}"}` -> null
6. `DataTableTools/get_rows {"data_table":{...},"row_names":["RowA"]}` -> `"{\"RowA\": {\"tag\": \"None\", \"devComment\": \"hello T002\"}}"` (equal to what was written).
Choose a struct with `search_row_structs {"struct_name":"*Table*"}`; GameplayTagTableRow has two string columns, handy for tests.

R2. CurveTable round trip: `CurveTableTools/create {folder_path, asset_name:"CT_T002"}` -> refPath; `add_row {curve_table:{refPath}, row_name:"Speed", default_value:1.0}`; `set_keys {curve_table, row_name:"Speed", keys:[{"time":0,"value":0},{"time":1,"value":10},{"time":2,"value":25}]}` -> true; `get_keys {curve_table, row_name:"Speed"}` -> `[{"time":0,"value":0},{"time":1,"value":10},{"time":2,"value":25}]`. `add_key {curve_table,row_name,key:{time:5.0,value:9.0}}` -> true. `rename_row` / `remove_row` return null.

R3. Filtered asset search: `AssetTools/find_assets {"folder_path":"{L}/Assets_T002","asset_type":{"refPath":"/Script/Engine.DataTable"}}` -> list of `<pkg>.<Name>` strings. Also `recursive:false`, `name:"T002"` (substring), `tags:{"RowStructure":"/Script/GameplayTags.GameplayTagTableRow"}` (registry tags).

R4. Copy / diff / move / delete: `AssetTools/duplicate {path, new_path}` -> true; `DataTableTools/diff {old_asset_path, new_asset_path}` -> unified diff text (after `rename_rows {"RowA":"RowAA"}` it shows `-"RowA"` / `+"RowAA"`); `CurveTableTools/diff` same; `AssetTools/move {path,new_path}` -> true then `exists` old false, new true; `AssetTools/delete {path}` -> true (works on a folder with content too, then `exists` false).

R5. Save and dirty: `is_dirty {asset_path}` true after an edit; `save_assets {asset_paths:[...]}` -> true; `is_dirty` false.

R6. Metadata and registry tags: `update_metadata_tags {asset_path, set_tags:{"T002Tag":"v1","Other":"x"}}` -> null; `get_metadata_tags` -> `{"T002Tag":"v1","Other":"x"}`; `get_asset_tags` -> `{"RowStructure":"/Script/GameplayTags.GameplayTagTableRow","AssetImportData":"[]"}`; `get_asset_class` -> `"DataTable"`.

R7. Graph reads: `get_dependencies` and `get_referencers {asset_path}` -> `[]` for an unreferenced table; `load_asset` and `reload_asset` return `{refPath}`.

### Previous findings re-run (criterion E)
- `find_assets {folder_path}` alone does NOT limit to the folder -> **diversa**: with the GUID folder path `folder_path` alone DID limit to that folder (4 assets). The old result probably came from a path the editor did not resolve; still always add a filter.
- `find_assets` with `name` -> riconfermata (substring filter works).
- `is_dirty` false after `save_assets` -> riconfermata (true before).
- `save_assets {asset_paths:["/Folder/X"]}` package path -> riconfermata (true).
- `duplicate` -> riconfermata (true; false when the target exists).
- `list_folders` -> riconfermata (a root returns the project folder; unfiltered recursive ~2 MB per old note, not re-dumped).
- Unfiltered `find_assets` (~120 MB), `ListTags` (~2.8 MB): cited, not run on purpose (see traps).
- `ObjectTools/set_properties` JSON-text rule -> same convention found for `DataTableTools/set_rows.values` (JSON text string).

## 3. Traps (exact messages)

- `find_assets` with no argument returns about 120 MB (old measurement, 2026-10-15; not re-run on purpose: heavy MCP calls can hitch the editor). Always pass `folder_path` (works with the GUID mount), `name`, `asset_type` or `tags`. Filtered calls here returned 2-4 paths, under 1 KB.
- `list_folders` on a big root with `recursive` true is about 2 MB (old measurement): pass `recursive:false` or a specific subfolder.
- `search_row_structs {"struct_name":"*"}` is 579 structs, about 38 KB (fine, but prefer a name filter).
- `update_metadata_tags` with `remove_tags`: `Function "update_metadata_tags", could not convert incoming function input params Json to a UStruct. Incoming function input params Json may be incorrect or contain unsupported types.` Same with `set_tags:{}` or `set_tags:null` together with `remove_tags`. 3 tries, no way found to remove a tag (set_tags works; added tags stay).
- `find_assets {tags:{"T002Tag":"v1"}}` returns `[]` for a tag set with `update_metadata_tags` (also after the table was saved): metadata tags are not the registry tags the `tags` filter searches. Registry tags such as `RowStructure` do match.
- DataTable errors (exact): `Rows do not exist in the data table: ['Nope'].` (get_rows and set_rows on a missing row); `Rows already exist in the data table: ['RowA'].` (add_rows); `Properties not found in schema: ['bogus']` (set_rows with an unknown column).
- CurveTable: `Row "Nope" does not exist in the curve table.` (get_keys). A new CurveTable already has one empty row named `Curve`.
- `get_asset_class` on a missing asset: `Asset does not exist: <path>`; use `exists` first (returns false, no error).
- `add_rows`, `set_rows`, `rename_rows`, `remove_rows`, `add_row`, `rename_row`, `remove_row` return `null` (not true): read back to verify. `duplicate`/`move`/`delete`/`save_assets` return true/false.
- An empty gameplay-tag column reads back as the string `"None"`.
- Git Bash rewrites a leading `/` unless `MSYS_NO_PATHCONV=1`; PowerShell has no such problem.

## 4. What does not work or is forbidden

- `DataTableTools/import_file` and `CurveTableTools/import_file`: refused by the lab guard (`refused: a path on the disk outside the project`) even for a file inside the project folder, because the lab refuses any drive path in a write call. Not circumvented; the tools were not reached, so their behaviour is unknown.
- Removing a metadata tag by tool (see trap).
- Row structs are limited to the 579 listed by `search_row_structs`; Verse-created structs not tried.

## 5. Tasks for a subagent (and what to return)

1. "Find assets": given a folder and optional class, run `find_assets` with filters; return the list of `<pkg>.<Name>` plus count. Never call it without a filter.
2. "Make a data table": create `DT_<Name>` with a given row struct (find it with `search_row_structs`), add N rows, set given column values, read back with `get_rows`; return refPath, the rows read back and whether they equal what was written.
3. "Edit a curve": create or open a CurveTable, set keys on a row from a list of (time,value), read back with `get_keys`; return the keys read back.
4. "Compare two tables": `duplicate` a DataTable or CurveTable, change one row, `diff`; return the unified diff text.
5. "Clean a lab folder": `find_assets` in the folder, `delete` each asset or the folder, `exists` check; return deleted count and any false.
6. "Save and verify": edit, `is_dirty` (expect true), `save_assets`, `is_dirty` (expect false); return before/after.

## 6. Tools never tried

None skipped: all 38 were called. Not reached for real: `DataTableTools/import_file` and `CurveTableTools/import_file` (refused by the lab guard, disk path). `update_metadata_tags` remove path blocked by an argument-conversion error after 3 tries. Test assets were deleted again (`Assets_T002` folder removed, `exists` false).
