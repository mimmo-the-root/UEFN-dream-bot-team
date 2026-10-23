---
description: What the agents changed in the open editor, session by session, and a plan to undo the newest session
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/editor_changes.py list` (use `python` if `py` is missing). With the argument `undo-plan` run `editor_changes.py undo-plan` instead. Report the result in at most 5 lines. The script never changes the editor. For the undo plan: say how many steps are deletions of created things and how many are "manual" (the editor's own Undo or a restore point), and do NOT run any step yourself unless the owner says yes to each deletion and the laboratory rules allow it.
