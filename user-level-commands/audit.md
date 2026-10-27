---
description: Audit the finished game for bugs: fix the minor ones by itself within the limits, list the serious ones for the owner
argument-hint: ""
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

You audit the game when the build is finished, before the delivery. Work in `Claude/docs/`; run scripts from `Claude/hooks` (`py -3` on Windows). Never change `GAME-SPEC.md`.

**1. Look.** Ask the agents `codebase-auditor` (code and structure), `qa-regression` (the acceptance criteria and the players of the spec) and `compliance-reviewer` (names, header, forbidden words of `CONSTITUTION.md`) for their findings. Run `/verse-check`, `/text-scan` and `python plan_check.py` too. Then the compliance scan, read-only (it never changes the map): `python ../../../../.claude/hooks/fab_assets.py <project>` or `/fab-check` (Fab rules: third-party assets, licences, personal names in file names; island rules: Publishing Validation). Privacy rule: where a personal name would appear, write `***anonymized***` (GDPR, Regulation (EU) 2016/679); only the user's own files, never assets made by Epic. A compliance finding that needs the owner (licence, name in a binary asset) is a medium finding with the manual step written in the text. Placement check (rule 7): every Verse device has its `DemoDisplay` outside the play area and the non-gameplay devices are on it, not lying in the scene; gameplay-position devices stay in place. In a multiplayer game look at: state shared or per player, a player who joins or leaves, the Island settings against the plan.

**2. Classify and record.** Each finding goes to the ledger: `python audit_log.py add "text" --class minor|medium|major --where file`. The classes are the ones of the Self-healing block of `CONSTITUTION.md`: minor (a clear compile error, an old header, a name outside the rules), medium (breaks an acceptance criterion), major (an error in the requirement, any change to `GAME-SPEC.md`).

**3. Heal.** Minor findings you fix yourself, one at a time: save a restore point first, fix, run the check again, then `python audit_log.py fix N` (or `fix N --failed`). The ledger enforces 3 attempts per finding and 10 automatic fixes; after that a finding goes to the owner. Medium and major findings you NEVER fix alone.

**4. Ask.** Show the owner only what is left: the medium and major findings, each with what breaks, who is affected, and your recommendation. One question per finding (fix it this way / leave it / change the spec). A change to the spec goes through `/spec` and the plan and tasks are redone. Then run the audit again until `python audit_log.py status` exits 0.

Report: how many fixed alone, how many for the owner, what you recommend. Name `AUDIT.md`; do not paste it. The next step is `/consegna`.
