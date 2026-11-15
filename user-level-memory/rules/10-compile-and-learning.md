<!-- Full text of base rule 10. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 10. Code that doesn't compile is not a finished task, and learning from errors

If the code you wrote doesn't compile, the task isn't done: it must be fixed and made to work,
not left as-is with the excuse that "everything else is fine." `coder` follows a
compile→read-the-exact-error→fix-precisely→recompile cycle, up to a maximum of 5 consecutive
attempts on the same error — beyond that, guessing at random costs tokens without solving
anything: better to stop, write in BUGS.md what was tried and the exact error, and ask.

`coder` and `qa-regression` have persistent per-project memory (`memory: project` in their
agent files' frontmatter): using it to avoid repeating the same mistakes is part of the job,
not optional. When something non-obvious specific to THIS project is discovered — a device
that behaves differently than documented, a design decision that trips up future work — save
it as a short note (one line, cause + how to recognize it) to that per-project memory, not a
long write-up: memory exists to save tokens in future sessions, not to become another document
to maintain. Check it before starting a task, so you don't always start from zero.

**Learning across projects, not just within one.** Per-project memory resets on every new
island — it never helps on project #37 with something learned on project #12. For lessons
about Verse, UEFN, or the MCP tooling itself (not this project's specific devices or design),
there's a second, shared layer: `~/.claude/skills/uefn-lessons/SKILL.md`, installed once
(Phase 1 of the setup guide) and read/added to by `coder` and `qa-regression` on every project
from then on. The rule for where a lesson goes: "would this help on a different island?" — if
yes, it's a `uefn-lessons` entry, not per-project memory. This is the actual mechanism for
getting measurably better at UEFN/Verse development the more projects this kit is used on —
it only works if entries stay short and are added consistently, not skipped because a session
is in a hurry to finish the task.

**One canonical answer per recurring MCP question, not one prose description per agent file.**
`~/.claude/skills/mcp-tool-contracts/SKILL.md` is the single source of truth for "which exact MCP
tool does X" (e.g. verifying which project UEFN has open). Every agent file that needs this
references the contract by name instead of describing the check in its own words — see that
skill's own header for why (a v1.67 incident traced back to the same instruction, worded slightly
differently in three separate files, quietly diverging). When a new MCP-tool gotcha is discovered,
it's added there as a new contract, not described inline in whichever agent found it.
