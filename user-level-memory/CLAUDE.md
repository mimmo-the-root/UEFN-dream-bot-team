# Base rules for all UEFN projects

Copy this file to `~/.claude/CLAUDE.md`: Claude Code loads it automatically in EVERY session,
on any project, without needing to repeat it in each project's own `CLAUDE.md`. The
project-level `CLAUDE.md` stays for things specific to that project (what it is, particular
conventions, identity); the rules that always apply live here.

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

## 2. Centralized logging

Every Verse file in the project must use this pattern instead of calling `Print()` directly
(a ready-made template is at `Claude/reference/logger-template.verse.txt` inside every
project):

```verse
@editable DebugLoggingEnabled : logic = true
Log(LogMessage : string):void=
    if (DebugLoggingEnabled?):
        Print(LogMessage)
```

- If a Verse file doesn't have it yet, add it — `coder` does this whenever it touches that
  file; `project-bootstrap` flags files still missing it in BUGS.md as a gap to close, during
  the initial quality check.
- **If the existing logs aren't enough to understand a bug, the next step is to add more of
  them at the critical points and re-test — never guess at the cause without first
  instrumenting the code.** This applies especially to `qa-regression` when analyzing a
  regression.

## 3. Always multiplayer

All projects are multiplayer. Any functional check — `coder` after a change, `qa-regression`
before marking a bug as resolved — must consider behavior in a real multiplayer context, not
just solo preview: state replication across players, server vs. client authority, what happens
if multiple players interact with the same device/object at the same time. If the available
MCP tool for playtesting only supports solo sessions, that must be flagged explicitly as a
limitation, with a recommendation for a manual multiplayer test before considering a feature or
fix truly done.

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

## 5. State machine as the primary pattern

For **new** projects, logic with multiple phases (e.g. lobby → round → end-of-match, or a
device's/character's states) should be structured as a state machine from the start, not with
scattered boolean flags. For **existing** projects that don't already use one, this isn't an
immediate rewrite requirement: `project-bootstrap` flags it in SPEC.md as a possible evolution
when the current flag-based logic is already hard to follow or shows bugs tied to inconsistent
states; `coder` proposes it as a targeted refactor when a new feature would require it, instead
of stacking more flags onto the existing logic.

## 6. Header documentation in Verse code

Every Verse file (created or modified) must have a comment block at the top in this form:

```verse
# <FileName>.verse
# Summary: <one or two sentences on what this script does>
# Last modified: <YYYY-MM-DD> — v<version number>
```

- **Summary**: what the file does, not how — useful to understand the purpose without reading
  all the code.
- **Section comments**: inside the file, one comment line above each significant logical block
  (e.g. `# Respawn handling`, `# Player input validation`) — no need to comment every line,
  just give the sections a readable structure.
- **Date and version**: `coder` updates the date (the real one — check it with a command
  instead of guessing) and increments the version number every time it substantially modifies
  that file. There's no Git tracking versions, so this header is the only history we have: keep
  it disciplined and up to date, don't let it fall behind.
