# Debug exchange rule

The planner (the person or session that plans and reviews) and the agent (the coding session in the project) exchange information for debugging and for improving the kit through six standard files. Nothing else is needed: if it is not in one of these files, the other side does not know it. Every file is plain text, one line per entry, appended at the bottom, never rewritten except where noted.

Which files the agent writes is controlled by the flags in `Claude/config/kit-settings.json` (section `debug`); see the kit settings rule.

## The six files

### 1. relay/* (mailbox)
- Path: `Claude/relay/` with the folders `inbox`, `running`, `done`, `outbox`.
- Writer: the planner puts packages in `inbox`; the agent moves them to `running`, then `done`, and puts reports in `outbox`.
- Reader: both sides.
- Format: one package per file, `NNN-title.md`, header lines `id:`, `title:`, `do:`, `report:`, `approved:`, `after:`.
- When: every poll; the agent never starts a package that is not approved.

### 2. plan/NUDGE.md
- Writer: the planner. Rewritten as a whole, not appended.
- Reader: the agent, at every relay poll.
- Format: a title line, an `Updated:` line, then numbered rules and the current go/stop order.
- When: the planner changes priorities or rules.

### 3. plan/ANSWERS.md
- Writer: the planner. Newest at the bottom.
- Reader: the agent, at every step.
- Format: `<date time> | <TOPIC>: <answer>`.
- When: the agent asked a question (Q line) or hit a recurring problem.

### 4. plan/FEEDBACK-FROM-COD.md
- Writer: the agent. Append only.
- Reader: the planner, at every check.
- Format: a wave line `time | agents_in_flight | done | running | blockers | needs`, a question line `Q: <question>`, and a choice line `DECISION: <what was unclear, what was chosen>`.
- When: after each finished wave; every Q and every DECISION at once.

### 5. plan/PROBLEMS-FROM-COD.md
- Writer: the agent. Append only.
- Reader: the planner, who acts on each line.
- Format: `<date time> | <task or package id> | <problem> | <what was tried> | <what is needed, or NONE>`.
- When: something failed, conflicted or is blocked.

### 6. plan/PENDING-TESTS.md and logs/task-status.log
Two small logs of work state:
- `plan/PENDING-TESTS.md`: the agent appends `<date time> | <package id> | <exact command that was blocked> | <what it should prove>` for a test it could not run; the planner runs it and reports in ANSWERS.
- `Claude/logs/task-status.log`: written by `Claude/hooks/task_status.py` only, one line `<date time> <T-id> -> <state> <note>`; the planner and the console read it. Never edit by hand.

## Templates
A new project gets empty files with headers for `FEEDBACK-FROM-COD.md`, `PROBLEMS-FROM-COD.md` and `PENDING-TESTS.md`, and an `ANSWERS.md` that carries the debug-flags rule, under `Claude/plan/` (see `project-template/Claude/plan/`). `NUDGE.md` is created by the planner when the first order is written.
