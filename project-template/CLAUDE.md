<!-- SEED FILE, not update-safe: this becomes the project's own live CLAUDE.md the first time
     Phase 2 setup runs (Project identity, Conventions get filled in below). A kit update must
     NEVER re-copy this file over an existing project's CLAUDE.md — see SETUP-GUIDE.md's
     "Updating an existing project" section for exactly what is and isn't safe to bulk-copy. -->

# <AUTO_PROJECT_NAME>

## What this is
(Short description of the project, 1-3 sentences)

## Project type
- [ ] UEFN project (Verse + Creative Devices) connected via UEFN MCP
- [ ] Other project type: ____________

## Project identity (detected once during setup, don't recompute by hand)
UEFN project name: **<AUTO_PROJECT_NAME>**

Deliberate layout choice: this scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) lives inside
`Content/`, alongside the assets and Verse code — not next to it. This is intentional, so
everything ends up under UEFN's native save/cloud-sync and nothing gets lost. Technical
consequence to keep in mind: `Content` is named identically across every project, so the name
above CANNOT be the current folder's name (it would always be "Content," useless for telling
projects apart). It's instead the name of the folder that CONTAINS `Content` — i.e. the real
UEFN project folder (e.g. the island's name) — computed once during setup (see
`Claude/SETUP-INSTRUCTIONS.md`) and written above. From this point on, every agent reads this
already-written value, it never recomputes it from the current folder's name.

