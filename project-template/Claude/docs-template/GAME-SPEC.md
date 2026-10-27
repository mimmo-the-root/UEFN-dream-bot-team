# Game spec: <GAME NAME>

<!-- Written by the /spec command, BEFORE any code. What the game is and why, never how it is built.
     The minimum is a playable loop. Checked by Claude/hooks/spec_check.py. -->

- Status: Draft
- Mode: normal
- Genre: <slug from the official genre list, or empty until confirmed>
- Days left: <number or empty>

## Idea
<one sentence>

## Loop (MVP)
- Action: <what the player does>
- Rule: <what limits or drives it>
- Reward: <what the player gets>
- End: <how a round ends>
- Replay: <why the player plays again>

## Stories
### Story 1 - <title> (P1)
<plain language: the playable loop>
- Independent test: <how this story alone is tested in game>
- Given <state>, when <action>, then <result>

## Success criteria
- SC-001: <measurable in game, e.g. a player completes a round in under 3 minutes>
- SC-002: <measurable>
- SC-003: <measurable>

## Assumptions
- <every choice the AI made instead of the owner, one per line>

## Sources consulted
- <the study before proposing: second brain, genre skill and its lessons, retention skills, feasibility skills; what each told us. "none found" is an honest answer>

## Theme
- How the theme enters the game: <empty until the contest theme is known; required in jam mode after the announcement>

## Technical risks
| Risk | Level | Fallback or cut |
|---|---|---|
| <what the API, MCP or UEFN may not do; manual steps such as @editable; asset dependencies; performance> | low / medium / high | <alternative or scope cut> |

## Out of scope
- <what is cut, and why>

## To clarify
- <[NEEDS CLARIFICATION: question] markers go here; none may be left open at approval>

## Score and approval
- Score: <NN>/100
- Forced: no
- Approved: no
