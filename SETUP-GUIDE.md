# Claude Code team setup for UEFN projects

## About the author

Built by **Mimmo_the_root**. This kit exists to solve my own problem: working with AI tools
across the ~50 islands I've built over the years, without losing my mind keeping them
straight. That's the lens everything here was designed through.

A few setup steps are left manual on purpose, not because they couldn't be scripted — I'd
rather you see and understand what's being installed on your machine than hide it behind a
one-click installer. That's a deliberate transparency choice, not a limitation.

If this kit saves you time, support code: **ROOT** in the Item Shop, and consider following
along:

- Discord (get the scripts, ask questions, see what's next): https://discord.gg/WXF9UgzvRX
- YouTube: https://www.youtube.com/@Mimmo_the_root
- Twitch: https://www.twitch.tv/mimmo_the_root
- X: https://x.com/mimmo_the_root
- TikTok: https://www.tiktok.com/@mimmo_the_root
- Instagram: https://www.instagram.com/mimmo_the_root
- Epic Games community page: https://communities.epicgames.com/community/U1gO/mimmo-the-root

## What this kit does

This is a Claude Code setup for developing UEFN (Unreal Editor for Fortnite) projects with a
small team of specialized subagents, designed so a developer working across many projects can
keep them from mixing together. Point it at a project and it handles:

1. **One-time setup**: reads a project's existing code and maps its structure — or, if the
   project is still empty, asks the owner for requirements instead of inventing them.
2. **Initial project analysis**: on an existing codebase, produces a functional spec deduced
   from the code, a quality check that finds pre-existing bugs with a prioritized bug-fixing
   roadmap, and concrete proposals to increase playtime and reduce drop-off in the first 5
   minutes of gameplay.
3. **Ongoing development**: a coder agent that implements features and fixes, always following
   a compile-and-fix loop so a task is never left in a state where the code doesn't build.
4. **Automatic regression search and documentation updates** after every playtest session, via
   a Claude Code hook — no manual step required.
5. **Release readiness**: a go/no-go verdict before a release or showcase, based on open bugs
   and documented progress.
6. **Getting better across projects, not just within one**: a shared `uefn-lessons` skill (see
   section 3b) that Verse/UEFN gotchas get added to as they're discovered on any project, so
   coding on island #37 benefits from what was learned on island #12 — not just from what
   happened earlier in the same project.
7. **Optional Obsidian second brain** (see section 3c): a separate, browsable wiki of reusable
   game mechanics and Verse device implementations that a dedicated agent,
   `second-brain-librarian`, maintains on `coder`/`project-bootstrap`'s behalf when configured,
   kept current per device/mechanic instead of as a pile of snapshots — and consulted, not just
   fed, so a pattern already catalogued gets reused instead of reinvented on the next project.
8. **Optional real-time Agent Console** (see section 5b): a local, browser-based, arcade-style
   dashboard that lights up each agent's card the moment it starts/stops working and draws a
   pulse between two agents when one hands off to another (e.g. `coder` invoking
   `second-brain-librarian`) — a live view into what the team is actually doing, not just its
   documentation output.

Five agents divide the core work, each with a narrow role: **project-bootstrap** (one-time
initial analysis or requirements gathering), **coder** (writes/fixes code), **qa-regression**
(finds bugs and regressions), **planner-docs** (keeps the documentation updated), and
**release-gate** (final go/no-go verdict). A sixth, optional agent, **second-brain-librarian**,
maintains the Obsidian second brain from section 7 above on the other five's behalf. A seventh,
also optional, **second-brain-trainer**, orchestrates a deliberate parallelized sweep of the
current project when you want to backfill the vault faster than the normal one-thing-at-a-time
flow — see section 3c below. Details on each are in section 2 below.

---

## Two setup phases — read this first

Setup happens in two separate phases, done from two different folders. Mixing them up is the
most common source of confusion, so keep this straight:

| | Phase 1 — Environment setup | Phase 2 — Per-project setup |
|---|---|---|
| **How often** | Once per machine | Once per UEFN project |
| **You launch `claude` from** | The UEFN **installation** folder (e.g. `C:\Program Files\Epic Games\Fortnite`) | Each project's own `Content/` folder |
| **What it does** | Gets the MCP server running and registers it with Claude Code | Installs the per-project scaffold (docs, agents' working files, hooks) and connects it to that specific project |
| **Covered in** | Phase 1 below | Phase 2 below |

Do Phase 1 once, completely, before touching any individual project. Then repeat Phase 2 for
every project you want to use this kit on.

## Phase 1 — Environment setup (once per machine)

1. **Create the MCP server config.** In your **UEFN installation folder** (not a project
   folder — on Windows typically `C:\Program Files\Epic Games\Fortnite`, adjust for your setup),
   create a file named `.mcp.json` with this content:
   ```json
   {
     "mcpServers": {
       "unreal-mcp": {
         "type": "http",
         "url": "http://127.0.0.1:8000/mcp"
       }
     }
   }
   ```
2. **Start (or restart) UEFN.** If UEFN was already open, close it first — this file needs to
   already be in place when UEFN starts for the server to be configured correctly.
3. **Enable the server**, in UEFN: **Edit > Editor Preferences > Model Context Protocol** →
   turn on *Auto Start Server*.
4. **Verify the server is listening** (default port 8000, adjust if you changed it):
   - Windows: `netstat -ano | findstr :8000`
   - macOS/Linux: `lsof -i :8000` (or `netstat -an | grep 8000`)

   A line naming the port as listening means it worked — move on. No output at all means it
   didn't: recheck steps 1-3 before continuing (file content and location, UEFN actually
   restarted after the file was created, *Auto Start Server* actually toggled on).
5. **Install this kit's user-level files:**
   - Copy everything from `user-level-agents/` into `~/.claude/agents/` (Windows:
     `%USERPROFILE%\.claude\agents\`). Fourteen files: coder, qa-regression, planner-docs,
     project-bootstrap, release-gate, second-brain-librarian, second-brain-trainer,
     second-brain-scout, coder-prep, growth-manager, intent-gate, intent-reviewer,
     compliance-reviewer, and codebase-auditor.
     `second-brain-scout` and `coder-prep` are internal helpers (`second-brain-trainer` and
     `coder` dispatch them for their own parallel work) — you never invoke either directly, but
     they need to be installed alongside the others. `growth-manager` is the entry point for the
     eight `fortnite-*` marketing/growth skills below — see section 2 and 3e. `intent-gate` runs
     before `coder` starts; `intent-reviewer` then `compliance-reviewer` run after, in that order
     — the two-gate compliance check `coder` invokes on itself before reporting any task done, see
     section 2. `codebase-auditor` is an independent, on-demand whole-codebase quality audit — see
     section 2.
   - Copy `user-level-memory/CLAUDE.md` into `~/.claude/CLAUDE.md`. If that file already
     exists, paste this content at the end of it — don't overwrite what's already there.
   - **Upgrading from an older kit version: delete removed agent files, don't just copy new ones
     on top.** Copying `user-level-agents/` into `~/.claude/agents/` only ever adds or updates
     files — it never deletes anything, so an agent this kit has since renamed or retired (e.g.
     `verse-reviewer.md`, replaced in v1.69 by `intent-reviewer.md` + `compliance-reviewer.md`)
     stays on disk and stays invokable unless you remove it yourself. A stale leftover like that
     can still get invoked from habit/old context and will confuse the Agent Console (it'll show
     activity for an agent that isn't in this kit's current roster at all, including the
     "auto-cleared — no stop event arrived" message if it never reports back). Before copying files
     in for a version upgrade: compare the file list above against what's actually in
     `~/.claude/agents/` and delete anything not on the list.
   - Copy `user-level-skills/uefn-lessons/` into `~/.claude/skills/uefn-lessons/`. This is the
     shared, cross-project knowledge base described below — install it once here so it's
     already in place before you set up your first project.
   - Copy `user-level-skills/mcp-tool-contracts/` into `~/.claude/skills/mcp-tool-contracts/` the
     same way — the single source of truth `coder`, `qa-regression`, and `project-bootstrap` all
     reference for "which exact MCP tool does X," instead of each describing the check in its own
     words (see that skill's own header for why this exists).
   - Copy the other seven `user-level-skills/` folders the same way, each into
     `~/.claude/skills/<name>/`: `verse-patterns`, `uefn-device-gotchas`,
     `performance-uefn-checklist`, `discover-retention`, `second-brain-query`,
     `token-aware-coding`, and `brand-collections-uefn`. These are progressive-disclosure skills
     (short description, dense body, detail loaded from `references/` only when actually needed)
     that keep `coder` and `project-bootstrap` from having to reason about common patterns,
     device quirks, performance, retention, and brand-collection recognition from scratch every
     time — see section 3d below for what each one covers.
   - Copy the eight `fortnite-*` growth/marketing skill folders the same way, into
     `~/.claude/skills/<name>/`: `fortnite-analytics-coach`, `fortnite-competitor-analyzer`,
     `fortnite-marketing-launch`, `fortnite-retention-gamedesign`, `fortnite-social-trailer`,
     `fortnite-thumbnail-pro`, `fortnite-title-description`, and `fortnite-update-writer`. Unlike
     the dev-side skills above, these aren't read by an agent at a fixed step — Claude Code picks
     the matching one on its own, straight from its `description`, whenever what you ask for
     matches (analytics/CTR questions, competitor research, a launch plan, retention/game-design
     advice, a trailer/social script, a thumbnail, a title/description, or patch notes). See
     section 3e below for what each one covers and how to make sure they actually fire.
6. **Install Anthropic's official Unreal Engine skills plugin.** A separate,
   Anthropic-maintained plugin with its own Unreal Engine/Verse skills — required, complements
   this kit rather than replacing it:
   - **Prerequisite: Git.** The plugin install needs Git available on your machine. If you don't
     have it, install it first — [Git for Windows](https://gitforwindows.org/) on Windows (any
     Git distribution on macOS/Linux). **Windows-specific gotcha**: if Claude Code is already
     running in a PowerShell session when you install Git, that session won't see the new `git`
     command — PowerShell only reads environment variables (like `PATH`) when it starts. Close
     that PowerShell window entirely and open a new one before continuing, otherwise the plugin
     install will fail saying Git is missing even though it's installed.
   - Then install the plugin:
     ```
     /plugin install unreal-engine-skills-for-claude-code@claude-plugins-official
     ```
7. **Optional — connect an Obsidian second brain.** A separate, browsable wiki (not part of any
   single project), maintained by a dedicated sixth agent, `second-brain-librarian` (already
   copied to `~/.claude/agents/` in step 5), that `coder`/`project-bootstrap` hand reusable game
   mechanics and Verse device implementations off to, kept current per device instead of piling
   up snapshots. Skip this step entirely to leave the feature off — nothing else in the kit
   requires it.
   - If you don't have a vault for this yet: create one anywhere on your machine (it does NOT
     go inside any UEFN project), following `second-brain-template/README.md` in this kit —
     create its `raw/`, `wiki/`, `output/` folders and copy `second-brain-template/CLAUDE.md`
     into the vault's root. **Windows gotcha, verified on a real setup**: File Explorer with
     extensions hidden (the default) can silently save/rename that file as `CLAUDE.MD.md`
     instead of `CLAUDE.md` — it hides the trailing `.md` since it's a "known" extension, so the
     wrong name looks identical to the right one in Explorer's file list. Verify the real
     filename from a terminal instead — `dir CLAUDE*` (Windows) / `ls CLAUDE*` (macOS/Linux)
     inside the vault folder must show exactly `CLAUDE.md`, nothing else — before moving on.
   - Note that vault's full absolute path, then open `~/.claude/CLAUDE.md` and set it as the
     "Second brain path" value in rule 11 ("Second brain (Obsidian) integration") — e.g.
     `C:\SecondBrainOssidian` on Windows, or the literal placeholder `<SECOND_BRAIN_PATH>` to
     keep the feature off.
   - That's the entire setup — no registration command needed. `second-brain-librarian` reads
     that path from `~/.claude/CLAUDE.md` automatically from the next session onward, on any
     project.
   - **Optional extra, independent of this kit**: if you spend time in the vault yourself (not
     only through `second-brain-librarian`'s handoffs), the community `obsidian-skills` Claude
     Code plugin marketplace (by kepano, an Obsidian team member) teaches Claude Code better
     Obsidian-specific conventions — formatting, linking, front matter, and similar habits. Run
     once, from any terminal:
     ```
     /plugin marketplace add kepano/obsidian-skills
     /plugin install obsidian@obsidian-skills
     ```
     See `second-brain-template/README.md` in this kit for the same note.
8. **Optional but recommended — register the MCP server right now, as a sanity check.** You can
   skip steps 8-10 entirely if you want: `Claude/SETUP-INSTRUCTIONS.md` (Phase 2, step 2) checks
   for the server itself and registers it automatically the first time you set up a project, if
   it isn't registered yet. Doing it here too just confirms everything from step 1-4 actually
   works before you move on to a real project. Open a terminal inside the UEFN installation
   folder — the same one from step 1 — and launch `claude`.
9. **Register the MCP server once, at user scope**, so every future project on this machine
   sees it automatically, with nothing to copy per project:
   ```
   claude mcp add --transport http unreal-mcp --scope user http://127.0.0.1:8000/mcp
   ```
10. **Verify it's registered**: `claude mcp list` should show `unreal-mcp` with scope "user".
   Optionally, ask Claude to list the available MCP tools to confirm the connection works
   end-to-end, not just that it's listed.

Phase 1 is done. You won't repeat any of this for future projects — go to Phase 2 for each one.

## Phase 2 — Per-project setup (repeat for every project)

Prerequisite in UEFN, for this specific project: **Project Settings** → enable *Python Editor
Scripting* and *UEFN MCP Toolsets*. This one is per-project and can't be skipped by Phase 1.

1. **Copy by hand** (drag & drop from your file explorer, or copy/paste) the entire **contents**
   of this kit's `project-template/` folder into the project's `Content/` folder (see the next
   section for why it goes inside `Content/` specifically, not next to it) — without renaming
   or moving anything else already there. This is a **brand-new project only**: `project-template/`
   is a seed, and nothing in it is live project data yet (see "Updating an existing project"
   below for the very different — and much narrower — procedure once a project already has
   history).
2. **Open a terminal inside that `Content/` folder** — not the installation folder from Phase 1
   — and launch `claude`.
3. Tell it: **"Read Claude/SETUP-INSTRUCTIONS.md and set up this project."**

From there Claude Code takes over, following the included `Claude/SETUP-INSTRUCTIONS.md`: it
goes up one level to read the real project name (not "Content") and writes it into `CLAUDE.md`,
double-checks the MCP connection is actually reachable from here, asks you for the missing
descriptive information (what the project is, its type, any particular conventions), lists the
available MCP tools and sets up the post-playtest hook's matcher on its own, verifies the
project open in UEFN is the right one, and finally — only if everything checks out — uses
`project-bootstrap` for the first analysis (or to gather requirements if the level is empty).

`Claude/SETUP-INSTRUCTIONS.md` is only needed for this first configuration: afterward you can
leave it there (it doesn't get in the way) or ask Claude to delete it.

## Updating an existing project to a new kit version

This is the answer to "can I just overwrite the project folder to update everything" — yes, for a
clearly-defined subset, by construction: this kit keeps template/seed material physically separate
from a project's own live data specifically so a bulk update can never destroy it. Two lists,
memorize the shape once:

**Update-safe — copy these over an existing project any time, in full, no risk:**
- `Claude/hooks/` (all of it — the Agent Console, its server, every hook script)
- `Claude/reference/` (the logger template)
- `Claude/SETUP-INSTRUCTIONS.md`
- `Claude/docs-template/` (pristine doc seeds — see its own `README.md`; copying it changes
  nothing live, it's only ever read once by a brand-new project's setup)
- `.claude/settings.json` — technically safe to overwrite (no per-project data lives in it), but
  diff it first if you've ever hand-edited a hook's `matcher` for this specific project (step 6 of
  `SETUP-INSTRUCTIONS.md`) — a blind overwrite would silently drop that customization.

None of these ever hold a project's real progress, so overwriting them picks up every fix/feature
from a newer kit version with zero risk of data loss.

**Never bulk-copy these — they ARE the project's own data, not template material:**
- `Claude/docs/` — SPEC/STATUS/ROADMAP/BUGS/RETENTION-NOTES/RELEASE-READINESS: this project's
  entire tracked history (see the plan-first workflow, section 2b). Overwriting it with a fresh
  `docs-template/` would wipe every task, every log entry, every bug.
- `CLAUDE.md` (project root) — holds this project's filled-in identity and conventions, not a
  placeholder anymore after Phase 2 setup.
- `Claude/logs/` — the running record of session activity.
- Any per-agent persistent memory (`coder`/`qa-regression`'s `memory: project` state) — this
  lives outside the project folder entirely, in Claude Code's own storage, so a project-folder
  copy never touches it either way.

**A one-line copy command for the safe subset** (adjust paths; run from wherever you keep the
kit's `project-template/`, targeting the project's `Content/` folder):

- macOS/Linux: `rsync -av --include='Claude/hooks/***' --include='Claude/reference/***' --include='Claude/docs-template/***' --include='Claude/SETUP-INSTRUCTIONS.md' --include='.claude/settings.json' --include='*/' --exclude='*' project-template/ /path/to/project/Content/`
- Windows: `robocopy project-template\Claude\hooks Content\Claude\hooks /E` and the same pattern
  for `reference`, `docs-template`, plus copying `SETUP-INSTRUCTIONS.md` and `.claude\settings.json`
  individually (`robocopy` doesn't have a single-command include-list the way `rsync` does — run
  one `robocopy /E` per safe folder instead of trying to do it in one call).

After copying, if `Claude/hooks/agent-console.html` changed version, the existing browser tab is
now stale (see the Agent Console's own version-tag troubleshooting, section 5b) — hard-refresh it
rather than wondering why it looks out of date.

## Why the MCP server is set up this way

The MCP server config lives at the UEFN installation level and gets registered with Claude Code
once, globally — not per project — because the server itself is a single instance for whichever
UEFN editor window is open: it's not tied to any one project's folder, and there's nothing to
gain from repeating its setup 50 times. The `user` scope registration from Phase 1 step 9 saves
the connection in `~/.claude.json` and makes it available automatically in every Claude Code
project on this machine — verify it any time with `claude mcp list`. (If you'd rather scope
registration to a single project instead, `--scope project` does that, at the cost of repeating
step 9 for every project.)

**The one thing to always keep in mind:** that server always serves only the project *currently
open in UEFN* — not "whichever project's folder Claude Code was launched from." If you open
Claude Code inside a project's `Content/` but UEFN still has a different project open, the MCP
tools will silently act on that other project. The simplest practical rule: open the project
you want to work on in UEFN first, before starting a Claude Code session for it. Every
MCP-using agent in this kit also double-checks this itself before touching anything (see
section 4).

**Moving a project to a new machine (or opening it on a second one).** Because registration
lives in `~/.claude.json` — per machine — and not in the project's own files, this is expected:
a project you already finished setting up on machine A shows no MCP tools the first time you
open it on machine B, even though `CLAUDE.md`'s "Project identity" is already filled in (proof
it was set up before). This is NOT a sign the project needs to be re-onboarded. `coder`,
`qa-regression`, and `project-bootstrap` all check for this themselves before doing any MCP work
(same auto-find-and-register routine as `Claude/SETUP-INSTRUCTIONS.md` step 2 uses on first
setup): if `claude mcp list` doesn't show `unreal-mcp` but the project is clearly already set
up, they check port 8000 and register the server automatically — you don't need to do anything
manually for this, and you don't need to re-run `Claude/SETUP-INSTRUCTIONS.md`. What you DO
still need to do once per new machine is the actual Phase 1 environment setup above (steps 1-6:
`.mcp.json` in the UEFN installation folder, UEFN restarted with *Auto Start Server* on, this
kit's user-level agents/CLAUDE.md/skills copied to `~/.claude/`, and the Unreal Engine skills
plugin installed) — the agents' self-registration only covers the Claude Code registration step,
not the UEFN-side server setup.

## 1. Disk layout: work inside the project's `Content/` folder

Deliberate choice: the per-project scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) lives INSIDE
`Content/`, not next to it. `Content/` is the native subfolder UEFN creates on its own in every
project for assets and Verse code, and it's the one covered by UEFN's native save/cloud-sync —
putting our documentation, logs, and scripts inside it too means nothing is lost even if you
switch machines or reinstall. Open Claude Code directly inside `Content/`:

```
<UEFNProjectName>/                <- the real project folder (unique name, e.g. the island's name)
└── Content/                       <- UEFN's NATIVE folder — this is where we launch `claude`
    ├── CLAUDE.md                   <- fixed location, required by Claude Code
    ├── .claude/
    │   └── settings.json            <- fixed location (hidden), required by Claude Code
    ├── Claude/                      <- everything else we manage, clearly visible and separate
    │   ├── docs/
    │   │   ├── SPEC.md
    │   │   ├── STATUS.md
    │   │   ├── ROADMAP.md
    │   │   ├── BUGS.md
    │   │   ├── RETENTION-NOTES.md
    │   │   └── RELEASE-READINESS.md
    │   ├── logs/
    │   ├── reference/
    │   │   └── logger-template.verse.txt
    │   └── hooks/
    │       └── after-playtest.sh
    └── (the rest of Content/: native assets, Verse, levels — whatever UEFN already manages)
```

**The technical problem this choice introduces, and how we solve it**: `Content/` is named
identically across every project. If the "project name" were read from the name of the folder
you launch `claude` from, it would always come out as "Content" — useless both for telling
projects apart and for the MCP safety check above. That's why the real name isn't read from the
current folder but from the one that CONTAINS `Content/` (one level up): a computation done
once during Phase 2 setup, written at the top of `CLAUDE.md`, and from then on only ever read —
never recomputed from the current folder's name. If the name written in `CLAUDE.md` is
"Content" or "content," setup was run from the wrong place (one level too high, not inside
`Content/`): it needs to be redone from inside `Content/`.

`.claude/` (with the dot, hidden) and `Claude/` (no dot, visible) are two different things and both are needed — it's not a mistake that both exist. The first is a **reserved** folder that Claude Code itself reads for its own configuration — a fixed path the program looks for at startup, just like `.git/` for Git. It can't be renamed, and `settings.json` can't be moved elsewhere (into `Claude/`, for instance): if you do, Claude Code silently stops reading it — no error, the post-playtest automation hook and the configured permissions simply stop being applied, and you only notice because "nothing happens automatically anymore." The second, `Claude/`, is entirely ours: you can open it, read it, reorganize it, no constraints — everything Claude Code doesn't need to find in one exact spot goes here.

`CLAUDE.md` stays at the root you launch `claude` from — `Content/`, per the above — because that's where Claude Code looks for it automatically at startup (alternatively it can also live at `.claude/CLAUDE.md`, but not inside `Claude/`).

## 2. The twelve agents in your team

Separating "who writes," "who verifies," and "who documents" is the recommended pattern for Claude Code agents, because each one works with a role narrowly scoped to its task and doesn't interfere with the others. This kit adds a fourth agent for the most delicate moment (a project's very first run, with no historical documentation yet), a fifth to evaluate release readiness, a sixth (optional) that owns the second-brain vault instead of the other agents writing to it themselves, a seventh (optional, and only useful if the sixth is configured) that parallelizes a large training sweep across the vault's one-writer bottleneck without breaking it, an eighth that owns marketing/growth instead of the owner having to know which of the eight `fortnite-*` skills to reach for, and — for reviewing coder's own output — three more that split "is this even clear enough to start" (`intent-gate`, before any code exists), "does this match the spec" (`intent-reviewer`), and "does this follow the mechanical rules" (`compliance-reviewer`) into three separate, narrower gates instead of one agent judging all three at once. See rule 13a in `~/.claude/CLAUDE.md` for why that split exists.

- **project-bootstrap** — use it ONCE ONLY, the first time on a project (while `Claude/docs/SPEC.md` is still empty). It figures out on its own whether it's looking at existing code or a new project:
  - **Existing code** → maps the project structure (where assets, devices, Verse scripts are) into `Claude/docs/SPEC.md`; deduces its functional spec (flagging what needs confirming); does a quality check covering three separate tracks in `Claude/docs/BUGS.md`, each with its own priority-ordered roadmap — **bugs** (by severity), **deprecated Verse/UEFN APIs** found in the code (with their replacement if known), and a static **performance review** (per-tick work, unbounded loops, expensive calls not throttled/cached, and similar, for `qa-regression` to confirm at playtest); proposes concrete, evolutionary improvements in `Claude/docs/RETENTION-NOTES.md` to increase playtime and reduce drop-off, grounded in how Fortnite's Discover surfacing actually measures engagement (see section 3b below).
  - **New/empty project** → doesn't invent anything: it stops and asks targeted questions (goal, audience, main mechanics, references, constraints, what's needed for a first playable MVP), then populates `Claude/docs/ROADMAP.md` and `Claude/docs/STATUS.md` with the answers.
- **intent-gate** — runs BEFORE `coder` writes a single line: an independent check (not `coder`
  judging its own readiness) on whether the task's acceptance criteria, and any owner-supplied
  base code, are concrete enough to implement without guessing. AMBIGUO goes straight to you, not
  through `coder`'s own best guess at which reading is more plausible.
- **coder** — writes and modifies code/Verse, implements features, refactors. Refuses to start
  without a matching task ID already open in `Claude/docs/ROADMAP.md`'s `Tasks` table (see section
  2b below) — it flips that task's own Status to In corso itself, but never opens one. Always
  reads `CLAUDE.md` and `Claude/docs/STATUS.md` before starting, so it picks up where things were
  left off instead of reinventing context. For a task that splits into genuinely independent
  devices/areas, it can dispatch `coder-prep` (a cheaper-context internal helper, not a full agent
  of its own) in parallel, one per area, to write that area's Verse — MCP calls and compiles always
  stay coder's own job afterward, one area at a time, since UEFN only exposes one editor instance
  to write against. Before it reports any task complete, it must get a PASS from **intent-reviewer**
  and then a PASS from **compliance-reviewer** below (in that order), then hand off to
  **planner-docs** to actually mark the task Fatto — it stays the sole owner of implementation and
  of deciding when a task is finished, it just no longer grades its own compliance, on either axis,
  or closes the task on its own say-so.
- **intent-reviewer** — the first of two review gates, checking ONLY whether `coder`'s output
  actually matches the task's acceptance criteria — line by line, no invention, no
  silently-resolved ambiguity. Runs before any mechanical check. Never writes code, never touches
  devices — reads and verifies, then returns PASS or an itemized REJECTED list `coder` has to fix
  before resubmitting.
- **compliance-reviewer** — the second gate, and only runs once `intent-reviewer` has already
  PASSed the same task: checks that what `coder` built follows this kit's mechanical rules
  (centralized logger, naming/organization, `DemoDisplay` presence and accuracy, no new calls to
  deprecated APIs, multiplayer authority handling, state machines where called for) and, if the
  second brain is configured, that a reusable pattern was actually checked against/recorded in the
  vault rather than only living in this project's own memory. Never writes code, never touches
  devices. Distinct from `qa-regression` (runtime/gameplay regressions at playtest) and
  `release-gate` (whole-project readiness before a release) — these two review one task, right
  after it's written.
- **qa-regression** — doesn't write features: analyzes build/runtime logs, looks for regressions against what's already marked "done," and also flags bugs nobody explicitly asked about ("unseen" bugs), adding them to `Claude/docs/BUGS.md`. If the project is connected to UEFN via MCP, it can run a verification play-session — and it's also invoked automatically after every playtest (see section 5).
- **planner-docs** — the gatekeeper of the plan-first workflow (section 2b): the only one who
  opens a new ROADMAP.md task row, edits its content, or marks it **Fatto** — always after
  `coder` reports PASS verdicts from BOTH `intent-reviewer` and `compliance-reviewer` for it, never
  on unverified say-so. Also keeps STATUS.md's "Current state" summary honest and triages
  `BUGS.md`'s "Newly reported" section. Invoke it both to open a task before `coder` starts and, as
  before, at the end of a session.
- **release-gate** — use it before a release/showcase, not in day-to-day work. Doesn't find new bugs and doesn't write code: it reads the already-existing `BUGS.md`, `STATUS.md`, `ROADMAP.md`, and `SPEC.md`, cross-checks every task at the current release's Priority against ROADMAP's Fatto status, and gives a verdict (ready / ready with reservations / not ready) in `Claude/docs/RELEASE-READINESS.md`, with dated entries that don't overwrite history.
- **codebase-auditor** — an independent, whole-codebase quality audit, run on demand at any project stage rather than tied to a single task: a senior developer seeing the codebase for the first time, understanding the architecture/data flow before judging anything, then checking structural problems, duplicated code, performance bottlenecks, maintainability risk, and — specifically — issues that only surface after a long, uninterrupted play session (a growing collection never cleared, event bindings that stack up round after round, per-player state never cleaned up on leave) rather than what a short playtest would catch. Never writes code or touches devices; hands its structured findings to `planner-docs`, which opens a ROADMAP task per finding worth tracking (or routes a small one into BUGS.md instead). Distinct from `intent-reviewer`/`compliance-reviewer` (one task's compliance, right after `coder` finishes) and `qa-regression` (runtime regressions from an actual play-session).
- **second-brain-librarian** — optional (see section 3c), the only agent whose work happens OUTSIDE the current project: it owns the Obsidian second-brain vault. `coder` and `project-bootstrap` hand off to it (a short brief) instead of writing to the vault themselves; it can also be invoked directly to run that vault's own `compile`/query/`audit` workflows.
- **second-brain-trainer** — optional (see section 3c), only useful if `second-brain-librarian` is configured. Use it for a deliberate, larger sweep of the current project — not routine syncing of the one thing you just built. It splits the project into areas, dispatches a `second-brain-scout` (a cheaper-model internal helper, not a full agent of its own) for each area in parallel, then hands the combined findings to `second-brain-librarian` in a single call, so the fan-out speeds up analysis — cheaply — without ever letting more than one writer touch the vault at once.
- **growth-manager** — everything about getting the map discovered, clicked, played longer, and returned to (analytics, competitor research, launch/growth plans, retention game-design, trailers/social content, thumbnails, titles/descriptions, update comms). Doesn't touch Verse or devices, and doesn't write `STATUS.md`/`ROADMAP.md`/`BUGS.md` itself. It's the entry point for the eight `fortnite-*` skills (section 3e): ask it in plain language and it routes to the matching skill(s) — you don't need to know their names or invoke them directly.

If a specific project ever needs different agent behavior, create an agent with the same name inside that project's `.claude/agents/` — it takes priority and only overrides it there.

## 2b. Plan-first workflow: ROADMAP.md and STATUS.md

The order the whole team follows, end to end: **Request → task opened/updated → code → review →
task closed.** No agent skips a step or writes code before there's a tracked task — see
`~/.claude/CLAUDE.md` rule 13 for the full rule; this section is the practical walkthrough.

**`ROADMAP.md`'s `Tasks` table** is the single source of truth for what's planned:

| ID | Feature | Status | Acceptance criteria | Priority |
|---|---|---|---|---|
| T-014 | Double-jump | Fatto | Player can jump a second time mid-air exactly once per fall | MVP |
| T-015 | Storm shrink phase 2 | In corso | Storm radius shrinks to 50% at the 3-minute mark | MVP |
| T-016 | Leaderboard UI | Da fare | Top 5 players by score shown at round end | Later |

Only **planner-docs** creates a row or edits Feature/Acceptance criteria/Priority, and only it
ever sets **Fatto**. **coder** may flip Status between Da fare/In corso/Bloccato on a row it's
actively working — nothing else in that file.

**`STATUS.md`'s "Current state" block** (replaced on every update, sits above the append-only
dated log) is what you read first when reopening a project:

```
## Current state
_(updated: 2026-09-07)_

**In progress:** T-015 — Storm shrink phase 2 (coder)
**Planned next (this release):** T-016 — Leaderboard UI
**Done so far (this release):** T-001…T-014
**Recommended next step:** finish T-015, then start T-016
```

**A typical feature request, walked through:**
1. Owner: "add a double-jump." No `T-xxx` row matches yet.
2. `coder` checks ROADMAP.md, finds nothing, stops and asks for one line of acceptance criteria
   instead of guessing.
3. `planner-docs` opens `T-014 | Double-jump | Da fare | Player can jump a second time mid-air
   exactly once per fall | MVP`.
4. `coder` flips `T-014` to **In corso**, writes the ID to `Claude/docs/.active-task`, invokes
   `intent-gate` (CHIARO — the acceptance criteria are concrete), implements it, runs the
   compile-fix loop.
5. `coder` invokes `intent-reviewer` with `T-014` and the touched files → PASS, then
   `compliance-reviewer` the same way → PASS (or fixes and resubmits to whichever one flagged
   something, until both are clean).
6. `coder` hands off to `planner-docs`, which sets `T-014` to **Fatto**, updates STATUS.md's
   Current state block and appends a dated log entry.
7. At release time, `release-gate` cross-checks every MVP-priority task is Fatto before giving a
   verdict.

**Where this doesn't apply**: `growth-manager`'s marketing/growth work, `second-brain-librarian`'s
vault work, and a bug fix small enough to stay inside `BUGS.md`'s own severity queue rather than
becoming its own release-tracked feature — see rule 13 for the exact boundary.

## 3. Base rules that apply to every project

A handful of base rules — naming/organization, centralized logging, always-multiplayer, performance/FPS, state machine — aren't specific to any one project: they apply across the board. Instead of repeating them in every project's `CLAUDE.md`, they live in `user-level-memory/CLAUDE.md` (already copied to `~/.claude/CLAUDE.md` in Phase 1) — Claude Code loads this file in EVERY session, on any project, automatically.

In short, what it contains and where it's applied:
1. **Naming/organization**: new content in `custom_*` folders (e.g. `custom_verse/`), organized by content/asset type/use per [Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/starting-and-organizing-a-project-in-fortnite). Also covers the **Outliner**: devices grouped into folders matching the experience's actual areas (Lobby, Game Area 1, Devices, etc.), each named `<DeviceType>_<Function>` (e.g. `teleport_lobby`) instead of left with a default name. `project-bootstrap` detects the convention already in use on an existing project and, if the Outliner is disorganized, proposes a reorganization plan for the owner to review rather than renaming things itself.
2. **Centralized logging**: the `DebugLoggingEnabled` pattern is in the scaffold as `Claude/reference/logger-template.verse.txt`. `coder` uses/adds it where missing; `qa-regression` cites it as the first move when logs aren't enough to diagnose a bug ("add logging, don't guess").
3. **Always multiplayer**: `coder` and `qa-regression` must explicitly reason in multiplayer terms (server/client authority, multiple players on the same object), not just "works in solo preview."
4. **Performance/FPS and deprecated APIs**: `project-bootstrap` does a static review during its initial quality check, flagging patterns likely to cost performance (per-tick work, unbounded loops, uncached/unthrottled expensive calls, and similar) plus any deprecated Verse/UEFN API calls it finds, both as their own sections in BUGS.md; `qa-regression` in turn flags actual framerate drops or suspicious logic during playtests, even when it isn't a strict error. `coder` avoids introducing new calls to something already flagged deprecated and migrates one opportunistically when already touching that code.
5. **State machine**: default pattern for phase-based logic in new projects; targeted refactor proposal (not a full rewrite) when needed on existing flag-based projects.
6. **Header documentation in Verse code**: every file must have a comment block summarizing what it does, comments above logical sections, and a date + version number updated on every substantial change (there's no Git, so this is the only history available). `coder` maintains it; `project-bootstrap` flags files still missing it in BUGS.md.
7. **DemoDisplay for every Verse device**: each custom Verse device gets a dedicated `DemoDisplay` stand — one per Verse device, grouping every device it configures by function, sized via its `width`/`depth`/`height` properties (not actor Scale) to fit them, with the devices placed on it (not stacked, not lined up) at the stand's base height. Devices whose position is gameplay-functional (Storm Controller, Player Spawner, etc.) are never moved onto a stand — they're only referenced by name in its description. Created or updated every time `coder` places or modifies that device or its connections, not just when it's first created. `project-bootstrap` flags a missing, stale, or wrongly-grouped `DemoDisplay` as a non-blocking follow-up in BUGS.md.
8. **Support devices outside the play area**: logic/support devices that aren't gameplay-critical in position (Item Granter, Timer, Elimination Manager, `DemoDisplay`, etc.) go outside the playable area, grouped on their function's `DemoDisplay` stand, so players never see or reach them — devices players are meant to encounter (Player Spawner, a central display case) or whose position is gameplay-functional are the exception. `project-bootstrap` flags misplaced support devices in BUGS.md rather than moving them itself.
9. **Second brain (Obsidian) integration, optional**: when a vault path is configured (rule 11), `coder` and `project-bootstrap` hand off to the dedicated `second-brain-librarian` agent to write/update reusable device/mechanic articles there — see section 3c below.

## 3b. Getting smarter across projects: the `uefn-lessons` skill

Per-project agent memory (`memory: project` on `coder`/`qa-regression`) is siloed to one
island — something learned fixing a bug on project #12 is invisible on project #37. That's
fine for lessons that only make sense on that one project (this project's specific devices,
this project's design decisions), but a waste for lessons that are really about Verse, UEFN,
or the MCP tooling itself and would save time on every island.

For those, this kit adds a second, shared memory layer: `user-level-skills/uefn-lessons/`,
installed once (Phase 1, step 5) to `~/.claude/skills/uefn-lessons/SKILL.md`. `coder` and
`qa-regression` both read it before starting work, the same way they read their own project
memory, and both add a short entry to it — not to per-project memory — whenever they hit
something non-obvious that isn't specific to the current project (a Verse syntax gotcha, a
device type that behaves differently than documented, a recurring MCP quirk). The file ships
with a handful of placeholder examples showing the expected one-line format; replace them with
real entries as they come up.

This is the actual mechanism for coding getting measurably better across your projects over
time, rather than each new island starting from the same blind spots as the last one — but
only if entries are added consistently rather than skipped when a session is focused on
finishing its task. Since it's a single shared file across every project, occasionally skim it
yourself and prune anything that turned out to be wrong or too specific to have been added
there in the first place.

The file also ships with a curated (not agent-accumulated) **"Discover / retention signals"**
category, summarizing what Fortnite's Discover surfacing actually measures — average playtime,
bounce rate (the concrete reason a 5-minute session threshold matters), player retention, and
Qualified Play-Through Rate — sourced from
[Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite).
`project-bootstrap` reads it when writing retention/evolutionary proposals, so those proposals
target what actually moves Discover visibility instead of generic playtime advice.

## 3c. Optional: an Obsidian second brain for reusable mechanics

`uefn-lessons` (above) is for short, one-line tooling/syntax gotchas. This is a different,
complementary layer, for a different kind of knowledge: full, browsable wiki articles about
**game mechanics and Verse device implementations** — kept current per device/mechanic, so a
pattern that already works on one island can be reused by copying an up-to-date snippet from the
wiki instead of rebuilding it from scratch on the next one.

It's not part of any single UEFN project — it's its own Obsidian vault, set up once (Phase 1,
step 7, optional) and reused across every project. `second-brain-template/` in this kit has the
vault's own `CLAUDE.md` (a librarian/knowledge-base agent role — different rules than the UEFN
agents above, since it's managing a wiki, not a game project) and a `README.md` explaining the
one-time vault setup.

A dedicated sixth agent, **`second-brain-librarian`**, owns all reads/writes to this vault — the
only agent in this kit that works outside the current project's folder. `coder` and
`project-bootstrap` don't touch the vault themselves; they hand off to it instead, so the vault's
own conventions live in one place rather than being duplicated (and potentially drifting) across
every agent that might want to contribute to it.

This isn't write-only — it feeds back into new work too. Once `~/.claude/CLAUDE.md`'s rule 11
has a real path instead of the `<SECOND_BRAIN_PATH>` placeholder:
- **`coder`** invokes `second-brain-librarian` with a short brief after implementing/changing a
  device or Verse pattern reusable beyond the current project — not every change, only ones
  worth keeping a snippet for. It also **queries** the vault before implementing a common
  pattern (respawn, item pool, round progression, and similar) from scratch, to check whether a
  ready implementation already exists to adapt instead of reinventing it.
- **`project-bootstrap`** writes to the vault as a closing step (A6) after its initial analysis
  of an existing project, for generalizable mechanics it identified while mapping the codebase.
  It also **queries** the vault during its retention step (A4), to prefer proposals with a
  track record on other projects over purely theoretical ones.
- **`second-brain-librarian`** reads the vault's own `CLAUDE.md` before writing anything, rather
  than relying only on this guide's summary, since you can customize your vault's conventions
  over time and that file is the authority on its own structure. You can also invoke it directly
  for that vault's own `compile` (ingest `raw/` material you dropped in yourself), query, and
  `audit`/`lint` workflows — plus a fourth one, **UEFN release-notes sync**: it fetches Epic's
  "What's new in UEFN" page and keeps `wiki/note-di-rilascio-uefn/` current, backfilling
  everything on the first run and adding only new entries afterward. `second-brain-template/`
  has `weekly-release-notes-sync.ps1`/`.sh` plus README instructions to run this automatically
  every Thursday via your OS's own scheduler (Task Scheduler / cron) — Claude Code has no
  built-in weekly scheduler, so this is standard OS automation, same idea as the kit's own
  post-playtest hook.
- Articles about a device/mechanic keep one section, `## Implementazione Verse (ultima
  versione)`, updated **in place** on every change (version/date bumped, snippet replaced) —
  never a new snapshot appended alongside the old one. That's the whole point: one place per
  device/mechanic that's always current.
- This never blocks or fails a UEFN task: if the vault path is wrong, unreachable, or unset, the
  agents skip this step silently (or note it once) and continue with the actual project work.

This is entirely optional — nothing else in the kit depends on it, and leaving the placeholder
unset keeps it off.

**Optional seventh agent: `second-brain-trainer`, for a deliberate parallelized sweep.** The
flow above is naturally one-thing-at-a-time — `coder` syncs one pattern after finishing one
change, `project-bootstrap` syncs a handful at the end of one analysis pass. That's fine for
day-to-day work, but slow if you deliberately want to backfill the vault from a large or
unfamiliar project all at once. `second-brain-trainer` speeds that up by splitting the project
into areas (level zones, systems, whatever grouping makes sense — either given by you or inferred
from `Claude/docs/SPEC.md`'s project-structure section and the Outliner's own grouping) and
dispatching one `second-brain-scout` per area **in parallel** — genuinely concurrent subagents, so
if you have the Agent Console open you'll see several nodes light up at once. `second-brain-scout`
is a small internal helper (you never invoke it yourself) that runs on a cheaper model (Haiku,
not Sonnet) since this analysis step is read-only and low-judgment — it exists purely to make
training passes cost less; it doesn't count toward "seven agents" since it only ever runs as
`second-brain-trainer`'s own dispatch, never on its own. The one rule it never breaks: those
parallel scouts only ever gather findings, they never touch the vault themselves —
`second-brain-trainer` collects every scout's findings and hands them to
`second-brain-librarian` in exactly ONE call at the end. This is deliberate, not an oversight: the
vault is plain markdown files with no locking, so two writers touching it around the same time
risks corrupting or silently losing content, not merging cleanly. Parallelizing the reading is
safe and fast; the writing stays strictly single-threaded either way. Invoke it directly when you
want this ("run a second-brain training pass on this project," "parallelize capturing reusable
patterns from this project") — it's not something the other agents invoke on their own.

**Parallelizing `coder` across independent devices/areas.** `coder` used to be strictly
one-device-at-a-time even when a task obviously split into unrelated pieces (say, three unrelated
game-area systems in one request) — deliberately, because UEFN only exposes ONE MCP server per
editor, serving whichever project is open, and a Verse compile is a whole-project build rather
than an isolated per-file one. Two concurrent device placements or two concurrent compiles
wouldn't fail safely, they'd race against that one shared live editor state. So `coder` still
never does that part in parallel — but when the areas are genuinely independent (no shared state,
no cross-references, order doesn't matter), it can now dispatch `coder-prep` — one per area, run
concurrently — to do the part that IS safely parallel: reading each area's own context and writing
its actual Verse code. Each `coder-prep` reports back exactly what needs placing/configuring via
MCP; `coder` then applies those plans itself, one area at a time, running its normal
compile-fix loop between each so the shared editor state only ever sees one actor working on it at
once. `coder-prep` is a small internal helper (you never invoke it yourself) — same model as
`coder` (Sonnet), since this is real implementation work, not a lightweight scan; the savings come
from running areas concurrently and each clone only loading its own area's context, not from a
cheaper model. Same caution as `second-brain-trainer`'s own fan-out: `coder` should skip this and
just work through a task normally if the areas aren't truly independent, or the task is small
enough that splitting wouldn't save meaningful time.

## 3d. Seven more skills, for keeping token usage down

`uefn-lessons` (3b) and the second brain (3c) are the two original shared-knowledge layers. This
kit adds seven more, all following the same **progressive disclosure** shape: a short, precise
`description` in each `SKILL.md`'s frontmatter (so Claude Code knows when it's relevant without
loading it), a dense body covering just the core workflow, and a `references/` subfolder with
longer detail loaded only when actually needed — instead of that detail sitting inline in
`~/.claude/CLAUDE.md` or an agent file, which loads in every single session whether or not it's
relevant to the task at hand.

- **`verse-patterns`** — reusable Verse code idioms (state machines, multiplayer authority,
  centralized logging/timers, item pools, round progression) at high density. `coder` reads the
  one matching reference file before writing a common pattern from scratch. Distinct from the
  second brain: this is generic language/structure shape, not a validated, project-tested
  implementation with history.
- **`uefn-device-gotchas`** — device-TYPE-specific quirks (DemoDisplay sizing/orientation math,
  Elimination Manager/Item Granter timing, Storm Controller/Player Spawner position-critical
  behavior). Complements `uefn-lessons`, which stays generic Verse/UEFN/MCP tooling; this one is
  specifically about individual device types' behavior.
- **`performance-uefn-checklist`** — the short, actionable checklist `project-bootstrap` works
  through during its A3 static review (see section 2), and `qa-regression` can reference the
  same list when watching for FPS issues at playtest.
- **`discover-retention`** — the Discover/retention signal facts (bounce rate, QPTR, and
  similar) plus a growing log of retention proposals actually tried and their outcome.
  `project-bootstrap` reads it during A4 instead of reasoning about playtime from scratch.
- **`second-brain-query`** — a handful of rules for asking the second brain narrowly (specific
  question, not "everything about X") so a query round-trip stays short. Read before `coder` or
  `project-bootstrap` invoke `second-brain-librarian` in query mode.
- **`token-aware-coding`** — general habits (prefer targeted search over a full file read,
  precise `@file` mentions, periodic internal summarization, don't re-read what's already in
  context) that apply across any agent, any task.
- **`brand-collections-uefn`** — see rule 12 above. A marker table (Content Browser folder names,
  device class names, template naming) for recognizing which official Fortnite Game Collection
  (TMNT, LEGO, Fall Guys, and others) a project is built on, plus the procedure for capturing real
  markers from a project when an unrecognized brand shows up. `project-bootstrap` reads it during
  A1 whenever a project's assets/devices/template name look brand-themed.

None of these are required reading every session — each is scoped to a specific step where it's
actually useful, and their descriptions are written so Claude Code (or the agent files that
explicitly point to them) only reaches for the relevant one.

## 3e. Eight more skills, for the growth/marketing side of a map (not just the build)

Everything in 3b-3d is about building the island correctly. These eight are about what happens
once it exists: getting it discovered, getting people to click, keeping them playing, and getting
them to come back for the next update. They're plain Claude Code skills, not subagents — no
`model` field of their own — but unlike the dev-side skills above they now have a dedicated
owner: the **`growth-manager`** agent (section 2). Talk to `growth-manager` in plain language
("help me plan the launch," "why is my CTR low," "write a thumbnail for this map") and it reads
the matching skill(s) for you — that's the normal way to reach them. Claude Code's own
description-based skill matching (same mechanism as `discover-retention` and
`brand-collections-uefn`) is still there as a second path if you invoke a skill directly without
going through the agent, but you don't need to rely on it.

- **`fortnite-analytics-coach`** — reads Creator Portal metrics (CTR, playtime, Day 1/7
  retention, CCU) plus public trackers (Fortnite.GG, UEFN Stats, Fortnite.FYI, Goodnite) and
  turns them into a prioritized, concrete action plan. Fires when you paste metrics or ask for a
  performance read.
- **`fortnite-competitor-analyzer`** — studies top maps in your genre on the same public sources
  to find what works, what's weak, and where you can differentiate. Fires when you ask about
  competitors or "what's working in this genre."
- **`fortnite-marketing-launch`** — a full pre-launch/launch/post-launch plan, growth strategy for
  an already-live map, content calendar, and outreach ideas. Fires when you're about to launch or
  push growth on an existing map.
- **`fortnite-retention-gamedesign`** — game-design-level fixes for session length and Day 1/7
  retention (onboarding, core loop, progression systems, pacing). Complements
  `discover-retention`'s signal facts with actual design proposals. Fires when you want players to
  stay longer or come back.
- **`fortnite-social-trailer`** — trailer scripts, TikTok/Shorts hooks, captions, and viral clip
  ideas built around a strong first 1-3 seconds. Fires when you ask for promotional content.
- **`fortnite-thumbnail-pro`** — high-CTR thumbnail concepts and ready-to-use generation prompts,
  built around Epic's hard rules (1920x1080, no clickbait, no blood/weapons-at-camera/currency
  references). Fires when you ask for a thumbnail.
- **`fortnite-title-description`** — the full Discover publishing package: title (≤40 chars),
  description (≤500 chars), one main genre, 4 tags, and 3 how-to-play lines (≤150 chars each) —
  all in English with the character counts checked, not estimated — plus a community blog
  presentation (an extended and a short version, in whatever language you ask for) aimed at
  getting readers to actually go play. Fires when you're about to publish/republish a map, or
  for any single field on its own.
- **`fortnite-update-writer`** — patch notes, short Discord/social versions, hype announcements,
  and changelog copy, written to make players want to come back in. Fires when you need to
  communicate an update.

**Making sure they actually fire when you need them:**
- Default path: ask `growth-manager` directly ("@growth-manager help me plan the launch," or just
  describe what you need if it's the obvious next thing to do) — it routes to one skill or
  chains several, in a sensible order, without you needing to know any of the eight names.
- If you'd rather skip the agent, their descriptions still say "use when..." in plain terms, so
  Claude Code's own matching can pick the right one directly — or name it yourself:
  "use the fortnite-thumbnail-pro skill for this" always works regardless of how well the
  description matched.
- These eight are independent of each other and of the dev-side skills — `growth-manager` will
  happily chain several in one session (e.g. `fortnite-competitor-analyzer` →
  `fortnite-title-description` → `fortnite-thumbnail-pro` for a single launch push).

## 4. How to invoke them during work

Inside a Claude Code session opened inside the project's `Content/`:

- Natural language: *"use the coder agent to implement the respawn checkpoint"*
- Explicit mention (guaranteed delegation): `@"coder (agent)" implement the respawn checkpoint`
- Claude can also pick the right agent on its own based on each one's `description` field, if the task is clear.

### The very first session on a project

1. Open a terminal inside the project's `Content/` folder (after Phase 2 setup above), launch `claude`.
2. Ask it to use **project-bootstrap**. If code already exists, within a few minutes you'll have `Claude/docs/SPEC.md`, `Claude/docs/BUGS.md` (with a bug-fixing roadmap), and `Claude/docs/RETENTION-NOTES.md` ready to read and correct where needed. If the project is empty, it will ask you the necessary questions: answer them in the conversation.
3. From here on, for that project, use the normal workflow (below).

### Typical workflow for later sessions

1. Open a terminal inside the project's `Content/`, launch `claude`.
2. Work with **coder** to implement/fix code.
3. Once changes are made, ask **qa-regression** to check logs and regressions (and, if connected to UEFN, run a verification play-session) — or let it fire automatically after the playtest (section 5).
4. Before closing, ask **planner-docs** to update `Claude/docs/STATUS.md` with what was done, known issues, and the next step.
5. Close the session: next time you reopen that project, just ask Claude to "read the project status" and it'll immediately know where things were left off.

If you work on one project at a time, this flow is linear: open the right project in UEFN, open Claude Code inside its `Content/`, work, close, move to the next.

## 5. Automation: bug/regression search and doc updates after every playtest

Claude Code has a **hook** system: commands that fire on their own when a specific event happens — including `PostToolUse`, which fires right after a given tool has been used. This lets us hook into exactly the moment "a test play-session just ended," which is different from "Claude Code was closed": you can test multiple times in the same session and get an automatic check every time.

**Discovered through live testing:** the `unreal-mcp` server doesn't expose a distinct tool per action (one for "start session," one for "stop session," etc.) — it exposes a single **generic dispatcher tool**, `mcp__unreal-mcp__call_tool`, which internally routes all of its toolsets' actions via the call's payload. This means the `matcher` alone can't distinguish "a play-session just ended" from any other MCP call (reading a Verse file, moving a device, etc.) — it would fire on everything.

So in the scaffold's `.claude/settings.json`, the matcher fires on every call to the dispatcher, and the real filter lives inside the hook script, which reads the hook's JSON payload from stdin:

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "mcp__unreal-mcp__call_tool",
      "hooks": [
        {
          "type": "command",
          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"${CLAUDE_PROJECT_DIR}/Claude/hooks/after-playtest.ps1\"",
          "timeout": 300
        }
      ]
    }
  ]
}
```

`Claude/hooks/after-playtest.ps1` (PowerShell — use it if bash isn't available on the machine, as on "pure" Windows; `after-playtest.sh` is the equivalent for bash/WSL/Git Bash) reads the payload from stdin and checks whether this specific call is really a session/game stop (it looks for `stopgame`/`stopsession` in the raw payload text, without depending on one exact JSON field that might change between server versions). Only if it matches:
1. It runs **qa-regression** in non-interactive mode, which analyzes logs and state and adds any problem found to `Claude/docs/BUGS.md` (under "Newly reported").
2. It runs **planner-docs**, which updates `Claude/docs/STATUS.md` and moves/prioritizes the new bugs in the backlog.
3. It also saves everything to a log file inside `Claude/logs/`, so there's always a readable trace of what happened.

On any other MCP call, the script exits immediately without doing anything — otherwise every single Verse file read would restart the whole check, wasting tokens.

**One thing to verify once per project** (included in `Claude/SETUP-INSTRUCTIONS.md`): run a test play-session and check that the log in `Claude/logs/` appears only when you stop it, not on every MCP action. If it never fires, or always fires, this server's payload might not contain the expected strings: uncomment the debug line at the top of the script to log the raw payload once and adjust the pattern accordingly.

**Tip:** let it run automatically, but check `Claude/docs/BUGS.md` and the logs in `Claude/logs/` every so often in the first few weeks, so you can correct course if you notice inaccurate reports.

## 5b. Optional: a real-time Agent Console

A small, arcade-console-style local web page that lights up each agent's card the instant it
starts or finishes working, and draws an animated pulse from one card to another when an agent
hands off to a second one mid-task (e.g. `coder` invoking `second-brain-librarian` while it's
still active) — a live view of what the team is actually doing right now, distinct from
`Claude/docs/STATUS.md`, which only records what's already finished.

**How it works.** Claude Code has no built-in way to broadcast "a subagent just started" to an
external page, so this is built from the same two building blocks already used elsewhere in this
kit: hooks (section 5 above) and a local web server.
- `Claude/hooks/agent-console-log.ps1` (or `.sh`) is wired into `.claude/settings.json` as a
  `PreToolUse` hook, matched on the internal tool Claude Code uses every time it invokes ANY
  subagent (coder/qa-regression/second-brain-librarian included) — **observed as either
  `"Task"` or `"Agent"` depending on the Claude Code build/version** (confirmed via a real
  payload capture on a live setup), so the matcher (`"Task|Agent"`, a regex) and the script
  accept either name rather than assuming one. It logs the "start" event.
- `Claude/hooks/agent-console-stop.ps1` (or `.sh`) is wired as a **`SubagentStop`** hook —
  logging "stop" from there, not from `PostToolUse` on the dispatch tool, was a deliberate fix:
  a subagent dispatched to run **in the background** returns control (and fires `PostToolUse`)
  the instant it's dispatched, not when the work is actually done — a real test showed the
  console reporting "finished" a couple seconds after "started" while the agent was still
  genuinely working. `SubagentStop` is the hook Claude Code fires on real completion either way.
  Since `SubagentStop`'s own payload doesn't reliably say which agent just finished, attribution
  goes through a small FIFO queue file, `Claude/logs/agent-console-active.json`: the start hook
  pushes onto it, the stop hook pops the oldest entry and uses its agent/description. This is
  itself best-effort (see the note further down on the console overall being a heuristic
  visualization) — right for the common case of one or a few overlapping invocations.
  Already set up in the scaffold, nothing to configure per project — but if a future Claude Code
  version renames the dispatch tool again, the console goes quiet the same way it did before
  this fix, and the same diagnostic applies (see Troubleshooting below).
- Every start/stop appends one line to `Claude/logs/agent-console.jsonl`.
- `Claude/hooks/agent-console-server.ps1` (PowerShell, no dependencies) or
  `agent-console-server.py` (Python, cross-platform) is a tiny local web server, normally started
  and kept correctly scoped to the current project for you automatically (see next paragraph) —
  you can still run it yourself in its own terminal window if you'd rather, see below. It also
  exposes a `/whoami` route (`{"project": "<this project's folder>"}`) purely so the
  session-start hook can tell "already running for this project" apart from "a different/stale
  project's server is still bound here."
- `Claude/hooks/agent-console.html` is the actual page: it polls the server once a second and
  animates accordingly.
- `Claude/hooks/session-start-reminder.ps1`/`.sh` is a third hook, on `SessionStart`, that's the
  automation piece described next.

**It starts itself automatically, every session — no asking.** A `SessionStart` hook
(`session-start-reminder.ps1`/`.sh`, matcher `startup` so it only fires when you launch `claude`
fresh — not on every `/clear`/`/compact`) deterministically makes sure the console server is
running and correctly scoped to THIS project before Claude's very first reply. It works by
checking a `/whoami` route every server instance exposes (reporting which project folder it's
actually serving): if a server is already up and it's already serving this exact project, it's
left alone; otherwise — nothing running, or a stale server from a different project still bound
to the same port — whatever's on port 8765 gets killed (only if it looks like one of this kit's
own server processes, never an unrelated program) and a fresh one is started **in the
background** (detached, so it doesn't block your session) for the current project. The hook then
opens it in your default browser automatically, every session — no need to open the tab yourself
or remember the URL. Claude also mentions the URL in its first reply, in case you closed the tab
or want to reopen it; there's nothing to say yes or no to, and nothing to remember to answer.
This also fixes a real cross-project bug: since every project uses the same
port, switching to a different UEFN project used to leave you looking at the *previous*
project's stale console (it looked "already running" from the outside) — now the `/whoami` check
catches that and replaces it automatically.

**To start it manually** instead (or if you'd rather run it yourself in its own terminal, which
also works and is a bit more transparent about what's running):
```
powershell -ExecutionPolicy Bypass -File Claude\hooks\agent-console-server.ps1
```
or, if you'd rather use Python:
```
python3 Claude/hooks/agent-console-server.py
```
Either way, open **http://127.0.0.1:8765/** in your browser — open it as that URL, not by
double-clicking the HTML file, since the page needs the real local server to fetch live data
from (a plain `file://` page can't reach it the same way). Leave the browser tab open while you
work in Claude Code; the console updates on its own, nothing to refresh.

**If you update the console's own files while the server is already running, restart the
server.** `agent-console-server.ps1`/`.py` reads `agent-console.html` and computes its file
paths once at startup — it doesn't notice you've copied in a newer version of any
`agent-console-*` file, including new endpoints like `/tokens`. A real test hit exactly this: a
server started before a file update kept serving the old page/routes, which looked identical to
the token feature simply not working. Stop it (Ctrl+C in its terminal, or end the PowerShell/
python process) and start it again after copying in updated files.

**Version tag next to the title (v1.56).** A small "v1.56"-style tag sits right after the title,
sourced from a single `KIT_VERSION` constant near the top of the page's script. Its only purpose
is troubleshooting: this is a single-page app, so replacing `agent-console.html` on disk does
nothing to a browser tab that's already open — it keeps running whatever JS it already loaded
until reloaded. That exact confusion has caused real dead-ends before (a fixed threshold looking
"still broken" because an open tab was silently still running the old file). If you just updated
the kit and something doesn't match what the changelog says it should, check this tag first —
if it's still the old version, hard-refresh the tab (Ctrl/Cmd+Shift+R) before assuming the fix
didn't work.

**What it shows**: a compact header (title + tagline + connection status on one row); a top stats
row (session timer, token count, and an agent status legend — see below); ten agent cards — the
seven working bots plus Obsidian Vault, YOU, and MCP Server — sharing one ring (a faint dashed
guide marks it), dim and idle by default, glowing in that agent's own color with a "WORKING" pill,
the current task description, a small colored ray burst around the icon, and a live elapsed-time
readout (`⏱ 1:24`, ticking every second) while active; a scrolling terminal-style log on the right
(now labeled with the current project's name, and matched in height to the ring panel beside it)
with a timestamped line per start/stop; a brief animated pulse between two cards when one agent
invokes another while still active; small particle "fountains" (💎 from Obsidian Vault, 📄 from
`planner-docs`) while those two are active; and a 🚀 missile-with-explosion from `qa-regression` to
`coder` whenever a stop event's own description mentions finding a regression. Obsidian Vault sits
between its two second-brain neighbors on the ring rather than wherever plain even-spacing would
put it (see below). History persists in `Claude/logs/agent-console.jsonl` across sessions —
delete that file if you want a clean slate.

**Agent status legend (v1.46).** The "Agents" stat box in the top row shows the total agent count
(7) plus a live breakdown with four colored dots: grey = idle, green = working, yellow = waiting
(blocked on a delegated child that hasn't finished yet), red = broken (that agent's own
invocation has been running unusually long — likely stuck or erroring). Each agent card's own
status LED uses the same four colors and the same rule, so the legend numbers and the individual
LEDs never disagree. This replaces the old three-color scheme where "waiting on a child" and
"stuck/erroring" were both shown as red — now only the second case is red, and the first is
yellow. That same box also shows "PROJECT: <name>" above the count (v1.50) — the same name shown
in the Activity Log panel's header, repeated here since this box is more prominent.

**Chief of Staff hub LED.** Green while either a subagent is actively delegated-to, or the main
session itself is working directly (editing files, calling the UEFN MCP server, and so on,
without delegating) — the second case used to be missed (v1.50 fix), so the hub could sit grey
while genuinely busy just because the work wasn't a subagent dispatch. Same `/session` polling
that drives the YOU node's own LED (green while the main session is actively working, grey once
it's yielded back to you and is waiting on your next message).

**The Obsidian Vault node is "connected to both brains."** It draws two spokes now —
`second-brain-librarian` (purple) and `second-brain-trainer` (teal, new since that agent was
added) — and pulses with a floating "💭 Thinking" indicator whenever either is active; when BOTH
are active at the same time, it switches to a stronger oscillating tug animation, as if being
pulled from two directions at once. All of this is purely decorative on top of the real
start/stop tracking underneath — none of it changes what actually gets logged.

**Session timer.** "Session running for" shows elapsed time since the console SERVER process
actually started — via a `started_at` timestamp `agent-console-server.ps1`/`.py` records at
launch and serves from `/whoami`, polled every 5 seconds. It resets the moment the server
restarts (a fresh `claude` session, a project switch, a kit file update), which is the whole
point: a v1.44 fix — the previous version computed this from the OLDEST line in
`agent-console.jsonl`, which deliberately persists across restarts (see below), so after using
the kit across a few sessions this stat kept showing hours or days of elapsed time seconds after
a genuine restart, looking exactly like "the server never actually restarted" even when it had.
If `/whoami`'s `started_at` field isn't available for some reason (a very old server build still
running), it falls back to the previous earliest-log-line behavior rather than showing nothing.

**Tokens this session (approximate, experimental).** A rough running total of token activity —
summed from the session transcript Claude Code writes to disk, via a new hook,
`agent-console-tokens.ps1`/`.sh` (`PostToolUse`, no matcher, so it fires after every tool call,
not only subagent ones — token usage happens on every turn). Reads incrementally (tracks a byte
offset per transcript file) so it stays cheap over a long session. **Read the caveats before
trusting the number**: it's a sum of `input_tokens + output_tokens + cache_read_input_tokens +
cache_creation_input_tokens` across every assistant turn seen so far — a reasonable proxy for
"how much activity has this session generated," but NOT a billing figure (Anthropic prices those
four token kinds very differently — a cache read is far cheaper than a fresh input token — and
each turn's `input_tokens` already reflects that turn's full context, not just what's new, so
the number climbs quickly on a long session by design). There is no documented, guaranteed way
to read this from outside the app — it's inferred from the transcript file's on-disk shape,
which could change between Claude Code versions; if it stays at "—" or looks obviously wrong,
see Troubleshooting below.

**MCP Server node.** A dedicated node (🛰️) lights up whenever the UEFN MCP server
(`mcp__unreal-mcp__call_tool`) is actually called, fed by `agent-console-mcp.ps1`/`.sh` — wired on
both `PreToolUse` and `PostToolUse` for that same matcher `after-playtest.ps1`/`.sh` already
uses (a second, independent hook command, not a replacement). It shows who's calling the editor:
if a bot (e.g. `coder`) made the call, a pulse animates from that bot's node to the MCP node; if
the main session called it directly, the node just shows connected to the hub. Its own event
stream lives in `Claude/logs/agent-console-mcp.jsonl`, separate from `agent-console.jsonl`, and
is served from a new `/mcp` route. The "what was called" label is a best-effort guess at a few
common field names in the MCP payload (`tool`/`action`/`toolset`/`method`/`command`) — see that
script's own header comment if it comes through empty or unhelpful.

**YOU node's status LED.** Separate from the existing red "approval required" alert (which stays
tied to `release-gate` being active — see the footer note in the console itself), the YOU node
now also has the same small idle/active status LED every agent card has: green while the main
Claude Code session is actively working on something, grey once it has yielded back and is
waiting on your next message. Fed by two hooks working together — `agent-console-tokens.ps1`/`.sh`
marks the session active on every tool call (piggybacking on that already-always-firing hook
rather than adding a third), and a new `agent-console-session-stop.ps1`/`.sh`, wired as a second
command on the existing `Stop` hook, marks it idle the moment the main session actually yields
back to you. Served from a new `/session` route.

**"fork" dispatches get a "\<parent\> clone" node that disappears when it's done (v1.53).**
Claude Code can dispatch a background agent via `subagent_type: "fork"` (visible in the
transcript as `● fork(<description>)` / "Backgrounded agent") — this is still the same
`Task`/`Agent` tool the console already listens for (confirmed via a live payload capture:
`tool_name` is `"Agent"`, `agent_type` on the matching `SubagentStop` is the literal string
`"fork"`, not empty or malformed), so it's already logged and attributed correctly, start and
stop, with the right description each time. Earlier versions gave every fork the same generic
fallback node (🤖, permanently, via `ensureNode()`) since that fallback keyed off
`subagent_type` alone — the literal string `"fork"` for every one of them regardless of what
each was actually doing, so they piled onto one shared card and stayed on the ring forever, idle,
after finishing. `ensureNode()` now also takes the id of whichever agent was on top of the active
stack when the fork started (the same parent-detection heuristic `pulseLink()` already used) — a
fork gets a 🧬 icon, the parent's own color, a "\<parent name\> clone" label, and its spoke points
at the parent instead of the hub, so a fork `coder` spawns itself (outside the named
`coder-prep` path) reads as "coder clone," not an unlabeled tenth bot. It's also now marked
ephemeral: once it goes idle, it's removed from the console entirely (DOM node, spoke, and every
tracking structure) instead of sitting there as a dead ring slot, and the ring re-spaces itself
immediately after. Two genuinely concurrent forks under the same parent still share one node —
`subagent_type` is still the only id available, and it's still the literal string `"fork"` for
both — that part of the limitation is unchanged, just less visible day-to-day since single forks
(the common case) now behave correctly and clean up after themselves.

**This is a best-effort visualization, not a rigorous tracer.** Claude Code's hook payloads
don't include a call-stack ID, so the console infers "who invoked whom" heuristically (the most
recently-started still-active agent is treated as the likely parent) — right in the common
cases this kit actually produces (a sequential handoff, or one agent invoking another), not
guaranteed to be perfectly accurate if you build a much more tangled agent graph of your own.

**Two real `coder` (or any named agent) calls running at once share one card — with a "×N"
badge, and a fixed status-attribution bug (v1.54).** Same underlying limitation as the fork case
above (no per-call id), but this time for a NAMED agent, which matters more now that `coder` can
legitimately have two independent top-level dispatches in flight (not through `coder-prep`,
which each get their own id) — say, one you asked for directly while another from earlier is
still running in the background. The card can't split into two, so it now shows a small "×N"
badge under the pill whenever more than one concurrent call to that agent id is active, instead
of the second one being entirely invisible. Older versions also had a real bug here, not just a
display limitation: the card's own "broken" (stuck/overdue) check used to be computed from
whichever concurrent instance happened to be OLDEST, even when a much fresher call to the same
agent was the one actually driving the card — so a `coder` call that had been running fine for a
minute could show as "broken" purely because an unrelated, genuinely-long-running background
`coder` call happened to share its card. It now uses the freshest concurrent instance for that
check instead. What's still genuinely unresolvable with the data Claude Code's hooks provide:
when a stop event arrives for an agent id with 2+ concurrent instances, there's no way to know
FOR CERTAIN which one actually finished — the console assumes first-started, first-finished
(FIFO), a reasonable default but not guaranteed. **The console is a read-only dashboard, not a
control panel** — it has no way to stop, cancel, or kill a running agent, "broken" included; if a
background call genuinely seems stuck, that has to be handled at the Claude Code session level
itself.

**Important: it only reacts to an actual subagent dispatch.** The console lights up when Claude
Code genuinely invokes its internal subagent-dispatch tool to hand work to a named subagent
(`coder`, `project-bootstrap`, and so on) — not every time Claude does something in the main
conversation. If you ask a general question or make a small edit without explicitly delegating
("use the coder agent to...", or a task clearly matching an agent's own `description`), Claude
Code may just do it inline in the main thread, with no subagent dispatch at all — and the
console has nothing to show for that, which is expected, not a bug. To see it react reliably
while testing, explicitly say "use the coder agent to..." (or similar for another agent).

**Troubleshooting — it doesn't start itself / you're seeing a different project's data.** If
nothing's running at `http://127.0.0.1:8765/` after a fresh session start: confirm you actually
launched a fresh `claude` session (the `startup` matcher doesn't fire on `/clear`/`/compact`);
confirm `Claude/hooks/agent-console.html` exists in this project (the hook silently does nothing
if it's missing); confirm `jq` (macOS/Linux) is installed, since `session-start-reminder.sh`
exits quietly without it; and if it still doesn't happen, `CLAUDE.md`'s own "Rules for this
project's agents" section carries the same deterministic-start instruction in plain prose as a
guaranteed fallback (CLAUDE.md always loads, unlike hook output in some Claude Code versions) —
just tell Claude directly "check CLAUDE.md's Agent Console rule" if even that doesn't kick in on
its own. If the console loads but shows the **wrong project's** agents/history: that means the
`/whoami` check itself didn't catch a stale server — most likely something other than a
powershell/python process is squatting on port 8765 (the kill step deliberately only touches
processes that look like our own server, to avoid killing something unrelated), or `curl`/`jq`
aren't available for the check to run at all on macOS/Linux. Manually stop whatever's on 8765 and
let the next session start bind a fresh one, or start `agent-console-server.ps1`/`.py` yourself
for this project (see below).

**Troubleshooting — Claude Code itself asks you to authorize the console before it opens.** This is
Claude Code's own permission system, not the kit or the browser: starting the server (a `Bash`
command) and/or opening the page in your browser are tool calls, and depending on your permission
settings (`.claude/settings.json`'s `permissions` block, or whatever you approved/denied earlier in
that session) Claude Code will pause and ask you to approve the specific command before running it
— same as it would for any other shell command or browser action, not something this kit adds or
can suppress from inside a hook or the console page itself. Approve it once (or use "always allow"
for that command if you're comfortable doing so, per Claude Code's own permission UI) and it won't
ask again for the same command in that session. If it asks on every single session, check whether
that command is actually allow-listed in `.claude/settings.json` the way `SETUP-INSTRUCTIONS.md`
sets it up — a hand-edited or missing `permissions` entry for the server-start command is the usual
reason it keeps re-prompting instead of running automatically.

**Troubleshooting — "Session running for" shows hours/days right after a fresh restart.** This
was a real bug, fixed in v1.44 (see the Session timer note above) — if you're still seeing it,
you're on a server build from before that fix: check `curl http://127.0.0.1:8765/whoami`, and if
the response has no `started_at` field, the running server is old. Stop it and let the next
session start bind a fresh one (or start `agent-console-server.ps1`/`.py` yourself), same as the
previous entry. If `started_at` IS present and recent but the stat on the page still looks stale,
hard-refresh the browser tab (the page polls `/whoami` every 5 seconds on its own, but a tab left
open from before this fix won't have the new polling code until it's reloaded).

**Troubleshooting — cards never light up once it's running.** (1) Confirm the server is
actually running and the page shows 🟢 LIVE, not 🔴 DISCONNECTED; (2) confirm `.claude/
settings.json` actually has the `PreToolUse` block matched on `"Task|Agent"` calling
`agent-console-log.ps1`/`.sh`, AND a `SubagentStop` block calling `agent-console-stop.ps1`/`.sh`
— a project set up before this feature existed needs that file fully replaced, not just the new
hook scripts copied in (see the update instructions for existing projects); (3) make sure you're
testing with an explicit subagent dispatch, per the note above, not general conversation; (4)
check whether `Claude/logs/agent-console.jsonl` is growing at all while a subagent runs — if
it's empty even with an explicit dispatch, the logging hook itself isn't firing or is failing
silently, uncomment the `$debugLog`/`debug_log` lines in `agent-console-log.ps1`/`.sh` (same
pattern as `after-playtest.ps1`'s own debug switch) to capture a raw payload once and confirm the
field names (`tool_name`, `hook_event_name`, `tool_input.subagent_type`) still match what your
Claude Code version actually sends — if `tool_name` turns out to be something other than
`"Task"` or `"Agent"`, add it to both the
script's check and the settings.json matcher the same way `"Agent"` was added.

**Troubleshooting — an agent that no longer exists in this kit (e.g. `verse-reviewer` after
upgrading past v1.69) shows up once and gets "auto-cleared — no stop event arrived."**
`Claude/logs/agent-console.jsonl` persists across restarts by design — it's meant to keep activity
history, not get wiped every session. If that agent was renamed/retired (like the
`verse-reviewer` → `intent-reviewer`/`compliance-reviewer` split) while a start event for it was
still logged with no matching stop event, that unresolved entry stays in the file until the
console's own 45-minute stale-cleanup surfaces and clears it — once, the next time the console
processes the full log. This is the stale-cleanup mechanism working exactly as designed on a piece
of history that predates the rename; it doesn't mean an agent file is still installed, and it
doesn't repeat once that old entry has been surfaced and cleared. (It's still worth checking
`~/.claude/agents/` for genuinely leftover files after any version upgrade — see the Phase 1 step
above — but a one-off historical entry like this isn't evidence of one.)

**Troubleshooting — an MCP log line shows garbled characters (e.g. `argumentsâ€¦` instead of
`arguments…`).** Known cosmetic issue in `agent-console-mcp.ps1`'s long-label truncation (it appends
a real `…` character to a UTF-8 log line); depending on the PowerShell version and locale writing
it, that byte sequence can get re-interpreted as Windows-1252 somewhere downstream and show up
mangled. It's harmless — the underlying event data is intact, only the truncated display label is
affected — and isn't tied to any agent/pipeline change in this kit; if it bothers you, the safe
workaround is editing that line in `agent-console-mcp.ps1` to truncate with plain `...` instead of
the `…` character.

**Troubleshooting — a card stays stuck on "WORKING" forever, "finished" attributes the wrong
agent/description, or an "unknown" node/card appears.** As of this kit's current
`agent-console-stop.ps1`/`.sh`, attribution is read directly from `SubagentStop`'s own
`agent_type` field, not guessed from queue order — a live payload capture found that
`SubagentStop` also fires for internal orchestrator events that are NOT a real subagent
finishing (an empty `agent_type`, an `agent_id` that never appeared in any start event — one
even carried the session's own scheduled-wakeup id). The older version of this script treated
every one of those as a real stop and blindly popped the oldest entry off
`Claude/logs/agent-console-active.json`, which both produced the "unknown" card and could "eat"
a real agent's stop event, leaving its own card stuck on WORKING. If you're on an older copy of
these scripts, replace them with the current ones from this kit — that's the actual fix, not a
config issue. If it's still happening on the current scripts: (1) confirm both
`agent-console-log.ps1`/`.sh` and `agent-console-stop.ps1`/`.sh` were actually updated together
(a stale server process or a half-copied update is a common cause — see the note near the top of
this section about restarting the server after any file change); (2) it's always safe to delete
`Claude/logs/agent-console-active.json` to reset the queue — it gets recreated empty on the next
subagent start and only affects attribution of in-flight invocations, not the persisted history
in `agent-console.jsonl`; (3) if it keeps happening, capture a few raw hook payloads (both
scripts' commented-out `$debugLog`/`debug_log` lines) across a run with several
overlapping/background subagents and check the real field names Claude Code is sending —
`agent_type`/`agent_id` were confirmed correct on one setup but could still change between Claude
Code versions the same way `tool_name` once did (see the `"Task"`/`"Agent"` note above). As a
safety net regardless of cause, the console auto-clears a card (stopping its comet/pulse
animation) if no matching stop arrives within 45 minutes (v1.55; was 20 before a real report
showed it firing on genuinely still-running background `coder` work), logging an "⚠ auto-cleared"
note when it does — so a stuck card self-heals even if the underlying attribution issue
resurfaces. It only actually marks the card idle if no OTHER concurrent call to the same agent id
is still within that window — otherwise a fresher, genuinely still-running sibling (see the "×N"
concurrency badge, v1.54) would get wrongly flipped to idle just because an unrelated stale entry
sharing its card finally timed out.

**Troubleshooting — token count stays at "—" or looks obviously wrong.** (1) Confirm
`.claude/settings.json` has the no-matcher `PostToolUse` block calling
`agent-console-tokens.ps1`/`.sh` — a project set up before this feature existed needs the file
fully replaced; (2) confirm `Claude/logs/agent-console-tokens.json` is being created/updated at
all after a few tool calls — if it never appears, uncomment the `$debugLog`/`debug_log` lines in
`agent-console-tokens.ps1`/`.sh` to capture a raw hook payload and confirm `transcript_path` is
actually present and points at a real file; (3) if the file appears but stays at all zeros,
uncomment the same debug line, look at a captured payload, open the `transcript_path` file it
names, and check whether an assistant message line actually has a `usage` object at
`.message.usage` or `.usage` — if it's nested somewhere else in your Claude Code version, adjust
the `$usage = ...` lookup in the script (PowerShell) or the `$u = ...` filter (bash) to match.
This whole feature is explicitly best-effort/experimental — if it turns out unreliable on your
setup, it's safe to just remove the `PostToolUse` block calling `agent-console-tokens.ps1`/`.sh`
and keep the rest of the console working exactly as before.

Entirely optional — remove the `SessionStart`/`PreToolUse`/`SubagentStop`/`PostToolUse`
"startup" blocks from `.claude/settings.json` and ignore the
`agent-console-*`/`session-start-reminder.*` files if you don't want any of it; nothing else in
the kit depends on it.

## 6. Scaling to many projects: a dashboard idea

Once you want a bird's-eye view across all your projects (instead of opening them one by one), the fact that every `Claude/docs/STATUS.md` follows the same format makes it easy to build a script that scans every project folder and reads `Claude/docs/STATUS.md` from each one, producing a single summary (a table with last update, next step, open issues). This isn't included in the kit itself, since it depends on how and where projects are laid out on disk — it's a natural next step to build once you have a few projects set up with this kit.

## Heads up: there are TWO files called `settings.json`, in two different places — they are not the same thing

A common source of confusion, so it's worth spelling out. Your machine has (or will have) two folders both named `.claude`, in different places, each with its own `settings.json` that should NEVER be merged by hand:

| | `~/.claude/settings.json` | `<project>/.claude/settings.json` |
|---|---|---|
| **Where it lives** | In your user folder (one, on the whole machine) | Inside EVERY project folder (one copy per project) |
| **Who creates it** | Claude Code itself, the first time it's installed/started | The kit — you'll find it ready in `project-template/.claude/settings.json`, to copy |
| **What it contains** | Your personal app preferences: `theme`, `autoUpdatesChannel`, etc. | THAT project's post-playtest automation hook and permissions |
| **What to do with it** | **Don't touch it.** It has nothing to do with this kit, leave it as is | Copy it (or better: copy all of `project-template/`) into every project, as is |

Claude Code reads both automatically and combines them on its own (project settings are layered on top of user settings) — you never need to paste one's content into the other.

---

### Sources
- [Unreal MCP is now available in UEFN — Fortnite.com](https://www.fortnite.com/news/unreal-mcp-is-now-available-in-uefn)
- [UEFN MCP — official Epic Games documentation](https://dev.epicgames.com/documentation/en-us/fortnite/uefn-mcp) — note: Epic's own instructions describe a per-project `.mcp.json` created in each project's root folder instead of the machine-level setup above. This kit uses the machine-level approach described in Phase 1 instead, confirmed working across multiple projects; if you hit issues with it, Epic's per-project method is the documented fallback.
- [Claude Code — Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code — Settings](https://code.claude.com/docs/en/settings)
- [Claude Code — Hooks](https://code.claude.com/docs/en/hooks)
