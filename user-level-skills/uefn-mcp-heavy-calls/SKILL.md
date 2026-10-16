---
name: uefn-mcp-heavy-calls
description: Cost limits of UEFN MCP reads: which calls return huge payloads and how to filter them. Use before any potentially large read.
last_reviewed: 2026-10-16
sources: [original]
---
# uefn-mcp-heavy-calls

## Measured costs
| Call | Payload | Rule |
|---|---|---|
| `find_assets` without filters | ~120 MB | NEVER |
| `find_assets` StaticMesh/NiagaraSystem without filters | ~1.7 MB | always `folder_path` + `asset_type` |
| recursive `list_folders` on the root | ~2 MB | non-recursive, narrow `root_path` |
| `GetLogEntries maxEntries 0` | ~2.4 MB | always `pattern` |
| `ObjectTools/list_properties` on a mesh component | ~55 KB | `get_properties` with one name |
| `GetLogCategories` | ~125 KB | avoid |
| `GetEmitterTopology` | ~56 KB | only if needed |

## Filters
Always `folder_path`, `name`, `asset_type`, `pattern`. Paths in GUID form `/<guid>/<project>/...`.

## Verified recipes
- `AssetTools/find_assets {"folder_path":"{lab_mount}/X","asset_type":{"refPath":"/Script/Engine.DataTable"},"recursive":true}`.
- `AssetTools/list_folders {"root_path":"{lab_mount}/X","recursive":false}`.
- `GetLogEntries#filter_noise`, `GetLogEntries#why_startsession_failed`.
- `execute_tool_script#batch_reads` to group small reads.

## Don't
A deliberately unfiltered `find_assets`; calling `NiagaraToolset_System/GetDynamicInputSchema` on a non-Dynamic input (suspected crash, editor left closed, T-009): only on inputs in Dynamic mode; bypassing a guard refusal. If a call fails: exact error and stop.

## To try (not verified)
`GetDynamicInputSchema` on Dynamic inputs: no response obtained, not verified.
