<!-- Full text of base rule 6. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 6. Header documentation in Verse code

Every Verse file (created or modified) must have a comment block at the top in this form:

```verse
# <FileName>.verse
# Summary: <one or two sentences on what this script does>
# Last modified: <YYYY-MM-DD> — v<version number>
```

- **Summary**: what the file does, not how — useful to understand the purpose without reading
  all the code.
- **Section comments**: inside the file, one comment line above each significant logical block
  (e.g. `# Respawn handling`, `# Player input validation`) — no need to comment every line,
  just give the sections a readable structure.
- **Date and version**: `coder` updates the date (the real one — check it with a command
  instead of guessing) and increments the version number every time it substantially modifies
  that file. The header keeps the CURRENT state only: file name, an English Summary that is
  always up to date (rewrite it when the behaviour changes), and the real date and version.
- **No change history in the file.** Do not write `# v12 2026-..: ...` lines, "History" blocks or
  fix notes in the header. The history of changes goes to the log instead:
  `python Claude/hooks/verse_changes.py add <file.verse> --summary "what changed" --reason "why"`
  (one line in `Claude/logs/verse-changes.jsonl`, next to `verse-errors.jsonl`; the learning
  system reads both). A header that still has history lines is cleaned by `history_trim.py`
  (lines archived in `Claude/docs/archive/verse/`, one "migrated" row in the log); a decision that
  still matters goes into the Summary in a few words.
- If an existing Verse file doesn't have this header, `coder` adds it the first time it touches
  that file (starting at v1 with today's date); `project-bootstrap` flags files still missing
  it in BUGS.md as a non-blocking gap.
