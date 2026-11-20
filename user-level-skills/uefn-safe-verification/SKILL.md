---
name: uefn-safe-verification
description: Checks a build, script or package in a disposable state so the check cannot commit, deploy or alter the owner's island. Use when a verification might write files, before a release, or when a generated script has not been trusted yet.
---

# Side-effect-free verification

## Result

A verdict backed by a read-back, and no trace in the owner's project. The check runs against a copy, a sandbox or a read-only path. If a file cannot be removed afterwards, it is parked in `_to_delete` with a timestamp and reported; nothing is force-deleted.

## When to use

- Before a publish or a handoff, when someone asks "does it really work".
- A generated script or tool will run and its writes are not yet understood.
- A check needs to create test actors, files or sessions in a live editor.
- Two different checks would otherwise reuse the same mutable state and mask each other's result.

**When not to use:** an actual playtest with real players (use `uefn-session-regression`), the real Verse compile that ships the build (use `uefn-verse-build`), or packaging a Fab product (use `fab-product`). For a single test object in the lab, the shorter `uefn-create-use-remove-one-script` flow is enough.

## Workflow

1. Write down what a pass looks like in observable terms, and what would count as a side effect.
2. List every path, actor, asset and session the check could touch. Unknown writes mean the check is not ready to run.
3. Prepare an isolated state: a copy of the files, a throwaway lab project, or a session that is explicitly discarded afterwards.
4. Run the check once. Do not stack retries on the same state, because a failure may have changed it.
5. Read back the specific result named in step 1. A quiet process is not a pass.
6. Return to the original state: restore files, remove test actors, stop the session. If removal is refused, park the item and say so.
7. Report the verdict with the evidence and the list of things left behind. A check that could not look is reported as not assessed, never as a pass.

## Errors (symptom, cause, remedy)

- **Check passed but the real island changed:** it ran against the live project. Re-run from a copy and compare the two states.
- **Test actor left in the level:** cleanup was skipped after a failure. Park or remove it before the next check, and record why it happened.
- **Two checks disagree:** they shared mutable state. Give each one its own copy and compare the read-backs.
- **Silent pass with no output:** the check never reached the assertion. Add a read-back that must produce a value.
- **Deletion refused by the editor:** a file is locked or protected. Move it to `_to_delete` with a timestamp; do not force it.
- **Baseline moved during the check:** generated files were counted. Exclude them and re-measure from the clean state.

## See also

`uefn-mcp-lab-guard`, `uefn-create-use-remove-one-script`, `uefn-session-regression`, `uefn-editor-logs`, `uefn-plan-verify`, `uefn-editor-dispatch`
