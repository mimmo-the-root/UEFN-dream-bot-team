---
description: Run all the Fab checks on this product, then propose a fix for every problem and apply the ones the owner picks
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), AskUserQuestion
---

This is a Fab product (a UEFN project registered as Fab). Find its root: the folder that contains the `.uefnproject` file (the current folder or its parent). Run from `~/.claude/hooks` (use `py -3`, or `python` if `py` is missing), one after the other:

1. `fab_pack.py check "<root>"` (Epic's upload rules)
2. `fab_assets.py "<root>"` (imports and names from other projects, Windows user names in paths)
3. `fab_checklist.py "<root>"` (listing checklist)

**Step 1 - report** in plain language, at most 8 lines: what is OK in one line, then each problem.

The check also verifies the DOCUMENTS for publication (README.md, AUTHOR.md, listing.md, third_party.md): a TODO left in any of them, a README that points to a SETTINGS.md that does not exist, a third_party.md that says "nothing detected" while the textures come from other authors. All of these are problems to fix, not notes.

**Step 2 - propose the fix of EVERY problem, do not stop at the report.** For each problem write the concrete fix and classify it:
- *Safe, you can do it now*: TODO fields in the documents (run `fab_pack.py listing-fill "<root>"`: it fills Technical details, the README parts the product answers by itself, and refreshes third_party.md with the authors found; then write what is left, the README paragraph, Usage, Known limits, the listing title, descriptions and tags, yourself from what the product really contains, never invent features; no TODO may remain), `third_party.md` rows (`docs` and `fab_assets.py` list the authors found in the texture source paths: each needs a row, licence is the owner's), missing Documentation/ or FabListing/ files (`fab_pack.py docs "<root>"` dry run, then `--apply`), a forbidden folder or file inside Content (`Claude/`, `CLAUDE.md`, `Saved`, `Intermediate`): MOVE it next to the project (never delete), generated texts of the listing, tags replaced with the portal's list (`fab_checklist.py tags`).
- *Needs UEFN closed* (texture/asset paths that the check could not clean because the editor holds the files): do NOT stop. Ask the owner once, inside the same question, "Close UEFN, clean and reopen". If yes run `python "~/.claude/hooks/fab_clean_cycle.py" "<root>" --apply` with a 600 s timeout (it closes UEFN politely like the X button, cleans with a backup outside the project, reopens the project, waits until it is open and runs the check). If it says UEFN did not close (it asks to save), tell the owner to save, then run it again; use `--force` only if the owner agrees to lose unsaved work. Its own check output is the final result: report it.
- *Needs the editor*: renaming or moving an asset (AssetTools/move through the UEFN MCP, one at a time, only with the editor open), assets imported from another project, names too long or vague. Say which asset and the proposed new name.
- *Needs the owner*: screenshots, price, licence of third-party content, anything creative.

Then ask ONE AskUserQuestion (multiSelect) listing the fixes ("Apply all safe ones" first, then each other fix), and apply only what the owner picks. After applying, run the check again and report what is left in at most 4 lines. Never run `zip` unless `$ARGUMENTS` says `zip` and the check is clean.
