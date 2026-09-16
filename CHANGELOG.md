# Changelog

## v1.70.4 — Loud warning when launched from the wrong folder (silent hook failures, root cause of the last incident)

Root cause of the "logs stopped, console stopped animating" incident: the session had been
launched from the UEFN project's outer root instead of from inside `Content/`, where this kit's
scaffold actually lives. Every hook in `.claude/settings.json` builds its script path from
`CLAUDE_PROJECT_DIR`, so from the wrong folder every one of them points at a `Claude/hooks/` that
doesn't exist — they fail silently, one at a time, with nothing visibly wrong until you notice the
console is stale. The owner asked for a warning so this is caught immediately instead of
discovered later through cold logs.

**`session-start-reminder.ps1`/`.sh`** (fires on every fresh `claude` launch, matcher `"startup"`)
now checks, before anything else: if `Claude/hooks/agent-console.html` isn't found at
`CLAUDE_PROJECT_DIR` but IS found one level down at `Content/Claude/hooks/agent-console.html`,
that's this exact mistake — emit a loud, explicit `additionalContext` warning telling the owner,
in Claude's very first reply, to close the session and relaunch from inside `Content/`. This can't
silently fail the same way the thing it's warning about does: it only depends on `Test-Path`/
`[ -f ]` file checks, no server, no network call, so it still runs even when every other hook in
this file would be broken by the same wrong-folder mistake it's catching.

Tested directly (bash version): simulated both the wrong-folder case (warning fires, correct
`additionalContext` JSON) and the correct-folder case (no false positive, existing "console
started" message unaffected) — both confirmed via `bash -n` syntax check and running the script
with `CLAUDE_PROJECT_DIR` pointed at each location in turn.

## v1.70.3 — Migration/troubleshooting notes from real-world v1.70 upgrade feedback (root cause corrected)

Docs-only patch, no agent/console logic changed. Three things surfaced testing the v1.70 upgrade on
a real project:

1. **A stale `verse-reviewer` entry surfaced in the console after upgrading — root cause corrected.**
   First suspicion was a leftover `verse-reviewer.md` still installed in `~/.claude/agents/` (this
   kit only ever adds/updates agent files on copy, never deletes retired ones) — but the owner
   confirmed that file was already removed before this happened, so that wasn't it. The actual cause:
   `Claude/logs/agent-console.jsonl` **persists across restarts by design** (see
   `agent-console-server.py`'s own header comment — it's meant to keep activity history, not get
   wiped on every session). A `verse-reviewer` start event logged before the v1.69 rename, with no
   matching stop event, was still sitting in that file; the console's 45-minute stale-cleanup (see
   its own `STALE_ACTIVE_MS` check) surfaced and auto-cleared it exactly as designed — same as it
   would for any genuinely-abandoned entry. Nothing was broken and no fix was needed: it's expected,
   one-time noise from history predating the rename, not a recurring issue. **SETUP-GUIDE.md** Phase
   1 keeps its "delete agent files no longer on the roster before upgrading" step regardless — it's
   still good practice for the general case where an old file WOULD stay invokable — but it wasn't
   what caused this specific incident.
2. **`Content/Claude/docs/` vs `Claude/docs/` confusion.** Confirmed NOT a regression — this kit's
   scaffold has always lived inside the project's `Content/` folder by design (see SETUP-GUIDE
   section 1 and `project-template/CLAUDE.md`), so `Content/Claude/docs/STATUS.md` is the correct,
   intended path. A search from the wrong working directory (project root instead of `Content/`)
   will miss it — worth remembering when troubleshooting, not a path to fix.
3. **Two new troubleshooting entries added to SETUP-GUIDE.md's Agent Console section**: Claude
   Code's own permission prompt pausing before it starts the server / opens the console (this is
   Claude Code's standard tool-permission system reacting to a `Bash` command and/or a browser
   action, not something the kit or the console page itself triggers — approve it, or check
   `.claude/settings.json`'s `permissions` block if it keeps re-prompting every session instead of
   being allow-listed once), and a cosmetic mojibake in MCP log labels (`argumentsâ€¦` instead of
   `arguments…`, a UTF-8/Windows-1252 re-interpretation in `agent-console-mcp.ps1`'s truncation —
   harmless, the underlying event data is intact).

   *(Correction: an earlier draft of this note misattributed the permission prompt to a browser/OS
   security dialog — it's Claude Code's own permission system, corrected above.)*

## v1.70 — Bounded review cycles, fixed report contracts, a durable verdict log, cheaper models on structural-check agents

Follow-through on a "graph engineering" gap audit the owner asked for after sharing an article on
node/edge contracts, bounded cycles, and model tiering. The audit ran as six parallel evaluation
passes over the kit against those principles, then one synthesis pass; six things already matched
the vision (bounded-contract nodes, `.active-task` as a real data-contract edge, structural runtime
routing via CHIARO/AMBIGUO and PASS/REJECTED, independent verifiers on the review edges, no
unnecessary node isolation, pipeline-first topology). Seven trivial/low-effort gaps closed:

1. **Bounded REJECTED cycles.** The `intent-reviewer`/`compliance-reviewer` fix-and-resubmit loop
   had no attempt cap, unlike `coder`'s own compile-fix loop (capped at 5). Both reviewers and
   `coder.md` now share the same 5-consecutive-attempt cap: past that, stop, write the unresolved
   items to `Claude/docs/BUGS.md`, and ask the owner — exactly like a stuck compile error.
2. **Fixed report contract for closing a task.** `coder`'s hand-off to `planner-docs` was free
   prose ("a concise summary of what changed"). It's now a fixed shape: Task ID, Files/devices
   touched, both reviewers' verdicts with attempt numbers, second-brain interaction, one-line
   summary.
3. **Fixed output lines for `planner-docs`.** Both of its modes (opening a task, closing a task/
   end-of-session update) now report back in a fixed shape instead of freeform recap prose.
4. **Honesty fix in `compliance-reviewer`.** Two of its checks (naming/Outliner state, DemoDisplay
   stand positions) claimed "if MCP is available, verify live" — but its frontmatter tools are
   `Read, Grep, Glob` only, no MCP access at all. Reworded to check what's actually verifiable from
   files and explicitly say when a claim rests on `coder`'s report rather than independent
   confirmation, instead of implying a live check that can't happen.
5. **`.task-verdicts` (new durable log).** Both reviewers now append one line per verdict
   (`timestamp reviewer task-id verdict attempt-n`) to `Claude/docs/.task-verdicts`, append-only,
   same single-writer/independent-reader pattern as `.active-task`. `planner-docs` cross-checks it
   before marking a task Fatto, so "both reviewers PASSed" is independently checkable instead of
   resting on `coder`'s prose relay.
6. **Model tiering on structural-check agents.** `intent-gate` and `compliance-reviewer` moved from
   `sonnet` to `haiku` — both are bounded, checklist-shaped checks (ambiguity naming, mechanical
   rule conformance against a fixed list), not open-ended judgment calls, so a cheaper model fits
   the actual cost/latency lever the audit called out as underused. `intent-reviewer` (spec-adherence
   judgment) and `coder` stay on `sonnet`.

Deliberately not done this round, flagged instead for a separate decision: `codebase-auditor`'s
five audit lenses (structural, duplication, performance, maintainability, long-session risk) are a
genuine parallel fan-out/fan-in diamond currently run serially in prose — real opportunity, but
medium effort and an architecture change, proposed rather than applied unprompted. `release-gate`
and `planner-docs` model-tier changes were left alone too — lower-confidence, "pilot only" per the
audit's own caution, worth revisiting only after the two changes above are validated in practice.

No changes to `agent-console.html`'s JS logic — only its `KIT_VERSION` string was bumped to
`"v1.70"` to match; none of the fixes above touch the console's rendering or polling code, so the
full Playwright verification pass wasn't needed this round.

## v1.69 — Structural pipeline hardening: split the review gate, add intent-gate, a single MCP-tool source of truth, and a task-lock file; Agent Console miniflow rail

Follow-through on a flow audit the owner asked for after three separate incidents (v1.65-v1.67)
turned out to share one root cause: an agent judging its own readiness/correctness, or the same
instruction duplicated in prose across multiple files where it could quietly diverge. Four
structural changes, all confirmed by the owner, implemented together:

1. **`intent-gate` (new agent)** — runs BEFORE `coder` writes anything. Independently checks
   whether a task's acceptance criteria (and any owner-supplied base code) are concrete enough to
   implement without guessing, and returns CHIARO or AMBIGUO. Moves the "is this actually clear"
   judgment out of `coder`'s own Step 0.5 self-check and into an agent with no stake in getting to
   start the work.
2. **`verse-reviewer` split into `intent-reviewer` + `compliance-reviewer`.** `intent-reviewer`
   checks only spec adherence (the old check 1) and must PASS before `compliance-reviewer` — the
   eight mechanical checks (logger, naming, header, DemoDisplay, deprecated APIs, multiplayer
   authority, state machine, second-brain compliance) — is even invoked. This makes the ordering
   structural instead of a convention inside one agent's single-pass checklist: the incident this
   split responds to was a combined reviewer PASSing a guessed integration because spec adherence
   was one item among nine, not the precondition for the rest.
3. **`~/.claude/skills/mcp-tool-contracts/SKILL.md` (new skill)** — single source of truth for
   "which exact MCP tool does X," starting with the project-identity check
   (`ValkyrieToolset.VerseToolset.ListFiles`, not `AssetTools.find_assets`). `coder.md`,
   `qa-regression.md`, and `project-bootstrap.md` now reference this file by name instead of each
   restating the check in its own words — the exact pattern that let the v1.67 incident happen
   (the same generic instruction, worded slightly differently, in three places at once).
4. **`Claude/docs/.active-task` (new lightweight file)** — `coder` writes the task ID here when it
   flips a task to In corso; `intent-reviewer`/`compliance-reviewer` cross-check the ID `coder`
   reports against this file instead of trusting the report alone.

Agents removed: `verse-reviewer.md`. Agents added: `intent-gate.md`, `intent-reviewer.md`,
`compliance-reviewer.md`. Net: eleven → fourteen agent files installed (two new internal-helper
files were already excluded from that count; the public-facing roster goes from eleven to twelve
directly-invokable agents). Updated for the new gate names/order: `coder.md` (Step 0 writes
`.active-task`, new Step 0.4 invokes `intent-gate`, compliance gate now two sequential PASSes),
`planner-docs.md`, `release-gate.md`, `codebase-auditor.md`, `project-template/CLAUDE.md`,
`user-level-memory/CLAUDE.md` (new rule 13a), `docs-template/ROADMAP.md`, `SETUP-GUIDE.md`.

**Agent Console**: added a miniflow rail (the owner picked "V1" of three mockups presented) above
the orbit — a horizontal row of ring-progress nodes tracking where the CURRENT task sits in
intent-gate → coder → intent-reviewer → compliance-reviewer → planner-docs, derived purely from
the same `/log` event stream already driving the orbit (no new server plumbing required for the
rail itself). A stage shows a live mm:ss timer while active, and a small red "×N" badge if the
task was ever sent backward through it (detected as a regression: an earlier pipeline stage going
active again after a later one was already reached) — the one signal specifically meant to make it
visible, at a glance, when the review gates are actually catching something rather than rubber-
stamping. Added a best-effort `/active-task` endpoint to both `agent-console-server.py` and `.ps1`,
serving `Claude/docs/.active-task`'s content for the rail's task-ID label (the rail still works
fully without it). New node colors `indigo`/`lime` added (all ten previous slots were already
taken); `KIT_VERSION` bumped to v1.69; header text "ten agents"/"ten bots" → "twelve agents"/
"twelve bots". Verified: extracted `<script>` block passes `node --check`; scratch server + seeded
`agent-console.jsonl` + Playwright screenshot confirms the rail renders correctly mid-pipeline
(two stages done, one active with a live timer, task ID shown, zero `pageerror` events) before
cleanup.

## v1.68 — Added `codebase-auditor`: an independent, whole-codebase quality audit

Requested directly: an audit role independent from `coder` itself, styled as a senior developer
who just joined the team — understands architecture/data flow first, then hunts for structural
problems, duplicated code, performance bottlenecks, and maintainability risk, with a specific eye
on what only breaks after a long, uninterrupted play session (a growing collection never cleared,
event bindings stacking up round after round, per-player state never cleaned up on leave) rather
than what a short playtest would catch. Feeds findings to `planner-docs` to queue as ROADMAP
tasks instead of queuing them itself.

Added `user-level-agents/codebase-auditor.md` (model: sonnet). Deliberately distinct from what's
already in the kit: `verse-reviewer` gates one task's compliance right after `coder` finishes;
`qa-regression` hunts regressions from an actual play-session's logs; `project-bootstrap`'s A3
step is a one-time static pass before `SPEC.md` exists. `codebase-auditor` is the repeatable,
whole-codebase second opinion the owner runs on demand at any project stage — never writes code,
never touches devices or documentation files itself.

`planner-docs.md` updated: its task-opening procedure now explicitly covers a batch of findings
handed off from `codebase-auditor` (one ROADMAP task per finding worth tracking, small ones routed
to BUGS.md instead — `planner-docs` makes the final call, `codebase-auditor` only suggests).
`project-template/CLAUDE.md` and SETUP-GUIDE.md updated (ten agents now, install file count
eleven → twelve). Agent Console: new `codebase-auditor` node (🕵️), reusing `red` as a second
regular-node color (added a plain `.node[data-color="red"]` CSS rule alongside the existing
`.node.special[data-color="red"]` used by YOU — every other defined color was already assigned to
a different agent), `KIT_VERSION` bumped to v1.68, header text "nine agents"/"nine bots" → "ten
agents"/"ten bots". Verified with a scratch server + Playwright screenshot: zero `pageerror`
events, 10/10 idle, new node renders correctly on the shared ring.

