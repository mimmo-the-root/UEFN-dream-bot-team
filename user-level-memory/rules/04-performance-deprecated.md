<!-- Full text of base rule 4. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 4. Performance, FPS, and deprecated APIs

Always keep an eye on performance impact: Tick loops, the number of devices/events active at
once, the cost of repeated operations. `project-bootstrap` does a static performance review
during its initial quality check (see its A3 step); `qa-regression` reports any FPS drop or
suspicious-looking expensive behavior found at playtest in BUGS.md (with severity based on
impact), even when it isn't strictly an error. `coder` avoids patterns known to be costly (tight
polling, allocations inside a loop) when an event-driven alternative exists.

Alongside performance, also watch for **deprecated or soon-to-be-removed Verse/UEFN APIs and
device features**: `project-bootstrap` checks existing code for calls to deprecated functions
during its A3 quality check and lists each one in BUGS.md with what replaces it, if known;
`coder` doesn't introduce new calls to something already flagged as deprecated, and replaces one
opportunistically when it's already touching that code for another reason (not as a dedicated
pass unless asked). When in doubt whether something is deprecated, check Epic's official UEFN/
Verse API documentation rather than guessing from the compiler still accepting it — deprecated
APIs often still compile right up until they're removed.
