# Roadmap

<!-- Owned by planner-docs: it creates new task rows (ID, Feature, Acceptance criteria, Priority)
     and is the only one who marks a task "Done" or edits its Feature/Acceptance
     criteria/Priority. coder may flip a task's own Status between "To do" / "In progress" /
     "Blocked" while working on it — a narrow, mechanical exception (see coder.md and CLAUDE.md
     rule 13), never touching Feature/Acceptance criteria/Priority, and never inventing a new row.
     No code gets written against a task that doesn't already have a row here with a real ID. -->

## Project goal
(What the experience/project should do once finished)

## Current MVP / release target
(Which Priority the current push is aiming to finish — e.g. "MVP" — so release-gate knows what
"this release" means when checking task completeness below.)

## Tasks

| ID | Feature | Status | Acceptance criteria | Priority |
|---|---|---|---|---|
| T-001 | (example — replace) | To do | (short, verifiable — "the player can X and Y happens") | MVP |

Status values: **To do** (not started) / **In progress** (coder is actively on it — flips this
itself) / **Blocked** (blocked — coder flips this and says why in STATUS.md) / **Done** (done —
only planner-docs sets this, only after both intent-reviewer and compliance-reviewer return PASS on the task's work).

ID format: `T-<3 digits>`, assigned once, never reused or renumbered even if a task is later
dropped (mark it "Out of scope" below instead of deleting its row, so old references in
STATUS.md/BUGS.md still resolve).

## Out of scope (for now)
- ...
