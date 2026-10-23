# ADR 0001: A recipe is proven only by real work or a deliberate replay

Status: accepted (2026-10, kit 1.107)

**Context.** A recipe says how to call a UEFN MCP tool. A tool that "answered once" in an exploration is not the same as a recipe that works in real work. An early count showed 227 "proven" recipes that were only exploration rows.

**Decision.** A recipe is `proven` only when the same call form (tool, argument names, booleans; values ignored) succeeded in real work (`src: "work"`) or in a replay the owner started on purpose (`src: "replay"`, while `Claude/logs/replay.on` exists). Rows from the exploration batteries never count.

**Rejected.** Counting every answered tool as proven (the card showed numbers nobody could trust); asking agents to mark recipes by hand (it drifts).

**Consequence.** The console says "Recipes cover X of N tools (Y proven)". Multi-step notes and `avoid` entries are left out of the totals.
