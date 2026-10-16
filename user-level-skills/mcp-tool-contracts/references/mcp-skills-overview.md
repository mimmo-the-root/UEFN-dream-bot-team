# MCP skills: overview

14 skills for the UEFN MCP toolset (Epic's `unreal-mcp`), built in the lab project from 388 mapped tools and installed with the kit.

- Cross-cutting: `uefn-mcp-lab-guard`, `uefn-validation-failure-diagnosis`, `uefn-create-use-remove-one-script`, `uefn-mcp-heavy-calls`.
- Per area: `uefn-ui-widgets`, `uefn-assets-data`, `uefn-editor-logs`, `uefn-level-devices`, `uefn-verse-build`, `uefn-session-regression`, `uefn-scripting-batch`, `uefn-materials`, `uefn-vfx-niagara`, `uefn-physics-mesh`.
- Detail per area: `areas/<area>.md`; recipes with a `status` field: `areas/recipes.json`; coverage: `areas/COVERAGE-FINAL.md`; the five MCP sub-agents are agents of the kit (`mcp-build`, `mcp-session`, `mcp-level`, `mcp-ui-assets`, `mcp-material-vfx`) and the `coder` orchestrates them.

Status of a recipe (`status` in `areas/recipes.json`):
- `tool-ok`: the tool answered ok in the lab. The exact arguments are not re-checked: read the recipe as a template.
- `proven`: an agent called the tool with the same call form (same argument names and true/false values) and it worked. This is found automatically from the ledger: `py -3 Claude/hooks/recipes_status.py --report` shows what your own work has proven and what failed; `--export out.json` writes counts only (no arguments, no paths) that you can share with the kit's community pool.
- `unverified`: not proven.
If a recipe fails, report the exact error and stop; do not improvise. The failure is logged and shows up in `mcp_lessons.py`.
