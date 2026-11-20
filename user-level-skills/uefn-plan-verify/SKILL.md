---
name: uefn-plan-verify
description: Breaks island work into small tasks with a written Done.when check, then runs Diagnose, Fix and Verify so a task closes only after evidence exists. Use when a task is vague, a fix keeps returning, or someone wants to mark work Done before it is checked.
---

# UEFN plan to verified result

## Result

Every task ends with a check that can be observed: a clean Verse build, a device binding read back from the editor, a log line from a real session, or a document that contains the required text. A task is not Done when the code looks plausible. The loop is Diagnose, Fix, Verify, and the verifier is not the person or agent who wrote the fix.

## When to use

- A task covers more than one phase, such as build the device, wire it, then test it.
- The same bug has come back after a previous "fix".
- A reviewer cannot tell what would prove the task finished.
- A session is about to be called green on a single solo playtest.

**When not to use:** a one-line spelling or property fix with an obvious visible result; pure conversation or a question about the kit; a public release package (use `fab-product`). For multiplayer gameplay, add the missing player-count checks before closing any task.

## Workflow

1. Read the task row and the current state document. If no task exists, stop and ask for one instead of starting work.
2. Diagnose first: collect the exact error, the device or file involved, and the smallest reproduction. Do not choose a fix yet.
3. Split the task until each leaf can be finished in one pass and has one owner. A leaf that says "make it work" is not a leaf.
4. Write the Done.when sentence before editing: what tool will show what value, in which state, with how many players.
5. Apply the smallest change that addresses the diagnosed cause. Leave unrelated systems alone.
6. Verify with a tool that was not used to write the change: build, read-back, session log or screenshot. Record the result next to the task id.
7. Send the evidence to an independent reviewer. The implementer never closes their own task.
8. If verification fails, return to step 2 with the new error. After five attempts on the same error, stop and record it rather than guessing again.

## Errors (symptom, cause, remedy)

- **Task marked Done but nothing proves it:** no Done.when was written. Add the check and reopen the task.
- **Verifier repeats the implementer's reasoning:** both used the same tool and the same assumption. Verify from a different source, such as editor log or live session.
- **Fix works for one player only:** the check omitted replication and late join. Add the multiplayer cases to Done.when.
- **Leaf is too large to review:** several systems were bundled. Split by owner and by observable result.
- **Build passes but device is unwired:** the check stopped at compilation. Read back the binding after the build.
- **Same error returns after several cycles:** the cause was never identified. Stop, write the symptoms and evidence, and ask.

## See also

`uefn-verse-build`, `uefn-session-regression`, `uefn-editor-logs`, `uefn-editor-dispatch`, `uefn-lessons`, `mcp-tool-contracts`
