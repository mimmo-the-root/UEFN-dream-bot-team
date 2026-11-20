---
name: uefn-private-publish
description: Uploads a private build of an island, captures the private code and verifies it in a Fortnite client before calling the build publishable. Use when the owner asks for a private version, a playtest package, or a pre-release check with a code.
---

# Private island build handoff

## Result

A private version exists, its access code is recorded somewhere the owner can find it, and at least one client has joined it successfully. Nothing is public, no Store listing is touched, and no version number in the kit changes.

## When to use

- The owner wants reviewers or testers on a build that is not public yet.
- A fix must be checked on a real client rather than in the editor.
- A release checklist asks for proof that a private build was uploaded and played.

**When not to use:** a public or Fab listing (use `fab-product`), a new engine version migration (use `uefn-version-upgrade`), a compile-only check (use `uefn-verse-build`), or a local editor smoke test (use `uefn-session-regression`).

## Workflow

1. Confirm the project is the intended island and that the working Verse build is clean. Do not upload from a dirty or switched project.
2. Save the current state and note the task id and change list that this private build represents.
3. Run the editor's Upload Private Version command. Wait for the operation to finish instead of assuming the button click was enough.
4. Read every dialog that appears. Dismiss only the dialogs whose meaning is understood; if a size or memory calculation step is requested, run it and read its result.
5. Copy the private code from the confirmation screen and write it into the project's status document. Never leave it only in a chat message.
6. Join the private version from a Fortnite client with that code. Confirm the expected map loads and the tested change is present.
7. If the build is for a multiplayer change, join with a second client or record clearly that a manual multiplayer test is still outstanding.
8. Report the code, the verification result and any manual steps left to the owner. Stop there; publishing publicly is a separate decision.

## Errors (symptom, cause, remedy)

- **Upload never completes:** the editor is still busy or a modal is hidden behind another window. Check window state and the editor log before retrying.
- **No code shown:** the confirmation step was dismissed too early. Repeat the upload only after confirming that no private version was already created.
- **Code loads an old build:** the project was not saved or the upload used a previous state. Recompile, save and upload again, then label the code with its change list.
- **Memory calculation dialog blocks the flow:** a size check is required before publishing. Run it and read the outcome; do not click through blindly.
- **Client joins but the fix is missing:** the verified build was not the one uploaded. Compare the change list recorded at upload with the current one.
- **Code shared in chat only:** the owner loses it after the session. Store it in the project status document at step 5.

## See also

`fab-product`, `uefn-version-upgrade`, `uefn-session-regression`, `uefn-profiling`, `uefn-editor-logs`, `uefn-plan-verify`
