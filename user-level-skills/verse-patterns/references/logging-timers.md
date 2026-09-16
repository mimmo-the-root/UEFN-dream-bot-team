# Logging and timer patterns

One-line pattern entries, replace the placeholder as real ones get validated.

- Centralized logging: use the `DebugLoggingEnabled` pattern in
  `Claude/reference/logger-template.verse.txt` instead of calling `Print()` directly — see
  `~/.claude/CLAUDE.md` rule 2. This is the one entry here that's not a placeholder: it's a
  base-rule requirement, not a suggestion.
- (example — replace) a cooldown/timer pattern that survives a device reset cleanly (what to
  cancel/reset on round end so a stale timer doesn't fire into the next round).
