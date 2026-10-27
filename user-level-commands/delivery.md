---
description: Before delivery: the list of what only the owner can do, the private release, the memory check with the owner's flags, then the playtest
argument-hint: ""
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

The last step before the players. Work in `Claude/docs/`; run scripts from `Claude/hooks` (`py -3` on Windows).

1. Run `python audit_log.py status`. If a medium or major finding is open, stop: back to `/audit`.
2. Run `python release_gate.py init`. It writes `DELIVERY-GATE.md` with five sections: 1 Configuration you cannot do (Beta Access, Python scripting, the Island settings, the manual steps of the plan), 2 Compliance (Fab and island rules, with the `Scan:` line from the read-only scan), 3 Private release, 4 UEFN Publishing Validation and memory (Memory Usage, Download Size, Cooked for Platforms, Project Size), 5 Playtest. Give the list to the owner in plain words, one line per item, with where to click.
3. **Claude never ticks a box.** The owner ticks `- [x]` each line, and writes `Memory used: NN%` read from UEFN. Ask for it; when the owner says done, run `python release_gate.py check`. It blocks while a box is open or the memory is missing; 100% or more blocks, 85% or more warns (tell the owner what to cut).
4. When the gate is ready: the private release is made by the owner (publish as private, write the code in the file). Then the playtest: `python env_check.py --playtest` into `PLAYTEST.md` with the real number of players. The owner plays; every failed row becomes a task, and a bug goes back to `/audit`.
5. After a good playtest: the game is delivered. From here the usual cycle starts again: collect new ideas, `/spec` (iteration), `/game-plan`, `/task-list`.

Short report; name the files.
