# Playtest checklist

Fill 'observed' while you play. A failed row becomes a regression task (T-xxx) in ROADMAP.md.

## S1 - Round up the chickens (P1)
- Expected: start a round, tame one chicken, deliver it, and see the score go up by one step.
- Observed: 
- Result: ok / fail

- [ ] Given a chicken is free, when the player picks it up, then it follows the player.
- [ ] Given a tamed chicken, when it enters the pen, then it counts once and the score rises.

## S2 - Two chickens at once (P2)
- Expected: tame two chickens, deliver both, and see the score count two, not one.
- Observed: 
- Result: ok / fail

- [ ] Given two tamed chickens, when both enter the pen, then each counts once.

## Success criteria
- [ ] SC-001: a new player finishes a round in under 4 minutes without help. | observed: 
- [ ] SC-002: with all chickens delivered, the final score equals the number of chickens times the points per chicken. | observed: 
- [ ] SC-003: the same chicken never counts twice (checked with two tamed and one delivered). | observed: 

