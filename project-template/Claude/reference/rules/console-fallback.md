<!-- Full text of the project rule "Agent Console fallback start". The short version is in this project's CLAUDE.md (KIT block console-fallback); kit_sync keeps this file current. -->

# Agent Console fallback start

- **Agent Console (if `Claude/hooks/agent-console.html` exists in this project)**: this normally
  starts itself automatically via the `SessionStart` hook (`session-start-reminder.ps1`/`.sh`,
  see the manual, chapter "The console") before your first reply — don't ask permission, it's already
  handled. Use this fallback ONLY if that hook's context note didn't reach you (e.g. an older
  Claude Code build that doesn't support hook `additionalContext`): check whether a server is
  already correctly serving THIS project by requesting `http://127.0.0.1:8765/whoami` and
  comparing its `"project"` field to this project's own folder path. If it matches, nothing to
  do. If it doesn't match (or nothing answers), whatever's bound to port 8765 is stale — kill it
  first (Windows: find the PID via `netstat -ano | findstr :8765`, confirm it's a
  powershell/python process, then `Stop-Process -Id <pid> -Force`; macOS/Linux: `lsof -ti
  tcp:8765` piped the same way, then `kill -9`) — never kill a process that isn't one of our own
  servers — then start a fresh one in the background for this project (don't run it in the
  foreground, it would block this session — Windows: `Start-Process powershell -ArgumentList
  '-ExecutionPolicy Bypass -File "Claude\hooks\agent-console-server.ps1"' -WindowStyle Hidden`;
  macOS/Linux: `nohup python3 Claude/hooks/agent-console-server.py > /dev/null 2>&1 &`), then open
  `http://127.0.0.1:8765/` in the owner's default browser too (Windows: `Start-Process
  "http://127.0.0.1:8765/"`; macOS: `open http://127.0.0.1:8765/`; Linux: `xdg-open
  http://127.0.0.1:8765/`) — the owner wants it opened automatically every session, not just
  mentioned. Never ask permission first — just do it and say so.
