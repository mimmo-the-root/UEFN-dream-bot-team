---
name: game-ai-uefn
description: Rules for enemies and creatures in a UEFN map: which spawner to use, how many, how they find and chase the player, how their pressure scales, and how to keep the map fast. Use when the owner says enemy AI, guards, creatures, wildlife, NPC behavior, patrol, chase, aggro, spawn count, difficulty of enemies or enemies do not move.
kind: discipline
last_reviewed: 2026-10-30
sources: [original]
---

# Enemies and creatures in UEFN

Let the stock spawners and behaviors do the moving and fighting. Verse decides when they appear, how many, and what their death means.

## When to use
- Choosing between a guard spawner, a wildlife or creature spawner and a custom NPC behavior.
- Tuning how hard enemies are, or fixing enemies that stand still, spread out or lag the map.

**When not to use:** wave scripts and money (use the `wave director` and `currency and shop` recipes in the `mechanics` skill), conversations with NPCs (use `llm-npc-conversations`), device placement rules (use `uefn-level-devices`).

## Workflow
1. Define the role of each enemy: pressure (comes at you), area (holds a place), target (is hunted). One role each.
2. Pick the spawner that already behaves that way, set the type and count in the Details panel, read it back.
3. Keep counts low and spread by zone, so only a few enemies are active near the player at any time.
4. Subscribe to the spawner's events for spawn and elimination, and let the Verse score or advance from them.
5. Test the paths: enemies need open floor, no blocked corridors, and a way back to their post.
6. Tune pressure with three numbers together: enemy health, damage and count.

## Rules (symptom, cause, remedy)
- Wrong creature: the default type is not the one the design needs (it can be a hostile animal). Read and set the type every time.
- Standing still: the enemy has no reason or route to move. Check the spawn area is walkable and a target exists.
- Lag: too many active at once. Lower the count, raise the spacing, disable far spawners until needed.
- No readable threat: players cannot tell what will attack. Give each type a distinct look and sound.
- Counted twice or never: score taken from several events. Use one event for each enemy and count it once.
- Flat difficulty: only the count rises. Change one other thing each few waves (speed, armor, a new role).

Role table: `references/roles-and-pressure.md`.
