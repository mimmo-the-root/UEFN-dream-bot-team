# Roadmap

<!-- Owned by planner-docs: it creates new task rows (ID, Feature, Acceptance criteria, Priority)
     and is the only one who marks a task "Done" or edits its Feature/Acceptance
     criteria/Priority. coder may flip a task's own Status between "To do" / "In progress" /
     "Blocked" while working on it — a narrow, mechanical exception (see coder.md and CLAUDE.md
     rule 13), never touching Feature/Acceptance criteria/Priority, and never inventing a new row.
     No code gets written against a task that doesn't already have a row here with a real ID. -->

## Project goal
(What the experience/project should do once finished)

## Current phase and release
(The Active phase and the release being built, e.g. "Phase 0 - MVP, release P0-R1". release-gate uses it to know
what "this release" means.)

## Phases

<!-- DELIVERY STANDARD (planner-docs owns this section; the Agent Console shows it):
     ONE table, columns: ID | Phase | Goal | Exit criteria | Status. IDs are PH-0, PH-1, PH-2 (add PH-3.. only if needed).
     Status starts with Planned / Active / Done. Exactly one phase is Active.
     Releases inside a phase are named P<phase>-R<n> (P0-R1, P1-R1, P1-R2...). Plan the releases of the Active phase and of
     the next one only. Everything else is backlog: Release = Later. A request that arrives mid-release goes to Later
     unless the owner says what it replaces. Phase exit: planner-docs proposes it, the owner confirms. -->

| ID | Phase | Goal | Exit criteria | Status |
|---|---|---|---|---|
| PH-0 | Phase 0 - MVP | The smallest playable version, to learn whether the idea works | One playtest with up to 3 players completes the core loop without a blocking bug, and the owner decides: go on, change, or stop | Active |
| PH-1 | Phase 1 - Launch | Publishable and stable: onboarding, base balance, no blocking bugs | (set when Phase 0 closes) | Planned |
| PH-2 | Phase 2 - Growth | Retention, content, events | (set when Phase 1 closes) | Planned |

## Tasks

<!-- FORMAT CONTRACT (the Agent Console reads exactly this; run `python Claude/hooks/docs_lint.py` after every edit):
     ONE table under this heading, columns in this order: ID | Feature | Status | Acceptance criteria | Priority | Release.
     The Release cell is never empty: P0-R1, P1-R2... or Later (the backlog). The console groups tasks by it.
     Never add a second tasks table, never move tasks into prose sections, never rename or reorder columns. -->

| ID | Feature | Status | Acceptance criteria | Priority | Release |
|---|---|---|---|---|---|
| T-001 | (example — replace) | To do | (short, verifiable — "the player can X and Y happens") | MVP | P0-R1 |

Status values (the cell must START with one of these words; any note goes after it, e.g. "Done - verified in play"): **To do** (not started) / **In progress** (coder is actively on it — flips this
itself) / **Blocked** (blocked — coder flips this and says why in STATUS.md) / **Done** (done —
only planner-docs sets this, only after both intent-reviewer and compliance-reviewer return PASS on the task's work).

ID format: `T-<3 digits>`, assigned once, never reused or renumbered even if a task is later
dropped (mark it "Out of scope" below instead of deleting its row, so old references in
STATUS.md/BUGS.md still resolve).

## Out of scope (for now)
- ...