- If an existing Verse file doesn't have this header, `coder` adds it the first time it touches
  that file (starting at v1 with today's date); `project-bootstrap` flags files still missing
  it in BUGS.md as a non-blocking gap.

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

## 8. Support devices stay outside the play area

All support/logic devices that are not gameplay-critical in position — Item Granter, Timer,
Elimination Manager, `DemoDisplay`, and similar — go outside the playable area, grouped on their
function's `DemoDisplay` stand (see rule 7 above), not scattered in the middle of the map, so
they're never visible to or reachable by players. This does NOT apply to devices players are
meant to encounter during gameplay, like a Player Spawner or a central display case, or to any
device whose position is gameplay-functional (see the exception in rule 7) — those stay wherever
the design/gameplay calls for them. `coder` places new support devices outside the play area,
grouped by function, from the start; `project-bootstrap` flags any existing support device found
inside the play area, or ungrouped, as a non-blocking follow-up in BUGS.md, for the owner to
review before moving it (relocating a device can affect existing triggers/volumes tied to its
position).

## 9. Response style: concise

Go straight to the results. No preamble like "I'll now proceed to..." or narration of what
you're about to do — do it, then report what you found/changed. This applies to every agent
when reporting its output.

## 10. Code that doesn't compile is not a finished task, and learning from errors

If the code you wrote doesn't compile, the task isn't done: it must be fixed and made to work,
not left as-is with the excuse that "everything else is fine." `coder` follows a
compile→read-the-exact-error→fix-precisely→recompile cycle, up to a maximum of 5 consecutive
attempts on the same error — beyond that, guessing at random costs tokens without solving
anything: better to stop, write in BUGS.md what was tried and the exact error, and ask.

`coder` and `qa-regression` have persistent per-project memory (`memory: project` in their
agent files' frontmatter): using it to avoid repeating the same mistakes is part of the job,
not optional. When something non-obvious specific to THIS project is discovered — a device
that behaves differently than documented, a design decision that trips up future work — save
it as a short note (one line, cause + how to recognize it) to that per-project memory, not a
long write-up: memory exists to save tokens in future sessions, not to become another document
to maintain. Check it before starting a task, so you don't always start from zero.

**Learning across projects, not just within one.** Per-project memory resets on every new
island — it never helps on project #37 with something learned on project #12. For lessons
about Verse, UEFN, or the MCP tooling itself (not this project's specific devices or design),
there's a second, shared layer: `~/.claude/skills/uefn-lessons/SKILL.md`, installed once
(Phase 1 of the setup guide) and read/added to by `coder` and `qa-regression` on every project
from then on. The rule for where a lesson goes: "would this help on a different island?" — if
yes, it's a `uefn-lessons` entry, not per-project memory. This is the actual mechanism for
getting measurably better at UEFN/Verse development the more projects this kit is used on —
it only works if entries stay short and are added consistently, not skipped because a session
is in a hurry to finish the task.

**One canonical answer per recurring MCP question, not one prose description per agent file.**
`~/.claude/skills/mcp-tool-contracts/SKILL.md` is the single source of truth for "which exact MCP
tool does X" (e.g. verifying which project UEFN has open). Every agent file that needs this
references the contract by name instead of describing the check in its own words — see that
skill's own header for why (a v1.67 incident traced back to the same instruction, worded slightly
differently in three separate files, quietly diverging). When a new MCP-tool gotcha is discovered,
it's added there as a new contract, not described inline in whichever agent found it.

## 11. Second brain (Obsidian) integration — optional

**Second brain path**: `C:\SecondBrainOssidian` (this machine's Obsidian vault root — the folder
containing `raw/`, `wiki/`, `output/`, and its own `CLAUDE.md`, see `second-brain-template/` in
this kit. If you're setting this up on a different machine, or reusing this kit yourself,
replace it with your own vault's absolute path — or with the literal placeholder
`<SECOND_BRAIN_PATH>` to keep this feature off.)

`uefn-lessons` (rule 10 above) captures short, one-line tooling/syntax gotchas. This is a
different, complementary layer: a full Obsidian wiki of **game mechanics and Verse device
implementations**, kept current per device/mechanic so a pattern that already works on one
island can be reused by copying its up-to-date snippet, instead of rebuilt from scratch — see
`second-brain-template/CLAUDE.md` (or the copy already installed in your vault) for the full
article format and the update-in-place rule for device/mechanic articles.

A dedicated agent, `second-brain-librarian`, owns all reads/writes to this vault — it's the only
agent in this kit whose job is outside the current project's folder. Neither `coder` nor
`project-bootstrap` write to the vault directly; they hand off to it instead.

If `<SECOND_BRAIN_PATH>` is still the unfilled placeholder, skip this rule entirely — don't
invoke `second-brain-librarian`, don't mention it every session, it's simply off. If it's set:

- **When `coder` hands off**: after implementing or meaningfully changing a device or Verse
  pattern that's reusable beyond this one project (same bar as `uefn-lessons`: "would this help
  on a different island?" — but for a working implementation, not a one-line gotcha) — not for
  every small change, only ones worth having a snippet for. It invokes `second-brain-librarian`
  with a short brief (device/mechanic, what it does, what changed, this project's name, today's
  date) rather than writing to the vault itself.
- **When `project-bootstrap` hands off**: as a closing step after its initial analysis (its A6
  step — see `project-bootstrap.md`), for generalizable mechanics/devices it identified while
  mapping an existing project. Same handoff, not a direct write.
- **What `second-brain-librarian` does with a handoff**: reads `<SECOND_BRAIN_PATH>/CLAUDE.md`
  for that vault's actual current conventions (frontmatter fields, folder naming, the
  update-in-place rule for device/mechanic articles) rather than assuming any summary elsewhere
  is exhaustive — the owner may have adjusted their own vault's rules over time, and the vault's
  own `CLAUDE.md` is the authority. In short: finds or creates the matching wiki (e.g.
  `wiki/device/`, `wiki/meccaniche/`) and article, updates its `## Implementazione Verse (ultima
  versione)` section in place (bumps version/date, doesn't append a second snippet), cites the
  source as `conversazione: <date>, progetto <name>`, updates that wiki's `indice_wiki.md` (and
  `wiki/indice.md` if a new wiki was created).
- **This agent is also the one to invoke directly** for the vault's own `compile` (ingest
  `raw/` material), query, and `audit`/`lint` workflows — when the owner is working inside the
  vault itself rather than a UEFN project, or wants those run from within a project session.
