---
description: Scan publication texts for emoji, decorative Unicode and invisible characters
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/text_scan.py` (use `python` if `py` is missing), or add the files or folders to check after it. With no argument it scans `Claude/docs/publish/`. It prints one JSON line: `state` is `clean`, `found` or `nothing_to_scan`. For `found`, list each file, line, column and advice in a short table. It only reports; change a text only if the owner asks.
