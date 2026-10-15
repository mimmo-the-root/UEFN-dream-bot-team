# The MCP engine

UEFN's MCP server is how the agents read and change what is inside UEFN: devices in the level, widgets, Verse files, assets, even a running session. It is the engine under almost everything the kit does, and it grows quickly.

## Why the kit maps it

Epic adds tools to the MCP faster than it announces them. A tool nobody knows about is a tool nobody uses. On the first full map, made on UEFN 42.40, the server offered **28 toolsets and 388 tools**, while the kit's own tool contracts documented **6**. That is under 2%.

So the kit does two things: it takes one complete map of the MCP, and from then on it tells you what changed.

## What is in it today

These families were seen in the first map. Read-only use is always fine; anything that writes, saves, builds or starts a session asks you first.

| Family | What it can do |
|---|---|
| Devices | Read and set device properties, wiring and events; place devices. |
| Widgets (UMG, Verse fields, view bindings, animations) | Read widget trees and fields, create and edit widget blueprints. |
| Verse | List and write Verse files, build the project. |
| Sessions | Start a session, push changes, read client logs. |
| Scene graph | Entities and their components. |
| Editor | Capture the viewport, read logs, run batches of calls. |
| Assets | Materials, Niagara, physics, data and curve tables, textures, meshes. |

Most of this is **not yet used by the kit**. Reading widget trees worked on the first test; writing is exposed but still to be tried. Starting a session, reading client logs and capturing the viewport look like the road to automatic playtests and screenshots, but that is a guess from the tool names, not something proven.

## The kit maps it by itself

You do nothing. At every session start the kit looks, in a fraction of a second, whether UEFN's MCP is answering. If it is, and the last full map is older than six hours, it maps the whole MCP in the background and tests the safe tools. It costs no AI tokens and never delays the session. If UEFN is closed it stays silent and tries again next time.

The kit saves:

- the **map**, a readable catalog grouped by toolset, with a read or write guess for each tool, whether it was tested, and a mark on the ones the kit already uses;
- the **news**: the tools added, removed or changed since the last map, with a line on what each new tool does;
- the **history**: the previous map, and a line in a change log for every change, with the date and the UEFN version.

This works on its own, whether or not a new kit release is published: it reads your UEFN, not the kit repository.

The MCP belongs to UEFN, not to a project, so there is **one map for all your projects**. It lives in `.claude\skills\mcp-tool-contracts\references\map\` in your user folder. The descriptions in it are Epic's text, so this folder stays on your computer and is never published or copied into a project.

## The tests

The kit also tests the MCP, safely. It only calls tools that are read-only (the server says so, or the name starts with get, list, find, describe, query, search, count, is or has) and that need no arguments. Writing tools are never called. Each result is recorded, and a tool that worked last time and fails now is reported as **stopped working**: that is how you notice an UEFN update that broke something before it breaks your session.

You can see the numbers on the **Skills** page of the console, in the UEFN MCP section: how many tools the kit uses out of the total (this share is recomputed at every map, so you see it grow as the kit learns to use more), what the tests found, and the latest news.

## How the agents use it

The coder, the QA agent and the bootstrap agent are told: before doing something through UEFN, search the map (`mcp_map.py --find` followed by a few words) and prefer a purpose-built tool to a workaround. They never guess a tool name. When the map finds news at the start of a session, the agent tells you in two lines what is new and what it could do for your maps, and only proposes.

## Noticing what changed

The map refreshes itself, so the news arrive the next time you open a session after UEFN was open. `/mcp-snapshot` does the same right away if you do not want to wait. `/kit-doctor` adds a note when there is no map yet, or when UEFN has not been open for a month. It is a note, never a problem.

## What happens with the news

1. The agent tells you what is new and what it could be used for. Nothing changes because of it without your yes.
2. When a tool proves useful, it goes into the kit's tool contracts, so every agent uses the same one and the same way.
3. Tools the kit relies on are listed in `Claude/reference/mcp-known-tools.json`; that is what the "kit uses" count is based on.

> **Warning** Writing tools change your project. Save only the paths you changed: an empty list saves every unsaved asset in the project, including work you did not mean to save. The agents are told this, and it is worth knowing yourself.

> **Note** If UEFN is closed or the MCP is not reachable, the map is not made and nothing is guessed. An old map is better than an invented one.

## The exploration lab

To learn what a tool really does, the kit has a lab module (`Claude/hooks/mcp_lab.py`). An agent uses it to call any MCP tool; every call is written to `Claude/logs/explore-ledger.jsonl`, and the safety rules live in the code, not in a request.

- **In a real project** the lab only writes inside a `KitTest` folder, needs a switch for level and play-session tools, and never deletes.
- **In a laboratory project** (a clean project you can throw away) you set `LAB_AGGRESSIVE=1` and `LAB_ROOT=/<project name>` and create the file `Claude/LAB-PROJECT.txt`. The lab starts only if that file exists and the open level is really inside that project. Then it can delete, place devices, run game sessions, edit Verse and run Python. It never quits or restarts the editor and never touches a disk path outside the project.

What an exploration finds is written once, per area, in the kit (`mcp-tool-contracts/references/areas/`), so nobody repeats the work. The mission to give to the explorer is in `mcp-tool-contracts/references/exploration-mission.md`.

## Long batteries

In a laboratory project the kit can test the whole toolset without anyone writing a test per tool. `Claude/hooks/mcp_cover.py` reads each tool's input and output schema, notices which tools produce which kind of object (a tool that returns a widget blueprint can make the fixture another tool needs), builds those fixtures, and calls every tool, in several passes. Destructive tools run last, and listing tools are limited to a test folder so they cannot return the whole engine. The result is `Claude/docs/mcp/COVERAGE.md`: how many tools answered, how many are alive but still need a recipe, and which kinds of object we cannot make yet.

Three more suites repeat things to find what a single call hides: `soak` repeats create, edit, compile, save and delete many times and warns if the editor gets slower; `session` runs the game-session loop several times with timings and always stops the session; `mapcheck` confirms the saved map still matches the server.

`Claude/hooks/mcp_queue.py` runs them one after the other. Start it in a second terminal and it waits, spending no tokens, until the exploration is finished, then runs the four suites and writes `QUEUE-REPORT.md`.
