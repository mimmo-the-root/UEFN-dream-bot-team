<!-- Full text of base rule 9. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 9. Response style: concise

Go straight to the results. No preamble like "I'll now proceed to..." or narration of what
you're about to do — do it, then report what you found/changed. This applies to every agent
when reporting its output.

- No filler openers ("Great! I can certainly help...") and no closers ("Let me know if you need
  clarification!"). No explanations unless asked. Answer, then stop.
- Code: show the diff or the changed function, never the whole file again.
- Do not repeat what the owner just said or what a tool already showed. Reference task ids (`T-014`) instead
  of re-describing work.
- A subagent's final report is at most 15 lines in the fixed shape its own file defines; details go to the
  files it edits, not to the report.
