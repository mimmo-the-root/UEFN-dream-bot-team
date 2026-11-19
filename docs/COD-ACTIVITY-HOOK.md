# Cod activity hook (T-111)

`Claude/hooks/cod_activity.py` appends one JSON line per event to `Claude/logs/cod-activity.jsonl` (newest 2000 lines kept):
`time, ts, event, tool, ok, blocked, reason (first 200 chars, only for a denial or classifier block), pkg`.
`tools/watchdog.py` reads that file (and `plan/FEEDBACK-FROM-COD.md`) to tell busy, idle and blocked apart.
It never fails, never blocks and prints nothing. Switch off with `UEFN_COD_ACTIVITY=0`.

Events (all six exist in the Claude Code hook reference): PostToolUse, PostToolUseFailure, Stop, SubagentStop, Notification, PermissionDenied.

Add this to `.claude/settings.json` (merge into the existing `hooks` object; nothing here edits it for you):

```json
{
  "hooks": {
    "PostToolUse":        [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }],
    "PostToolUseFailure": [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }],
    "Stop":               [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }],
    "SubagentStop":       [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }],
    "Notification":       [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }],
    "PermissionDenied":   [{ "hooks": [{ "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/Claude/hooks/cod_activity.py\"", "timeout": 10 }] }]
  }
}
```

The package id comes from `UEFN_PACKAGE_ID` (or `COD_PACKAGE_ID`, `CLAUDE_PACKAGE_ID`), else from the newest file in `relay/running`.

Schedule `python tools/watchdog.py --lab <LAB>` every 5 minutes. Add `--dry-run` to see what it would do.
