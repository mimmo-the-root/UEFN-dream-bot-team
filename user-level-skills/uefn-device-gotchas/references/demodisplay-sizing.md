# DemoDisplay sizing, orientation, and placement (full detail)

`~/.claude/CLAUDE.md` rule 7 states the summary and the two things that must never be violated
(function-based grouping, the gameplay-critical-position exception). This file has the actual
mechanics — read it when you're about to size or place a stand, not for the general rule.

## Sizing
Resize a `DemoDisplay` using its own **`width`/`depth`/`height` properties** (via `ObjectTools`)
— NOT the actor's Scale, which stays `1,1,1`. Defaults `width=6, depth=5, height=4` give a
footprint of roughly 500×633uu; each `+1` to `width` adds roughly 100uu along the Y axis. For a
typical group of 5-6 devices, `width=8-10` is usually enough.

## Orientation
At yaw=0 the `DemoDisplay`'s "front" is `+X` and its "right" is `+Y` — always check the actor's
actual yaw before picking an axis; a real attempt got this backwards and moved along X believing
it was "right" when it was actually "front." To place a new stand "to the right" of an existing
one: keep the same X (or the equivalent rotated X), start the new stand's Y at the existing
stand's maximum-footprint Y plus the required gap (e.g. 500uu for a 5-meter gap), then center the
new stand on that Y by adding half of its own Y extent.

## The `get_actor_bounds` gotcha
It can include asymmetric components (e.g. a spotlight's cone) that stretch the bounding box well
past the stand's physical footprint on one side only — don't trust it blindly to compute the
usable perimeter. Instead compute the "real" footprint from the `width`/`depth`/`height` you set
(symmetric around the actor's location, verified empirically on the side unaffected by the
asymmetric component), and use `get_actor_bounds` only to sanity-check the side you expect to be
symmetric.

## Placing devices on the stand
The Verse device and the devices it configures (Item Granter, Elimination Manager, Accolade,
Timer, etc. — only those whose behavior does NOT depend on their position in the world, see
`storm-spawner-position-critical.md` for the ones that DO) go **inside the `DemoDisplay`'s X/Y
footprint, at the same Z as the `DemoDisplay`'s base** (its minimum Z / resting plane) — NOT
stacked with a Z offset, NOT lined up in an evenly-spaced row in front of the display: group or
scatter them freely within its footprint. In practice: size the `DemoDisplay` large enough first,
then move the devices into its X/Y coordinates at Z = the `DemoDisplay`'s base.
