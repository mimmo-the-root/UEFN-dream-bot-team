---
description: Look up a game mechanic (what it needs, its parameters, edge cases, bugs, how UEFN does it) or check a set of mechanics before you build them
argument-hint: "find WORDS | show ID | check ID ID ..."
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read
---

Input: `$ARGUMENTS`. Run from the project folder: `py -3 Claude/hooks/mechanic_catalog.py $ARGUMENTS` (use `python` if `py` is missing). It reads the catalog of 223 mechanics shipped with the kit and prints the answer; nothing is changed.

- `find parry block` lists the mechanics that match (add `--genre shooter` or `--cat combat` to narrow it).
- `show combat.parry` prints the card: purpose, the systems it needs, parameters with their usual ranges, edge cases, common bugs, balance and accessibility notes, links to other mechanics, its cost, and the UEFN line (a recipe, a device or a Verse way the kit has checked, or "not checked in UEFN yet").
- `check id id id` is for planning: the mechanics a chosen one requires that you did not choose, hard conflicts, soft conflicts (who owns the decision), systems to build once, a rough cost and the first slice to build.

Tell the owner in plain words what matters for THIS game: which edge cases to decide now, which mechanic is a risk for a multiplayer island (rounds, saving), and what UEFN already offers. When a mechanic says "not checked in UEFN yet", say so and do not promise a device; ask for the check (the worker looks the devices up in the editor). Cost numbers are a guide, never hours.
