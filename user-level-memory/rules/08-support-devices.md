<!-- Full text of base rule 8. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 8. Support devices stay outside the play area

All support/logic devices that are not gameplay-critical in position — Item Granter, Timer,
Elimination Manager, `DemoDisplay`, and similar — go outside the playable area, grouped on their
function's `DemoDisplay` stand (see rule 7 above), not scattered in the middle of the map, so
they're never visible to or reachable by players. This does NOT apply to devices players are
meant to encounter during gameplay, like a Player Spawner or a central display case, or to any
device whose position is gameplay-functional (see the exception in rule 7) — those stay wherever
the design/gameplay calls for them. `coder` places new support devices outside the play area,
grouped by function, from the start; `project-bootstrap` flags any existing support device found
inside the play area, or ungrouped, as a non-blocking follow-up in BUGS.md, for the owner to
review before moving it (relocating a device can affect existing triggers/volumes tied to its
position).
