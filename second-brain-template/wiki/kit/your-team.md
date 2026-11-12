---
tags: [kit, manual]
created: kit-1.123.13
updated: kit-1.123.13
sources: [docs/manual/your-team.md]
type: kit
status: current
---
# Your team

Twenty-two agents, each with one narrow job, so that the one who writes is never the one who approves.

You do not need to remember all of them. In day-to-day work you talk to Claude, and it calls the right agent. You can also ask for one by name.

## How to call an agent

- In plain words: *use the coder agent to add the respawn checkpoint*.
- By name, which guarantees the hand-off: `@"coder (agent)" add the respawn checkpoint`.
- Or just describe the task. Claude can pick the agent from each one's description.

## The path of one task

Every change follows the same five stages, shown live on the console:

1. **planner-docs** opens a task in the roadmap with its acceptance criteria.
2. **intent-gate** checks that the task is concrete enough to build without guessing.
3. **coder** writes the code and compiles it.
4. **intent-reviewer** checks that the result matches the acceptance criteria, line by line.
5. **compliance-reviewer** checks the kit's mechanical rules: logging, naming, multiplayer authority and so on. Only then does **planner-docs** mark the task Done.

> **Note** The coder never closes its own task. Two independent reviewers must pass it first.

## The agents and their models

Cost matters. The kit puts the cheaper model on work that is mostly checking or bookkeeping, and the stronger one where judgment and code are needed.

