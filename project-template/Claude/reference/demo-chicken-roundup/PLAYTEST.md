# Playtest checklist

Fill 'observed' while you play. A failed row becomes a regression task (T-xxx) in ROADMAP.md.

## Players (4)
- [ ] Play with 1 player alone: the round starts and ends
- [ ] Play with 4 players: everyone can join, the round starts, the shared state is correct
- [ ] A player joins a running round (if Join in progress is on) and one leaves: nothing breaks
- [ ] Island Settings in UEFN match the plan (max players, teams, respawn)

## S1 - Round up the chickens (P1)
- Expected: start a round, herd one chicken into the egg, and see the score go up by one step.
- Observed: 
- Result: ok / fail

- [ ] Given a chicken is free, when the player picks it up, then it follows the player.
- [ ] Given a herded chicken, when it enters the egg, then it counts once and the score rises.

## S2 - Two chickens at once (P2)
- Expected: herd two chickens into the egg, and see the score count two, not one.
- Observed: 
- Result: ok / fail

- [ ] Given two chickens, when both enter the egg, then each counts once.
- [ ] Given four players, when each leads one chicken into the egg, then the shared score counts four.

## Success criteria
- [ ] SC-001: a new player finishes a round in under 4 minutes without help. | observed: 
- [ ] SC-002: with all chickens in the egg, the final score equals the number of chickens times the points per chicken. | observed: 
- [ ] SC-003: the same chicken never counts twice (each spawner makes one chicken and the egg removes it once). | observed: 

