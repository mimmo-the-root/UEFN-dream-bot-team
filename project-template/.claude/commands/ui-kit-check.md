---
description: Check that Epic's Verse UI Kit and its AGENTS.md are installed, and whether Epic changed the guide
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run from the project folder: `py -3 Claude/hooks/ui_kit_check.py --check` (use `python` if `py` is missing). It prints one JSON line with `state`: `ok`, `package_missing` (tell the owner to install the free Verse UI Kit from Fab), `agents_missing` (Epic's AGENTS.md is a separate download on the Fab page; it is kept once for all projects, the message says where, or use `--store <file>`) or `agents_changed` (Epic changed the guide: offer to analyze it, change nothing without the owner's yes). Report the state and the `message` in one or two lines. Run `--accept` only after the owner agreed to the new version.
