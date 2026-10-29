---
name: level-design-uefn
description: Lays out a UEFN map so it plays well: blockout first, sizes taken from the player, a pace of tension and rest, gates that teach before they test, and no dead ends. Use when the owner says level design, layout, blockout, whitebox, pacing, flow, critical path, arena size, spawn area or soft-lock.
kind: discipline
last_reviewed: 2026-10-30
sources: [original]
---

# Level design in UEFN

Build the shape of the play first with plain pieces, then dress it. Every size comes from what the player can do, not from what looks good in the editor.

## When to use
- Starting the layout of a new map or a new section.
- Players get lost, get stuck, meet the end too soon or too late, or a fight area feels too big or too small.

**When not to use:** placing devices and their folders (use `uefn-level-devices`), asset and memory cost (use `performance-uefn-checklist`), the scenery recipe of the demo (`SCENERY.md`).

## Workflow
1. Blockout: plain shapes for floor, walls and the one thing the section is about. Play it before anything else is placed.
2. Measure: walk and jump the longest distances in the editor with a test player and write the numbers down. Build everything from those numbers.
3. Pace: alternate tension (fight, jump, puzzle) and rest (loot, view, story). Mark each section T or R and avoid three T in a row.
4. Gate: every new thing is shown safely first, then used alone, then combined.
5. Path: from spawn to goal there is one path the player can always find (light, color, line of sight), and no dead end without a way back.
6. Dress: add detail last, from the center of attention outward.

## Rules (symptom, cause, remedy)
- Dressing before playing: the layout is beautiful and boring. Blockout and play first.
- Sizes by eye: gaps and rooms feel wrong. Measure with the real character.
- Flat pace: all sections have the same intensity. Insert rests and one peak.
- Unlearned test: the first obstacle already needs a skill the player never used. Teach it in a safe place.
- Soft-lock: a required item or door can end up unreachable. Make requirements re-obtainable or give a reset.
- Lost player: nothing points to the next goal. Add a clear landmark or a line on screen.
- Support devices in the field: timers, managers and signs sit in the play area. Keep them on a stand outside it.

Metrics and a section checklist: `references/metrics-and-pacing.md`.