## v1.67 — New uefn-lessons entry: use ValkyrieToolset.VerseToolset.ListFiles, not AssetTools.find_assets

Root-caused by the owner directly, on a case that had already needed a rollback: `coder.md`
only ever said, generically, "read/list a couple of Verse files or assets through the MCP tools"
for its project-identity safety check — it never named which toolset to use. `coder` picked
`AssetTools.find_assets` on `/Game`, the intuitive choice for "search for assets," without
knowing that in this kit's MCP/UEFN setup that path never surfaces the project's actual custom
content, even with the right project open — it fails silently (empty result, no error), which
reads exactly like "MCP has the wrong project open" and sends debugging in the wrong direction.
The owner verified directly that `ValkyrieToolset.VerseToolset.ListFiles` is the toolset that
actually works.

Added to `~/.claude/skills/uefn-lessons/SKILL.md` under "MCP / tooling quirks" — this is a
property of the MCP/UEFN configuration itself, not this one project, so it belongs in the shared
cross-project lessons file rather than per-project memory (same bar as every other entry there:
"would this help on a different island?"). Also fixed at the source in the three agents that ran
the same generic, toolset-unspecified safety check and would have hit the identical trap:
`coder.md`, `qa-regression.md`, and `project-bootstrap.md` all now name
`ValkyrieToolset.VerseToolset.ListFiles` explicitly and warn against `AssetTools.find_assets` for
this purpose, instead of leaving the toolset choice to intuition.

## v1.66 — No invention: coder must read/restate/ask, verse-reviewer must check the spec was followed

Reported directly, a concrete failure: the owner gave `coder` ready-made base code plus a spec to
integrate with an existing device; `coder` interpreted an unclear point instead of asking,
producing a wrong implementation that needed a rollback — and `verse-reviewer` PASSed it anyway,
because it was only checking rule mechanics (logger, naming, DemoDisplay), never whether the
implementation actually matched what was asked.

**`coder.md`** gains a new mandatory **Step 0.5 — Understand before you touch. Never invent,
never interpret.**: read an unfamiliar device's actual current implementation/config before
touching it (no more guessing from a device's name/type); treat a gap in the task's acceptance
criteria as a blocker to ask about, not a decision to make; when handed ready-made base code,
read it fully and restate the intended integration back to the owner in concrete terms before
editing anything; treat spec ambiguity with the same weight as an unresolvable compile error —
never proceed on a guess "to keep moving."

**`verse-reviewer.md`** gains a new check 1, **Spec adherence — no invention**, checked first,
before every mechanical rule: compares the implementation against the task's acceptance criteria
line by line, and treats a silently-interpreted ambiguity as a REJECTED finding even when the
resulting code is otherwise clean and every other rule passes — compliant code built on a guess
is still wrong. Its "Why this agent exists" section now documents this failure mode directly, and
its description/frontmatter lead with spec adherence instead of burying it among the mechanical
checks.

## v1.65 — Templates physically separated from live project data, safe to bulk-update

Asked directly: "can I overwrite the whole project folder to update everything, without losing
data?" The honest answer before this release was no — `project-template/Claude/docs/` held the
SPEC/STATUS/ROADMAP/BUGS/RETENTION-NOTES/RELEASE-READINESS templates at the *same path* a real
project's live, populated versions of those files live at, so re-copying `project-template/` over
an existing project (to pick up hook/agent fixes from a newer kit version) would have silently
wiped a project's entire tracked history — every task, every log entry, every bug.

Fixed by construction, not by a warning to remember: renamed `project-template/Claude/docs/` to
**`Claude/docs-template/`** (added its own `README.md` explaining it's a seed, never live data).
`Claude/SETUP-INSTRUCTIONS.md` gained step 3b: seed a brand-new project's real `Claude/docs/` from
`docs-template/`, but only if `Claude/docs/` doesn't already exist yet — every step in that file is
now explicitly documented as safe to re-run after an update. `project-template/CLAUDE.md` got a
header comment flagging it as a seed file too (it becomes the project's own live `CLAUDE.md`,
identity and conventions filled in, the first time Phase 2 runs).

Added a new **"Updating an existing project to a new kit version"** section in SETUP-GUIDE.md with
the exact two lists — update-safe (`Claude/hooks/`, `Claude/reference/`,
`Claude/SETUP-INSTRUCTIONS.md`, `Claude/docs-template/`, `.claude/settings.json`) vs. never-bulk-
copy (`Claude/docs/`, project-root `CLAUDE.md`, `Claude/logs/`, per-agent persistent memory) — plus
copy commands (`rsync`/`robocopy`) for the safe subset. This replaces answering "what do I update"
ad hoc after every release with a standing, mechanical procedure.

## v1.64 — Plan-first workflow: no code without a tracked, ID'd task

Requested directly, after a from-scratch project surfaced a bigger structural gap than any single
bug: nothing in the kit stopped `coder` from writing code before specs/status were updated, and
reopening a project after time away didn't make "what's in progress / what's next / what's done"
immediately obvious. This release restructures the documentation flow around one rule
(`~/.claude/CLAUDE.md`, new **rule 13**): every task is a row in `Claude/docs/ROADMAP.md`'s
`Tasks` table (ID, Feature, Status, Acceptance criteria, Priority) before any code gets written
against it, and it's only marked **Fatto** after `verse-reviewer` PASSes it.

**Orchestrator decision (asked for explicitly, decided against a new agent):** the alternative
considered was a dedicated `orchestrator` subagent enforcing Request → task → code → review →
close. Rejected: a Task-tool subagent is a stateless dispatch, not a supervisor of the main
session's own tool-call sequence — it can't actually intercept "coder is about to start without a
task" from outside. The main Claude Code session already *is* the orchestrator; what it needed
was an unambiguous rule loaded into every session (rule 13) plus `planner-docs` actually enforcing
it as gatekeeper — not one more hand-off hop, which would have worked against this same release's
other goal of cutting down on loops.

**Templates rewritten**: `ROADMAP.md` now has a `Tasks` table plus a "Current MVP / release
target" line `release-gate` reads. `STATUS.md` now opens with a **Current state** block (In
progress / Planned next / Done so far / Recommended next step) that's replaced on every update,
sitting above the existing append-only dated log.

**Agents updated**: `coder` gets a mandatory Step 0 plan-first gate (find the task ID or stop and
ask; flip Status to In corso itself — the one narrow exception to not touching ROADMAP.md — never
Fatto) and now closes a task by handing off to `planner-docs` after a `verse-reviewer` PASS,
instead of just reporting done. `coder-prep` explicitly never touches these files at all — the
gate and the closing hand-off are `coder`'s job once per wave. `planner-docs` is rewritten as the
two-mode gatekeeper (opening a task / closing one) instead of an end-of-session-only recap agent.
`verse-reviewer` now expects and reports a task ID for traceability. `release-gate` gets an
explicit ROADMAP-completeness criterion (every current-release task Fatto, and Fatto tasks
actually backed by a recorded PASS). `project-bootstrap` (both branches) now seeds real `T-<3
digits>` tasks with acceptance criteria instead of a prose "planned features" list or a vague
"next step" line.

**Skills reviewed against the new flow**: all sixteen (`uefn-lessons`, `verse-patterns`,
`uefn-device-gotchas`, `performance-uefn-checklist`, `discover-retention`, `second-brain-query`,
`token-aware-coding`, `brand-collections-uefn`, the eight `fortnite-*`) — none contradicted
plan-first (none of them touch ROADMAP/STATUS or tell an agent to start coding directly), so only
one needed a change: `token-aware-coding` gained a line about grepping one task row instead of
reading the whole ROADMAP.md once it grows across releases. Deliberately did NOT add a padding
entry to `uefn-lessons` just to check a box — this release's gap was process, not a Verse/UEFN/MCP
gotcha, and that skill's own stated bar ("would this help on a different island?") doesn't apply
to something documented directly in rule 13 instead.

`project-template/CLAUDE.md`'s per-project rules list and `SETUP-GUIDE.md` (new section **2b**,
with a full worked example of a feature request end to end) updated to match.

## v1.63 — Added `verse-reviewer`, a compliance gate before a task counts as done

Reported directly by the owner on a from-scratch project: devices shipped without the mandatory
logger, devices with class/configuration problems because the second brain was never consulted,
and reusable patterns that only ever reached a project's own memory instead of the shared vault.
Nothing in the kit caught this — `qa-regression` looks for runtime/gameplay regressions at
playtest, not rule conformance right after a task; `release-gate` looks at whole-project
readiness before a release, not one task right after it's written.

Added `user-level-agents/verse-reviewer.md` (model: sonnet) — the functional-analyst role: never
writes code or touches devices, only checks `coder`'s own output against this kit's mandatory
rules (logger, naming/organization, `DemoDisplay` presence and accuracy, deprecated APIs,
multiplayer authority, state machine) and, when the second brain is configured, cross-checks in
query mode whether a reusable pattern actually reached the vault instead of only living in project
memory. Returns PASS or an itemized REJECTED list; `coder` fixes and resubmits.

`coder.md` updated with a mandatory compliance gate: before reporting any task done, invoke
`verse-reviewer` and only report "done" after a PASS — for a `coder-prep` wave, this runs once for
the whole wave, same reasoning as the existing single-writer second-brain handoff. This keeps the
kit's "one agent owns the task" rule intact: `coder` is still sole owner of implementation and of
deciding when work is finished, it just no longer grades its own compliance.

Also updated: `project-template/CLAUDE.md`'s per-project agent rules list; SETUP-GUIDE.md (agent
count seven→eight→nine across this and the prior two releases, install file count ten→eleven,
section 2's roster); and the Agent Console — new `verse-reviewer` node (🛡️, a new `yellow`
regular-node color variant added to CSS since every other defined color was already assigned),
`KIT_VERSION` bumped to v1.63, header text "eight agents" → "nine agents"/"nine bots". Verified
with a scratch server + Playwright screenshot: zero `pageerror` events, 9/9 idle, new node
renders correctly on the shared ring.

## v1.62 — `fortnite-title-description` rebuilt into a full publishing package

Rebuilt `fortnite-title-description` per direct spec from the owner: it now produces the whole
Discover publishing package in one pass — Title (max 40 characters), Description (max 500
characters), one Main genre proposal, 4 Discover tags, and 3 how-to-play instruction lines (max
150 characters each) — everything in English, with explicit instructions to actually count
characters per field (and show the count, e.g. "37/40") rather than estimate or truncate
mid-sentence to fit. Added a second, distinct deliverable — the **community blog presentation**
(an extended description and a short one), aimed explicitly at getting readers to go play, in
whatever language the owner asks for (the five publishing fields stay English regardless).
Updated `growth-manager.md` and `SETUP-GUIDE.md` section 3e's description of this skill to match
the new scope.

## v1.61 — Agent Console updated for growth-manager

Caught by the owner asking directly ("hai aggiornato anche la console?") after v1.59 added the
`growth-manager` agent without touching `agent-console.html` — it was still showing the old
seven-agent roster. Added `growth-manager` to the `AGENTS` array (📈, orange — the one color slot
already defined in CSS but unused by any agent), bumped `KIT_VERSION` to v1.61, and updated the
static "seven agents"/"seven bots" header text to eight. Nothing else needed changing: node
layout, angle spacing, and the legend/footer counts all derive from `AGENTS.length` dynamically
(confirmed in code, no hardcoded "7" anywhere else), so the new node slotted in on the shared ring
automatically. Verified with a scratch server + Playwright screenshot against a throwaway copy of
`project-template` — zero `pageerror` events, new node renders correctly at 8/8 idle.

## v1.60 — Confirmed thumbnails now get installed into the project (Resources/ + keyArt)

Requested directly: once a thumbnail from `fortnite-thumbnail-pro` is confirmed, it needs to
land in the project itself, not just be handed over as an image. Added
`references/install-thumbnail.md` to `fortnite-thumbnail-pro` with the exact procedure: create
`Resources/` at the project root if missing (the root is the folder that *contains* `Content/`,
named per `CLAUDE.md`'s "Project identity" — never the current folder, always literally
`Content`), save the confirmed file there, and update the `"keyArt"` key in
`<ProjectName>.uefnproject` (also at the project root) to point at it, e.g.
`"keyArt": "Resources/Thumbnail.png"` — editing only that key, not reformatting the rest of the
JSON. `growth-manager` (v1.59) now owns actually doing this when a thumbnail is confirmed
through it. This is a deliberate, narrow exception to the kit's standing "no agent touches files
outside `Content/`" rule, called out explicitly both in `growth-manager.md` and in
`project-template/CLAUDE.md`'s per-project rules list, scoped to exactly `Resources/` and the
`keyArt` key — nothing else at the project root.

## v1.59 — Added `growth-manager`, a dedicated agent for the eight marketing skills

