<!-- Full text of base rule 3. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 3. Always multiplayer

All projects are multiplayer. Any functional check — `coder` after a change, `qa-regression`
before marking a bug as resolved — must consider behavior in a real multiplayer context, not
just solo preview: state replication across players, server vs. client authority, what happens
if multiple players interact with the same device/object at the same time. If the available
MCP tool for playtesting only supports solo sessions, that must be flagged explicitly as a
limitation, with a recommendation for a manual multiplayer test before considering a feature or
fix truly done.
