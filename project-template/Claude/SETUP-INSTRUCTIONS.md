# Setup instructions — for you, Claude, to read and execute

This file is only for this project's very first configuration, just copied here into the
`Claude/` folder along with the rest of the scaffold. The owner will simply tell you "read
Claude/SETUP-INSTRUCTIONS.md and set up the project": follow these steps in order, asking for
confirmation only where indicated. Once setup is done this file isn't needed anymore (you can
suggest deleting it, but don't do it without asking).

**Safe to re-run**: every step here is written to be idempotent — running it again after a kit
update (once the update-safe files from `project-template/` have been copied over, see
SETUP-GUIDE.md's "Updating an existing project" section) does nothing destructive: step 3 only
fills in `<AUTO_PROJECT_NAME>` if it's still the placeholder, step 3b only seeds `Claude/docs/` if
it doesn't already exist. Never delete or overwrite an existing `Claude/docs/` or a `CLAUDE.md`
that already has real content, here or anywhere else in this kit.

**⚠️ Warning before anything else**: this session must have been started with `claude` launched
from inside this project's `Content/` folder — not from a parent folder, not from the UEFN
installation folder. If you're not sure that's the case, check now (step 0 below) before doing
anything else.

0. **Preliminary check — you must be inside `Content`**: look at the current folder's name. It
   must be literally `Content` — that's where this scaffold is meant to be installed and run,
   on purpose: `Content` is the subfolder UEFN saves/syncs through its own cloud system, so
   keeping `CLAUDE.md`, `.claude/`, and `Claude/` inside it too means documentation, logs, and
   configuration aren't lost if the owner switches machines. If the current folder's name is
   NOT `Content`, stop and flag it to the owner: the scaffold needs to be moved inside
   `Content/` (not left next to it), then `claude` needs to be relaunched from inside there.
   (This is only the one-time setup check. For every session after that, `session-start-reminder.
   ps1`/`.sh` checks this automatically — if `claude` is ever launched from one level above
   `Content/` by mistake, it now surfaces a loud warning in Claude's very first reply instead of
   failing silently, since every hook in `.claude/settings.json` would otherwise point at a
   `Claude/hooks/` that doesn't exist from there.)

1. **Determine the project's name**: it is NOT the name of this folder — that would always be
   "Content," identical across every UEFN project, useless for telling them apart. It's the
   name of the folder that CONTAINS `Content` (one level up, `cd ..`): that's the real root of
   the UEFN project, with a unique name (e.g. the island's name). Verify it with a simple
   command.

2. **Find the UEFN MCP server and register it for this project.** Don't assume Phase 1 was
   already completed on this machine — check for yourself and register automatically if
   needed, so this step is self-sufficient. Do it before anything else that depends on MCP:
   a. **Search for the server automatically**: check whether port 8000 (the default; check the
      owner's UEFN Editor Preferences if it was changed) is listening.
      - Windows: `netstat -ano | findstr :8000`
      - macOS/Linux: `lsof -i :8000` (or `netstat -an | grep 8000`)
      A line naming the port as listening means the server is running — continue to (b). No
      output at all means it isn't: skip straight to (e), don't waste time on the rest of this
      step.
   b. Run `claude mcp list` to see whether a server for UEFN (typically named `unreal-mcp`) is
      already registered.
      - **If it's already registered**: skip to (c).
      - **If it's NOT registered yet**: register it now, automatically, don't ask the owner to
        do it manually — `claude mcp add --transport http unreal-mcp --scope user
        http://127.0.0.1:<port found in step a>/mcp`. User scope means this registration also
        covers every other project on this machine from now on, so this only needs to happen
        once, whichever project happens to do it first.
   c. Confirm it worked: `claude mcp list` should now show `unreal-mcp`.
   d. Try a lightweight MCP call (e.g. listing the available tools, or a harmless read-only
      action) to confirm the server actually responds end-to-end, not just that it's listed.
      If it responds, continue to step 3 below.
   e. **If the port wasn't listening in (a), or the MCP call in (d) still doesn't respond**:
      stop here — this isn't something you can fix by registering, it needs the owner to check
      UEFN itself:
      - **In UEFN's Editor Preferences > Model Context Protocol**: that *Auto Start Server* is
        enabled, and that `.mcp.json` exists in the UEFN installation folder (see the setup
        guide's Phase 1) — both require UEFN to have been (re)started after being set.
      - **In THIS project's Project Settings**: that *Python Editor Scripting* and *UEFN MCP
        Toolsets* are enabled — this one is per-project and can't be fixed at the install level.
        If the owner just enabled them right now, while the project was already open in UEFN,
        tell them that's very likely the whole problem: these settings only take effect on
        reload — ask them to close this project in UEFN and reopen it (not necessarily quit
        UEFN entirely, just close and reopen the project), then come back and re-run this step.
      Don't proceed with any MCP-dependent step below until this is confirmed working —
      filesystem-only steps (3 onward for non-MCP fields) can still continue in the meantime if
      useful, but skip anything involving MCP tools.

3. **Fill in the identity in CLAUDE.md**: open `CLAUDE.md` at the root. If it still contains the
   placeholder `<AUTO_PROJECT_NAME>`, replace it everywhere it appears with the name detected in
   step 1.

3b. **Seed the real docs folder, if it doesn't exist yet**: check whether `Claude/docs/` already
   exists (a real project re-running this after an update, or a project that already has history,
   will already have it — in that case skip this entirely, don't touch it). If `Claude/docs/`
   doesn't exist yet, create it by copying every file from `Claude/docs-template/` into it
   (skip `docs-template/README.md` itself, it's not a doc). This is the ONLY time
   `Claude/docs-template/` ever gets copied anywhere — from here on, `Claude/docs/` is the
   project's own live data, `docs-template/` stays an untouched seed for the next brand-new
   project.

4. **Gather the missing information**: ask the owner, one item at a time, for the values of the
   still-empty sections of `CLAUDE.md` — "What this is" (short description), "Project type",
   "Conventions" (only exceptions to the base rules already in `~/.claude/CLAUDE.md`, don't
   repeat those). Write the answers into the file.

5. **List the available MCP tools** in this session. Report to the owner what you find. If
   there are distinct tools per action (one that starts, one that stops a play-session), note
   the exact names. If instead the server exposes a single generic dispatcher tool (e.g.
   `mcp__unreal-mcp__call_tool`) that routes all actions internally via the payload, note that
   instead — filtering on the specific action can't be done by tool name alone.

6. **Wire up the automation hook**: open `.claude/settings.json`.
   - If in step 5 you found distinct tools per action, fix the `PostToolUse` hook's `matcher`
     to the EXACT name of the tool that stops the play-session.
   - If instead it's a generic dispatcher, the `matcher` should stay pointed at that tool (e.g.
     `mcp__unreal-mcp__call_tool`, fires on every call) and the filtering happens inside the
     hook script (`Claude/hooks/after-playtest.ps1` or `.sh`), which reads the JSON payload from
     stdin and proceeds only if the action is actually a session/game stop — this is already
     set up in the scaffold, just verify the pattern used in the script matches how this
     server's stop action is actually named (run it once and check it fires when the
     play-session ends, not on every MCP call).
   - On Windows without bash available, use `after-playtest.ps1` (PowerShell) instead of
     `after-playtest.sh` — update `command` in `.claude/settings.json` accordingly if it isn't
     already set that way.

7. **Identity safety check**: verify that the project currently open in UEFN matches the name
   detected in step 1, by looking at the Verse/asset paths returned by the MCP tools (the MCP
   server is a single instance per editor and always serves whatever project is currently open,
   not necessarily this folder). Report to the owner whether it matches or not BEFORE going any
   further.

8. **First analysis**: only if step 7 confirms the match, use the `project-bootstrap` agent for
   the project's first analysis (if code already exists) or to gather requirements (if the
   level is still empty).

9. **Mention the optional Agent Console**: this scaffold also ships `Claude/hooks/
   agent-console.html` plus `agent-console-log.ps1`/`.sh` (already wired into
   `.claude/settings.json`'s `PreToolUse`/`PostToolUse`, matched on `"Task|Agent"`, no setup
   needed) and `agent-console-server.ps1`/`.py` (a small local server). From the NEXT session
   onward, a `SessionStart` hook (`session-start-reminder.ps1`/`.sh`, also already wired) asks
   the owner automatically whether they want it open — you don't need to do anything about that
   here, just mention the console exists in your final setup summary so the owner isn't
   surprised the first time that question shows up.

If anything in these steps is unclear, or an expected tool doesn't exist, stop and ask the
owner how to proceed instead of guessing.
