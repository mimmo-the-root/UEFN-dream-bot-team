#!/usr/bin/env bash
# weekly-release-notes-sync.sh
#
# Runs the second-brain-librarian agent's UEFN release-notes sync workflow (defined in the
# kit's second-brain-librarian.md, installed at ~/.claude/agents/second-brain-librarian.md).
#
# Meant to be registered as a weekly cron job (Thursdays) - see second-brain-template/README.md,
# "Automate the weekly sync" section, for the exact crontab line. Can also be run by hand any
# time to force a sync.
#
# Requires: Claude Code CLI ("claude") available on PATH, and this vault's path already set in
# ~/.claude/CLAUDE.md rule 11 ("Second brain path"). Uses claude -p (non-interactive/print mode)
# so it can run unattended without anyone watching a terminal.
#
# Same two gotchas as the Windows .ps1 version, fixed here too even though bash's single-quoting
# doesn't hit the argument-truncation bug the way PowerShell-to-.exe does: cd into the vault
# (and pass --add-dir as a belt-and-suspenders measure) so claude -p, which can't prompt for
# confirmation, doesn't refuse to read/write outside its working directory; and keep the prompt
# free of embedded double quotes for consistency with the Windows script.

set -euo pipefail

VAULT_PATH="$(dirname "$(readlink -f "$0")")"

PROMPT='Use the second-brain-librarian agent'"'"'s UEFN release-notes sync workflow: fetch
https://dev.epicgames.com/documentation/fortnite/whats-new-in-unreal-editor-for-fortnite,
compare against wiki/note-di-rilascio-uefn/indice_wiki.md in the configured second brain vault,
and add articles only for entries not already captured, or do the full backfill if this is the
first run ever. Report what you added.'

cd "$VAULT_PATH"
claude -p "$PROMPT" --agent second-brain-librarian --add-dir "$VAULT_PATH"
