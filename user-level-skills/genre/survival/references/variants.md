# Variants — Survival

List of recognized variants for the Survival genre, with independent
status for each. Confidence is tracked per pattern (hypothesis / confirmed / proven / contested), see `SKILL.md`.

| variant slug       | description (working label)                            | status |
|--------------------|-------------------------------------------------------|-------|
| loop-100           | structured cycle loop (e.g. round/wave with a fixed count) | draft |
| loop-infinito      | continuous-loop survival with no structural ending      | draft |
| space-war-2team     | space setting, 2 opposing teams                         | draft |

## Adding a new variant

If a map doesn't clearly fit any existing variant, add a row here and use its slug in the `variant` field of new lessons. There's no need to pre-write
any pattern: the variant starts empty and gets populated map by map (map names and notes stay in the private `local/` layer).

## Note on official Epic tags

Once `~/.claude/skills/genre/fortnite-tags-known.json` has enough real, confirmed
entries (captured via `/islands/{code}` on known islands), it should be
checked whether the Epic tags already offer a finer or different
classification than these variants — if so, the variants should be
realigned to the real tags instead of remaining purely internal labels.
