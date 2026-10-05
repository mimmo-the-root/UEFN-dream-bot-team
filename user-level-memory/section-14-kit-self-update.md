<!-- KIT:BEGIN kit-self-update -->
## 14. Kit self-update for older projects (automatic)

Projects with a kit older than v1.84 have no update hook, so they never refresh themselves. As the very
first action of ANY session in a project that has a `Claude/` folder next to a `CLAUDE.md` (with or without
`Claude/KIT-VERSION`; a missing version file means a very old kit), compare the project's
`Claude/KIT-VERSION` with `~/.claude/kit-template/Claude/KIT-VERSION`. If the project file is missing, older,
or `.claude/settings.json` has no `kit-sync` entry, run once, without asking:

`python ~/.claude/kit-template/Claude/hooks/kit_sync.py <project folder>` (use `py -3` if `python` is missing;
the project folder is the one that contains `Claude/` and `.claude/`).

It backs up replaced files under `Claude/logs/kit-backup/`, adds missing hooks and files, never touches
Claude/docs or your permissions. Then tell the owner in one line: "Kit updated from vX to vY: restart the
session so the new files are read." If the profile template folder does not exist, say so once and continue.
Do not repeat the check when the versions already match.
<!-- KIT:END kit-self-update -->