- **The second brain isn't write-only.** `coder` also queries it (via `second-brain-librarian`)
  before implementing a common device/mechanic pattern from scratch, to check whether a
  ready, current Verse implementation already exists to adapt instead — see `coder.md` step 5.
  `project-bootstrap` queries it during its A4 retention step, to prefer proposals with a
  track record on other projects over purely theoretical ones — see `project-bootstrap.md`'s A4.
  Neither is required to query every time; it's a time-saver when the pattern is common enough
  to plausibly already be catalogued, not a mandatory step for every task.
- **Never block on this.** If the vault path is unreachable (wrong path, drive not mounted,
  Obsidian vault moved), `second-brain-librarian` reports that and stops — `coder` and
  `project-bootstrap` treat a handoff exactly like a missing/misconfigured `uefn-lessons` file:
  note it once and move on, this is a nice-to-have layer on top of the actual UEFN work, never a
  reason to stop or fail a task.
- **Never write to `raw/` or `output/` in the vault** (beyond the `_COMPILED` rename `compile`
  itself does): those are the owner's own inbox and scratch space per that vault's `CLAUDE.md` —
  only `wiki/` (plus its indexes) is this integration's target.

## 12. Recognizing UEFN brand collections — optional

Epic partners with real-world franchises ("Game Collections" — TMNT, LEGO, Fall Guys, Star Wars,
KPop Demon Hunters, Squid Game, The Walking Dead Universe, Rocket Racing, and others added over
time) for exclusive assets/devices used to build themed "brand islands." `project-bootstrap`
checks for this during its A1 structure-mapping step whenever a project's folders/devices/
template name look brand-themed — see `~/.claude/skills/brand-collections-uefn/SKILL.md` for the
marker table (confirmed technical markers for some collections, name-only for others not yet
confirmed against a real project) and the procedure for capturing real markers straight from a
project when an unrecognized brand shows up, writing them both to that skill's own reference file
(works immediately, no vault needed) and, if the second brain (rule 11) is configured, to a
`type: pattern` article there via `second-brain-librarian` for cross-machine reuse. This never
blocks or fails a task — an unmatched brand-looking name is just noted in `SPEC.md`, not treated
as an error.

## 13. Plan-first: no code without a tracked task

Every change to a project's code/devices is tied to a task row in `Claude/docs/ROADMAP.md`'s
`Tasks` table (ID, Feature, Status, Acceptance criteria, Priority) — the code follows the task,
never the other way round. This applies to `coder` (and, through it, `coder-prep`); it doesn't
apply to `growth-manager`'s marketing/growth work, `second-brain-librarian`'s vault work, or a bug
fix small enough to stay inside `BUGS.md`'s own severity-ordered queue rather than becoming its
own release-tracked feature.

**Who owns what in ROADMAP.md's Tasks table**: `planner-docs` is the only one who creates a task
row or edits its Feature/Acceptance criteria/Priority, and the only one who ever sets a task to
**Fatto**. `coder` may flip a task's own Status between **Da fare** / **In corso** / **Bloccato**
directly — a narrow, mechanical exception (same shape as `growth-manager`'s `Resources/`/`keyArt`
exception elsewhere in this kit): it's allowed to move the workflow marker on a task it's actively
working, never to touch the row's content or invent a new row.

