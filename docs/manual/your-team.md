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
| growth-manager | Sonnet | Everything about getting the map found and played: titles, thumbnails, trailers, launch plans. |
| materials-expert | Sonnet | Audits and reuses materials in the project. |
| template-reader | Sonnet | Reads an Epic template, read only. |
| second-brain-librarian | Sonnet | Optional: keeps a shared Obsidian vault of reusable mechanics. |
| second-brain-trainer | Sonnet | Optional: a deliberate sweep of the project to fill that vault. |
| second-brain-scout | Haiku | Internal helper of the trainer: analyses one area, read only. |

Haiku is the lighter, cheaper model; Sonnet is the stronger one. No agent uses Opus.

> **Tip** Agents that only check keep their reports short on purpose: their report lands in your main session, the most expensive place to spend words.

## The five MCP sub-agents

Five of the twenty-two are sub-agents that do the hands-on work through UEFN's MCP. You do not call them yourself: the `coder` calls them, one narrow task each (about 15 MCP calls, a reply of 10 lines at most), and assembles the result. Only one of them writes at a time, because the editor is a single shared instance.

| Sub-agent | Model | Job |
|---|---|---|
| mcp-build | Haiku | Verse writes, `BuildAll`, scripting batches. |
| mcp-session | Sonnet | Play-in-editor smoke test and the log verdict. |
| mcp-level | Sonnet | Actors, devices, event bindings, entities, meshes, physics assets. |
| mcp-ui-assets | Haiku | Widget Blueprints, assets and data tables. |
| mcp-material-vfx | Haiku | Materials, material instances and Niagara. |

## What reports tell you

The audit agents (`qa-regression`, `release-gate`, `codebase-auditor`) end every report with two lines: what they **verified** and what they did **not** verify. A pass is never silent about what it did not check.

## Overriding an agent for one project

Create an agent with the same name in that project's `.claude/agents/` folder. It wins there and only there.
