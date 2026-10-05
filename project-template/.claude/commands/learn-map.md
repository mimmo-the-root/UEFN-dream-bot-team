---
description: Learn now from the Verse map: read the cards not learned yet and queue skill proposals for approval
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Grep
---

Learning step from the Verse map (planner-docs step 4b), forced now. Repeat steps 2-4 until `learn` says 0 cards to read.

1. Make sure `Claude/docs/.genre` names the genre (not `epic-template`); if it is missing, say so and stop. If there is no map, run `py -3 Claude/hooks/verse_map.py build` first (use `python` if `py` is missing).
2. Run `py -3 Claude/hooks/verse_map.py learn`. It prints the next batch of unread cards, complete and never truncated (signal-only view: roles, links, subscriptions, per-player state, pitfall comments). Add `--full` only when a card needs its functions and variables. Do not cut the output with head/cut/truncation.
3. From that batch only, find reusable, generalized rules (no map names, ids or links). Check `skills_lib.py patterns <genre>`, reuse existing wording, queue with `skills_lib.py propose` (`for`, or `against` when the cards show the opposite). No minimum count; the owner approves on the Skills page. Strategy patterns (death/retry, progression, purchases) are patterns too, with a variant, never invented numbers.
4. Run `verse_map.py learned` (marks only that batch). Go back to step 2.
5. Devices in the level: follow "Detecting MCP mode" in `~/.claude/skills/mcp-tool-contracts/SKILL.md`. If the UEFN MCP is reachable, read read-only the devices and wiring that the batch's files reference; otherwise list which devices were not inspected. Never skip this silently.
6. Report in three lines: cards read, proposals queued, devices inspected or not.
