# When Epic updates its guide

`/ui-kit-check` compares a fingerprint (SHA-256) of Epic's `AGENTS.md` (kept once in `~/.claude/skills/verse-ui-kit/references/epic/`, shared by all projects; a copy inside a project's `VerseUIKit` folder wins when present) with the versions this kit was written against. Epic's text is never copied into the kit (Fab EULA); only fingerprints are kept.

When the state is `agents_changed`:
1. Tell the owner in one line. Do not edit this skill yet.
2. If an earlier version was accepted on this computer, run `Claude/hooks/ui_kit_check.py --diff` to see what changed. Otherwise compare with the original download by hand.
3. Read the changed parts and sort them: a rule this skill already states differently, a new rule, a removed rule, a new tool or workflow (for example new MCP abilities).
4. Propose edits to `references/rules.md` and `references/snippets.md` in this kit's own words, and show them to the owner. Apply only after a yes.
5. After the owner agreed to the new version, run `ui_kit_check.py --accept` so it is not reported again in any project. To install a new download, run `ui_kit_check.py --store <file>` first. A snippet touched by a change goes back to "not yet compiled" until `/verse-check` passes.
6. Then run `/mcp-snapshot`: guide updates often come with new MCP tools.
