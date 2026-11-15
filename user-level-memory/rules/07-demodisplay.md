<!-- Full text of base rule 7. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 7. DemoDisplay for every Verse device (since 2026-08-26, refined 2026-08-26)

Every custom Verse device in the project (e.g. `pillar_game_manager`, `item_pool_manager`) has a
dedicated `DemoDisplay` stand, placed outside the play area, organized **by function**: one
Verse device's stand groups ALL the devices that Verse device configures — e.g. "Game Manager"
or "Item Pool" — not one `DemoDisplay` per individual connected device.

**Sizing, orientation, the `get_actor_bounds` gotcha, and how devices are placed on the
stand**: full detail (exact `width`/`depth`/`height` defaults and math, yaw/axis rules, the
asymmetric-bounds pitfall) now lives in `~/.claude/skills/uefn-device-gotchas/references/
demodisplay-sizing.md` — read it before sizing or placing a `DemoDisplay`, don't reason about the
math from scratch here.

**Gameplay-critical-position exception — always check this first, before reading the skill
above.** A device whose position IS functional gameplay data (Storm Controller/Beacon = storm
circle center, Player Spawner = spawn point, and in general any device that would change in-game
behavior if moved) must NEVER be moved onto a stand — it stays in its gameplay position, and is
only **referenced by name** in the `DemoDisplay`'s text description, never physically relocated.
Before moving any device onto a stand, always check whether its position is gameplay-critical —
this is a general rule, not just for the Storm Controller; project memory may already document a
specific case (e.g. `storm_controller_location_is_circle_center.md`), and
`uefn-device-gotchas/references/storm-spawner-position-critical.md` covers the general pattern.

**Fields to fill in:**
1. A minimal description of what the Verse device does.
2. The full list of devices it's connected to/uses — noting which are physically on the stand
   and which stayed in place for gameplay reasons.

This isn't a one-time setup task: the matching `DemoDisplay` must be created or updated every
time `coder` places or modifies a Verse device or changes its connections, not just when that
device is first created. If a `DemoDisplay` update is skipped, the documentation drifts out of
sync with the actual device graph — which defeats the point.

For **existing projects**, `project-bootstrap` checks during its quality check whether custom
Verse devices already have a `DemoDisplay` and whether it's current (including whether grouping
by function and the gameplay-position exception are respected); where it's missing or stale, it
flags it as a non-blocking follow-up in BUGS.md (same treatment as missing logging or header
documentation) rather than creating them itself.
