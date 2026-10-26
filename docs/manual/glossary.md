# Glossary

Short definitions of the words this manual uses.

## Agent
A helper with one narrow job and its own instructions, for example the coder or the QA agent. Agents are files in `~/.claude/agents/`. See [Your team](ch:your-team).

## Blueprint
What the kit learned about how a map of your kind is built: layout, game loop, devices and their wiring, rules with observed numbers, build order. Kept inside the genre skill and rewritten when your map changes.

## Console
The local web page, at `http://127.0.0.1:8765/`, that shows the agents working. See [The console](ch:the-console).

## Content folder
The `Content/` folder of a UEFN project. Claude Code is started here, and the kit's project files live inside it.

## Curator
A step in the community pipeline that proposes which lessons to promote. The maintainer validates every proposal before a release. See [Community](ch:community).

## Doctor
`/kit-doctor`, a command that checks the health of a project's kit files.

## Genre
One of Epic's official Discover genres. The kit asks you to confirm the genre and the map type before it saves anything.

## Hook
A command that Claude Code runs by itself when an event happens, such as the end of a playtest.

## Kit
This whole package: agents, skills, rules, project scaffold and console.

## Lesson
One short, general thing learned from a map, with a trust level. You approve, edit or reject each one. See [Skills and lessons](ch:skills-and-lessons).

## Recipe
How to rebuild something (a device, a mechanic, a map template, a material), step by step, with its Verse code. Not the same thing as a lesson: a lesson is a short rule. See [Community](ch:community).

## Map type
A free name for the kind of map inside a genre, such as pillars or checkpoint-race.

## MCP
Model Context Protocol, the way Claude talks to a running UEFN editor. The server listens on port 8000. See [The MCP engine](ch:mcp-engine).

## Plan first
The rule that no code is written before a task with acceptance criteria is open in `ROADMAP.md`.

## Published map
A map that has an island code on Epic's side. Only lessons from a published map can be shared with the community.

## Restore point
A snapshot of your Verse code and documents made with `/restore-point`.

## Second brain
An optional Obsidian vault, kept by `second-brain-librarian`, where reusable mechanics are written once and found again in later projects.

## Skill
A folder of knowledge that Claude reads only when a task needs it. See [Skills catalog](ch:skill-catalog).

## UEFN
Unreal Editor for Fortnite.

## Verse
The programming language of UEFN.
