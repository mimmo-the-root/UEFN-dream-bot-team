<!-- Full text of base rule 2. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 2. Centralized logging

Every Verse file in the project must use this pattern instead of calling `Print()` directly
(a ready-made template is at `Claude/reference/logger-template.verse.txt` inside every
project):

```verse
@editable DebugLoggingEnabled : logic = true
Log(LogMessage : string):void=
    if (DebugLoggingEnabled?):
        Print(LogMessage)
```

- If a Verse file doesn't have it yet, add it — `coder` does this whenever it touches that
  file; `project-bootstrap` flags files still missing it in BUGS.md as a gap to close, during
  the initial quality check.
- **If the existing logs aren't enough to understand a bug, the next step is to add more of
  them at the critical points and re-test — never guess at the cause without first
  instrumenting the code.** This applies especially to `qa-regression` when analyzing a
  regression.
