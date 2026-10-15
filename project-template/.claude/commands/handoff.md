---
description: Write a short HANDOFF.md so a fresh session (or another model) can continue without re-reading everything
---

Stop the current work and write `Claude/docs/HANDOFF.md` (replace it if it exists), under about 60 lines, only from what really happened in this session:

1. **Goal**: what the owner asked for, in one or two lines.
2. **Done**: what is finished and verified (say how: a `/verse-check` result, a playtest, a test).
3. **Files touched** and why, one line each.
4. **Tried and failed**: what did not work and the exact error, so nobody repeats it.
5. **Next**: the next three concrete steps, and any decision the owner still has to make.

Do not paste code or long logs; point to the file and line instead. Then tell the owner to run `/clear` (or `/model` to switch model) and start the new session with: `read Claude/docs/HANDOFF.md and continue`.
