---
description: Cut a big task into small pieces, each run in a fresh short session; failures are cut again or retried on other models, never a stop
argument-hint: <task id> [--mode free|auto|plan]
---

Use this for every task of size L, for any job that will need more than about 15 tool calls, and always when Cod works on
free models. A long session re-reads its whole conversation on every call (measured: 67% of each request); small pieces
with short notes do not.

Start the `piece-orchestrator` agent with the task id (and `--mode free` when the plan must not be used). It cuts the task
into 2-6 pieces and runs `python Claude/hooks/pieces.py run <task>`, which:

- runs each piece in a NEW short session that reads only its brief and the notes of the pieces before it;
- cuts a failed piece again into 2-6 smaller pieces (up to 3 levels): a failure means the piece was too big;
- tries a piece that still fails at the smallest size on at least 10 other free models, one after the other;
- skips it only when every model failed, tells the next pieces, and goes on: the run completes as many pieces as it can.

Without the agent (by hand): `pieces.py split <task> "goal | files | done when" ...`, then `pieces.py run <task>`;
`pieces.py status <task>` shows the tree. When no piece is left, the task goes to intent-reviewer, then
compliance-reviewer, as usual; skipped pieces are reported to the owner (expected / seen / tried).