| Agent | Model | What it does |
|---|---|---|
| project-bootstrap | Sonnet | Use once, at the start of a project: maps existing code or asks the questions for a new one. |
| planner-docs | Haiku | Owns the roadmap and the status. Opens and closes tasks. |
| intent-gate | Haiku | Checks the task is clear before any code is written. |
| coder | Sonnet | Writes and fixes code, in a compile and fix loop. |
| coder-prep | Sonnet | Internal helper: writes one independent area of code in parallel. |
| intent-reviewer | Sonnet | First review gate: does it do what the task asked? |
| compliance-reviewer | Haiku | Second review gate: does it follow the kit's rules? |
| qa-regression | Sonnet | Finds regressions and unseen bugs after changes and playtests. |
| release-gate | Sonnet | Go or no-go before a release, from the project's own documents. |
| codebase-auditor | Sonnet | Independent audit of the whole codebase, on demand. |
| skill-reflector | Haiku | Proposes lessons for your genre after a real playtest. |
| learn-slicer | Sonnet | Internal: runs ONE slice of the map learning (a batch of code, a batch of documents, the devices, the blueprint) with a fresh context; started only by `/learn-map`. |
| growth-manager | Sonnet | Everything about getting the map found and played: titles, thumbnails, trailers, launch plans. |
| materials-expert | Sonnet | Audits and reuses materials in the project. |
| template-reader | Sonnet | Reads an Epic template, read only. |
| second-brain-librarian | Sonnet | Optional: keeps a shared Obsidian vault of reusable mechanics. |
| second-brain-trainer | Sonnet | Optional: a deliberate sweep of the project to fill that vault. |
| Explore | Haiku | Read-only search and reading: finds files, reads logs, lists what a folder holds, summarizes long documents. Use it instead of a general-purpose agent (which runs on the session's model and costs about ten times more for the same reading). It never edits or decides. |
| second-brain-scout | Haiku | Internal helper of the trainer: analyses one area, read only. |

Haiku is the lighter, cheaper model; Sonnet is the stronger one. No agent uses Opus.

> **Tip** Agents that only check keep their reports short on purpose: their report lands in your main session, the most expensive place to spend words.

## The five MCP sub-agents

Five of the thirty-two are sub-agents that do the hands-on work through UEFN's MCP. You do not call them yourself: the `coder` calls them, one narrow task each (about 15 MCP calls, a reply of 10 lines at most), and assembles the result. Only one of them writes at a time, because the editor is a single shared instance.

| Sub-agent | Model | Job |
|---|---|---|
| mcp-build | Haiku | Exploration lab: Verse writes, `BuildAll`, scripting batches, in a disposable lab project. Not used to build your game. |
| mcp-session | Sonnet | Play-in-editor smoke test and the log verdict. |
| mcp-level | Sonnet | Exploration lab: actors, devices, event bindings, entities, meshes, physics assets, in a disposable lab project. Not used to build your game. |
| mcp-ui-assets | Haiku | Widget Blueprints, assets and data tables. |
| mcp-material-vfx | Haiku | Exploration lab: materials, material instances and Niagara, in a disposable lab project. Not used to build your game. |

## The ten area agents

For your own game, ten more agents each own one area of UEFN's tools. The main session (or Cod as coordinator) hands one step to the right one; each reads back what it changed and answers in ten lines. The kit's guard refuses a tool that belongs to another agent and says who owns it, so two agents never fight over the editor. Reads of the editor core are open to all.

| Agent | Model | Owns |
|---|---|---|
| scene-scout | Haiku | Reads of the scene and assets; scene capture. Never changes anything. |
| env-builder | Sonnet | Actors, components, folders, data layers, camera, PCG, geometry, physics assets. |
| asset-builder | Sonnet | Materials, textures, data tables, collections, meshes, imports. |
| device-builder | Sonnet | Place devices, properties, event bindings, gameplay tags. |
| entity-builder | Sonnet | Scene Graph entities, components, prefabs. |
| verse-dev | Sonnet | Verse build, push, sessions, logs. |
| ui-builder | Sonnet | Widgets, view models, widget animations. |
| fx-audio | Sonnet | Niagara and MetaSound. |
| perf-profiler | Sonnet | Spatial Profiler and Insights measurements. |
| cinematics | Sonnet | Sequencer sequences, tracks, keys. |

## What reports tell you

The audit agents (`qa-regression`, `release-gate`, `codebase-auditor`) end every report with two lines: what they **verified** and what they did **not** verify. A pass is never silent about what it did not check.

## Overriding an agent for one project

Create an agent with the same name in that project's `.claude/agents/` folder. It wins there and only there.

## Spending fewer tokens

The session that writes stays on one model (Sonnet 5.5 at medium effort is enough for well-scoped coding) and stays the only one that writes in the editor. The savings come from who does the reading, not from a bigger model.

- **Reading goes to `Explore` (Haiku).** Finding files, reading logs, listing a folder or the level, summarizing long documents: ask for `Explore`, not for a general-purpose agent. Reading on Haiku costs about a tenth of reading on Sonnet. `coder`, the reviewers and the auditor keep their own models.
- **Do not set `CLAUDE_CODE_SUBAGENT_MODEL`.** Depending on the Claude Code version it can force every agent, the coder included, onto the small model without a warning.
- **Learning runs in slices** (`/learn-map`): one fresh `learn-slicer` per slice. The old single agent, resumed again and again, re-read 136k to 425k tokens at every resume and was the largest single cost in the measured project.
- **Keep the first message of a task short and exact**, with file names, so no agent has to scan the project.

### Measuring during a real job

Before changing anything else, take measures on real work (a game jam is a good one). For each finished task, add one line to `Claude/logs/token-notes.md`: date, task ID, model and effort of the session, which sub-agents ran (type and model), and the numbers from `/usage` (and `/context` at the start of the session). Compare tasks of the same size only.

What to test afterwards, one change at a time, against those lines:
1. Tasks with an automatic check (`/verse-check`, the tests, the Fab checklist): run at low effort and repeat at high effort only if the check fails.
2. `learn-slicer` on Haiku instead of Sonnet: keep it only if the proposals it queues stay as good.
3. `CLAUDE_CODE_SUBAGENT_EFFORT` (Claude Code 2.1.316 or later) for sub-agents, in a lab project first.
4. Moving the situational parts of the two `CLAUDE.md` files into references read on demand, after `/context` shows how large the fixed part really is.
A coordinator that starts writer agents is adopted only if it costs the same or less per finished task than the single writer, with the same final check.

## Sources
- The kit manual, chapter "Your team" (docs/manual/your-team.md), kit v1.123.13. Rebuilt on every kit release: do not edit this page, edit the manual.
