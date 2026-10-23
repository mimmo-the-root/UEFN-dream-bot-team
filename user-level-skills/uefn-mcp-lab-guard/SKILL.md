---
name: uefn-mcp-lab-guard
description: UEFN MCP lab guard: path forms (GUID vs LAB_ROOT), shell, what the guard refuses. Use before any MCP tool that WRITES, or any script that sets LAB_ROOT/LAB_AGGRESSIVE.
last_reviewed: 2026-10-16
sources: [original]
---
# uefn-mcp-lab-guard

## Rules
1. Asset paths and tool arguments: ALWAYS GUID form `/<guid>/<project>/...` (here `/09e4e8d3-83f9-4ee0-9777-072ed3984380/root_ai_lab`). The editor refuses `/root_ai_lab` as an asset path (`outside this project's valid asset roots`).
2. `LAB_ROOT` (the guard's environment variable): the form depends on the guard. Read the header of `Claude/hooks/mcp_lab.py` in the project and use the documented form (after T-014: `/root_ai_lab`; wrong form = every write refused with `path outside /<guid>/root_ai_lab`). Do not confuse it with the argument form.
3. Shell: use PowerShell for anything that touches `LAB_ROOT` or paths starting with `/`. Git Bash rewrites `/09e4...` in `C:/Program Files/Git/...` and the lab does not start; if unavoidable `MSYS_NO_PATHCONV=1`.
4. Activation: `$env:LAB_AGGRESSIVE="1"; $env:LAB_ROOT=...` set by `Content`.
5. Ledger `Claude/logs/explore-ledger.jsonl`: every call has `r` = ok / rejected / refused / no_answer. Cite a recipe only from an `ok` line with the exact arguments.
6. The guard refuses: strings that start with `/` outside the lab and outside the accepted source roots (`/Script`, `/Engine`, `/Niagara`, `/Game`, `/FortniteGame`) per create/duplicate/place/add; drive paths in writes; editor quit/restart. It is blind inside `execute_tool_script` (it only sees the outer call).

## Don't
- Bypassing a refusal: report the exact message and stop.
- Using paths from another project (`root_pillars`), closing or killing a running editor (relaunch only through `uefn_session.py recover`, opt-in), writing outside the lab, exploiting B-002 (`values` as a JSON string).
- Improvising when a recipe fails: exact error and stop.

## Recipes (recipes.json, status tool-ok or proven)
- `AssetTools/find_assets` with `folder_path` and `asset_type` (filtered read in the lab).
- `AssetTools/list_folders` with a non-recursive `root_path`.
- `GetLogEntries#filter_noise`: pattern `^(?!.*LogModelContextProtocol)`.

## To try (not verified)
- Duplicates from other projects with `extra-root` (e.g. `/mech-drone`): unverified, requires `extra-root` in LAB-PROJECT.txt.

## Known editor traps (UEFN 42.20)

- A call that changes something and times out (or loses its answer) may have worked: read the editor state before any retry; never replay it blindly (duplicate devices, entities, files or sessions).
- `AssetTools/save_assets` with an empty or missing `asset_paths` saves EVERY unsaved asset: the guard refuses it; name the assets you changed (`allow_save_all: true` only on purpose).
- Safe ways to get static mesh numbers without the crashing getters: the asset-registry tag `Triangles`, `static_materials`, `get_bounding_box()`, `nanite_settings`. Try any new editor call on one asset, alone, after saving, before a loop.
- Also crash the editor: the console command `EDIT COPY` with no world context, and opening asset editors from Python (use `EditorAppToolset/OpenEditorForAsset`).
- UEFN does not tick at full speed when its window is not in front (the setting 'Use Less CPU when in Background'): a call that waits for the editor may stall; report it, do not loop.

- Never call `get_lod_count`, `get_number_verts`, `get_num_triangles`, `get_num_sections` or `agg_geom.export_text()` on a static mesh: they crash the editor.
- `ObjectTools`-style dynamic input schema: `GetDynamicInputSchema` crashed the editor once on an input that was not dynamic. Call it only on a verified dynamic input (`GetScriptStackTopology` says `bIsDynamic: true`).
- UI components: `AddUIComponent` accepts only the classes the project permits (others answer "is not permitted in this project"); ask the project before assuming a class is allowed.
- Creating an asset with an existing name opens a modal "Overwrite Existing Object" that blocks the MCP: use a new name or check first.
- A tool tagged `[experimental]` is ask-the-owner-first. A call that hangs while UEFN is in the background: report it, do not loop.
- With Revision Control disconnected `StartSession` fails (Validation failed): reconnect it first.
