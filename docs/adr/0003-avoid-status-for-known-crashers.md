# ADR 0003: A known crasher is documented as `avoid` and never replayed

Status: accepted (2026-10, kit 1.107.3)

**Context.** `StaticMeshTools/get_lod_count` crashes the editor. It had a recipe, so it showed up as "not verified" and invited a replay.

**Decision.** A recipe can have the status `avoid`: documented with the reason and a safe alternative, never replayed, left out of the totals. A test fails if a skill, agent or command names an `avoid` tool.

**Rejected.** Deleting the recipe (the trap would be forgotten and met again); leaving it `unverified` (it keeps asking for a replay).
