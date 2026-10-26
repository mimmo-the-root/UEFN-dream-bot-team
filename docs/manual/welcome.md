# What this kit is

A team of 22 AI agents for your UEFN maps, a console to watch them work, and a kit that learns from every map you build.

Dream Bot Team is a setup for [Claude Code](https://claude.com/claude-code) made for UEFN (Unreal Editor for Fortnite). Instead of one assistant doing everything, you get specialists with one narrow job each: one writes the Verse code, others check it, one keeps your plan and documents honest, one gives a go or no-go before a release. It was built by a creator juggling about 50 islands, to keep them from getting mixed up.

## What it does for you

- **Writes and fixes Verse code in a safe loop.** The coder agent follows a compile-and-fix cycle, and two independent reviewers check every task before it counts as done.
- **Keeps a plan.** Every change starts from a task in `Claude/docs/ROADMAP.md`. The agent that writes code never opens or closes tasks on its own say-so.
- **Finds regressions after every playtest,** automatically, and updates your documents.
- **Learns from your maps.** It reads your Verse code, your documents and your devices, and proposes lessons for your genre. You approve them. See [Skills and lessons](ch:skills-and-lessons).
- **Shows you what is happening.** A local console lights up each agent while it works. See [The console](ch:the-console).
- **Helps the map get found,** with eight growth skills for titles, thumbnails, trailers, launch plans and patch notes.

## What it does not do

- It does not replace UEFN or Claude Code. It runs inside Claude Code, in a terminal opened in your project's `Content/` folder.
- It does not send anything to anyone by itself. Sharing lessons with the community is on by default but nothing leaves until you press a button, lessons only, and only after you press a button. See [Community](ch:community).
- Every real change still goes through you. The console says it plainly: *every real change still waits on you*.

> **Note** The kit is free and open source under the MIT License. It is not affiliated with Epic Games.

## What you need

- UEFN installed, with the project you want to work on.
- Claude Code, signed in.
- Python 3, used by the console server and the learning scripts. Windows is the main platform; `.sh` versions of the hooks exist for macOS and Linux.

Ready? Go to the [quick start](ch:quick-start).
