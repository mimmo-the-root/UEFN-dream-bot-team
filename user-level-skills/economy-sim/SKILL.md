---
name: economy-sim
description: Plans a tycoon or arena economy with numbers before building it: milestone times, generator payback, and what is never worth buying. Use when designing prices, income, upgrades or rewards.
last_reviewed: 2026-10-23
sources: [original]
---

# economy-sim

Helper: `python ~/.claude/hooks/economy_sim.py` (in your profile, pure arithmetic: no AI tokens, no editor).

## Steps
1. Write the planned numbers into `Claude/docs/economy.json`: `python ~/.claude/hooks/economy_sim.py init Claude/docs/economy.json` creates an example that never overwrites an existing file. Replace the example numbers with the game's.
2. `python ~/.claude/hooks/economy_sim.py run Claude/docs/economy.json` (add `--json` for the raw result).
3. Read the flags: a milestone that is never reached or needs more than three visits, a milestone that arrives in the first tenth of a visit (the first one may be early), a generator that is never bought.
4. Change one number at a time and run again. Put the final numbers in SPEC.md and the Verse `@editable` defaults.

## What it is and is not
The simulated player buys the best-payback generator and never clicks, dies or quits. A milestone counts when the TOTAL EARNED passes its cost. It shows the shape of the curve, not what real players do: confirm with a playtest, and say so in the report ("Verified: simulated; NOT verified: real play").
