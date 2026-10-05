---
description: Learn now from the Verse map: read the cards not learned yet and queue skill proposals for approval
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Grep
---

Learning step from the Verse map (planner-docs step 4b), forced now.

1. Run `py -3 Claude/hooks/verse_map.py learn` (use `python` if `py` is missing). If it says there is no map, run `verse_map.py build` first. It lists the cards not learned yet: the whole map the first time, afterwards only changed files.
2. Make sure `Claude/docs/.genre` names the genre (not `epic-template`); if it is missing, say so and stop.
3. Read ONLY the listed cards (not the sources). For each reusable, generalized rule (no map names, ids or links): check `skills_lib.py patterns <genre>` and reuse the existing wording, then queue it with `skills_lib.py propose` (`for`, or `against` when the cards show the opposite). No minimum count; the owner approves each proposal on the Skills page.
4. Run `verse_map.py learned`.
5. Report in two lines: how many cards were read and how many proposals were queued.
