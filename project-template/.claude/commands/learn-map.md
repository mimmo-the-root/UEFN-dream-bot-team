---
description: Learn now from the Verse code, the project documents and the devices in the level, one slice at a time with a fresh agent per slice; queue skill proposals; report where documents disagree with code
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Agent
---

Learning step (planner-docs step 4b), also forced by hand. You are only the ORCHESTRATOR: you never read code, documents or devices yourself, so your context stays small however large the map is. A long single agent re-reads its whole history every time it is resumed (136k to 425k tokens per resume on a real map); a fresh agent per slice reads only its own slice (about 15k tokens for a batch of code).

Loop, in the foreground and one slice at a time (the batch state of `verse_map.py` is single):
1. Run `python Claude/hooks/verse_map.py next` (zero tokens). It prints one JSON line `{"slice": ..., "left": n}`.
2. `done` -> go to the report. `stuck` -> stop, say which slice (`kind`) did not progress and why you think so (read the last agent's reply), and finish: the next session start tries again. Otherwise start ONE agent with the Agent tool (type `general-purpose`, foreground) and this prompt, nothing else: `Run /learn-slice <slice> in this project (Claude Code project folder: the current one). Follow .claude/commands/learn-slice.md for that slice only, then stop and answer in at most three lines.` The agent's reply is the only thing you keep (three lines); do not repeat it to the owner during the loop.
3. Back to 1. Never run a slice yourself, never start two at once, never skip `next`.

Report (seven lines, built from the slice replies and `python Claude/hooks/verse_map.py status`): files read (complete) and proposals queued; patterns assigned to a section; documents read and patterns from them; document-vs-code discrepancies with the proposed fix (or "none"); MCP mode with the project name returned; devices read from the level and differences from the baseline, or not inspected; the map blueprint saved, with its layout/devices/rules counts. If the session stops early nothing is lost: a slice is marked only by `learned`/`docsdone`/the files it writes, `verse_map.py next` continues from there at the next session start. Never ask the owner to continue. The details of every slice are in `.claude/commands/learn-slice.md`.
