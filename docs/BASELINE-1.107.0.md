# Baseline 1.107.0 (UEFN MCP, console, recipes)

Sealed on 2026-10-16. What this version contains, what was checked, and what is still open. The next work starts from here.

## What is in it

- UEFN MCP: 388 tools in 30 toolsets mapped; 357 answered in the lab (92%); `mcp-known-tools.json` with what the lab found for each tool.
- 14 MCP skills and 5 MCP sub-agents in the kit; the `coder` can delegate UEFN work to them (one editor writer at a time).
- 246 recipes: 230 `tool-ok`, 16 `unverified`, 0 `proven` in the shipped file. `proven` grows from real work (`mcp_work_log.py` notes real calls, `recipes_status.py` counts them, the community can share counts).
- Editor recovery after a crash (opt-in), known traps of UEFN 42.20, lab guard, batteries (`mcp_cover.py`, `mcp_queue.py`), lessons report (`mcp_lessons.py`).
- Console as a solar system with token arcs, detail card, pins, queue label, chain numbers, "needs you" line and six switches. Skills page: the UEFN MCP card with recipe rings, area bars and weekly line, and a Contribute line for recipes.

## Checked

- `python tests/run_all.py`: 44 of 44 steps pass (privacy scan, skills validation, token budget, manual, console pages, MCP scripts).
- Live, in the throw-away lab project (owner, 2026-10-16): editor killed and closed on purpose, recovery refused after a normal close and after two tries in 30 minutes, relaunch worked (T-018). The work hook wrote the right lines for successful calls and, after the fix, for failed calls (T-020).
- Console in a browser with made-up data: layout, motion, switches, detail card and pins work, no script errors.
- Existing projects receive the new hooks through `/kit-update` (`kit_sync.merge_settings`, checked against the 1.106.0 settings: adds `PostToolUse` and `PostToolUseFailure` entries once, then nothing).

## Not checked yet

- The Console against the real server and real logs (restart the console server and look). The token arcs read `/agent-costs` every 90 seconds.
- The work hook in a real project during real work: after the first session look for lines with `"src": "work"` in `Claude/logs/explore-ledger.jsonl`, then run `python Claude/hooks/recipes_status.py --report`.

## Not built

- Weekly-limit gauge and forecast (Claude Code gives no local number for the weekly limit).
- Labels for what an agent passes to another on the chain; a real queue (the `⏳` label counts agents in the waiting state).
- Skills that learn from MCP errors on their own (genre packs per area, Skills-tab cards): wait for real agent rows.
- Long batteries (T-017): replay of recipes that are not `proven` (suite still to write; it must skip proven ones), soak of 100 cycles, session loop, client log with a Verse device. Optional: community evidence can replace them.

## Owner steps

1. `python tests/run_all.py`, then commit, tag `v1.107.0` and release with `publish.cmd`.
2. Work on the islands through the agents; later check the evidence (see "Not checked yet").
3. Still open from before: clean `KitTest` and temp files in `root_pillars`, check GitHub Pages, redo the other README screenshots (older than 1.107).
