# Test plan — <release or system>  (copy to `Claude/docs/TEST-PLAN.md`)

> "Done" = verified. A failed check is never turned into PASS by approval; fix it or record it in BUGS.md.

Scope: <what is tested> · Build: <version> · Date: <YYYY-MM-DD> · Players: <1..4>

## Setup
Level / session settings, what to enable, how to reset state.

## Cases
| ID | Area | Steps | Expected | Result (PASS/FAIL/BLOCKED) | Bug id |
|---|---|---|---|---|---|

## Multiplayer checks
Join late · leave mid-round · two players hitting the same device · host migration.

## Exit criteria
- [ ] All blocking cases PASS
- [ ] No open Critical/High bug in BUGS.md
- [ ] Core loop completes with up to 3 players (Phase 0 exit)
- [ ] Owner decision recorded in STATUS.md