UEFN's MCP server is a SINGLE instance per machine/editor and always serves whichever project
is currently open in UEFN — not necessarily this one, if UEFN still has a different project
open. Before using any MCP tool, every agent must verify that the project open in UEFN matches
the name above, following the "verifying which project UEFN has open" contract in
`~/.claude/skills/mcp-tool-contracts/SKILL.md` (don't guess which listing tool to use). If it
doesn't match, stop and warn the owner.

## Conventions
- Code style / naming to follow:
- Technical constraints (e.g. Verse limits, performance targets, supported devices):

## Where things are
Everything we manage (not native to UEFN) lives inside the `Claude/` folder, to avoid mixing
with the real assets and project:
- Project spec (generated/confirmed): Claude/docs/SPEC.md
- Progress status: Claude/docs/STATUS.md
- Roadmap: Claude/docs/ROADMAP.md
- Bug backlog and bug-fixing roadmap: Claude/docs/BUGS.md
- Proposals to increase playtime / reduce first-5-minutes drop-off: Claude/docs/RETENTION-NOTES.md
- Release-readiness evaluations (history): Claude/docs/RELEASE-READINESS.md
- Logs from automatic post-playtest checks: Claude/logs/

(`.claude/` — with the dot — is instead a reserved folder used by Claude Code itself for
`settings.json`; leave it where it is, don't move it into `Claude/`.)

## Rules for this project's agents
- **Plan-first (rule 13 in `~/.claude/CLAUDE.md`): no code without a tracked task.** Every task
  `coder` works on must already have a row in `Claude/docs/ROADMAP.md`'s `Tasks` table (ID, Status,
  acceptance criteria). No row yet → describe it in one line so **planner-docs** can open it
  first. This is the plan → code → review → close order the whole team follows; see rule 13 for
  the full mechanics (who owns which field, the narrow Status-flip exception `coder` has).
- The very first time on this project (Claude/docs/SPEC.md still empty), use **project-bootstrap**: if code already exists, it analyzes structure/specs/bugs/retention; if the project is new, it gathers requirements from the owner and opens the first ROADMAP tasks instead of inventing them.
- The **intent-gate** agent runs BEFORE coder writes anything: an independent check (not coder's own self-check) on whether the task's acceptance criteria, and any owner-supplied base code, are concrete enough to implement without guessing. An AMBIGUOUS verdict goes straight to the owner — coder doesn't try to resolve it on its own.
- The **coder** agent writes/modifies code but doesn't update documentation, beyond flipping its own task's Status (To do/In progress/Blocked — never Done, never the row's content). Before reporting any task done, it must get a PASS from **intent-reviewer**, then a PASS from **compliance-reviewer** (in that order — the second doesn't run until the first has PASSed), then hand off to **planner-docs** to actually close it — a task that hasn't passed both gates and been marked Done isn't finished yet, regardless of what coder itself thinks of its own work.
- The **intent-reviewer** agent checks ONLY whether coder's output actually matches the task's acceptance criteria — line by line against what was asked, no invention, no silently-resolved ambiguity. It never writes code or touches devices, and it runs before any mechanical check.
- The **compliance-reviewer** agent checks coder's output against this kit's mechanical rules (logger, naming, DemoDisplay, deprecated APIs, multiplayer authority, state machine, second-brain consultation) — but only after `intent-reviewer` has already returned PASS on the same task; it doesn't run otherwise. It never writes code or touches devices either — both reviewers only review and send non-compliant work back to coder with specifics.
- The **qa-regression** agent checks for regressions and logs but doesn't modify code; after every play-session (including automatically via the hook) it reports new problems in Claude/docs/BUGS.md.
- The **planner-docs** agent is the gatekeeper of ROADMAP.md/STATUS.md: it's the only one who opens a new task row, edits its content, or marks it Done (always after reported PASS verdicts from BOTH intent-reviewer and compliance-reviewer), and it keeps STATUS.md's "Current state" block honest — typically invoked before coder starts a new task, at the end of a session, or after an automatic post-playtest check.
- The **release-gate** agent evaluates whether the project is ready for release, based on open bugs, task completeness against ROADMAP.md, and already-documented progress status. Use it before a release/showcase, not during day-to-day development — it doesn't find new bugs and doesn't write code.
- The **codebase-auditor** agent is an independent, whole-codebase quality audit — architecture, duplication, performance, maintainability, and issues that only surface after a long play session — run on demand, not tied to any single task. It never writes code; it hands findings to **planner-docs**, which opens a ROADMAP task per finding worth tracking (or files it in BUGS.md if it's too small to be its own task).
- No agent should read or modify files outside this project's folder (`Content/`), with one
  narrow exception: **growth-manager**, once the owner confirms a final thumbnail, may create
  `Resources/` at the project root (the folder containing `Content/`) and update the `"keyArt"`
  key in `<ProjectName>.uefnproject` (also at the project root) to point at it — nothing else at
  that level.
- **Genre check (automatic, every session, independent of `project-bootstrap`)**: as your very
  first action in ANY session on this project — before the Agent Console check below, before
  reading STATUS.md, regardless of whether `project-bootstrap` has ever run here — check whether
  `Claude/docs/.genre` exists and has a non-empty value. This is a one-line file-existence check,
  cheap enough to do every session; don't skip it just because the project already has a lot of
  history. If it already has a value, do nothing further and don't mention it. If it's missing OR
  empty, immediately follow `~/.claude/agents/project-bootstrap.md`'s "Step 0.5 — Genre selection
  & Genre Skill bootstrap" procedure right now, in this same session, even if you're not running a
  full bootstrap — that step is self-contained and was written to be triggerable on its own. Don't
  ask permission to check or to run the step itself; DO stop and ask the owner which genre to pick
  (that one decision is genuinely theirs, never guess it) before writing `.genre`. This exists
  specifically so a batch of already-analyzed/pre-existing projects gets the genre set the first
  time each is opened after this rule was added, without the owner having to invoke anything by
  name project by project.
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
- **Agent Console (if `Claude/hooks/agent-console.html` exists in this project)**: this normally
  starts itself automatically via the `SessionStart` hook (`session-start-reminder.ps1`/`.sh`,
  see `SETUP-GUIDE.md` section 5b) before your first reply — don't ask permission, it's already
  handled. Use this fallback ONLY if that hook's context note didn't reach you (e.g. an older
  Claude Code build that doesn't support hook `additionalContext`): check whether a server is
  already correctly serving THIS project by requesting `http://127.0.0.1:8765/whoami` and
  comparing its `"project"` field to this project's own folder path. If it matches, nothing to
  do. If it doesn't match (or nothing answers), whatever's bound to port 8765 is stale — kill it
  first (Windows: find the PID via `netstat -ano | findstr :8765`, confirm it's a
  powershell/python process, then `Stop-Process -Id <pid> -Force`; macOS/Linux: `lsof -ti
  tcp:8765` piped the same way, then `kill -9`) — never kill a process that isn't one of our own
  servers — then start a fresh one in the background for this project (don't run it in the
  foreground, it would block this session — Windows: `Start-Process powershell -ArgumentList
  '-ExecutionPolicy Bypass -File "Claude\hooks\agent-console-server.ps1"' -WindowStyle Hidden`;
  macOS/Linux: `nohup python3 Claude/hooks/agent-console-server.py > /dev/null 2>&1 &`), then open
  `http://127.0.0.1:8765/` in the owner's default browser too (Windows: `Start-Process
  "http://127.0.0.1:8765/"`; macOS: `open http://127.0.0.1:8765/`; Linux: `xdg-open
  http://127.0.0.1:8765/`) — the owner wants it opened automatically every session, not just
  mentioned. Never ask permission first — just do it and say so.
