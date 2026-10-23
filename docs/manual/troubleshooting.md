# Troubleshooting

Updates, the doctor, and the problems people meet most.

## Keep the kit up to date

Every time you start `claude` in a project, the kit compares that project's files with the copy in `~/.claude/kit-template/` and updates what is old or missing. The previous version of a replaced file is saved in `Claude/logs/kit-backup/`. Your own data is never touched: `Claude/docs/`, `Claude/logs/` and your `CLAUDE.md` outside the kit blocks.

> **Note** Kits older than v1.108.3 do not update themselves: run `/kit-update --fetch` once (see [Installing](ch:install)).

The copy in `~/.claude/` updates itself too: at most once every 6 hours the session start checks GitHub in the background and, if a newer release exists, downloads it without slowing the session. The project then updates at its next session start. The update downloads the release file `kit.zip`; GitHub counts those downloads, which is how the author knows roughly how many machines take each version (nothing is sent from your computer). The check logs one line in `~/.claude/kit-auto-update.log`. To switch it off, create an empty file `~/.claude/kit-auto-update.off`. Both the project hook and the global hook start the check. The very first time, run `/kit-update --fetch` (or `update-my-profile.cmd`) once, so that the new files are in place.

- `/kit-update` updates the current project now.
- `/kit-update --fetch` first downloads the latest release from GitHub into `~/.claude/kit-template/`, then updates the project.
- After an update, **open a new session** (rules, agents and hooks are read at the start) and reload the console page.

## The doctor

`/kit-doctor` checks the project's health: versions, hooks, backups. It tells you in a few lines what is fine, what is wrong and what to do. `/kit-doctor --fix` repairs the common problems.

## Restore points

`/restore-point` makes a snapshot of your Verse code and documents, shows what changed since, or undoes a change. Run it without arguments to see what changed. A restore always shows what would change before it does anything, and never deletes files.

## The console shows a red status

The page cannot reach its local server. In order:

1. Open the console as `http://127.0.0.1:8765/`, not as a file from your disk.
2. Start the server by hand in a terminal opened in the project:

```
powershell -ExecutionPolicy Bypass -File Claude\hooks\agent-console-server.ps1
```

or, on any system with Python 3:

```
python3 Claude/hooks/agent-console-server.py
```

3. Reload the page. If you just updated the kit while the server was running, restart it: it does not notice file changes by itself. Opening a new session does this for you.

## The console is quiet while agents work

Nothing shows until an agent actually runs. If agents run and the page stays empty, check that the project's `.claude/settings.json` still has the kit's hooks, which `/kit-doctor` does for you. After a Claude Code update that renames its internal dispatch tool, the console goes quiet the same way until the hooks are updated by a kit update.

## Claude loses UEFN

The UEFN server listens on `http://127.0.0.1:8000/mcp` by default. Go in this order:

1. **Is anything listening on port 8000?** In PowerShell: `Get-NetTCPConnection -LocalPort 8000 -State Listen`. No result means the server is off.
2. **Read the editor Output Log** for the server start-up lines. A port conflict shows up there.
3. **It listens but does not answer?** Run `npx @modelcontextprotocol/inspector` and connect to `http://127.0.0.1:8000/mcp` with the Streamable HTTP transport. If the tools are listed, the server is fine and the problem is on the Claude side: restart the session.
4. **Restart the server by hand** from the editor console: `ModelContextProtocol.StartServer`, optionally with a port, such as `ModelContextProtocol.StartServer 8000`.

## There are two files called settings.json

They are different and must never be merged by hand. `~/.claude/settings.json` is yours: Claude Code's own preferences. `<project>/.claude/settings.json` belongs to that project: the kit's hooks and permissions. Claude Code reads both and combines them. The full table is in [Full installation](ch:install#two-files-called-settings-json).

## The What's new page is empty

It shows the summary of the last release, shipped with the kit. After a release, run `/kit-update --fetch` and open a new session. Sections about contributors fill up only when lessons from other creators arrive.

## My map shows as "not published"

The page says why. The usual reasons: the project has no island code saved, Epic has no public data for it yet, or Epic could not be reached. See [Community](ch:community).

## Something is wrong with a community lesson

Use **Submit an issue** on the What's new page. See [Community](ch:community).

## Still stuck?

Open an issue on the [GitHub repo](https://github.com/mimmo-the-root/UEFN-dream-bot-team/issues/new/choose), or ask on the creator's [Discord](https://discord.gg/WXF9UgzvRX). Tell us your kit version (shown at the top of every console page) and what `/kit-doctor` said.
