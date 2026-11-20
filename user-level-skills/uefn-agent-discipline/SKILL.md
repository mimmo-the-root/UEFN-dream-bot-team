---
name: uefn-agent-discipline
description: Efficiency and evidence rules for agents working on an island, including batching reads, never repeating a search, owning a lane and proving a result before it is called done. Use when an agent redoes work, floods context, edits outside its lane or claims success without a read-back.
---

# Agent discipline on an island

## Result

Less repeated work, visible decisions and a result that can be checked. Reads are batched, searches happen once, each agent edits only its own lane, and every claim of completion points at something the owner can inspect. In a live editor, the order of tools matters as much as the tools themselves.

## When to use

- Several agents or tools are working on the same island at once.
- Context is filling with files and searches that were already read.
- A change is about to reach a running editor or a player session.
- A report says "done" but contains no evidence.

**When not to use:** a single-line fix in one file, a question that needs no tool, or a conversation about design where no code or device will change. For narrow vault questions use `second-brain-query`; for token habits while coding use `token-aware-coding`.

## Workflow

1. Read only what the task needs. Prefer a targeted search to opening a whole file, and never re-read a section already in context.
2. Load the relevant skill before guessing an API or a device behaviour. If no skill covers it, say so rather than inventing a rule.
3. Batch independent reads in one request. Run dependent calls in order and use each result before planning the next step.
4. Search once per question. If the answer was not found, change the question or ask the owner; do not repeat the same search.
5. Ask the owner at most once per blocked decision. While blocked, keep working on the parts that are not blocked.
6. Stay in your lane: edit only the files and devices assigned to you. Another agent's lane is read-only.
7. Keep command output visible. A hidden failure is a failure that will be discovered after publish.
8. Use the smallest sufficient tool for the editor: check readiness first, go through the mapped editor call, and treat direct Python inside the engine as the last resort.
9. Commit small, reviewable steps with a clear message. Never leave unrelated changes in the same commit.
10. End with evidence: the read-back, the build result, the log line or the reviewer verdict. If there is no evidence, the task is still open.

## Errors (symptom, cause, remedy)

- **The same file is read three times:** no note of what was already loaded. Track loaded sections and reuse them.
- **Two agents overwrite each other:** lanes were not assigned or were ignored. Stop both, compare the changes and redo from separate lanes.
- **Editor call fails after an update:** the tool map changed. Recheck `mcp-tool-contracts` before rewriting code.
- **Direct editor scripting was used first:** the mapped tool was not tried. Undo the script if possible and use the supported path.
- **Report says done with no proof:** step 10 was skipped. Add the read-back or log, then re-report.
- **The owner is asked the same question twice:** the first answer was not recorded. Write the decision in the task notes before continuing.

## See also

`token-aware-coding`, `mcp-tool-contracts`, `uefn-mcp-lab-guard`, `uefn-editor-dispatch`, `uefn-plan-verify`, `second-brain-query`
