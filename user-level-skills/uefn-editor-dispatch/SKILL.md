---
name: uefn-editor-dispatch
description: Routes every UEFN editor operation through one checked entry point and keeps calls that fight over the same island from overlapping. Use when placing actors, editing assets, starting a session, or batching MCP tools that touch the same level.
---

# UEFN editor dispatch

## Result

One door, one order. Every call that can change the island passes through a single decision point that checks editor readiness and tool compatibility first. Two operations that touch the same actor, device, level or asset are queued rather than launched together. Reads that cannot change state stay outside the queue.

## When to use

- A change is about to reach a live editor: actors, devices, assets, materials, widgets or Verse files.
- Several MCP calls are planned in one request, and some of them depend on earlier results.
- A session is starting or stopping while another operation may still be running.

**When not to use:** reading logs or inspecting a value without writing (use `uefn-editor-logs`), deciding which tool exists for a job (use `mcp-tool-contracts`), or a heavy read that needs filtering rather than ordering (use `uefn-mcp-heavy-calls`).

## Workflow

1. Split the work into reads and writes. Only writes need the door; keep reads cheap and parallel when they are independent.
2. Check that the editor is present and the expected island is open. If it is not, stop and report it instead of retrying against a different project.
3. Name the resource each write will touch: actor, device, asset path, Verse file or session. Two writes with the same resource are incompatible.
4. Order compatible writes so each one sees the result of the previous one. Never assume a batched script commits step by step.
5. Send one write at a time through the door. Record what it returned before starting the next one.
6. Read back the changed thing. A call that returned success is not proof that the island changed.
7. If the editor rejects a call, stop the queue. Fix the first failure, then restart from the state you actually observed.

## Errors (symptom, cause, remedy)

- **Two calls race and one silently wins:** they targeted the same resource in one batch. Serialize them and read back after each.
- **Change lands in the wrong project:** the open island was not checked. Verify the project before the first write, not after the last.
- **Tool not found after an update:** the tool map changed. Recheck `mcp-tool-contracts` before rewriting the call.
- **Editor is busy and every retry fails:** an earlier session is still running. Wait for the session state, do not stack new calls.
- **Write reported success but nothing changed:** no read-back. Add a read of the actor, property or file after the call.
- **Queue grew during a failure:** retries were added on top of pending calls. Clear the pending list and re-plan from the last confirmed state.

## See also

`mcp-tool-contracts`, `uefn-mcp-lab-guard`, `uefn-scripting-batch`, `uefn-session-regression`, `uefn-level-devices`, `uefn-verse-build`
