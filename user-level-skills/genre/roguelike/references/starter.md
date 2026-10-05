# Starter skeleton - Roguelike (structure only, no invented content)

Use when the owner starts a NEW project of this genre. This file gives the questions and the sections to fill; it contains no rules from general knowledge. Answers come from: approved patterns of this skill (SKILL.md), Epic template facts (`template-reader`), the owner's maps (Verse map), and the owner's decisions. Anything not backed by one of these stays "open question".

For each section produce a short `Claude/docs/DESIGN-<system>.md` (template in `docs-template`) and a line in `DEPENDENCY-MAP.md`. Do not write code before the owner approves the design.

1. **Run loop** - What is one run, how does it start, end (win, death, timeout) and restart? What is shared between players in a run?
2. **Architecture** - Which Verse files/classes own: run state, round transitions, player state, spawning, rewards? One owner per transition. Which level devices exist, who wires them?
3. **Devices checklist** - Spawners, trackers, modifiers, UI devices: which are global and which per player? (`mcp-tool-contracts`: read them in the level when the MCP is `live`; otherwise list them as not inspected.)
4. **Progression** - What persists between runs, what resets? Unlocks, currencies, difficulty scaling. Numbers only from the owner or from his maps' data.
5. **Strategies around death and progress** - Retry rules, paid retry or continue, rewards, boosts. These are design strategies, learned as patterns with a variant; list the options the owner is considering and mark each hypothesis until his maps back it.
6. **Persistence** - What is stored per player, what happens when data is not loaded yet or the player left (`uefn-lessons`).
7. **Performance** - Item/NPC pools, listeners, per-frame work (`performance-uefn-checklist`).
8. **Launch checklist** - First 10 minutes of a new player, a full run, a death, a restart, two players at once, a player leaving mid-run.

Sections 5 and 8 are where the owner's learned patterns matter most: read the SKILL.md list first and apply by tier (proven = rule, hypothesis = suggestion).
