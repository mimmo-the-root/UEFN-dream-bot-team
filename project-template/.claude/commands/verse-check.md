---
description: Ask the open UEFN to build the Verse project and report clean / errors / not analyzed
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/verse_check.py` (use `python` if `py` is missing). It needs UEFN open with this project loaded. It prints one JSON line with `state` = `clean`, `errors` or `not_analyzed`. Report that state in one line; for `errors` quote the file, line and message from `message`. Never say the code compiles unless the state is `clean`.

First run `py -3 Claude/hooks/verse_static.py` (static check, no editor needed): fix every ERROR it prints before you ask the editor to build. A clean static check is not a build: only the state `clean` from verse_check.py says the code compiles.
