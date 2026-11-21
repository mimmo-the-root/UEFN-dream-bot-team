# Changelog draft - Ibrido-0 and the local slices after it

Draft for the owner. No version bump: CHANGELOG.md is untouched and nothing here is a published release.
Last released kit version: v1.124.57. "ibrido-0" is local slices on release/ibrido-0, not published.
Sources: git log of release/ibrido-0 and the roadmap rows marked Done in the Lab roadmap copy.

## Measurement and telemetry

- runs.jsonl records the real provider and model on every run. A check fails only on new rows that say unknown; old rows stay as they are (T-022, T-072, T-073, T-074, T-075, T-076).

## Pinning and tiers

- One model is picked per work package and kept until the package ends. The pinning flag is on by default in routing.json (T-023, T-077, T-078, T-079, T-080).
- One tier table covers all 86 skills and agents: T1 small free, T2 best free, T3 paid. The router reads it (T-024, T-050, T-051, T-052).

## Budget

- The governor reads LIMIT.json and the owner's weekly_used_pct, decides plan or free, and flips routing.json with one log line per flip (T-025, T-053, T-054, T-055).

## Work packages

- The command template, validator and NOFIT parser are in the kit. A worker that cannot fit sends a NOFIT answer back to the planner (T-026, T-056, T-057, T-058).

## Router modes and safety

- Router mode paid forwards only to the plan without changing the session. GET /router/mode reads the mode and POST /router/mode sets it locally (T-059, T-060).
- The Models page and the console header have Free / Paid / Mixed controls. `cod.cmd --safe` starts Cod with the plan login while work goes through the router (T-061, T-062, T-084).
- The Lab-only permission block is opt-in with `lab-permissions: prudent` (T-085).
- Cloudflare Workers AI gets a plain string body and skips models with too small a context window. No live Cloudflare test yet (T-104).
- docs/REMOTE-CONTROL.md says which modes keep Remote Control, and a checker prints one line for the current mode (T-107).
- tools/mode_cost.py reports paid and free tokens per day and the plan share (T-108).

## Configuration, debug and console

- The debug exchange rule names the six relay and plan files that Cod and the planner use (T-086).
- kit-settings.json and tools/kit_config.py hold validated settings with defaults. Debug writers honour the flags and the agent template tells Cod to read them (T-087, T-088, T-091).
- GET /config and POST /config serve and change settings, with validation and a change log (T-089).
- The console has a problems panel, a sanitized debug-bundle export, editable config cards with source, history and undo, a server-side token ledger and weighted progress (T-093, T-094, T-098, T-105, T-106).
- task_status.py refuses In progress without --pct and accepts batched updates. The console pages are in the kit template and survive kit_sync (T-101, T-103, T-109).

## Planning and Director's Cut

- The PM queue and Auditor prototypes produce QUEUE.json and approve a replan (T-014).
- Director's Cut turns intake into release rows. The release contract, the swap rule and the parking lot rules are in place (T-028, T-035, T-067, T-068, T-069).
- Zero babysitting is merged: the DO FIRST hook, the 10-line rules file, Done only with PASS, and the HOT.md cache (T-030, T-063, T-064, T-065, T-066).

## Automation and integration

- The auto-integrator merges green branches in a temporary worktree and logs one COMMITTED line. It always removes the worktree, prunes stale ones and refuses a second run (T-110, T-116).
- The watchdog starts a non-interactive Cod run when there is idle work. The orchestrator keeps the inbox and the roadmap moving (T-111, T-112).
- Problems and closed releases add one lesson line to the second-brain hot cache (T-113).

## Providers

- The keyless probe found 0 of 21 candidates that answered, so no provider was added (T-019).
- airforce and orcarouter are in the router with free models only: names ending in `:free` and `orcarouter/free` (T-118).

## Golden set and retro

- A golden set of 20 packages runs nightly and on provider changes to catch silent degradation (T-038).
- A free retro agent proposes at most three config changes in one JSON pipeline (T-040).

## Kit checks and docs

- The kit suite was run on release/ibrido-0 and the result recorded (T-070).
- The console shows PAID/FREE route chips, a release slider, status dots and per-task tokens; the active release is listed first (git log of release/ibrido-0).
- Five pilot UEFN skills from UEFN-Ducky and tools/provider_scan.py were added (git log of release/ibrido-0).
- docs/HOW-TO-HYBRID.md is the plain-word owner page, updated here with what is shipped and what is still planned.
