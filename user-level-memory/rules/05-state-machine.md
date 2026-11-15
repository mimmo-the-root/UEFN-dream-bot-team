<!-- Full text of base rule 5. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 5. State machine as the primary pattern

For **new** projects, logic with multiple phases (e.g. lobby → round → end-of-match, or a
device's/character's states) should be structured as a state machine from the start, not with
scattered boolean flags. For **existing** projects that don't already use one, this isn't an
immediate rewrite requirement: `project-bootstrap` flags it in SPEC.md as a possible evolution
when the current flag-based logic is already hard to follow or shows bugs tied to inconsistent
states; `coder` proposes it as a targeted refactor when a new feature would require it, instead
of stacking more flags onto the existing logic.
