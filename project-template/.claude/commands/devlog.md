---
description: Write the jam dev log (what was built, day by day, and how AI was used) from the kit's logs
---

1. Run `python Claude/hooks/devlog.py` (on Windows use `py -3` if `python` is not found). It writes the automatic part of `Claude/docs/devlog.md` from `Claude/logs/verse-changes.jsonl` and `verse-errors.jsonl`; whatever is outside the markers is kept.
2. Read the file. In the part above the markers ("How AI was used"), propose short, true answers drawn ONLY from this project's logs and the owner's words in this session: what the human decided, what the agents did, what went wrong and how it was fixed. Mark anything you are not sure of with `(owner: confirm)`.
3. Show the owner the proposed text in one block and write it only after a yes. Never invent a decision or a step that is not in the logs.
