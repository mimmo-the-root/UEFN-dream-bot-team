# Variants — Survival

List of recognized variants for the Survival genre, with independent
status for each. A mature variant does NOT make the genre mature: see
`SKILL.md` for the two-tier promotion rule.

| variant slug       | description (working label)                            | status | maps analyzed |
|--------------------|-------------------------------------------------------|-------|-------------------|
| loop-100           | structured cycle loop (e.g. round/wave with a fixed count) | draft | 0 |
| loop-infinito      | continuous-loop survival with no structural ending      | draft | 0 |
| space-war-2team     | space setting, 2 opposing teams                         | draft | 0 |

## Adding a new variant

If a map doesn't clearly fit any existing variant, create
a new folder `variants/<new-slug>/` with an empty `evidence.md` and
add a row here with status `draft` and 0 maps. There's no need to pre-write
any pattern: the variant starts empty and gets populated map by map.

## Note on official Epic tags

Once `~/.claude/skills/genre/fortnite-tags-known.json` has enough real, confirmed
entries (captured via `/islands/{code}` on known islands), it should be
checked whether the Epic tags already offer a finer or different
classification than these variants — if so, the variants should be
realigned to the real tags instead of remaining purely internal labels.
