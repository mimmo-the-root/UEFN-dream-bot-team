# Questions and answers

## Does the kit change my map?

Only when you ask the coder for a change, and only through the editor's own tools. The kit also writes its own files: documents in `Claude/docs/`, logs in `Claude/logs/`, and the files it manages in `Claude/hooks/`.

## Does it cost money?

The kit is free (MIT license). You pay for Claude itself, as you normally would. The kit tries to keep that low: cheaper models for checks and helpers, task sizes, and history trimming. The [team chapter](ch:your-team) lists which model each agent runs on.

## Do I need Obsidian, an API key or a Discord account?

No to all three. The second brain is optional, the community curator's classifier needs an optional API key and the kit works without it, and Discord is only where questions are answered.

## Can I use it on several maps?

Yes, that is what it was built for. Do Phase 1 once and Phase 2 for each project. What the kit learns about genres is shared across your maps; each map's private notes stay inside that map.

## What leaves my computer?

Nothing, unless you switch on community sharing and press Contribute on a lesson, after seeing the exact text. Map names, code, blueprints and notes never leave. See [Community](ch:community).

## Does it work on macOS or Linux?

The commands in this manual are given for Windows first because that is where UEFN runs. The kit's scripts are Python and shell, and the console server exists in both Python and PowerShell.

## Claude says it cannot see my project in UEFN.

The MCP server serves the project that is open in UEFN. Open the right project first, then check [Claude loses UEFN](ch:troubleshooting#claude-loses-uefn).

## The console is empty.

Open it as `http://127.0.0.1:8765/`, not as a file. If the dot at the top is red, see [The console shows a red status](ch:troubleshooting#the-console-shows-a-red-status).

## What's new is empty.

See [The What's new page is empty](ch:troubleshooting#the-what-s-new-page-is-empty).

## How do I update?

Run `/kit-update --fetch` in a session, then open a new session. See [Troubleshooting](ch:troubleshooting).

## Can I change an agent?

Yes. Put an agent with the same name in the project's `.claude/agents/` folder. It overrides the user-level one in that project only.

## Where do I report a mistake or ask for a feature?

Open an issue on [GitHub](https://github.com/mimmo-the-root/UEFN-dream-bot-team/issues/new/choose), or ask on [Discord](https://discord.gg/WXF9UgzvRX).

## Is this official?

No. The kit is not affiliated with Epic Games. Fortnite and UEFN are trademarks of Epic Games.
