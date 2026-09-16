# weekly-release-notes-sync.ps1
#
# Runs the second-brain-librarian agent's UEFN release-notes sync workflow (the workflow itself
# lives in the kit's second-brain-librarian.md, installed at
# ~/.claude/agents/second-brain-librarian.md - not in this vault's own CLAUDE.md).
#
# Meant to be registered as a weekly Windows Scheduled Task (Thursdays) - see
# second-brain-template/README.md, "Automate the weekly sync" section, for the exact
# schtasks.exe command. Can also be run by hand any time to force a sync.
#
# Requires: Claude Code CLI ("claude") available on PATH, and this vault's path already set in
# ~/.claude/CLAUDE.md rule 11 ("Second brain path"). Uses claude -p (non-interactive/print mode)
# so it can run unattended without anyone watching a terminal.
#
# Two gotchas fixed here, found on a real run:
# 1. Permissions: claude -p can't prompt for confirmation, so it refuses to read/write outside
#    its working directory unless that directory is explicitly granted. Fixed by both cd-ing
#    into the vault AND passing --add-dir as a belt-and-suspenders measure.
# 2. Argument truncation: a prompt with embedded double quotes (e.g. "UEFN release-notes sync")
#    gets silently cut off at the first embedded quote when PowerShell hands it to an external
#    .exe - Windows' native argv parsing treats it as closing the argument. Fixed by keeping the
#    prompt text free of double quotes entirely (no nested quoting).

$ErrorActionPreference = "Stop"

$vaultPath = "C:\SecondBrainOssidian"

$prompt = @"
Use the second-brain-librarian agent's UEFN release-notes sync workflow: fetch
https://dev.epicgames.com/documentation/fortnite/whats-new-in-unreal-editor-for-fortnite,
compare against wiki/note-di-rilascio-uefn/indice_wiki.md in the configured second brain vault,
and add articles only for entries not already captured, or do the full backfill if this is the
first run ever. Report what you added.
"@

Set-Location $vaultPath
claude -p $prompt --agent second-brain-librarian --add-dir $vaultPath
