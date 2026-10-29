# Game spec: Chicken Roundup

- Status: Draft
- Mode: normal
- Genre: survival
- Players: 4
- Teams: none (everyone plays together)
- Days left:

## Ideas
### Idea 1 - Chicken Roundup
- Pitch: Herd the escaped chickens into the big egg in the pen before the round ends, up to 4 players together.
- Idea score: 72/100
- Verdict: build it
- Weak points: taming may not exist as a command in Verse; the flock needs a simple follow rule
- Iterations: 58 -> 66 -> 72
- Status: chosen

### Idea 2 - Fox Watch
- Pitch: Players guard the coop at night and scare foxes away with lanterns.
- Idea score: 61/100
- Verdict: smaller scope
- Weak points: needs enemy movement and night lighting; fewer reasons to replay
- Iterations: 61
- Status: alternative

### Idea 3 - Egg Hunt Relay
- Pitch: Teams race to carry eggs across the farm without breaking them.
- Idea score: 54/100
- Verdict: pick another
- Weak points: physics of carrying is fragile in UEFN; scope grows with every obstacle
- Iterations: 54
- Status: dropped

## Idea
A farm game for up to 4 players together: herd the wandering chickens and lead them into the big egg in the pen before time runs out.

## Loop (MVP)
- Action: the player walks up to a loose chicken, herds it and leads it into the egg.
- Rule: a chicken that enters the egg is removed by its damage volume (creatures only, never players); the round lasts 3 minutes.
- Reward: each chicken that goes into the egg gives the team 1 point and plays a short feedback sound.
- End: the round ends when time runs out or every chicken has gone into the egg.
- Replay: the final score is shown and the chickens spawn in new places, so the player tries for a better score.

## Stories
### Story 1 - Round up the chickens (P1)
The player herds chickens and leads them into the egg to score. This is the whole playable loop.
- Independent test: start a round, herd one chicken into the egg, and see the score go up by one step.
- Given a chicken is free, when the player walks up to it, then it follows the player.
- Given a herded chicken, when it enters the egg and disappears, then it counts once and the score rises.

### Story 2 - Two chickens at once (P2)
The player can lead several chickens together.
- Independent test: herd two chickens into the egg and see the score count two, not one.
- Given two chickens, when both enter the egg, then each counts once.
- Given four players, when each leads one chicken into the egg, then the shared score counts four.

## Success criteria
- SC-001: a new player finishes a round in under 4 minutes without help.
- SC-002: with all chickens in the egg, the final score equals the number of chickens times the points per chicken.
- SC-003: the same chicken never counts twice (each spawner makes one chicken and the egg removes it once).

## Assumptions
- Co-op for 4 players, no teams: everyone shares one egg and one score.
- One egg, one round length (3 minutes): the owner may change both.
- Scoring (owner decision): a big egg prop with a damage volume that affects creatures only; the elimination event of the chicken spawners gives the point. No capture area, no pen spawner.
- Points per chicken are equal for every chicken.

## Sources consulted
- second brain: no note on tame-and-deliver loops (none found).
- genre skill survival: patterns read, none about companion animals yet.
- uefn-device-gotchas: references to spawners are assigned by hand (this is risk R1).
- Epic farm example (community tutorial): build in two passes and try one sample first.

## Theme
- How the theme enters the game:

## Technical risks
| Risk | Level | Fallback or cut |
|---|---|---|
| Verse references to spawners and the pen are not assigned by MCP and need manual @editable work | high | List them for the owner and verify after he assigns them |
| Vegetation or assets not allowed in a playable island fail the session validation | medium | Read the validation errors and swap in allowed assets |
| Chickens may stop following the player at some distances | medium | Test one chicken first and tune the follow distance |

## Out of scope
- Competition between players (PvP) and a leaderboard: not needed to test the loop.
- Day and night cycle: scope.

## To clarify
- None.

## Score and approval
- Score: 72/100
- Forced: no
- Approved: yes
