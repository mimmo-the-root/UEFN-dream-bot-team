---
description: Break the approved plan into tasks (T-xxx) with verifiable criteria, stories, dependencies and parallel marks, ready for coder
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, Agent, AskUserQuestion
---

You turn the approved `PLAN.md` into the task list in `Claude/docs/ROADMAP.md`. The owner of that file is `planner-docs`: do it through that agent, which keeps the ID rules and the table contract. Run scripts from `Claude/hooks` (`py -3` on Windows).

**Gate.** `PLAN.md` must say `Approved: yes` and `CONSTITUTION.md` must exist. If not, say so in one line and stop: `/game-plan` first.

**Tasks.** For each story, P1 first, ask `planner-docs` to add rows to the ONE Tasks table, keeping its six columns (ID | Feature | Status | Acceptance criteria | Priority | Release). The extra information lives inside the Feature cell, as tags:
- `[S1]` the story the task belongs to (every task has one);
- `[P]` the task can run in parallel with others (different files, no dependency);
- `(after T-001, T-002)` the tasks that must be done first;
- `[R1]` the risk of the spec this task reduces (the first three tasks must cover every HIGH risk).
Order: shared foundations first (the Verse device, the area), then S1, then S2, S3. The P1 loop must not depend on a task of a later story. Priority MVP for S1, High or Medium for the rest; Release `P0-R1` for the MVP, `Later` for the rest. Each acceptance criterion is a test the owner can do in play or a check the kit can run ("the round ends at 3 minutes"), never a restatement of the feature name. Keep the manual steps of the plan as their own tasks (the owner does them).

**Check.** Ask `intent-gate` about every new task and rewrite the AMBIGUOUS ones. Then run `python docs_lint.py` and `python plan_check.py`; fix every CRITICAL and HIGH line (they stop `coder`). Show the list as a short table (ID, feature, story, after) and ONE question: approve the list, or change something. Only after the yes the tasks go to `coder`, one at a time, the first one being the one that reduces a high risk.

Never create `coder` work before the approval. Short report; name the file.
