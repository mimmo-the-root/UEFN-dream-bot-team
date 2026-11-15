<!-- Full text of base rule 1. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 1. Project organization and naming convention

Official reference: [Starting and organizing a project in Fortnite](https://dev.epicgames.com/documentation/fortnite/starting-and-organizing-a-project-in-fortnite).

- All content we create (not native to UEFN/Epic, not third-party) should live in folders
  prefixed with `custom_` so it's distinguishable at a glance — e.g. `custom_verse/`,
  `custom_asset/`, and if needed `custom_device/`, `custom_ui/` following the same scheme.
- Inside each `custom_*` folder, organize hierarchically: Content type → Asset type → Specific
  use (Epic's official guidance) — not one flat folder with everything dumped in.
- File naming: PascalCase, no spaces, descriptive name (e.g. `RespawnManager.verse`, not
  `respawn manager 2.verse`). For assets with UEFN's native prefix-type conventions (`MI_`,
  `WBP_`, etc.) follow those instead.
- Consistency first: if an existing project already uses a different scheme, **don't rewrite
  it all retroactively without saying so first** — `project-bootstrap` notes it in SPEC.md as
  the "project's current convention," and the new convention applies to new code going
  forward, unless the owner says otherwise.

This convention isn't only about the Content Browser's folders and file names — it also
applies to how placed devices/actors are organized in the **Outliner** (Scene Graph), which is
a separate structure and just as easy to let turn into an unreadable flat list:

- **Outliner folders**: group placed devices into folders that mirror the actual areas/systems
  of the experience — e.g. `Lobby`, `Game Area 1`, `Devices`, `UI`, and so on, matching however
  the project is actually laid out. Don't leave dozens of devices ungrouped at the top level.
- **Device naming**: every device's name in the Outliner should say what it does at a glance,
  without opening it — pattern `<DeviceType>_<Function>`, e.g. `teleport_lobby` (a teleporter
  that sends the player to the lobby), `killzone_arena1` (a kill zone in arena 1),
  `spawner_wave2` (a spawner for wave 2). Default auto-generated names like `Device_17` should
  be renamed the first time that device is touched.
- For **existing projects** with an ungrouped Outliner or unrenamed devices, this isn't an
  immediate mass-rename: `project-bootstrap` proposes a reorganization plan (suggested folders,
  suggested renames) during its initial quality check, rather than applying it directly —
  renaming devices blind can break Verse references bound to their names, so the owner reviews
  the plan first and `coder` applies it once confirmed.
