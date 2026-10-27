---
description: Read-only coherence check of spec, plan and tasks with a severity per finding, before building or after a change
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read
---

Run from `Claude/hooks` (`py -3` on Windows): `python plan_check.py` (add `--stage plan` before the tasks exist). This command is READ ONLY: it never edits a file. Output: at most 50 findings, sorted CRITICAL, HIGH, MEDIUM, LOW.

Report in plain language, at most 8 lines: the verdict first (OK, or how many findings stop the build), then each CRITICAL and HIGH with the file to change and the command that fixes it (`/spec` for the spec, `/piano` for the plan and the principles, `/compiti` for the tasks). A CRITICAL is a conflict with `CONSTITUTION.md` or a spec that is not ready; it is never argued away, the spec, the plan or the tasks change instead. MEDIUM and LOW go in one line each.

Then offer the fix as a short plan and wait for the owner's yes before any file changes. When the owner has changed the spec after approval (`Approved: no`), say which stories, plan sections and tasks are touched, so only those go back to "to do".
