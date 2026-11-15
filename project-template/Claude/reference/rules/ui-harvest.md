<!-- Full text of the project rule "UI reference harvest". The short version is in this project's CLAUDE.md (KIT block ui-harvest); kit_sync keeps this file current. -->

# UI reference harvest

- **UI reference harvest (automatic, every session, independent of any single task or of
  `coder` having touched anything)**: if `~/.claude/skills/game-ui-designer/` exists, this has two
  parts — do BOTH every session, not just when a task happens to close:
  1. *Pending screenshots*: check `Claude/docs/ui-screenshots-pending/` for any image files — file
     each one into `~/.claude/skills/game-ui-designer/references/examples/<archetype>/`, append a
     row to `manifest.md` (source: this project's real work), then delete it from the pending
     folder so it isn't re-ingested next session.
  2. *UI code drift check (the important one for hand-authored UI)*: the owner may design/edit UI
     screens directly (by hand, outside any tracked `coder` task), so this can't depend on a task
     ever closing. Find this project's real UI/widget implementation files (`.verse` files
     constructing `canvas_panel`/`stack_box`/`button`/`text_block`/`image` and similar for a
     store/shop/mission/reward/inventory/HUD screen — same discovery heuristic as
     `game-ui-designer`'s "Direct source-code analysis" step). Compare each one's current content
     hash against `Claude/docs/.ui-code-ingested.json` (create it, empty `{}`, if missing — maps
     file path to last-ingested hash). For any file that's new or whose hash changed since last
     time: run the source-code analysis on it now, write/update its entry in
     `~/.claude/skills/game-ui-designer/references/examples/code-derived.md` and a `manifest.md`
     row (source: this project's name + the file path — note explicitly if this looks hand-authored
     rather than `coder`-written, e.g. no matching recent ROADMAP task), update
     `Claude/docs/UI-STYLE-NOTES.md` with any concrete style facts found, then record the new hash
     in `.ui-code-ingested.json`.
  This is a cheap check (file listing + hashing, only re-analyzes what actually changed), safe to
  do every session; don't ask permission, just do it and note in this session's summary how many
  screens were freshly ingested. This is what actually breaks the chicken-and-egg problem: the
  owner can keep hand-drawing UI screens entirely outside the task workflow, and the skill still
  learns from every one of them the next time this project is opened — no task, no screenshot, no
  explicit "analyze this" request required.
