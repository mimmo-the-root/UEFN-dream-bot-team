<!-- Full text of the project rule "Technique skills". The short version is in this project's CLAUDE.md (KIT block technique-skills); kit_sync keeps this file current. -->

# Technique skills

- Technique skills (automatic): before any audit, review, QA or implementation work, run
  `python Claude/hooks/skills_lib.py techniques .` (use `py -3` if `python` is missing). It lists the technique
  skills (LLM conversations, materials, and later Web UI or brand islands) that this project actually uses, by looking for
  their markers in the Verse code. For every slug it returns, read `~/.claude/skills/genre/<slug>/SKILL.md`
  and its patterns first, and apply them (and its audit checklist) without being asked. Items marked
  reference are official platform facts; items backed by the owner's maps outrank them. Mention in your
  report which technique skills you used. Do not ask permission.
  For materials work (audit, reuse, which material to use) delegate to the `materials-expert` agent.
