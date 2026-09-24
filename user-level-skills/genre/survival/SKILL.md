---
genre_slug: survival
status: draft
maturity: partial
variants_mature: []
variants_draft: [loop-100, loop-infinito, space-war-2team]
last_updated: 2026-09-22
---

# Genre Skill: Survival

STATUS: draft — no variant is "mature" yet. This file is read by the
kit whenever a project has `Claude/docs/.genre = survival`.

## How this skill gets populated

This skill does NOT yet contain pre-written design patterns. Patterns
arise ONLY from analyzing real maps of this genre, variant by
variant. See `variants/<slug>/evidence.md` for observations collected
map by map.

Rule for promoting a variant from draft to mature:
- at least 3 distinct maps of the same variant with a populated evidence.md
- at least 1 pattern (reproducible + causal + actionable — not
  an isolated observation) repeated in 2+ of those maps

Only once 2+ variants are mature are their patterns compared to
see if something converges ACROSS different variants too. If it converges, it goes in
`references/evidence-shared.md`. If it doesn't converge, `evidence-shared.md` stays
empty — that's a legitimate outcome, not a failure: it means the Survival
genre is genuinely heterogeneous across its variants.

## Known variants (proposed as a prototype, to confirm/rename with real data)

See `references/variants.md`. The 3 initial variants indicated by the creator:

1. **loop-100** — loop of a hundred (e.g. a structured wave/round with a
   fixed or near-fixed number of cycles)
2. **loop-infinito** — infinite-loop survival, with no predefined structural
   ending
3. **space-war-2team** — survival in a space setting, two
   opposing teams

These names are the creator's working labels, not necessarily
matching 1:1 with the official Epic tags (see
`~/.claude/skills/genre/fortnite-tags-known.json` — closed list of ~30/40 tags, still to
be populated with real captures). Once the real tags are known, this section
should be aligned to use the same terminology where it matches.

## Dependencies (one-way, never the reverse)

This skill can read/cite:
- Device Library (second-brain) — reusable systems
- Retention skill (`fortnite-retention-gamedesign`) — general retention hooks

Device Library and Retention must NEVER contain logic specific to the
Survival genre. The dependency only ever goes in this direction.

## evidence-shared.md

Empty for now (no variant mature yet). See
`references/evidence-shared.md`.
