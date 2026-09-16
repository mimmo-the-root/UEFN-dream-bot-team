# Multiplayer / authority patterns

One-line pattern entries, replace the placeholder as real ones get validated.

- (example — replace) shared counter touched by multiple players: hold it in a single
  server-authoritative device/agent, expose an event other devices react to, never let a client
  increment its own local copy and trust it.
- (example — replace) "does X apply to every player or just the triggering one" — default to
  per-player unless the mechanic is explicitly shared (e.g. a shared timer, a shared score).
