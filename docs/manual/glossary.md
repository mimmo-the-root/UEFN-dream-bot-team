# Glossary

Short definitions of the words this manual uses.

## ***anonymized***
The word the kit writes in place of a personal identifier (a Windows user name, an email, a home path) in reports, documents and logs, following the GDPR (Regulation (EU) 2016/679) principle of data minimisation. In binary assets the name is overwritten with asterisks of the same length. It applies only to your own files, never to assets created by Epic.

## Agent
A helper with one narrow job and its own instructions, for example the coder or the QA agent. Agents are files in `~/.claude/agents/`. See [Your team](ch:your-team).

## Aura
The accent colour of the console (six choices, picked with small cubes under the title). Status colours are never part of it.

## Blueprint
What the kit learned about how a map of your kind is built: layout, game loop, devices and their wiring, rules with observed numbers, build order. Kept inside the genre skill and rewritten when your map changes.

## Console
The local web page, at `http://127.0.0.1:8765/`, that shows the agents working. See [The console](ch:the-console).

## Constitution
The one-page rules of a game, written by `/game-plan` in `CONSTITUTION.md`: principles with their reason, forbidden words, names and budget, and the Self-healing block. A plan or task that breaks it is a CRITICAL finding. See [From an idea to a playable game](ch:from-idea-to-game).

## Content folder
The `Content/` folder of a UEFN project. Claude Code is started here, and the kit's project files live inside it.

## Curator
A step in the community pipeline that proposes which lessons to promote. The maintainer validates every proposal before a release. See [Community](ch:community).

## Doctor
`/kit-doctor`, a command that checks the health of a project's kit files.

## Drift
The console button that lets the Aura fade by itself from one colour to the next.

## Five needs
What `/kit-doctor` checks in a project: instructions, state, verification, scope and hand-over.

## Game spec
`GAME-SPEC.md`, written by `/spec`: the idea, the loop, the stories, the success criteria and the risks. It says what the game is and why, never how it is built. Not the same as `SPEC.md`, which is deduced from existing code.

## Genre
One of Epic's official Discover genres. The kit asks you to confirm the genre and the map type before it saves anything.

## Hook
A command that Claude Code runs by itself when an event happens, such as the end of a playtest.

## Kit
This whole package: agents, skills, rules, project scaffold and console.

## Lesson
One short, general thing learned from a map, with a trust level. You approve, edit or reject each one. See [Skills and lessons](ch:skills-and-lessons).

## Loop (MVP)
The minimum playable game in five lines: Action, Rule, Reward, End, Replay (why you play again). The first story of the spec is the loop itself.

## Map type
A free name for the kind of map inside a genre, such as pillars or checkpoint-race.

## MCP
Model Context Protocol, the way Claude talks to a running UEFN editor. The server listens on port 8000. See [The MCP engine](ch:mcp-engine).

## Pilot demo
Chicken Roundup, a complete example (spec, constitution, plan, tasks, playtest checklist) shipped with the kit. `/demo` (or `/demo --auto`) runs it in a new empty test project, never into your real map.

## Pixel wave
A short wave of small translucent cubes that passes over a panel when its data changes.

## Plan
`PLAN.md`, written by `/game-plan`: per story the devices, Verse files, assets, manual steps, build order and the task that reduces each risk.

## Plan first
The rule that no code is written before a task with acceptance criteria is open in `ROADMAP.md`.

## Published map
A map that has an island code on Epic's side. Only lessons from a published map can be shared with the community.

## Readiness
One honest number out of 100 on the Score page: only proven work counts.

## Recipe
How to rebuild something (a device, a mechanic, a map template, a material), step by step, with its Verse code. Not the same thing as a lesson: a lesson is a short rule. See [Community](ch:community).

## Restore point
A snapshot of your Verse code and documents made with `/restore-point`.

## Second brain
A folder of plain text files (an Obsidian vault) outside any project, kept by `second-brain-librarian`. It holds what worked, what did not, the lessons and the kit's own knowledge, and every project reads it. Off until you give it a folder.

## Hot cache
`wiki/hot.md` in the second brain: a dozen lines on what you are working on, what changed last and what is still open. It is the first thing read in every session.

## Self-healing
The kit fixes small bugs by itself, only those on the closed list in the constitution (3 attempts per bug, 10 per session, with a restore point and an undo). Anything bigger is asked first.

## Skill
A folder of knowledge that Claude reads only when a task needs it. See [Skills catalog](ch:skill-catalog).

## Sources consulted
The section of the spec and of the plan that lists what the study step used (second brain, genre lessons, skills, recipes). "None found" is an honest answer.

## UEFN
Unreal Editor for Fortnite.

## Verse
The programming language of UEFN.
