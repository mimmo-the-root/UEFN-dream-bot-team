---
tags: [kit, manual]
created: kit-1.115.0
updated: kit-1.115.0
sources: [docs/manual/uefn-map-project.md]
type: kit
status: current
---
# A UEFN map project

What the kit puts in a project that is a **map** (an island you will play and publish), and which documents it produces.

## Setting it up

Open a session from the `Content` folder of the project. If the project has no kit yet, the kit asks whether it is a map or a Fab product. Answer **map** and it shows how many files it would copy, asks for your yes, copies the contents of `project-template/` into `Content/` (never overwriting a file that already exists) and runs the setup steps. The hooks start working from the next session. The manual way is in the *Quick start*.

## Learning from the map

The kit reads the Verse code, the documents and the devices at every session start. To do it right now press **Learn from this map** on the Skills page: the kit prepares the recipes of your devices and mechanics by itself, and the agent finishes the learning at the end of its next answer (blueprint and how-to lessons). You approve the result in the tab *To approve*.

## What is in the project

| Where | What |
|---|---|
| `CLAUDE.md` | The project's identity and the rules the agents follow. |
| `.claude/` | Commands (`/verse-check`, `/handoff`, `/devlog`, `/jam-check`, `/concept-card` and more) and the pre-approved safe commands. |
| `Claude/hooks/` | The scripts and the console pages. Updated by the kit itself. |
| `Claude/docs/` | The project's own documents, listed below. This is YOUR data: the kit never overwrites it. |
| `Claude/logs/` | Logs: Verse changes, build errors, console events. |

## The documents the kit produces

- **`SPEC.md`**: what the map is and how it works.
- **`ROADMAP.md`** and **`STATUS.md`**: the plan and where you are in it.
- **`BUGS.md`**: known problems, with the resolved ones condensed.
- **`RETENTION-NOTES.md`**, **`RELEASE-READINESS.md`**, **`TEST-PLAN.md`**, **`DESIGN-SYSTEM.md`**, **`DEPENDENCY-MAP.md`**: filled in as the work needs them.
- **`map/`**: a map of your Verse code and devices that the agents read instead of the whole project.
- **`HANDOFF.md`**: written by `/handoff` for the next session.
- **`concept-card.md`** and **`devlog.md`**: written by `/concept-card` and `/devlog`, mostly useful for a jam.
- **`archive/`**: old status entries and old header history moved out of the files agents read.

## The Verse files

Every Verse file starts with its name, an English summary that is always up to date, and the real date and version. No change history lives in the file: each change is one line in `Claude/logs/verse-changes.jsonl`.

## Why the kit lives inside the project

`Content` is the folder UEFN syncs, so documents and logs travel with the project when you change computer. A map is yours to publish, so having the kit's files in it is harmless. That is exactly what is NOT true for a Fab product: see the next chapter.

## Sources
- The kit manual, chapter "A UEFN map project" (docs/manual/uefn-map-project.md), kit v1.115.0. Rebuilt on every kit release: do not edit this page, edit the manual.
