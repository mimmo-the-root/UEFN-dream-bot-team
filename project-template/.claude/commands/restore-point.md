---
description: Restore points for Verse code and docs: create one, see what changed since, or undo
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/safety_net.py <action>` (use `python` if `py` is missing). Actions: `snapshot`, `changes`, `list`, `restore <id>`. With no argument from the owner, run `changes`.

Report in at most 4 lines, in plain language. For `restore`, run it WITHOUT `--apply` first, show what would change, and add `--apply` only after the owner says yes. Never delete files.