**The gate**: before writing any code, `coder` finds the matching task ID in ROADMAP.md. If none
exists yet, it stops and says so instead of guessing or improvising a task — the fastest path is
usually asking the owner right there in conversation to describe the task so `planner-docs` can
open it (a quick, one-line acceptance criterion is enough; this is meant to take seconds, not
become paperwork). Once a task exists, `coder` writes its ID to `Claude/docs/.active-task`, flips
it to **In corso**, invokes `intent-gate` for an independent ambiguity check before touching
anything (see rule 13a below), does the work (compile-fix loop, all as already specified in
`coder.md`), and once `intent-reviewer` and then `compliance-reviewer` both return PASS, hands off
to `planner-docs` to mark the task **Fatto** and record it in `STATUS.md` — `coder` never sets
Fatto itself, since that's the point where the work has been independently verified on two
separate axes (intent, then mechanics), not just self-reported done.

### 13a. Two independent gates, not one combined check

Verifying a task's output is split across three agents, each with a narrower job than the whole:

- **`intent-gate`** — runs BEFORE `coder` writes anything. Checks whether the task's acceptance
  criteria (and any owner-supplied base code) are concrete enough to implement without guessing.
  An AMBIGUO verdict goes to the owner directly, not through `coder`'s own judgment of which
  reading is more plausible.
- **`intent-reviewer`** — runs after `coder` finishes, before anything else. Checks ONLY whether
  what was built matches the task's acceptance criteria — no mechanical rules yet.
- **`compliance-reviewer`** — runs only after `intent-reviewer` has already returned PASS on the
  same task. Checks the mechanical rules (logger, naming, header documentation, multiplayer
  authority, state machine, deprecated APIs, DemoDisplay, second-brain compliance).

This exists because a single combined reviewer checking spec adherence as one item among several
mechanical ones let a guessed integration through once, PASSed on rule-conformance alone — see
`intent-reviewer.md`'s own "why this agent is separate" section for the incident. Splitting the
check into two agents with a hard precondition between them makes the ordering structural instead
of a convention inside one agent's checklist: `compliance-reviewer` has nothing to review, and
shouldn't be invoked, until `intent-reviewer` has already PASSed the same task.

**`Claude/docs/.active-task`**: a one-line file holding the task ID `coder` is currently working,
written by `coder` when it flips a task to In corso. `intent-reviewer` and `compliance-reviewer`
cross-check the task ID `coder` reports against this file instead of trusting the report alone —
closes the small gap between "what coder did" and "what coder says it did."

**`Claude/docs/.task-verdicts`**: an append-only log, one line per verdict, in the form
`<ISO8601 timestamp> <intent-reviewer|compliance-reviewer> <task-id> <PASS|REJECTED> <attempt-n>`.
Each reviewer appends its own verdicts here directly — never edited or removed, only appended to.
`planner-docs` cross-checks this file against `coder`'s closing report before marking a task Fatto,
the same way `.active-task` closes the gap on task identity: this closes the equivalent gap on
verdict history, so "both reviewers PASSed" is independently checkable rather than resting on
`coder`'s own relay of what each reviewer said.

**Bounded review cycles.** The REJECTED→fix→resubmit loop between `coder` and each reviewer has the
same 5-consecutive-attempt cap as `coder`'s own compile-fix loop (rule 10 above): past that, the
reviewer stops issuing new REJECTED verdicts and `coder` stops resubmitting — the unresolved items
go to `Claude/docs/BUGS.md` and the owner decides how to proceed, exactly like a stuck compile
error. This keeps every retry loop in the kit bounded, not just the compile one.

**`STATUS.md`'s "Current state" block** (top of the file, replaced on every update — the dated log
below it is what's append-only) must always answer, at a glance: what's in progress, what's
planned next for the current release/MVP, what's done so far this release, and the recommended
next step. `planner-docs` keeps this current every time it touches the file — this is what makes
closing a session and reopening it later (or on a different machine) immediately legible, without
reading the whole log.

**`release-gate`** checks task completeness explicitly: every task whose Priority matches
ROADMAP.md's "Current MVP / release target" must be Status **Fatto**, or it's listed as missing
against the plan — this is on top of, not instead of, its existing bug/multiplayer/performance
criteria. A task marked Fatto without recorded PASS verdicts from both `intent-reviewer` and
`compliance-reviewer` is flagged too, the same way a missing task would be.

This rule exists specifically to cut down on repeated manual hand-offs and rediscovering context
between sessions: a task's ID, status, and acceptance criteria are the one thing that should never
need re-explaining from scratch, on this machine or a new one.
