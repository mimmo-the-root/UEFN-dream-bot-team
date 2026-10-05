---
description: Build or refresh the Verse map (index, component cards, symbols, wiring) so nothing has to be re-read
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/verse_map.py build` (use `python` if `py` is missing). It writes only `Claude/docs/map/`. With `check` instead of `build` it lists the files changed since the last build. Report the one-line result; do not open the generated files.
