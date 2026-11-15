<!-- Full text of the project rule "Plan-first and the team". The short version is in this project's CLAUDE.md (KIT block team-roles); kit_sync keeps this file current. -->

# Plan-first and who does what

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
