---
description: Check this project's kit health and repair common problems (versions, hooks, .verse backups, second brain path)
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder (the one that contains `Claude/`): `py -3 Claude/hooks/kit_doctor.py` (if `py` is missing use `python`). If the owner typed `--fix`, or asks for repair, add `--fix`.

Report the result in plain language, at most 6 lines: first what is fine in one line, then each PROBLEM and what the owner should do, then what was FIXED. Do not read other files, do not change anything yourself beyond what the script did, and do not paste the raw output.
