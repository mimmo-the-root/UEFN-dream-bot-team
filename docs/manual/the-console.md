# The console

A local web page that shows what your team is doing, what the kit has learned, and what changed.

The console runs on your own computer. It starts by itself when you open a session in a project, at `http://127.0.0.1:8765/`. Nothing in it is sent anywhere. Six pages share one menu at the top.

> **Tip** Open it as that web address, not as a file from your disk, and reload the page after a kit update.

## Console

The live view. Seventeen agents sit on a ring around the chief of staff, which is your main Claude session. An agent lights up while it works, and a pulse travels from one to another on a hand-off. Around the ring you also see the Obsidian Vault, you, and the UEFN MCP server.

- **Session running for** and **tokens this session** at the top. The token count is an approximation, summed from the session transcript.
- The **five-stage rail** follows the current task from intent-gate to planner-docs.
- The **activity log** on the right lists what each agent started and finished.
- A small light on each card: grey when idle, green while working, yellow while waiting for a helper, red when it has run suspiciously long.

Below the cards, **Tokens per agent (last 30 days)** opens a table with, for each agent, how many times it ran and how many tokens it used (input, output, cache read, cache write, total) and on which model. It is read from the transcripts Claude Code keeps for each helper, so it shows only what exists on this computer: if nothing is found, it says "not available" instead of zero. It counts tokens, not money, because prices change, and it leaves out your main session, which the box above already shows. The first opening can take a few seconds while older runs are read.

The long explanation of every animation is folded under **How to read this page**.

![The Console page while a task runs (demo data)](shot-console.png)

## Stats

Real numbers from Epic's public data about your island: plays, unique players, minutes played, minutes per player, favorites, recommends, peak players and day-1 and day-7 retention, over the last 7 days. Click a tile to see its chart.

Epic usually shows numbers only after the map is published and has had visitors, so a new map shows one message instead of empty tiles. The page needs the island code saved in the project.

![The Stats page (demo data)](shot-stats.png)

## Docs

The project's own documents, read from `Claude/docs/`: spec, status, roadmap, bugs and release readiness. It is a read-only view of what the agents keep up to date.

![The Docs page (demo data)](shot-docs.png)

## Flow

The whole pipeline: every agent and every hand-off, end to end, as an assembly line. Use it to see which agent comes after which.

![The Flow page (demo data)](shot-flow.png)

## Skills

What the kit has learned, in three parts:

- **The kit**: everything it knows across all your genres and maps.
- **This map**: the genre and type of the map you are in, its blueprint, and the lessons waiting for your approval.
- **Community**: the switch to share lessons, covered in [Community](ch:community).

The **SKILLS** tab blinks when something waits for you. More in [Skills and lessons](ch:skills-and-lessons).

![The Skills page (demo data)](shot-skills.png)

## What's new

The last release in plain words, the skills that improved, the top contributors, the thanks, and a link to submit an issue on GitHub. It also shows your own part: whether sharing is on, how many lessons you shared, and whether your map is published.

![The What's new page (demo data)](shot-news.png)

## Update banner

When your computer holds a newer kit version than the project you are in, the console says so. Run `/kit-update`, open a new session, and reload the page.
