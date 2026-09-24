# State machine patterns

One-line pattern entries, replace the placeholder as real ones get validated.

- (example — replace) phase-based logic (lobby → round → end-of-match): one enum/state var,
  one transition function that validates the move is legal before applying it, one function per
  phase for what happens on entry — not scattered boolean flags checked ad hoc across the file.
- (example — replace) a device with its own local state machine (open/closed, armed/disarmed):
  keep transitions logged via the centralized logger (see `logging-timers.md`) so QA can see the
  actual sequence from logs, not just the current state.
