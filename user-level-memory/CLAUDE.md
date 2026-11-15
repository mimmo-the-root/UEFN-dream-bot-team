# Base rules for all UEFN projects

Claude Code loads this file in every session. It is the short version: each rule says what to do; the full
text (examples, edge cases, why) is in `~/.claude/kit-rules/NN-*.md`. Read the full file of a rule only when
the task is about it (the trigger is written next to each rule), never all of them at once.

<!-- KIT:BEGIN base-rules -->
## 1. Organization and naming
Our content lives in `custom_*` folders (Content type → Asset type → Use), PascalCase names, UEFN prefixes
(`MI_`, `WBP_`) where they exist. Outliner: folders per area/system, devices named `<DeviceType>_<Function>`
(`teleport_lobby`). Existing projects: propose a rename plan, never mass-rename blind (Verse references break).
Full: `~/.claude/kit-rules/01-organization-naming.md` (before creating folders or renaming devices).

## 2. Centralized logging
Every Verse file uses `@editable DebugLoggingEnabled : logic = true` + `Log(LogMessage : string)` instead of
`Print()` (template: `Claude/reference/logger-template.verse.txt`). Logs not enough for a bug: add logs and
re-test, never guess. Full: `~/.claude/kit-rules/02-logging.md`.

## 3. Always multiplayer
Every check considers replication, server authority and players acting at the same time. A solo-only
playtest is flagged as a limitation with a manual multiplayer test to do. Full: `~/.claude/kit-rules/03-multiplayer.md`.

## 4. Performance and deprecated APIs
No tight polling or allocations in loops when an event exists; report FPS drops in BUGS.md. Never add calls
to deprecated APIs; check Epic's docs, not the compiler. Full: `~/.claude/kit-rules/04-performance-deprecated.md` (audits).

## 5. State machine
New multi-phase logic is a state machine, not scattered flags; existing projects: propose it only when
flags cause bugs or a feature needs it. Full: `~/.claude/kit-rules/05-state-machine.md`.

## 6. Verse header
Every Verse file starts with `# <File>.verse`, `# Summary: <what it does>`, `# Last modified: <real date> — v<n>`;
one comment per logical section. No history in the file: log changes with
`python Claude/hooks/verse_changes.py add <file.verse> --summary "..." --reason "..."`.
Full: `~/.claude/kit-rules/06-verse-header.md` (before editing a header).

## 7. DemoDisplay per Verse device
Each custom Verse device has a `DemoDisplay` stand outside the play area, grouped by function, listing what
it does and every device it uses; update it whenever devices or connections change. A device whose position
is gameplay (storm, spawner) is never moved, only named. Full: `~/.claude/kit-rules/07-demodisplay.md` and
`~/.claude/skills/uefn-device-gotchas/references/demodisplay-sizing.md` (before placing or sizing a stand).

## 8. Support devices outside the play area
Logic devices (granter, timer, elimination manager...) go outside the playable area on their stand; devices
players meet, or whose position matters, stay where gameplay needs them. Full: `~/.claude/kit-rules/08-support-devices.md`.

## 9. Concise style
Results first, no preamble or closing offers, diff not whole files, task ids instead of re-describing; a
subagent report is at most 15 lines. Full: `~/.claude/kit-rules/09-concise-style.md`.

## 10. Compiles = done; learn from errors
Code that does not compile is not done: compile → read exact error → fix → recompile, at most 5 tries on the
same error, then BUGS.md and ask. Save one-line project lessons in agent memory; lessons useful on any island
go to `~/.claude/skills/uefn-lessons/SKILL.md`; MCP "which tool does X" lives only in
`~/.claude/skills/mcp-tool-contracts/SKILL.md`. Full: `~/.claude/kit-rules/10-compile-and-learning.md`.

## 11. Second brain (optional)
**Second brain path**: `<SECOND_BRAIN_PATH>` (while it is this placeholder the feature is off: skip it).
Only `second-brain-librarian` reads/writes the vault (`wiki/` only); coder and project-bootstrap hand off to
it for reusable implementations and may query it before building a common pattern. Ask last: look in the
vault and genre/technique skills before asking the owner. Never block on it. In a session: rule 15.
Full: `~/.claude/kit-rules/11-second-brain.md` (before any vault work).