v1.58 added the eight `fortnite-*` growth/marketing skills but left them relying entirely on
Claude Code's own description-based matching, with no agent owning them — inconsistent with
every other skill-cluster in the kit (`coder` reads `verse-patterns`, `project-bootstrap` reads
`discover-retention`/`brand-collections-uefn`, etc.). Added `user-level-agents/growth-manager.md`
(model: sonnet) as the dedicated owner: a single entry point the owner can talk to in plain
language, which routes to the matching `fortnite-*` skill(s) — one for most requests, several in
sequence for a full launch push — instead of the owner needing to know or name any of the eight
skills. It explicitly stays out of Verse/device work (that's `coder`) and doesn't write
`STATUS.md`/`ROADMAP.md`/`BUGS.md` itself (that's `planner-docs`) — it summarizes for
`planner-docs` instead when something it produced should be recorded there. SETUP-GUIDE.md
updated: agent count (seven → eight agents, section 2), Phase 1 install file count (nine → ten,
section 5), and section 3e rewritten to describe `growth-manager` as the normal way to reach
these skills, with direct skill-matching/naming kept as a fallback.

## v1.58 — Added eight growth/marketing skills (analytics, competitors, launch, retention, trailer, thumbnail, title/description, update writer)

The kit so far only covered building the island (`coder`, `qa-regression`, and the dev-side
`user-level-skills/`). Added eight new skills under `user-level-skills/fortnite-*` covering the
other half of running a map: `fortnite-analytics-coach` (Creator Portal + public-tracker
analysis), `fortnite-competitor-analyzer` (genre/competitor research), `fortnite-marketing-launch`
(launch/growth plans), `fortnite-retention-gamedesign` (session-length/retention game design),
`fortnite-social-trailer` (trailer scripts, TikTok/Shorts hooks), `fortnite-thumbnail-pro`
(high-CTR thumbnail concepts + prompts), `fortnite-title-description` (Discover-optimized
titles/descriptions), and `fortnite-update-writer` (patch notes/announcements).

Unlike the dev-side skills, none of these are read by a fixed step in an agent — there's no
"marketing agent" in this kit to dispatch them from. They rely on Claude Code's own
description-based skill selection instead (same mechanism as `discover-retention` and
`brand-collections-uefn`), so SETUP-GUIDE.md's new section 3e is explicit about how to fall back
to naming the skill directly ("use the fortnite-thumbnail-pro skill") if a request doesn't get
matched automatically. Install step in Phase 1 (section 5) updated to include all eight folders.

## v1.57 — Fixed the footer line disagreeing with the "Agents" legend box

Found immediately after checking the new v1.56 version tag actually worked — it did (confirmed
"v1.56" in the screenshot), but the footer sentence at the bottom of the ring ("1 working, 6
idle...") and the "Agents" legend box at the top ("working 0, broken 1") disagreed about the
exact same agent at the exact same moment.

- **Root cause**: the footer line had its own much older, separate counting logic
  (`activeCount = active.length`) left over from before the broken/waiting distinction existed —
  it only ever knew "in the active stack" vs. "not," with no idea an entry could be flagged
  broken or waiting. The legend box's newer four-state logic was never wired back into it.
- **Fix**: extracted the legend's counting logic into one shared `computeAgentCounts()`, now used
  by both the legend box and the footer line. The footer's wording adapts too — it stays the
  familiar "N working, M idle" when nothing's flagged, and adds "broken"/"waiting" segments only
  when their count is above zero, so it doesn't get more cluttered than it needs to be on a
  normal day.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  20-minute-old `coder` call (well past the 15-minute broken threshold) now shows "0 working, 1
  broken, 6 idle" in BOTH the footer and the legend box.
- `KIT_VERSION` bumped to v1.57.

## v1.56 — Version tag next to the title, to kill a whole class of "did the fix actually apply" confusion

Prompted directly by the last two rounds of troubleshooting in this changelog: a real fix (v1.55)
looked like it hadn't worked, and the actual cause was almost certainly a browser tab left open
from before the file was replaced — this is a single-page app, so a tab doesn't notice its own
HTML file changing on disk until it's reloaded.

- **New `KIT_VERSION` constant** near the top of the page's script, rendered as a small tag right
  after the title (e.g. "v1.56"). Checking it is now the first troubleshooting step: if it still
  shows an old version after replacing the file, the fix is a hard refresh (Ctrl/Cmd+Shift+R), not
  more debugging of the actual feature.
- **This constant must be bumped on every release that touches `agent-console.html`**, matching
  `CHANGELOG.md`'s top heading — said plainly in a comment right above the constant itself as a
  standing reminder, since the whole point only holds if it never drifts out of sync.
- `SETUP-GUIDE.md` updated with a matching troubleshooting note, right at the top of the Agent
  Console section where it'll actually get read before someone goes looking for a phantom bug.
- Verified with the same headless-browser screenshot test as previous releases: confirms the tag
  renders next to the title with no layout shift and no JS errors.

## v1.55 — Auto-clear thresholds were too aggressive for real long-running background work

Found immediately after v1.54, from another live report on the same pre-fix session: the console
showed ALL agents idle while Claude Code's own session view confirmed two real `coder` calls
genuinely still running (9m49s and 25m8s, both climbing) — worse than v1.54's "broken"
misattribution, since now it looked like nothing was happening at all. Root cause: the hard
auto-clear (`STALE_ACTIVE_MS`, 20 minutes) force-removed both entries from tracking entirely, and
the log showed "⚠ auto-cleared 'coder' — no stop event arrived after 20 min" twice at the same
timestamp. Both thresholds were tuned for an older, more conservative assumption about how long a
subagent call normally runs — one this kit's own new parallel-work features (`coder-prep`,
`second-brain-trainer`'s waves, background `coder` calls) have since made outdated:

- **`STALE_ACTIVE_MS` raised from 20 to 45 minutes.** Still a real safety net for a truly
  orphaned entry (a lost `SubagentStop`), just far less likely to fire on legitimate long
  background work.
- **`LED_SOFT_WARN_MS` raised from 6 to 15 minutes**, same reasoning — 6 minutes was flagging
  completely normal memory-heavy reads as "broken" far too eagerly.
- **Real bug fixed in the auto-clear loop itself**: it force-marked a card idle unconditionally,
  without checking whether another concurrent call to the same agent id (see v1.54's "×N" badge)
  was still legitimately active — so clearing one stale sibling could wrongly hide a fresh,
  genuinely-running one. Now uses the same "only if no sibling remains" guard the normal
  stop-event path already used.
- Auto-clear log message updated to say plainly that it does NOT necessarily mean anything broke.
- Verified with the same headless-browser screenshot test as previous releases, this time
  replaying the exact reported timestamps (one `coder` call 25m8s old, one 9m49s old): both now
  correctly show "working ×2" instead of being cleared to idle.

## v1.54 — Fixed a real status-misattribution bug for concurrent same-agent calls, added a "×N" concurrency badge

Found from a live report: the console showed "1 broken" while two real `coder` calls were
running at once (one ~14 minutes old in the background, one fresh) — and the owner couldn't tell
who the second one even was, since the ring only ever showed one `coder` card.

- **Real bug fixed**: `refreshLeds()` and `updateLegendCounts()` both used `Array.find()` to look
  up a named agent's current activity in the `active` stack — which returns the FIRST matching
  entry, i.e. the OLDEST of any concurrent same-id calls. So the card's "broken" (stuck/overdue)
  check was silently keyed off however long the oldest concurrent instance had been running, even
  while a much fresher call to the same agent was the one actually active — exactly what produced
  "1 broken" while the fresh `coder` call was working normally. New `latestEntryFor()` uses the
  MOST RECENT matching entry instead, so the card reflects what's actually current.
- **New "×N" concurrency badge**, via `getConcurrency()`: when 2+ concurrent calls to the same
  named agent share one card (unavoidable — Claude Code gives no per-call id to split them), the
  card now visibly says so instead of the second (or third) instance being entirely invisible.
- **Documented, not fixed (can't be, with the data available)**: which exact stop event pairs
  with which concurrent start is inherently ambiguous without a real call-stack id — the console
  assumes first-started/first-finished (FIFO), a reasonable default, not a guarantee.
  `SETUP-GUIDE.md` now says this plainly, alongside a direct answer to "should broken agents get
  killed": the console is read-only telemetry, it has no way to stop/cancel/kill anything — a
  stuck call has to be handled at the Claude Code session level itself.
- Verified with the same headless-browser screenshot test as previous releases: two synthetic
  concurrent `coder` starts (one 14 minutes old, one fresh) confirm "working 1, broken 0" (was
  "broken 1" before the fix) and the "×2" badge on the shared card.

## v1.53 — Generic "fork" clones now get a "<parent> clone" label and disappear when done

Prompted by the owner spotting a plain "fork" node in the console after `coder` spawned a
background clone, and asking for two things: make it obviously coder's own child, and have it
leave the ring once it's finished instead of sitting there idle forever.

- **New `KNOWN_IDS`/`ephemeralIds` tracking.** The fixed roster (seven bots, Vault, YOU, MCP) is
  captured once at init; anything NOT in it — a generic `subagent_type: "fork"` dispatch being the
  common case — is now treated as ephemeral.
- **`ensureNode()` now takes the parent id** (whoever was on top of the active stack when the
  fork started — the same heuristic `pulseLink()` already used for handoff pulses). An ephemeral
  node gets a 🧬 icon, the parent's own color, a "\<parent name\> clone" label instead of the raw
  `"fork"` string, and its spoke now points at the parent instead of at the hub.
- **New `removeEphemeralNode()`**, called from `setIdle()` instead of the normal idle-in-place
  path whenever the node is ephemeral: removes the DOM node, its spoke, and every tracking
  structure it was registered in (`nodeEls`, `spokeEls`, `counts`, `BLURBS`,
  `SPOKE_TARGET_OVERRIDE`, `ALL_NODES`), then re-runs `recomputeAngles()` so the ring closes the
  gap immediately instead of leaving a dead idle slot.
- Known remaining limitation, unchanged: `subagent_type` is still the only id Claude Code reports
  for a fork, so two genuinely concurrent forks under the same parent still share one node — this
  matters far less now that a single fork (the common case) behaves correctly and cleans up after
  itself.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  `coder` → `fork` start/stop sequence confirms the "coder clone" label, parent-colored spoke, and
  full removal from the ring on stop, with zero JS errors.

## v1.52 — `coder` can now parallelize across independent devices/areas, via a new `coder-prep` helper

Prompted by the owner asking why `coder` stayed one-device-at-a-time even on tasks that obviously
split into unrelated pieces. The real reason: UEFN exposes exactly one MCP server per editor,
serving whichever project is open, and a Verse compile is a whole-project build, not an isolated
per-file one — two concurrent device placements or compiles wouldn't fail safely, they'd race
against that one shared live editor state. That part was never going to be safe to parallelize.
But most of `coder`'s actual time/cost per device is the part BEFORE any MCP call — reading
context, writing the Verse itself — and for genuinely independent areas, that part has nothing
shared to race against:

- **New agent**: `user-level-agents/coder-prep.md` — `model: sonnet` (real implementation work,
  not a lightweight scan, so no model downgrade here unlike `second-brain-scout`). Writes the
  actual Verse for ONE area, following every one of `coder`'s own conventions, but never touches
  MCP and never compiles — it reports back exactly what needs placing/configuring so `coder` can
  apply it afterward.
- **`coder.md`** gained a new "Splitting work across genuinely independent devices/areas" section:
  when a task splits cleanly, dispatch one `coder-prep` per area in parallel (capped ~6-8 per
  wave, same as `second-brain-trainer`), then apply every area's plan yourself, serially — MCP
  placement, `DemoDisplay`, compile-fix loop, one area at a time. Second-brain handoffs from the
  wave get combined into a single `second-brain-librarian` call at the end, same single-writer
  discipline as `second-brain-trainer` already uses. Skip all of this for a task that isn't
  genuinely independent-by-area, or one too small to be worth splitting.
- Nine agent files to install now, not eight — `SETUP-GUIDE.md` updated (install step, agent
  list, and a new explainer paragraph in section 3c). `coder-prep` doesn't get its own Agent
  Console node any more than `second-brain-scout` does — the console's existing fallback-node
  logic for an unrecognized `agent_type` already covers it.

## v1.51 — Documented the community `obsidian-skills` Claude Code plugin as an optional pairing

Not a kit feature — a documentation-only addition, at the owner's request, pointing to a
community Claude Code plugin marketplace worth knowing about if you spend time in the second-brain
vault yourself:

- **`second-brain-template/README.md`**: new step 5 in "Set up the vault (once)" — installing the
  `obsidian-skills` marketplace (by kepano, an Obsidian team member) teaches Claude Code better
  Obsidian-specific conventions (formatting, linking, front matter) on top of whatever
  `second-brain-librarian` already does. Explicitly marked as independent of this kit — not
  shipped or maintained by it, just a good pairing.
- **`SETUP-GUIDE.md`**, Phase 1 step 7 (connect an Obsidian second brain): same note added as a
  final optional bullet, with the same two commands:
  ```
  /plugin marketplace add kepano/obsidian-skills
  /plugin install obsidian@obsidian-skills
  ```

## v1.50 — Project name in the Agents stat box, and a real hub-LED gap fixed

Requested addition plus a real logic gap the owner spotted from a live screenshot (MCP Server node
glowing "working" while the Chief of Staff hub sat grey):

- **Project name in the "Agents" stat box.** A new line, "PROJECT: <name>", now sits above the
  agent-count/legend rows in that box — same project name `pollWhoami()` already fetches for the
  Activity Log panel's header, just also shown here since that box is more prominent.
- **Chief of Staff hub LED gap fixed.** The hub's own LED used to go green ONLY when a subagent
  was in the `active` stack (`active.length > 0`) — so when the main session did something
  directly without delegating to a subagent (e.g. calling the UEFN MCP server itself), the hub
  stayed grey/idle even though it was genuinely working, which is exactly what a live screenshot
  showed (MCP Server node glowing "working", hub LED grey). The hub LED now also turns green
  whenever the main session itself is active, via the same `/session` polling that already drives
  the YOU node's LED (`sessionActive`, kept in sync by `pollSession()`, consumed by
  `refreshLeds()`); `pollSession()` now also calls `refreshLeds()` immediately instead of waiting
  up to a second for the next tick.
- The YOU node's own LED was already correctly session-driven (green while the main session is
  actively working, grey once it's yielded back to you) — audited per the owner's request, no
  change needed there.
- Verified with the same headless-browser screenshot test as previous releases, this time seeding
  a synthetic `agent-console-session.json` with `active:true` and zero running subagents to
  confirm both YOU and the hub go green together in that specific case.

## v1.49 — New `second-brain-scout` helper: cheaper-model clones for second-brain-trainer's parallel analysis

Prompted by a real "Claude usage" report showing 38% of usage coming from unnamed/"fork" subagent
dispatches — almost certainly `second-brain-trainer`'s own parallel analysis clones, which
previously ran as generic unnamed Task dispatches (inheriting the session's default model, e.g.
Sonnet) with no way to configure them more cheaply, since a model override in this kit's design
only applies to a NAMED custom agent (one with its own `model:` frontmatter field), not a
generic/unnamed clone:

- **New agent**: `user-level-agents/second-brain-scout.md` — `model: haiku`. Analyzes exactly one
  project area, read-only, no vault access at all, and reports candidate reusable patterns in the
  same format the old generic clones used. You never invoke it yourself.
- **`second-brain-trainer` Step 2 updated** to dispatch `second-brain-scout` (one per area, per
  wave, still genuinely parallel) instead of a generic/unnamed clone — same behavior and output
  format, cheaper model for a step that's read-only and low-judgment by design.
- Eight agent files to install now, not seven (`SETUP-GUIDE.md` updated) — `second-brain-scout`
  doesn't count toward the kit's "seven agents" branding since it only ever runs as
  `second-brain-trainer`'s own dispatch, never on its own; it doesn't get an Agent Console node of
  its own either — the console's existing fallback-node logic for an unrecognized `agent_type`
  already covers it with no console changes needed.
- Also recommended to the owner, not kit changes: `/compact` mid-task and `/clear` between
  unrelated tasks (65% of usage came from >150k-context sessions), and disabling the `unreal-mcp`
  server when not actively playtesting (39% of usage) — MCP tool results stay in context for the
  rest of the session.

## v1.48 — Reverted the second ring: Obsidian Vault, YOU and MCP Server now share one ring with the bots

The v1.45 "second, further-out ring" for Obsidian Vault/YOU/MCP Server didn't land well visually
— reverted. All ten nodes (seven bots + the three special ones) now orbit on a single shared
ring at one radius, with one dashed guide circle instead of two:

- `OUTER_RING_IDS` and the separate outer-radius/second-guide-circle logic are gone from
  `layoutOrbit()`; every node uses the same `radius` (`halfDim * 0.72`, slightly larger than the
  old inner-ring radius since it's now the only ring).
- `recomputeAngles()` still special-cases Obsidian Vault's own angle — it's placed at the angular
  midpoint between `second-brain-librarian` and `second-brain-trainer` (the v1.47 fix, kept),
  it's just that midpoint is now a slot on the *one* ring instead of a separate outer one. Every
  other node (the six remaining bots, YOU, MCP Server) is spaced evenly around the rest of the
  circle in array order, and the Vault simply slots into the gap between its two second-brain
  neighbors without disturbing anyone else.
- Verified with the same headless-browser screenshot test used for the last few releases —
  confirms all ten nodes on one ring, Vault still between its two second-brain neighbors.

## v1.47 — Obsidian Vault repositioned between its two second-brain agents

Small but requested fix to `recomputeAngles()`: the outer ring used to space Obsidian Vault, YOU,
and MCP Server evenly by array order alone, which happened to land the Vault right next to
`project-bootstrap` — visually unrelated to it. The Vault is now placed at the angular midpoint
between `second-brain-librarian` and `second-brain-trainer` on the inner ring (the two agents it
actually draws spokes to and reacts to), computed via the shortest arc between their two angles;
YOU and MCP Server are then spaced evenly around the rest of the circle relative to that fixed
Vault angle, so nothing else shifts if more inner-ring agents are ever added. Verified with the
same headless-browser screenshot test used for the last two releases.

## v1.46 — Agent Console header/layout compaction: merged title row, new agent status legend, matched panel heights

Requested space-saving pass on `agent-console.html`'s header and layout, live-tested with the same
headless-browser + synthetic-event pattern used for v1.45 before packaging:

- **Merged header row.** The tagline ("seven agents. one chief of staff...") and the connection
  status line used to sit stacked below the title as two extra rows; they now sit to the right of
  the title on the same row (`.termlines` is a single flex row, `.termlines-side` stacks them
  right-aligned) — recovers two lines of vertical space.
- **Title changed to all-caps**: "DREAM BOT TEAM AGENT CONSOLE FOR UEFN" (title bar and `<title>`
  tag both updated; the blinking `_` cursor is kept).
- **Removed the decorative `.termbar`** (the three macOS-style red/yellow/green window-chrome
  dots) — recovers a third line. Those exact three colors aren't wasted: they're reused as the
  semantic colors in the new legend below (plus grey for idle).
- **Tokens stat box narrowed** (`.stat.compact`, `flex:0.65`) — it's a single number, it didn't
  need as much room as the other stat boxes.
- **New "Agents" stat box.** Shows the total agent count (7) plus a live idle/working/broken/
  waiting breakdown with a colored-dot legend (grey=idle, green=working, red=broken,
  yellow=waiting), computed by a new `updateLegendCounts()` call inside `refreshLeds()` so the
  numbers and the individual node LEDs can never disagree.
- **Four-state LED model.** The node LED heuristic used to have three states (idle / active /
  waiting, with "waiting" rendered red for both "blocked on a delegated child" and "stuck /
  running suspiciously long"). Those two very different meanings are now split: **yellow** =
  blocked waiting on a delegated child (not top of the active stack), **red** = the top-of-stack
  entry itself has been running past `LED_SOFT_WARN_MS` (likely stuck/erroring — "broken"). Green
  (working) and grey (idle) are unchanged.
- **Activity Log panel height now matches the orbit-ring panel.** `.main-grid` switched from
  `align-items:start` to `align-items:stretch`, and `.orbit-wrap` centers its ring vertically in
  whatever extra room that leaves — previously the two side-by-side panels could end up visibly
  different heights.

## v1.45 — Agent Console visual pass: second ring, vault "contested" effect, bot rays, regression missiles, fountains, project name

A full set of requested visual additions to `agent-console.html`, live-tested with a headless
browser (screenshots + a synthetic event stream) before packaging:

- **Second virtual ring.** Obsidian Vault, YOU, and MCP Server now orbit on a further-out ring
  (`OUTER_RING_IDS`), visually separate from the seven working-bot agents on the inner ring — a
  faint dashed guide circle marks each ring. `recomputeAngles()` now spaces the two rings
  independently so a node added to one never crowds the other.
- **Obsidian Vault "connected to both brains."** The vault now draws two spokes — one to
  `second-brain-librarian` (purple, existing), one to `second-brain-trainer` (new, teal) — and
  pulses (`vaultPulse`) whenever either is active, with a stronger oscillating "tug" animation
  (`.contested`, `vaultContested`) when BOTH are active at once, as if pulled from two directions.
  A floating "💭 Thinking" indicator with an animated ellipsis shows above it while active.
- **Bot ray bursts.** Every inner-ring agent gets a small, colored ripple-ring burst around its
  own icon while active (`.node-ray`) — the same idea as the hub's own ripple, scaled down and
  colored per-agent, so a working bot visibly radiates too, just far less dramatically.
- **Regression missiles.** When a `qa-regression` stop event's own description matches
  `/regression/i` (optionally with a count, e.g. "3 regressions" → up to 4 staggered launches), a
  small 🚀 flies from `qa-regression` to `coder` along an arced path and ends in a mini particle
  explosion (`spawnExplosion`) on arrival.
- **Fountains.** Obsidian Vault spawns a small stream of 💎 while active; `planner-docs` spawns a
  small stream of 📄 while active — both plain arc-and-fade particles (`spawnFountainParticle`),
  keyed by node id so start/stop is idempotent.
- **Project name in the activity log panel.** The right-hand panel's title now shows "📁
  <project folder name>" (from `/whoami`'s `project` field, already polled for the Session-running
  timer) so it's obvious at a glance which project's console you're looking at.
- Footer explanation text rewritten to document all of the above.

## v1.44 — Fixed "Session running for" showing hours/days right after a genuine server restart

Real bug, found from a live report ("the server isn't being restarted... it's been up 5 hours!!")
that turned out to be a display problem, not a restart problem — the v1.40 kill+restart mechanism
was working correctly, but the console's own "Session running for" stat made it look otherwise:

- **Root cause**: that stat was computed client-side from the OLDEST line in
  `Claude/logs/agent-console.jsonl`. That file deliberately persists across server
  restarts/sessions (it's the activity history — "delete it for a clean slate" is documented,
  intentional behavior). So once you'd used the kit across a few sessions, the stat kept showing
  hours/days of elapsed time no matter how recently the server had actually restarted — it was
  reading accumulated history, not server uptime.
- **Fix**: `agent-console-server.ps1`/`.py` now record their own real process-start time at
  launch and serve it from `/whoami` as a new `started_at` field (alongside the existing
  `project` field from v1.40). The console page polls `/whoami` every 5 seconds and prefers that
  real start time for "Session running for" — it now genuinely resets to zero the moment the
  server restarts, and also self-corrects mid-session if the server underneath the open tab gets
  restarted (project switch, kit update). Falls back to the old earliest-log-line behavior only
  against a server build that predates the `started_at` field, so an old server + new page combo
  degrades gracefully instead of showing nothing.
- `agent-console.jsonl`'s own persistence is untouched — this only changes what feeds the timer
  stat, not the activity log/history.
- SETUP-GUIDE.md's "Session timer" paragraph rewritten, plus a new troubleshooting entry for
  exactly this symptom.

## v1.43 — Console auto-opens in the browser; new brand-collections-uefn skill; console diagnostics confirmed clean

Three things landed together, per the owner's request to batch them into one update after two
rounds of diagnostics:

- **Console diagnostics: no code bugs found, only documentation gaps.** A live payload capture
  confirmed the console's "fork" background-agent dispatch (`● fork(...)` in the transcript) was
  already correctly tracked all along — it's the same `Agent`/`Task` tool the console already
  listens for, just with `subagent_type: "fork"`, not a different tool name needing a matcher
  fix. The only real finding: every fork shares one generic fallback node (🤖) instead of one per
  task, because the fallback keys off `subagent_type`, identical for every fork regardless of what
  each one does — a deliberate limitation of the generic-node mechanism, not a bug. Documented in
  SETUP-GUIDE.md's troubleshooting section instead of leaving it implying a matcher fix was
  needed. Likewise, the v1.40 stale-cross-project-server fix was independently re-confirmed
  working exactly as designed (kill+restart via `/whoami` happens automatically, before Claude's
  first reply) — the only gap was that nothing opened a browser tab, which is the next item.
- **The console now opens itself in your default browser, automatically, every session** — an
  explicit owner preference (previously the hook only started the server and mentioned the URL,
  leaving opening the tab up to you). `session-start-reminder.ps1` uses `Start-Process`; `.sh`
  tries `open` (macOS) then `xdg-open` (Linux), doing nothing on a headless box rather than
  failing the hook. `CLAUDE.md`'s fallback section and `.claude/settings.json`'s comment updated
  to match.
- **New optional skill: `brand-collections-uefn`.** Recognizes which official Fortnite Game
  Collection (brand island — TMNT, LEGO, Fall Guys, Star Wars, KPop Demon Hunters, Squid Game,
  The Walking Dead Universe, Rocket Racing) a project is built on, from real Content Browser
  folder names, device classes, and template names — not guesswork. Ships with a marker table
  researched directly from Epic's own Game Collections documentation: strong, confirmed technical
  markers for TMNT/LEGO/Fall Guys; name-only "weak" entries for the other five, since Epic's
  public pages for those don't publish folder/class-level detail. Includes a capture procedure
  for upgrading a "weak" entry (or adding a brand missing entirely) straight from a real project —
  writes to the skill's own reference file (works immediately, no vault needed) and, if the
  second brain is configured, to a `type: pattern` article via `second-brain-librarian` for
  cross-machine reuse; large projects can lean on `second-brain-trainer`'s parallel-analysis
  pattern for the capture pass itself. Wired into `project-bootstrap`'s A1 step and as a new rule
  12 in `user-level-memory/CLAUDE.md`. Install step 5 now copies seven skill folders instead of
  six.

## v1.42 — Agent Console: added the second-brain-trainer node

The console's `AGENTS` list still only had six entries after v1.41 added the seventh agent — it
now has its own node, so a training-sweep run is actually visible instead of falling back to a
generic/unknown node:

- New node for `second-brain-trainer` (🐝, a new `teal` color — every other slot in the existing
  8-color palette was already taken by another node) added to `agent-console.html`'s `AGENTS`
  array, with matching CSS rules (blob border/glow, name color, pill color) for the new `teal`
  `data-color`.
- The header tagline ("six agents. one chief of staff...") updated to "seven agents." The
  "N idle" footer counter was already computed dynamically from `AGENTS.length`, so it picks up
  the new total automatically — no fix needed there.
- No hook/server changes needed for this: `second-brain-trainer` dispatches its own parallel
  analysis clones and its one `second-brain-librarian` handoff exactly like any other agent-to-
  agent invocation the console already tracks (start/stop, FIFO attribution, comet/pulse) — this
  update only adds the node it lights up on the ring.

## v1.41 — New optional agent: second-brain-trainer (parallelized vault training pass)

New seventh agent, `second-brain-trainer`, for owners who want to backfill the Obsidian second
brain from a large or unfamiliar project faster than the normal one-thing-at-a-time flow:

- Splits the current project into areas (owner-given, or inferred from `Claude/docs/SPEC.md`'s
  project-structure section and the Outliner's own grouping) and dispatches one read-only
  analysis clone per area **in parallel** (batched in waves of ~6-8 if there are more areas than
  that) — genuinely concurrent subagents, visible as multiple simultaneous nodes if the Agent
  Console is open.
- Keeps the vault's single-writer rule intact: the parallel clones never touch the vault
  themselves, only gather findings; `second-brain-trainer` aggregates every clone's results and
  hands them to `second-brain-librarian` in exactly ONE call at the end. The vault is plain
  markdown with no locking, so this avoids the corrupted/lost-content risk of two writers
  touching it around the same time — parallelizing the reading is safe, the writing stays
  strictly single-threaded either way.
- Only useful when `second-brain-librarian` (and its vault) is already configured; skips itself
  with a clear message if it isn't. Owner-invoked only — not something the other agents call on
  their own.
- `user-level-agents/second-brain-trainer.md` added (Phase 1 install step 5 now copies seven
  agent files instead of six). SETUP-GUIDE.md updated: section 2's agent list, section 3c's
  second-brain writeup, and the intro's feature list and agent count.

## v1.40 — Agent Console: deterministic, per-project auto-start (no more asking, no more stale cross-project server)

Fixes a real bug the owner hit switching UEFN maps/projects, plus the matching feature request —
start the console with the very first command of a session, not after a round of asking:

- **Bug fixed: stale cross-project server.** Every project used the same fixed port (8765), and
  the old `SessionStart` hook only checked "is *something* listening on 8765" before deciding
  whether to start a new one — so switching to a different UEFN project while a previous
  project's server was still bound left you looking at the *wrong* project's console, since it
  looked "already running" from the outside. Fixed by giving every server instance a new
  `/whoami` route reporting which project folder it's actually serving; the session-start hook
  now compares that against the current project before deciding anything.
- **No more asking.** `session-start-reminder.ps1`/`.sh` no longer prompts Claude to ask whether
  you want the console open. It now deterministically: (1) checks `/whoami` on port 8765; (2) if
  it's already serving THIS project, leaves it alone; (3) otherwise kills whatever's bound to the
  port — only if it looks like one of this kit's own server processes (powershell/pwsh/python),
  never an unrelated program — and starts a fresh one scoped to the current project, in the
  background. Claude just mentions the URL in its first reply; there's nothing to answer.
- `agent-console-server.ps1` and `.py` both gained the `/whoami` route (`{"project": "<this
  project's folder>"}`), computed once at server startup from the script's own location — this is
  the mechanism the fix above relies on.
- `CLAUDE.md`'s fallback "Rules for this project's agents" section rewritten to match: describes
  the same deterministic check-and-replace behavior instead of "ask, then start if nothing's
  listening," for the rare case the hook's own context note doesn't reach an older Claude Code
  build.
- `.claude/settings.json`'s `SessionStart` block comment updated to describe the new behavior.
- SETUP-GUIDE.md section 5b rewritten (the "how it starts" paragraph and the troubleshooting
  entry) to match — including a new note for the specific symptom "it's showing a different
  project's data."
- No change needed for the very-first-ever-bootstrap case the owner also asked about:
  `Claude/hooks/agent-console.html` already ships as part of this kit's project template, so it's
  present from the very first session on a project regardless of whether `project-bootstrap` has
  ever been run — the deterministic auto-start above already covers it with no special-casing.

## v1.39 — Agent Console: new MCP Server node, YOU session-active LED

Two feature requests, implemented and live-tested by the owner's own Claude Code session (with
synthetic events for the MCP node, to avoid actually touching the UEFN editor during testing),
then backported into the kit source (including authoring the missing `.sh`/`.py` equivalents for
parity, since only the `.ps1` versions were provided):

- **New "MCP Server" node** (🛰️, orange), fed by a new pair of hooks,
  `agent-console-mcp.ps1`/`.sh`, wired on both `PreToolUse` and `PostToolUse` for the
  `mcp__unreal-mcp__call_tool` matcher (added as a second, independent command alongside
  `after-playtest.ps1`/`.sh` on that same matcher — not a replacement). It writes to its own log,
  `Claude/logs/agent-console-mcp.jsonl`, served from a new `/mcp` route. The node lights up (LED,
  "working" pill, call counter, tooltip with a best-effort label of what was called) while a call
  is in flight, and returns to idle on stop. When a bot made the call, a pulse animates from that
  bot's node to the MCP node so you can see *who's* talking to the editor; a direct call from the
  main session just shows the node connected to the hub.
- **YOU node now shows a session-active LED**: green while the main Claude Code session is
  actively working, grey once it's yielded back and is waiting on your next message — independent
  of the existing red "approval required" alert (still tied to `release-gate`, unchanged). Fed by
  `agent-console-tokens.ps1`/`.sh` (already firing on every tool call — now also writes
  `Claude/logs/agent-console-session.json` with `active:true`) and a new
  `agent-console-session-stop.ps1`/`.sh`, added as a second command on the existing `Stop` hook,
  which writes `active:false` at the exact moment the main session yields back to you. Served
  from a new `/session` route.
- Fixed a bug caught during testing: the MCP Server node's pill showed "undefined" instead of
  "idle" on first load (a special node with no `pillOff` defined had no fallback).
- `agent-console-server.ps1` gained the two new routes (already done upstream); backported the
  same `/mcp` and `/session` routes into `agent-console-server.py` for parity, since the uploaded
  copy was still the three-route version.
- `.claude/settings.json` updated: new `PreToolUse` block for `agent-console-mcp.ps1`, a second
  `PostToolUse` command on the existing `mcp__unreal-mcp__call_tool` block, and a second `Stop`
  command for `agent-console-session-stop.ps1`.
- New SETUP-GUIDE.md paragraphs documenting both features under section 5b.

## v1.38 — Agent Console: per-agent + hub status LEDs, comet moved fully outside the ring

The owner's own Claude Code session made further live-tested improvements directly to
`agent-console.html` (verified both with overlapping real subagents and by injecting synthetic
states into the page to check the logic deterministically, since real timings were too fast to
screenshot at the right millisecond):

- **Dynamic status LED on every agent card**, replacing the old fixed-green "online" dot:
  - grey = idle
  - green (pulsing) = genuinely working right now (top of the active-invocation stack)
  - red (blinking) = either waiting on a delegated task to finish (it's active but not on top of
    the stack — e.g. `coder` that just handed off to `second-brain-librarian`), or has been
    running longer than 6 minutes with no stop, a likely-stuck signal distinct from (and earlier
    than) the 20-minute hard auto-clear added in v1.36.
  Verified with 3 overlapping invocations: only the most-recently-started one shows green, the
  rest show red — the intended parent/child-delegation reading.
- **Chief of Staff hub** now has its own status LED too (green while supervising at least one
  active agent, grey when everything's idle), correctly positioned on the hub's own edge.
- **Comet orbit radius increased** from ~30px (effectively glued to the 32px blob edge) to ~46px,
  so it now clearly orbits outside the icon instead of riding along its border glow. Also added a
  real fading tail — a gradient arc trailing the comet's head — instead of just a glowing dot.
- Confirmed no "unknown" card remains in the current log history from the v1.37 fix; if one
  reappears after a hard refresh on `http://127.0.0.1:8765/`, it's worth a fresh capture with the
  same method used for the v1.37 diagnosis rather than assuming it's the same already-fixed bug.

## v1.37 — Agent Console: the real "unknown"/stuck-card root cause, found and fixed

The owner ran the diagnostic prompt from v1.36 in their own Claude Code session against a live
capture of `SubagentStop` payloads (2 real subagents dispatched overlapping) and found the actual
bug — the v1.36 auto-clear safety net was masking the symptom, not fixing it. Two real,
independent findings, backported into `agent-console-log.ps1`/`.sh` and
`agent-console-stop.ps1`/`.sh`:

- **`SubagentStop` fires for more than just a real subagent finishing.** Of 5 captured events,
  only 2 were real completions (a populated `agent_type` whose `agent_id` matched a prior
  dispatch); the other 3 were internal orchestrator-session events with `agent_type:""` and an
  `agent_id` never seen in any start event (one even carried the session's own scheduled-wakeup
  id). The old script treated every SubagentStop as a real stop and always popped the FIFO
  queue's oldest entry — so a ghost event would consume a real agent's queue entry, permanently
  desyncing every attribution after it. That's what actually produced the "unknown" cards and
  real cards (e.g. `coder`) staying stuck on WORKING — not a simple ordering race.
  `agent-console-stop.ps1`/`.sh` now reads the payload's own `agent_type` directly; if it's
  empty, the script exits immediately without touching the queue or logging anything. The queue
  is now used only to recover the matching `desc`, by searching for the oldest entry whose
  `agent` matches the real `agent_type` — not by blindly popping index 0 — which also fixes
  attribution when two different agent types are active at once and finish out of order.
- **A PowerShell 5.1 parsing gotcha**, found once the above was fixed and `desc` was still coming
  back empty: `@(Get-Content -Raw | ConvertFrom-Json)` — the outer `@(...)` around the pipe —
  double-nests the result once the queue has more than one element (`Object[1]{ Object[N]{ ... }
  }` instead of a flat `Object[N]`), silently breaking the agent-match search. Queue parsing in
  both `.ps1` scripts now normalizes explicitly ($null / already-an-array / single-object) with
  no outer `@(pipe)` wrap. The `.sh` scripts use `jq` and were never subject to this specific
  gotcha, but got the `agent_type`-based ghost-event fix ported over regardless, since that part
  is about hook payload behavior, not the shell.
- Confirmed end-to-end with `coder` + `qa-regression` dispatched overlapping and finishing in
  reversed order: correct `desc` on both, no `unknown`, and the queue back to `[]` clean.
- v1.36's 20-minute auto-clear safety net stays in place as a front-end fallback (still worth
  having in case a future Claude Code version changes these field names again — see the updated
  SETUP-GUIDE troubleshooting entry), but is no longer expected to be the thing doing the actual
  work here.
- Rewrote the SETUP-GUIDE.md troubleshooting entry for stuck/misattributed/"unknown" cards to
  describe the real mechanism instead of the earlier (incorrect) FIFO-ordering theory.

## v1.36 — Agent Console: fixed stuck animations, ring overlap, hub icon, vault connector

Direct feedback from a live run that surfaced a real "unknown" card in the console (see the new
SETUP-GUIDE troubleshooting entry) plus three follow-on asks:

- **Comet/pulse animations no longer run forever.** Root cause of the underlying symptom (a
  card's comet/pulse staying "active" after the real work finished): a `stop` event can get
  misattributed to a phantom `"unknown"` agent when the FIFO attribution queue
  (`agent-console-active.json`) is popped while already empty, which "eats" a stop that belonged
  to a real, still-active card. As a front-end safety net (independent of fixing the hook-side
  race, which needs a live capture to pin down per-setup), a card with no matching stop event
  after 20 minutes is now auto-cleared — its comet/pulse/glow turn off and the activity log gets
  an explicit "⚠ auto-cleared" note explaining why, instead of spinning indefinitely.
- **Ring layout no longer overlaps when a new node appears at runtime.** A dynamically-added
  fallback node (e.g. that same `"unknown"` card) used to keep the *original* even-spacing angle
  math from before it existed, so it could land right on top of an existing node instead of the
  ring re-spacing itself. All node angles are now recomputed whenever a new node is added.
- **Chief of Staff hub icon**: replaced the abstract coral starburst mark (read as "a little
  flower") with the same 🤖 robot glyph used for an unrecognized/fallback agent card, per direct
  feedback — same visual language, not a separate abstract mark.
- **Obsidian Vault's connector** now points at `second-brain-librarian` instead of at the hub —
  it isn't a bot the Chief of Staff talks to directly, it's the storage that
  `second-brain-librarian` actually writes into, so the line now reflects that relationship
  instead of implying a direct hub connection.
- Added a matching SETUP-GUIDE.md troubleshooting entry for the "unknown" node specifically,
  since it's a distinct enough symptom from the older generic stuck-card entry to deserve its own
  explanation and remedy.

## v1.35 — Agent Console: vivid colors, gem icon for Obsidian Vault, Claude-style hub mark

Follow-up to v1.34's redesign, based on direct feedback that the first pass looked too washed
out compared to the reference image (bright neon rings on a dark background, not muted glass):

- Removed the `grayscale`/`opacity` filter that was desaturating every idle node's ring and
  icon — that was the actual cause of the "muted" look, since it was graying out the
  already-correct per-agent border color. Every node's colored ring, glow, and label now render
  at full saturation all the time; only the glow intensity and a scale bump change between
  idle and active.
- Node shape switched from the organic "blob" to a clean circle with a thicker (3px) glowing
  ring, closer to the reference's neon-circle look; each node also got a small pulsing green
  "online" dot in the corner, and its name label is now colored to match its own ring instead of
  plain gray.
- **Obsidian Vault** now uses a gem icon (💎) instead of a folder, echoing the amethyst-crystal
  icon in the reference image.
- **Chief of Staff hub**: replaced the placeholder text glyph with a small custom inline-SVG
  mark (three overlapping coral-orange rounded bars radiating from a center dot) instead of a
  generic icon — a distinct, Claude-toned identity for the hub specifically, not the same icon
  reused for every other node. The hub's ring, glow, and ripple rings were retinted to match
  (coral / amber / magenta instead of blue / purple / cyan).

## v1.34 — Agent Console visual redesign: "Dream Bot Team AGENT CONSOLE_"

Cosmetic/UX redesign of `agent-console.html` only — no changes to the hooks, the FIFO queue, the
server, or the token/timer logic behind it. Two design passes in a row, both from live reference
images the owner supplied:

- Renamed the console's title to **"Dream Bot Team AGENT CONSOLE_"** (matches the existing
  blinking-cursor convention already used elsewhere in the file).
- Replaced the old two-column hex layout with a radial layout: a central **"chief of staff"** hub
  (a Claude-style glyph in a circular core) with three staggered expanding ripple rings
  (`@keyframes ripple`) so it reads as "alive" even at rest.
  Six agent nodes plus two new special nodes are arranged evenly around it and slowly orbit
  (~0.9°/s, one lap roughly every 6.5 minutes) via a `requestAnimationFrame` loop that recomputes
  each node's position, its SVG spoke back to the hub, and any in-flight pulse dot every frame.
- Distinct color per agent, reinforced (same six-color palette as before, now driving glow color,
  border color, and the new comet color together).
- Agent icons are now glassmorphic "blobs" — `backdrop-filter: blur()`, translucent gradient
  fill, an organic asymmetric `border-radius` loosely inspired by the Fortnite sprite gallery the
  owner referenced (not a literal copy — a from-scratch shape in that spirit, since the request
  left the exact execution up to me).
- Spokes now carry a **continuous traveling pulse** while an agent is active (not just on
  handoff) — a small dot flowing along the spoke toward the hub, in the agent's own color, so
  "this agent is working" is visible at a glance without reading the pill text.
- Added a small **comet**: a half-circle dot that orbits an agent's icon (`@keyframes
  spinComet`), shown only while that agent is `.active`, colored to match the agent.
- Added two new special, non-subagent nodes on the same ring:
  - **Obsidian Vault** ("shared memory") — lights up whenever `second-brain-librarian` is active,
    since that's the real agent that writes to the vault.
  - **YOU** ("approvals only") — turns red and pulses whenever `release-gate` is active. This is
    a **heuristic proxy**, called out explicitly in the footer: there's no dedicated
    "approval requested" hook in this kit yet, so `release-gate` running is used as the closest
    available signal that a real decision is waiting on a human. A matching red "⚠ approval
    required" stat card lights up in the top stats row at the same time, and the hub itself gets a
    red glow.
- Moved the activity/terminal log to the right-hand column (`.main-grid`, a two-column grid that
  collapses to one column under 960px) instead of full-width below the layout.
- `SETUP-GUIDE.md` section 5b's screenshots/description of the console's look are now stale and
  should be refreshed to match, next time that section is touched — not done in this pass since it
  was purely visual and no behavior changed.

## v1.33 — two more real bugs found testing the token/timer update, both fixed

The owner tested v1.32 live (guided by a diagnostic prompt) and found two genuine bugs, not
hypothetical ones:

- **Stale server process**: the running `agent-console-server.ps1` had been started before the
  updated files were copied in — it had already loaded the old `agent-console.html` and doesn't
  re-read routes/files after startup, so `/tokens` looked broken when the real cause was an old
  process still serving old content. Not a code bug, but common enough to call out explicitly:
  `SETUP-GUIDE.md` section 5b now has a dedicated note to restart the server after updating any
  `agent-console-*` file.
- **Real race condition**: `agent-console-log.ps1` and `agent-console-stop.ps1` both
  read-modify-write `Claude/logs/agent-console-active.json` (the FIFO attribution queue), and
  overlapping subagent invocations can run both at the same instant. Confirmed via a live test:
  concurrent unsynchronized writes corrupted a queue entry (a field serialized as a 2-element
  array instead of a plain string), which then threw uncaught inside `agent-console.html`'s
  render loop before `lastCount` advanced past the bad entry — permanently wedging the
  connection indicator on "🔴 DISCONNECTED" every poll thereafter, plus a stuck "WORKING" card
  and a stray ghost card, despite the server and network being completely fine. Fixed two ways:
  a named Mutex (`Local\AgentConsoleQueueMutex`, shared between both scripts) now serializes the
  read-modify-write section so the queue file can't be corrupted in the first place, and
  `agent-console.html`'s `processEntries()` now defensively skips any log entry whose
  `agent`/`desc` fields aren't plain strings instead of throwing — so even a future corrupted
  entry from some other cause degrades to "one skipped row," not a permanently broken console.

## v1.32 — session timer and approximate token counter in the Agent Console

- **Session timer**: a "Session running for" readout, ticking live every second, computed
  client-side from the earliest event already loaded — no new hook needed. Each active agent
  card also now shows its own live elapsed time (`⏱ 1:24`) while it's working.
- **Tokens this session (experimental/best-effort)**: a new stat showing a rough running total
  of token activity, summed from the session transcript Claude Code writes to disk. New hook
  `Claude/hooks/agent-console-tokens.ps1`/`.sh`, wired as a `PostToolUse` hook with no matcher
  (fires on every tool call, not just subagent ones), reads the transcript incrementally
  (tracked byte offset, so it stays cheap on a long session) and writes a cumulative snapshot to
  `Claude/logs/agent-console-tokens.json`. `agent-console-server.ps1`/`.py` gained a `/tokens`
  endpoint serving that file; the page polls it alongside `/log`.
- Explicitly documented as approximate: the total sums `input + output + cache_read +
  cache_creation` tokens across every assistant turn — a proxy for activity, not a billing
  figure, since prompt-caching pricing and per-turn full-context `input_tokens` aren't adjusted
  for. There's no documented API for this — it's inferred from the transcript's on-disk shape,
  which could change between Claude Code versions; `SETUP-GUIDE.md` section 5b has a
  troubleshooting entry (and a debug-capture switch in the script) for when it doesn't.
- `.claude/settings.json` updated with the new no-matcher `PostToolUse` block.

## v1.31 — fixed premature "finished" on backgrounded subagents

Found live: the owner dispatched `coder` to fix three bugs at once, Claude Code ran it in the
background ("Waiting for 1 background agent to finish"), and the console showed "finished" two
seconds after "started" while the agent was still genuinely working.

- **Root cause**: "stop" was logged from `PostToolUse` on the subagent-dispatch tool
  (`Task`/`Agent`) — but for a backgrounded dispatch, that tool call returns (firing
  `PostToolUse`) the instant the work is handed off, not when it's actually done. Foreground
  dispatches happened to look right by coincidence; background ones didn't.
- **Fix**: "stop" now comes from the `SubagentStop` hook instead — the hook Claude Code fires on
  a subagent's real completion, foreground or background. `agent-console-log.ps1`/`.sh` now only
  logs "start" (on `PreToolUse`, unchanged); a new `agent-console-stop.ps1`/`.sh` handles "stop"
  on the new `SubagentStop` hook.
- Since `SubagentStop`'s payload doesn't reliably say which agent just finished,
  attribution goes through a new small FIFO queue file, `Claude/logs/agent-console-active.json`:
  the start hook pushes an entry, the stop hook pops the oldest one and uses its
  agent/description. Best-effort (documented as such), correct for the common case.
  `.claude/settings.json` updated: removed the old stop-logging `PostToolUse` "Task|Agent"
  block, added a `SubagentStop` block.
- `SETUP-GUIDE.md` section 5b rewritten to describe the new two-hook/queue mechanism, plus a new
  troubleshooting entry for a card stuck on "WORKING" or a wrong attribution (delete
  `agent-console-active.json` to reset).

## v1.30 — real root cause found: the subagent tool isn't always named "Task"

The owner diagnosed this live (guided debug: uncommented the raw-payload capture, temporarily
widened the hook matcher to `.*`, invoked `coder` explicitly, inspected the captured payload).
Confirmed cause of the console staying at 0/IDLE even with a correct `.claude/settings.json`:
on this build, Claude Code's internal subagent-dispatch tool is named `"Agent"`, not `"Task"` —
every event was being filtered out before it ever reached the log. All other field names
(`hook_event_name`, `tool_input.subagent_type`, `tool_input.description`) were already correct.

- `agent-console-log.ps1`/`.sh` now accept **both** `"Task"` and `"Agent"` as the tool name,
  since it's been observed to vary by Claude Code build/version — future-proofs the console
  against needing this same diagnosis again on a different setup.
- `.claude/settings.json`'s two matchers changed from `"Task"` to the regex `"Task|Agent"`.
- `SETUP-GUIDE.md` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly, and the
  troubleshooting section now says explicitly what to do if a future version renames the tool to
  something else again (add it to both the script check and the matcher, same pattern).

## v1.29 — fixes from a real test of the Agent Console automation

Two problems found live-testing v1.28: the automatic session-start question never fired, and the
console stayed at 0/IDLE even after opening it manually.

- **Root cause of the silent prompt**: `session-start-reminder.ps1`/`.sh` printed plain text to
  stdout, which isn't reliably read as an instruction by Claude Code. Rewrote both to emit
  proper hook-output JSON (`hookSpecificOutput.additionalContext`), the documented way to inject
  context Claude actually sees at session start.
- **Guaranteed fallback added**: the same reminder now also lives as plain prose in
  `project-template/CLAUDE.md`'s "Rules for this project's agents" section — CLAUDE.md always
  loads regardless of any hook-output quirk in a given Claude Code version, so the console
  question surfaces even if the hook JSON approach doesn't land on some setup.
- **Clarified why cards can stay at 0/IDLE**: the console only reacts to a genuine `Task` tool
  dispatch to a named subagent — general conversation or an inline edit Claude does without
  delegating doesn't produce one, and isn't a bug. `SETUP-GUIDE.md` section 5b now says this
  explicitly, plus an expanded troubleshooting checklist covering the most likely real cause:
  `.claude/settings.json` needs to be fully replaced on an existing project, not just the new
  hook script files copied in.

## v1.28 — Agent Console asks to open itself, automatically

- New `Claude/hooks/session-start-reminder.ps1`/`.sh`, wired into `.claude/settings.json` as a
  `SessionStart` hook (matcher `startup`, so it fires when you launch `claude` fresh, not on
  every `/clear`/`/compact`). If the project has the Agent Console installed, it reminds Claude
  at the very start of the session to ask the owner whether they want it open — if yes, Claude
  checks port 8765 and, if nothing's listening, starts `agent-console-server.ps1`/`.py` itself
  in the background (detached, doesn't block the session) and tells the owner to open
  `http://127.0.0.1:8765/`. Says no once, doesn't ask again that session.
- `SETUP-GUIDE.md` section 5b and `Claude/SETUP-INSTRUCTIONS.md` step 9 updated to describe the
  automatic prompt as the default way to open the console, with manual startup kept as an
  alternative for anyone who'd rather run it in their own terminal.

## v1.27 — real-time Agent Console

A local, arcade-style dashboard that shows the team of agents actually working in real time —
which one is active, on what, and when one hands off to another — instead of only seeing the
finished output in `STATUS.md`/`BUGS.md`.

- New `Claude/hooks/agent-console.html`: a self-contained page with a card per agent (glows in
  that agent's own color and shows the current task while active), a scrolling activity log, and
  an animated pulse between two cards when one agent invokes another mid-task.
- New `Claude/hooks/agent-console-log.ps1`/`.sh`: wired into `.claude/settings.json` as
  `PreToolUse`/`PostToolUse` hooks matched on the `Task` tool (what Claude Code uses internally
  for every subagent invocation) — appends a start/stop line to
  `Claude/logs/agent-console.jsonl` per event, already configured in the scaffold, nothing to
  set up per project.
- New `Claude/hooks/agent-console-server.ps1` (PowerShell, no dependencies) and
  `agent-console-server.py` (Python, cross-platform): a small local web server serving the page
  and the live log — run manually, in its own terminal, kept open while working; not started
  automatically.
- `.claude/settings.json` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly;
  `SETUP-GUIDE.md` gets a new section 5b documenting setup, usage, and troubleshooting (same
  debug-payload pattern as the existing post-playtest hook).
- Entirely optional and safe to ignore/remove — nothing else in the kit depends on it.

## v1.26 — token-consumption reduction: six progressive-disclosure skills

Based on a set of recommendations the owner got analyzing the kit's token usage (same
adapt-don't-paste-verbatim approach as prior externally-sourced proposals):

- **Six new skills**, all following the progressive-disclosure shape (short `description`,
  dense body, `references/` loaded only on demand): `verse-patterns` (reusable Verse code
  idioms — multiplayer authority, state machines, logging/timers, item pool/round progression),
  `uefn-device-gotchas` (device-TYPE-specific quirks — DemoDisplay sizing/orientation,
  Elimination Manager/Item Granter timing, Storm Controller/Player Spawner position-critical
  behavior), `performance-uefn-checklist` (the static red-flag checklist), `discover-retention`
  (Discover signal facts plus a growing validated-proposal log, superseding `uefn-lessons`'
  "Discover / retention signals" category), `second-brain-query` (rules for asking the second
  brain narrowly), and `token-aware-coding` (general token-efficient habits — targeted search
  over full reads, precise `@file` mentions, periodic summarization).
- **`~/.claude/CLAUDE.md` rule 7 (DemoDisplay) trimmed**: the detailed sizing/orientation math
  and the `get_actor_bounds` gotcha moved to `uefn-device-gotchas/references/
  demodisplay-sizing.md`; CLAUDE.md now keeps only the always-needed core rule (one stand per
  Verse device, function-grouped) and the safety-critical gameplay-position exception, with a
  pointer to the skill for the rest — this file loads in every session, on every project, so
  trimming it has the largest leverage of any change in this pass.
- **`uefn-lessons/SKILL.md` de-duplicated**: its "Discover / retention signals" category now
  points to `discover-retention` instead of repeating the same facts; its "Device behavior
  surprises" category now points to `uefn-device-gotchas` for device-specific quirks, keeping
  the two skills' scopes non-overlapping (uefn-lessons = generic Verse/UEFN/MCP tooling,
  uefn-device-gotchas = per-device-type behavior).
- **Agent files wired to the new skills** rather than duplicating their content inline:
  `coder.md`'s pre-work checklist now points to `verse-patterns`/`uefn-device-gotchas`/
  `second-brain-query` at the relevant steps, and its DemoDisplay bullet points to the sizing
  reference instead of restating the math; `project-bootstrap.md`'s A3 now reads
  `performance-uefn-checklist` instead of inlining the checklist, and A4 reads
  `discover-retention` instead of `uefn-lessons`' (now-removed) Discover category;
  `qa-regression.md` references `performance-uefn-checklist` for what to watch at playtest.
- `SETUP-GUIDE.md` Phase 1 step 5 now lists all six new skill folders for installation, and a
  new section 3d explains what each one covers and why the progressive-disclosure shape matters
  for token usage.

## v1.25 — synthesis behavior applied consistently across every sync, not just `evolve`

Follow-up refinement (second round of feedback the owner got on v1.24, adapted rather than
applied verbatim):

- **Sync mode now checks for lateral synthesis too**: after `coder`/`project-bootstrap` hand off
  something to capture, `second-brain-librarian` checks related articles for a newly-surfaced
  connection (Level 1: update their "Connessioni e potenziali" directly) and adds a
  `wiki/meta/frontiere-conoscenza.md` entry when the sync reinforces or creates a genuinely
  interesting combination (Level 1 for a note, Level 2 to propose a new synthesis article) — so
  every ordinary sync feeds the KB's evolution, not only an explicit `evolve` run. Its report now
  says explicitly whether it touched other articles' connections or the frontier file.
- **"Connessioni e potenziali" got a concrete four-line template** (formalized links, latent
  links, synthesis candidates, open questions) instead of being described only abstractly —
  makes it actually consistent across articles and checkable by `audit`.
- `type: synthesis` articles now list their component concepts as a scannable inline
  `componenti: [[...]]` line under "Componenti combinati," for quick Dataview/graph use.
- **Query now prefers citing a synthesis article over its isolated components**, when one exists
  — the actual value-add of a second brain over flat search — applying whether the query comes
  from the owner or from `coder`/`project-bootstrap` asking before their own work.
- Release-notes sync (mode 3) now also updates a tracked device/mechanic article's "Connessioni e
  potenziali" (or adds a frontier entry) when a release note affects it, instead of leaving the
  conflict only inside the release-notes article itself.
- Step 0's near-miss-filename handling now gives the exact rename command, not just the
  diagnosis.
- Index-update steps now also remind to update any `moc-*.md` for a touched wiki, if one exists.
- Added an optional `wiki/meta/log-sessioni-sintesi.md` (a lightweight running tally of `evolve`
  runs), created only once `evolve` has actually run a few times, distinct from the narrative
  `evoluzione-kb.md`.
- The `second-brain-librarian.md` ↔ vault `CLAUDE.md` cross-reference on proactive-synthesis
  behavior is now stated as a direct instruction ("apply Level 1 immediately, propose Level 2")
  rather than just pointing at the other file.

Deliberately NOT added, per the owner's own judgment on the proposal: autonomous `evolve`
triggering, automatic versioning of the vault's `CLAUDE.md` itself, automatic Canvas/diagram
generation, or additional mandatory frontmatter fields — all flagged as premature/out of scope
for now.

## v1.24 — emergent synthesis and evolution for the second brain

Significant rewrite of `second-brain-template/CLAUDE.md`, incorporating and adapting a set of
proposals the owner got from another AI assistant, integrated to fit the existing architecture
rather than pasted verbatim:

- New **"Emergent synthesis and evolution"** section: `second-brain-librarian` now actively
  looks for connections between articles it wasn't explicitly asked to find — during `compile`,
  a query, or `audit` — not just when told to. Three levels of autonomy: apply directly (update
  an article, add a missing wikilink), propose-then-confirm (new synthesis article, merge, new
  wiki), and a dedicated Level 3 pass only on explicit command. Five named reasoning moves
  (structural analogy, generalization, composition, inversion, cross-domain transfer) to use
  when actively looking for a connection, with the "why" documented in 1-2 dense sentences.
- New **`evolve`/`sintetizza [topic]`** workflow (Level 3): a deliberate whole-KB (or scoped)
  synthesis pass — finds under-connected clusters, drafts 3-7 emergent ideas in
  `output/sintesi-YYYY-MM-DD.md`, and presents them for review. Never applies anything
  unconfirmed, same rule as `audit`.
- New `wiki/meta/` living files, created on demand (not pre-created empty):
  `frontiere-conoscenza.md` (open questions, untested hypotheses, patterns seen on 2+ projects
  without an article yet), `evoluzione-kb.md` (dated log of significant syntheses/reorganizations),
  `principi-design-second-brain.md` (observations about how this KB itself is working — a wiki
  article for the owner to read, explicitly NOT a mechanism for the agent to rewrite its own
  `CLAUDE.md` autonomously; structural changes to this file stay the owner's call).
- Richer, Dataview/graph-friendly frontmatter (`aliases`, `status`, `type`, `visto_su`,
  `versione_implementazione` — all optional, added where they genuinely apply), a new required
  `## Connessioni e potenziali` section on most articles, and a dedicated four-section structure
  for `type: synthesis` articles.
- `audit` gained four categories: under-synthesized clusters, weak connections, dormant ideas,
  stagnant evolution (a device/mechanic-specific case of staleness, called out because it
  directly hurts reuse value).
- `compile` gained a step 9 (synthesis side effect) and `query` a closing self-check, both
  tying back into the same "notice connections proactively" behavior.

`second-brain-librarian.md` updated to recognize `evolve`/`sintetizza` as a fourth direct
command alongside `compile`/query/`audit`, and to note the proactive-connection behavior applies
during ordinary work too, not only when `evolve` is explicitly invoked.

## v1.23 — "How I Want Claude to Help Me" section in the vault's CLAUDE.md

Added a new section to `second-brain-template/CLAUDE.md`: connect ideas between notes the owner
may have missed — while compiling, writing, or answering a query, `second-brain-librarian`
should actively look for related-but-unlinked existing articles (even across different thematic
wikis) and surface the connection (add the `[[wiki link]]`, mention it in the summary/answer),
not just handle the immediate task and move on.

## v1.22 — fixed two real bugs in the release-notes sync script

Found on a real Windows test run of `weekly-release-notes-sync.ps1`:

1. **Permission error reading the vault's `CLAUDE.md`.** The script never `cd`'d into the vault
   before calling `claude -p`; non-interactive/print mode can't prompt for confirmation, so it
   refused to touch anything outside its working directory. Fixed by `Set-Location` into the
   vault plus passing `--add-dir` as a belt-and-suspenders measure. Applied the same fix to the
   `.sh` version for consistency, even though bash's quoting doesn't hit the next bug.
2. **Prompt silently truncated mid-sentence.** The prompt had embedded double quotes (`"UEFN
   release-notes sync"`); when PowerShell hands a string like that to an external `.exe`,
   Windows' native argument parsing treats the embedded quote as closing the argument early —
   this is exactly what happened, the agent received the prompt cut off right before the quoted
   phrase. Fixed by removing all embedded double quotes from the prompt text.

`second-brain-template/README.md` now documents both gotchas and recommends testing the script
by hand once before wiring it into Task Scheduler/cron.

## v1.21 — weekly UEFN release-notes sync

`second-brain-librarian` gets a fourth mode, "UEFN release-notes sync" (added `WebFetch` to its
tool list): fetches
[Epic's "What's new in UEFN" page](https://dev.epicgames.com/documentation/fortnite/whats-new-in-unreal-editor-for-fortnite)
and keeps `wiki/note-di-rilascio-uefn/` current — one article per release. First run ever
backfills every entry found on the page; every run after that diffs against what's already
indexed and adds only newly published entries, never re-creating or duplicating one already
captured. Flags anything that looks like it deprecates something already noted elsewhere in the
KB (an `uefn-lessons` entry, a project's `BUGS.md`, an existing device article's snippet).

Added `second-brain-template/weekly-release-notes-sync.ps1` and `.sh` to actually run this on a
schedule, plus README instructions for wiring either into Windows Task Scheduler (`schtasks`,
Thursdays) or cron (macOS/Linux) — Claude Code itself has no built-in weekly scheduler, so this
is standard OS automation, the same pattern as the kit's own post-playtest hook. Can also be run
once by hand by asking any session to "use second-brain-librarian to sync UEFN release notes."

`note-di-rilascio-uefn/` added to the vault's suggested starting wikis in
`second-brain-template/CLAUDE.md`; setup guide's section 3c documents the new mode and the
automation setup.

## v1.20 — Windows hidden-extension gotcha on the vault's CLAUDE.md

Found on a real setup: saving/renaming `CLAUDE.md` through Windows File Explorer with
extensions hidden (the default) can silently produce `CLAUDE.MD.md` instead of `CLAUDE.md` —
Explorer hides the trailing `.md` because it's a "known" extension, so the wrong filename looks
identical to the correct one in the file list, and `second-brain-librarian` correctly reported
the vault as unconfigured (it reads the real filesystem, not Explorer's display) while the owner
saw what looked like the right file.

Fixes:
- `second-brain-template/README.md` and `SETUP-GUIDE.md` (Phase 1 step 7) now tell you to verify
  the vault's `CLAUDE.md` from a terminal (`dir CLAUDE*` / `ls CLAUDE*`) instead of trusting
  Explorer's file list, with the exact rename if it's wrong.
- `second-brain-librarian` now names the exact wrong filename (or missing folder) it actually
  found on disk when the vault looks misconfigured, instead of a generic "not configured" — so a
  five-second rename doesn't get reported the same way as an actually broken setup.

## v1.19 — second brain becomes read-write, not just write-only

Until now `coder` and `project-bootstrap` only fed the Obsidian second brain, never consulted
it — a project could reimplement something already catalogued from scratch without ever
checking. Fixed:

- **`coder`** (new step 5) queries `second-brain-librarian` before implementing a common
  device/mechanic pattern (respawn, item pool, round progression, elimination handling, and
  similar) from scratch, and adapts the existing snippet instead of reinventing it when a
  current implementation is already catalogued. Not mandatory on every task — only when the
  pattern is common enough to plausibly already exist.
- **`project-bootstrap`**'s A4 (retention proposals) now also queries the second brain for
  proposals already tried on other projects and their actual outcome, preferring a
  track-recorded proposal over a purely theoretical one when both apply.
- `second-brain-librarian`'s "direct vault commands" section now explicitly covers being queried
  by `coder`/`project-bootstrap` this way, not just by the owner.

Documented in `~/.claude/CLAUDE.md` rule 11, the setup guide's section 3c, and item 7 of "What
this kit does."

## v1.18 — second brain path set to `C:\SecondBrainOssidian`

`~/.claude/CLAUDE.md` rule 11's "Second brain path" now defaults to `C:\SecondBrainOssidian`
instead of the `<SECOND_BRAIN_PATH>` placeholder, so `second-brain-librarian` picks it up
automatically — no manual edit needed on this machine. Also updated as the worked example in the
setup guide's Phase 1 step 7 and in `second-brain-template/README.md`. Reusing this kit on a
different machine or vault location: replace the path with your own, or with the literal
`<SECOND_BRAIN_PATH>` placeholder to turn the feature off.

## v1.17 — dedicated second-brain-librarian agent

Added a sixth agent, `second-brain-librarian` — the only agent in this kit whose work happens
outside the current UEFN project's folder. It's now the sole owner of reads/writes to the
Obsidian second brain vault added in v1.16:

- `coder` and `project-bootstrap` no longer write to the vault themselves. When they identify a
  reusable device/mechanic worth capturing, they hand off to `second-brain-librarian` with a
  short brief (device/mechanic, what changed, project name, date) instead — keeping the vault's
  actual conventions in one place rather than duplicated (and potentially drifting) across every
  agent that might touch it.
- `second-brain-librarian` also runs the vault's own `compile` (ingest `raw/` material the owner
  drops in directly), query, and `audit`/`lint` workflows when invoked directly, exactly as
  defined in the vault's own `CLAUDE.md`.
- It always reads `<SECOND_BRAIN_PATH>/CLAUDE.md` before acting, since the vault's conventions
  are the authority and may be customized by the owner over time — nothing about the vault's
  structure is hardcoded into this agent beyond finding it and the handoff format.
- Never blocks UEFN work: if the vault is unreachable or unconfigured, it reports that and
  stops; `coder`/`project-bootstrap` treat a handoff exactly like a missing `uefn-lessons` file.

`~/.claude/CLAUDE.md` rule 11, the setup guide (Phase 1 step 7, section 2's agent list, section
3c), and `second-brain-template/README.md` all updated to describe the handoff model instead of
direct writes.

## v1.16 — optional Obsidian second brain for reusable mechanics

Added `second-brain-template/` (`CLAUDE.md` + `README.md`) — a separate, optional Obsidian vault
(not inside any UEFN project) that accumulates game-mechanic and Verse device implementations
across every project, kept current per device/mechanic rather than as a pile of snapshots, so a
working pattern can be reused by copying an up-to-date wiki snippet instead of rebuilding it.

New `~/.claude/CLAUDE.md` rule 11 ("Second brain (Obsidian) integration — optional") holds the
vault's path (`<SECOND_BRAIN_PATH>` placeholder, filled in once per machine, off by default) and
the writing rules: `coder` writes/updates an article after implementing a reusable device/
mechanic pattern; `project-bootstrap` does the same as a new closing step (A6) after its initial
analysis of an existing project. Both read the vault's own `CLAUDE.md` for its current
conventions before writing (it may be customized over time) rather than hardcoding assumptions
here. Never blocks a UEFN task: skipped silently if the path is unset or unreachable.

Setup guide: new optional Phase 1 step 7 (vault creation + path configuration), new section 3c
explaining the feature and how it differs from `uefn-lessons` (short tooling gotchas vs. full
wiki articles on reusable implementations), "What this kit does" item 7, and base-rules summary
item 9. Phase 1's later steps (register/verify) shifted from 7-9 to 8-10; a numbering gap
introduced in v1.13 (step 7 missing between 6 and 8) is also fixed by this renumbering.

## v1.15 — self-heal MCP registration on a new machine

Fixed a real gap: MCP server registration lives in `~/.claude.json`, per machine — it never
travels with the project (Git, cloud sync, a new computer), so a project already fully set up on
one machine showed no MCP tools the first time it was opened on another, with nothing telling
`coder`/`qa-regression`/`project-bootstrap` this was expected rather than a broken project.

All three MCP-using agents now check for this explicitly, before their existing identity-match
safety check: if `claude mcp list` doesn't show `unreal-mcp` but `CLAUDE.md`'s "Project identity"
is already filled in (proof this project was set up with MCP before), they treat it as a
new-machine first run — not a project problem — and register the server themselves (same
auto-find-and-register routine `Claude/SETUP-INSTRUCTIONS.md` step 2 already used for first-time
setup: check port 8000, then `claude mcp add ... --scope user` if missing). No manual step or
re-run of `Claude/SETUP-INSTRUCTIONS.md` needed on the new machine for this specifically.

Documented in the setup guide under "Why the MCP server is set up this way," with a reminder
that Phase 1's UEFN-side setup (`.mcp.json`, *Auto Start Server*, the kit's user-level files, the
Unreal Engine skills plugin) still needs to be done once on the new machine — this self-heal only
covers the Claude Code registration step, not UEFN's own server config.

## v1.14 — deprecated-API detection, a three-track roadmap, and Discover-grounded retention proposals

`project-bootstrap`'s A3 quality check now produces three separate, priority-ordered tracks in
`Claude/docs/BUGS.md` instead of one undifferentiated bug list:
- **Bugs**, ordered by severity (as before).
- **Deprecated functions**: calls to deprecated/soon-to-be-removed Verse/UEFN APIs or device
  features, each with its replacement if known from Epic's official docs. `coder` (rule 4 in
  `~/.claude/CLAUDE.md`) doesn't introduce new calls to something already flagged, and migrates
  one opportunistically when already touching that code. `qa-regression` flags any it comes
  across too.
- **Performance issues** (static review, added in v1.12), now explicitly its own track with its
  own impact-ordered roadmap rather than mixed into the bug list.

A4 (retention proposals) is now grounded in how Fortnite's **Discover** surfacing actually
measures engagement — average playtime, bounce rate (the concrete reason a 5-minute session
threshold matters for visibility, not just player experience), player retention, and Qualified
Play-Through Rate — sourced from
[Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite)
and added as a new curated "Discover / retention signals" category in
`user-level-skills/uefn-lessons/SKILL.md`, so proposals can name which specific signal they
target instead of offering generic playtime advice.

## v1.13 — Unreal Engine skills plugin is now required, with its Git prerequisite

Phase 1's plugin install step is no longer optional: `/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official` is now a required part of
environment setup (renumbered to step 6, shifting the later registration steps to 8-10). Added
its prerequisite: Git must be installed first ([Git for Windows](https://gitforwindows.org/) on
Windows), plus a Windows-specific gotcha — if Claude Code is already running in a PowerShell
session when Git gets installed, that session won't see the new `git` command until it's closed
and reopened (PowerShell only reads `PATH` at startup), which otherwise looks like a failed Git
install even though it succeeded.

## v1.12 — static performance review during bug identification

`project-bootstrap`'s A3 quality check (existing-project bug identification) now also does a
static performance review of the code, flagging patterns likely to cost FPS at runtime: per-tick
work that could run less often or on events instead, unbounded/growing loops or collections,
expensive calls (spawns, MCP/device queries, distance/trace checks) inside a loop or per-tick
path instead of throttled/cached, per-player work that scales badly with player count, and heavy
logic left running after it's no longer needed. Each finding becomes its own `BUGS.md` entry,
marked as a static finding for `qa-regression` to confirm at actual playtest — this doesn't
replace `qa-regression`'s existing runtime performance checks (rule 4 in `~/.claude/CLAUDE.md`),
it catches likely issues earlier, before the first playtest even happens.

## v1.11

Phase 1, step 5 of the setup guide now mentions, as an optional extra, installing Anthropic's
official Unreal Engine skills plugin (`/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official`) alongside this kit's own
user-level files — a separate plugin with its own Unreal Engine/Verse skills, complementary to
this kit rather than a replacement for it.

## v1.10 — DemoDisplay rule refined with real placement/sizing details

Replaced the v1.9 DemoDisplay/support-device rules (`~/.claude/CLAUDE.md` rules 7-8, `coder.md`,
`project-bootstrap.md`) with a much more precise version, based on hands-on testing on a real
project:
- **Grouping by function**: one `DemoDisplay` stand per Verse device, containing every device
  that Verse device configures — not one stand per connected device.
- **Sizing**: resize via the `DemoDisplay`'s own `width`/`depth`/`height` properties (through
  `ObjectTools`), never actor Scale (stays `1,1,1`). Documented the actual numeric relationships
  (`width=6/depth=5/height=4` defaults ≈ 500×633uu; `+1 width` ≈ `+100uu` on Y; `width=8-10`
  typically fits 5-6 grouped devices).
- **Orientation**: yaw=0 → front=+X, right=+Y, with a note to always check yaw before assuming
  an axis — a real attempt got this backwards.
- **`get_actor_bounds` gotcha**: asymmetric components (e.g. a spotlight cone) can skew the
  bounding box on one side; compute the real footprint from the set `width`/`depth`/`height`
  instead, and only use `get_actor_bounds` to check the side expected to be symmetric.
- **Placement on the stand**: devices go inside the stand's X/Y footprint at the same Z as its
  base — no Z stacking, no fixed-spacing rows, freely grouped within the footprint.
- **Gameplay-critical-position exception**: devices whose position IS functional gameplay data
  (Storm Controller/Beacon = storm circle center, Player Spawner = spawn point, etc.) are never
  physically moved onto a stand — they stay in place and are only referenced by name in the
  `DemoDisplay`'s description. `coder` and `project-bootstrap` now both check this before moving
  or flagging any device for relocation.

Also seeded two real entries into `user-level-skills/uefn-lessons/SKILL.md` ("Device behavior
surprises" and "MCP / tooling quirks") with the width/Scale and `get_actor_bounds` gotchas above,
replacing two of the placeholder examples.

## v1.9

Added two new base rules (`~/.claude/CLAUDE.md`, rules 7-8; older rule 7 shifted to 9, rule 8
to 10 — check cross-references if you customized the file):
- **DemoDisplay for every Verse device**: every custom Verse device gets a dedicated
  `DemoDisplay` device documenting what it does and what it's connected to, created or updated
  on every touch, not just at creation. `coder` maintains it going forward; `project-bootstrap`
  flags existing devices with a missing or stale one as a non-blocking BUGS.md entry.
- **Support devices outside the play area**: logic/support devices (Item Granter, Timer,
  Elimination Manager, `DemoDisplay`, etc.) must be placed outside the playable area so players
  never see or reach them — devices players are meant to encounter (Player Spawner, a central
  display case) are the explicit exception. `project-bootstrap` flags misplaced support devices
  it finds on existing projects rather than moving them itself.

## v1.8

Removed the packaging-warning notes ("verify `Claude/` and `.claude/` don't end up in the
released experience") from `CLAUDE.md`, `SETUP-GUIDE.md`, and `Claude/SETUP-INSTRUCTIONS.md`
(step 7bis). It's intentional that they ship with the release — the whole point of installing
the scaffold inside `Content/` is that it rides along as a backup, covered by UEFN's own
save/cloud-sync, not something to strip out before release.

## v1.7 — cross-project learning

Added `user-level-skills/uefn-lessons/SKILL.md`, a shared knowledge base installed once
(Phase 1) that persists across every project, unlike `coder`/`qa-regression`'s existing
per-project memory which resets on every new island. `coder` and `qa-regression` now read it
before starting work and add a short entry to it — instead of to their per-project memory —
whenever they hit a lesson that's about Verse/UEFN/MCP itself rather than something specific to
the current project's own devices or design. This is the mechanism for actually getting better
at UEFN development the more projects use this kit, instead of every new island starting from
the same blind spots. Documented in the setup guide as new section 3b, and in
`~/.claude/CLAUDE.md` rule 8 alongside the existing per-project memory rule.

## v1.6

Added Outliner (Scene Graph) organization and device naming to the naming/organization base
rule — previously it only covered the Content Browser's folders and files:
- Devices should be grouped in the Outliner into folders matching the experience's actual
  areas/systems (e.g. `Lobby`, `Game Area 1`, `Devices`), not left flat.
- Devices should be renamed `<DeviceType>_<Function>` (e.g. `teleport_lobby`) instead of kept
  at their default auto-generated name, so what a device does is clear without opening it.
- `coder` follows this when placing/configuring devices going forward.
- `project-bootstrap` now also reviews existing projects' Outliner organization during its
  quality check and, if it's disorganized, proposes a reorganization plan (folders + a
  current-name → suggested-name list) in `SPEC.md` for the owner to review — it doesn't rename
  devices on its own, since a blind rename can break Verse references bound to a device's name.

## v1.5

`Claude/SETUP-INSTRUCTIONS.md` step 2e now covers the most common false alarm: if the owner
just enabled *Python Editor Scripting* / *UEFN MCP Toolsets* while the project was already open
in UEFN, those settings don't take effect until the project is reloaded. The instructions now
tell the owner to close and reopen the project in UEFN (not necessarily quit UEFN) before
re-checking, instead of leaving them to guess why a setting they just enabled still isn't
working.

## v1.4

`Claude/SETUP-INSTRUCTIONS.md` step 2 now finds and registers the MCP server on its own instead
of just checking whether Phase 1 already did it: it probes port 8000 directly (`netstat`/
`lsof`), and if the server is up but not yet registered in Claude Code, registers it
automatically at user scope — no manual `claude mcp add` required from the owner. This makes
per-project setup self-sufficient: whichever project you set up first also does the one-time
registration, and every later project just finds it already there. Phase 1 in the setup guide
now marks its own registration steps (6-8) as optional — useful as an early sanity check, but
no longer required before setting up your first project.

## v1.3

Added an "About the author" section at the top of the setup guide (Mimmo_the_root — creator
code ROOT, Discord, socials) and a note on why some setup steps are left manual on purpose
(transparency: see and understand what's installed, rather than hide it behind a one-click
installer).

## v1.2 — Two-phase setup restructure

Fixed a real ordering/confusion problem, verified against Epic's official UEFN MCP docs and
against a real working setup tested on multiple projects:

- Setup is now explicitly split into **Phase 1 (environment setup, once per machine)** and
  **Phase 2 (per-project setup, repeated for every project)** — with a table up front spelling
  out the two different folders you launch `claude` from in each phase, since that was the
  actual source of confusion.
- Phase 1 now correctly sequences: create `.mcp.json` inside the **UEFN installation folder**
  → (re)start UEFN → enable *Auto Start Server* → verify the port is listening (`netstat`/
  `lsof`) → install the kit's user-level agents/CLAUDE.md → launch `claude` from that same
  installation folder → register the server once at Claude Code user scope → verify. Previously
  these steps were scattered across a "prerequisites checklist" and two later sections, in an
  order that didn't match how it actually needs to be done.
- Per-project `Claude/SETUP-INSTRUCTIONS.md` step 2 is now a lightweight double-check (assumes
  Phase 1 already ran) instead of repeating full registration instructions.
- Note: Epic's own documentation describes a different, per-project `.mcp.json` approach
  (created in each project's root folder). This kit deliberately uses the machine-level
  approach in Phase 1 instead — tested and working across multiple real projects — and says so
  explicitly in the guide's sources section, so readers comparing against Epic's page aren't
  thrown off by the difference.

## v1.1

Clarified the MCP server prerequisites, which were previously conflated into a single
per-project checklist: split *Auto Start Server* (once per machine) from *Python Editor
Scripting* / *UEFN MCP Toolsets* (once per project), and added a port-listening check
(`netstat`/`lsof`) as the first diagnostic step. Superseded by the fuller restructure in v1.2
above.

## v1.0 — Community edition (English)

First public release. Five user-scope Claude Code subagents (project-bootstrap, coder,
qa-regression, planner-docs, release-gate) plus a per-project scaffold for developing UEFN
projects at scale without mixing them up. Key design decisions baked into this release:

- The scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) is installed **inside** each project's
  `Content/` folder on purpose, so it's covered by UEFN's own save/cloud-sync. Since `Content`
  is named identically in every project, the project's identity is read from the parent folder
  name once during setup and stored in `CLAUDE.md`, never recomputed from the current folder.
- The MCP server is registered once at Claude Code **user scope**, so every project on the
  machine sees it automatically — no per-project `.mcp.json`.
- The `unreal-mcp` server exposes a single generic dispatcher tool for all actions; the
  post-playtest hook filters on the call's JSON payload rather than the tool name.
- `Claude/reference/logger-template.verse.txt` uses a `.verse.txt` extension on purpose — UEFN
  compiles every `.verse` file under `Content/`, and this template isn't a valid standalone
  Verse module.
