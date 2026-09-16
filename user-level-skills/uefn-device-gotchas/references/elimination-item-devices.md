# Elimination Manager / Item Granter / Accolade / Timer gotchas

One-line entries, replace the placeholders as real ones get validated.

- (example — replace) Elimination Manager edge case: what happens when the eliminated and
  eliminator are the same team, if teams aren't configured the way the device assumes.
- (example — replace) Item Granter timing: granting on `BeginPlay` before a player is fully
  spawned/possessed can silently no-op — grant on the player-ready event instead.
- (example — replace) Timer device reset behavior on round end — does it auto-cancel or does the
  callback still fire once into the new round if not explicitly stopped.
