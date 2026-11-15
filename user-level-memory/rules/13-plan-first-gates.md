<!-- Full text of base rule 13. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 13. Plan-first: no code without a tracked task

Every change to a project's code/devices is tied to a task row in `Claude/docs/ROADMAP.md`'s
`Tasks` table (ID, Feature, Status, Acceptance criteria, Priority) — the code follows the task,
never the other way round. This applies to `coder` (and, through it, `coder-prep`); it doesn't
apply to `growth-manager`'s marketing/growth work, `second-brain-librarian`'s vault work, or a bug
fix small enough to stay inside `BUGS.md`'s own severity-ordered queue rather than becoming its
own release-tracked feature.

**Who owns what in ROADMAP.md's Tasks table**: `planner-docs` is the only one who creates a task
row or edits its Feature/Acceptance criteria/Priority, and the only one who ever sets a task to
**Done**. `coder` may flip a task's own Status between **To do** / **In progress** / **Blocked**
directly — a narrow, mechanical exception (same shape as `growth-manager`'s `Resources/`/`keyArt`
exception elsewhere in this kit): it's allowed to move the workflow marker on a task it's actively
working, never to touch the row's content or invent a new row.

**The gate**: before writing any code, `coder` finds the matching task ID in ROADMAP.md. If none
exists yet, it stops and says so instead of guessing or improvising a task — the fastest path is
usually asking the owner right there in conversation to describe the task so `planner-docs` can
open it (a quick, one-line acceptance criterion is enough; this is meant to take seconds, not
become paperwork). Once a task exists, `coder` writes its ID to `Claude/docs/.active-task`, flips
it to **In progress**, invokes `intent-gate` for an independent ambiguity check before touching
anything (see rule 13a below), does the work (compile-fix loop, all as already specified in
`coder.md`), and once `intent-reviewer` and then `compliance-reviewer` both return PASS, hands off
to `planner-docs` to mark the task **Done** and record it in `STATUS.md` — `coder` never sets
Done itself, since that's the point where the work has been independently verified on two
separate axes (intent, then mechanics), not just self-reported done.

### 13a. Two independent gates, not one combined check

Verifying a task's output is split across three agents, each with a narrower job than the whole:

- **`intent-gate`** — runs BEFORE `coder` writes anything. Checks whether the task's acceptance
  criteria (and any owner-supplied base code) are concrete enough to implement without guessing.
  An AMBIGUOUS verdict goes to the owner directly, not through `coder`'s own judgment of which
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
written by `coder` when it flips a task to In progress. `intent-reviewer` and `compliance-reviewer`
cross-check the task ID `coder` reports against this file instead of trusting the report alone —
closes the small gap between "what coder did" and "what coder says it did."

**`Claude/docs/.task-verdicts`**: an append-only log, one line per verdict, in the form
`<ISO8601 timestamp> <intent-reviewer|compliance-reviewer> <task-id> <PASS|REJECTED> <attempt-n>`.
Each reviewer appends its own verdicts here directly — never edited or removed, only appended to.
`planner-docs` cross-checks this file against `coder`'s closing report before marking a task Done,
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
ROADMAP.md's "Current MVP / release target" must be Status **Done**, or it's listed as missing
against the plan — this is on top of, not instead of, its existing bug/multiplayer/performance
criteria. A task marked Done without recorded PASS verdicts from both `intent-reviewer` and
`compliance-reviewer` is flagged too, the same way a missing task would be.

This rule exists specifically to cut down on repeated manual hand-offs and rediscovering context
between sessions: a task's ID, status, and acceptance criteria are the one thing that should never
need re-explaining from scratch, on this machine or a new one.
