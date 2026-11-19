# Director's Cut — parking lot rules

These are the rules for managing the parking lot of deferred ideas.

## Rules

1. **Freeze at 20% time left** — When 20% of the release time remains, no new tasks may enter the release.
2. **Two-sprint archive** — Ideas not picked for 2 consecutive sprints are archived (moved to LATER).
3. **Regret log** — Every rejected or deferred idea gets one line in the regret log with the reason.
4. **Reply in minutes** — The owner must answer clarification requests within minutes; silence = defer.

## Verification

- `python tools/check_rules2.py` exits 0.