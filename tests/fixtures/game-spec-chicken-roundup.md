# Game spec: Chicken Roundup

- Status: Draft
- Mode: normal
- Genre: survival
- Days left:

## Idea
A single-player farm game: tame the wandering chickens and bring them back to the pen before time runs out.

## Loop (MVP)
- Action: the player walks to a chicken and picks it up to tame it, then it follows the player.
- Rule: a tamed chicken follows within a few metres; the round lasts 3 minutes.
- Reward: each chicken delivered to the pen adds points and plays a short feedback sound.
- End: the round ends when time runs out or every chicken is in the pen.
- Replay: the final score is shown and the chickens spawn in new places, so the player tries for a better score.

## Stories
### Story 1 - Round up the chickens (P1)
The player tames chickens and delivers them to the pen to score. This is the whole playable loop.
- Independent test: start a round, tame one chicken, deliver it, and see the score go up by one step.
- Given a chicken is free, when the player picks it up, then it follows the player.
- Given a tamed chicken, when it enters the pen, then it counts once and the score rises.

### Story 2 - Two chickens at once (P2)
The player can lead several chickens together.
- Independent test: tame two chickens, deliver both, and see the score count two, not one.
- Given two tamed chickens, when both enter the pen, then each counts once.

## Success criteria
- SC-001: a new player finishes a round in under 4 minutes without help.
- SC-002: with all chickens delivered, the final score equals the number of chickens times the points per chicken.
- SC-003: the same chicken never counts twice (checked with two tamed and one delivered).

## Assumptions
- Single player: the farm prototype of the Epic example has no teammates.
- One pen, one round length (3 minutes): the owner may change both.
- Points per chicken are equal for every chicken.

## Theme
- How the theme enters the game:

## Technical risks
| Risk | Level | Fallback or cut |
|---|---|---|
| Verse references to spawners and the pen are not assigned by MCP and need manual @editable work | high | List them for the owner and verify after he assigns them |
| Vegetation or assets not allowed in a playable island fail the session validation | medium | Read the validation errors and swap in allowed assets |
| Chickens may stop following the player at some distances | medium | Test one chicken first and tune the follow distance |

## Out of scope
- Several players and a leaderboard: not needed to test the loop.
- Day and night cycle: scope.

## To clarify
- None.

## Score and approval
- Score: 72/100
- Forced: no
- Approved: yes
