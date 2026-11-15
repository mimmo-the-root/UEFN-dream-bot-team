<!-- Full text of the project rule "Skill Harness". The short version is in this project's CLAUDE.md (KIT block skill-harness); kit_sync keeps this file current. -->

# Skill Harness

- **Skill Harness — the genre skill learns from this map (v1.81+)**: this project's genre skill
  (`~/.claude/skills/genre/<slug>/SKILL.md`, slug in `Claude/docs/.genre`) is where the kit keeps
  what it has learned about building this KIND of map. Two duties, both cheap:
  1. *Use it*: before designing or changing core gameplay, read that SKILL.md once per session. Its
     "Learned patterns" block says how far to trust each pattern (proven = rule, confirmed =
     default, hypothesis = suggestion and tell the owner it is unproven, contested = show both
     options and ask). If the block is empty, nothing is learned yet — never invent patterns.
  2. *Feed it*: when a playtest finishes, a release-gate check passes, or a batch of tasks closes
     and something reusable about this genre became clear, invoke the `skill-reflector` agent
     (after-playtest already does it automatically). It only QUEUES lessons; the owner approves or
     rejects each one on the Knowledge page. Never edit anything under `~/.claude/skills/genre/`
     yourself, and never put map names, island codes or task/bug IDs into a lesson — those stay on
     this computer only.
  3. *Feed it after an audit* (automatic): when `codebase-auditor` reports that a skill needs feeding (`skills_lib.py needs-feeding <slug>`: fewer than 3 owner-backed patterns), invoke ONE `skill-reflector` call with the audit's verified findings as evidence. Do not ask first; the lessons only reach the owner's approval queue.