## 12. Brand collections (optional)
Brand-looking projects (LEGO, TMNT, Fall Guys...): project-bootstrap checks
`~/.claude/skills/brand-collections-uefn/SKILL.md`; an unknown brand is a note in SPEC.md, never an error.
Full: `~/.claude/kit-rules/12-brand-collections.md`.

## 13. Plan-first: no code without a task
Every code/device change has a task row in ROADMAP.md. Only `planner-docs` creates tasks and sets Done;
`coder` only flips To do / In progress / Blocked, writes the id to `Claude/docs/.active-task`, and stops if
no task exists. Order: `intent-gate` (before code) → coder → `intent-reviewer` PASS → `compliance-reviewer`
PASS → planner-docs marks Done. Verdicts are appended to `Claude/docs/.task-verdicts`; review loops stop after
5 rejections (BUGS.md, owner decides). STATUS.md "Current state" always says in progress / next / done / next step.
Full: `~/.claude/kit-rules/13-plan-first-gates.md` (coder, reviewers, planner-docs, release-gate: read it once per session).
<!-- KIT:END base-rules -->

<!-- KIT:BEGIN kit-self-update -->
## 14. Kit self-update for older projects (automatic)

Projects with a kit older than v1.84 have no update hook, so they never refresh themselves. As the very
first action of ANY session in a project that has a `Claude/` folder next to a `CLAUDE.md` (with or without
`Claude/KIT-VERSION`; a missing version file means a very old kit), compare the project's
`Claude/KIT-VERSION` with `~/.claude/kit-template/Claude/KIT-VERSION`. If the project file is missing, older,
or `.claude/settings.json` has no `kit-sync` entry, run once, without asking:

`python ~/.claude/kit-template/Claude/hooks/kit_sync.py <project folder>` (use `py -3` if `python` is missing;
the project folder is the one that contains `Claude/` and `.claude/`).

It backs up replaced files under `Claude/logs/kit-backup/`, adds missing hooks and files, never touches
Claude/docs or your permissions. Then tell the owner in one line: "Kit updated from vX to vY: restart the
session so the new files are read." If the profile template folder does not exist, say so once and continue.
Do not repeat the check when the versions already match.
The same script also checks, at every session start, that the project's `.uplugin` has `"EnableVerseAssetReflection": true` (old maps lack it, so the assets digest is never generated) and adds it with a backup.
<!-- KIT:END kit-self-update -->

<!-- KIT:BEGIN no-delete -->
## 15. If you cannot delete a file, park it in `_to_delete`

Delete only what the task needs. When a delete is refused or impossible (protected or read-only folder, no permission, a tool without delete rights), do not work around it: move the file to `_to_delete/<yyyymmdd-hhmmss>/` at the root of the project (or the kit folder) and say in one line what was parked and why. The owner empties that folder. It applies to files replaced or removed during a kit update too. Never use `git clean` or bulk deletes on the owner's files.
<!-- KIT:END no-delete -->

<!-- KIT:BEGIN second-brain-session -->
## 15. Second brain in a session (automatic, only when rule 11 has a real path)

While the "Second brain path" in rule 11 is still the placeholder, ignore this rule: the second brain is off.

When it is set, the project hook `Claude/hooks/brain_brief.py` prints `wiki/hot.md`, the read order and the pending-ingest count at the start of every session, and runs the free checks after every page written under `<vault>/wiki`. What you do:

- Read order: `wiki/hot.md`, then `wiki/index.md`, then the thematic `wiki-index.md`, then the page. Never read the vault for a general coding question.
- Before asking the owner a question, look for the answer in the vault (`second-brain-librarian` query) and in `wiki/kit/` (how the kit itself works); skip silently if nothing is found.
- If a hook reports a broken link or a quote that is not in its raw file, fix the page in the same turn: the checks cost no tokens.
- Only `second-brain-librarian` writes to the vault. `vault_check.py status` lists the raw sources still to ingest; `done raw/<file> wiki/<page>...` records one.
<!-- KIT:END second-brain-session -->
