# Second brain template (Obsidian)

Optional. This is a separate knowledge base, meant to live in its own Obsidian vault — not
inside any single UEFN project — that accumulates game mechanics and Verse device
implementations across every project set up with this kit, so a pattern that already works on
one island can be reused by copying an up-to-date snippet instead of rebuilding it from scratch.

It's a different thing from `user-level-skills/uefn-lessons/`: that one is short, one-line
Verse/UEFN/MCP tooling gotchas read by every Claude Code session automatically. This one is a
full Obsidian wiki — structured articles, cross-links, kept current per device/mechanic — that
you browse yourself in Obsidian, and that the kit's agents read and write to when configured.

## Set up the vault (once)

1. Create (or reuse) an Obsidian vault folder anywhere on your machine — it does NOT need to be
   inside any UEFN project.
2. Inside it, create exactly these three folders and nothing else yet: `raw/`, `wiki/`,
   `output/`. Create `wiki/indice.md` too, titled "Indice delle wiki" with a one-line note:
   "Elenco delle wiki nell'ordine in cui sono state create."
3. Copy `CLAUDE.md` from this folder into the vault's root.
   - **Windows gotcha, verified on a real setup**: if File Explorer has file extensions hidden
     (the default), renaming or saving this file through Explorer can silently produce
     `CLAUDE.MD.md` instead of `CLAUDE.md` — Explorer hides the trailing `.md` because it's a
     "known" extension, so the double extension looks identical to the correct name in the file
     list and is easy to miss. Before moving on, verify the REAL filename from a terminal, not
     Explorer: open a terminal in the vault folder and run `dir CLAUDE*` (Windows) or `ls
     CLAUDE*` (macOS/Linux) — it must show exactly `CLAUDE.md`, nothing else. If it shows
     `CLAUDE.MD.md` (or any other variant), rename it: `ren "CLAUDE.MD.md" "CLAUDE.md"` on
     Windows. This same terminal-over-Explorer check is worth doing for `raw/`, `wiki/`,
     `output/` too if anything looks off later — Explorer's view can be stale or misleading in
     ways a directory listing isn't.
4. Note the vault's full absolute path — you'll need it for the kit-side setup step below (see
   the main `SETUP-GUIDE.md`, Phase 1). This kit's own default vault lives at
   `C:\SecondBrainOssidian`; if you're reusing this kit yourself, point it at your own vault's
   path instead.
5. **Optional but recommended**: install the community `obsidian-skills` Claude Code plugin
   marketplace (by kepano, an Obsidian team member) — a set of skills that teach Claude Code
   better conventions for working inside an Obsidian vault (formatting, linking, front matter,
   and similar Obsidian-specific habits), on top of whatever `second-brain-librarian` already
   does. Run once, from any terminal:
   ```
   /plugin marketplace add kepano/obsidian-skills
   /plugin install obsidian@obsidian-skills
   ```
   This is independent of this kit — it's a general-purpose Obsidian plugin, not something this
   kit ships or maintains — but it's a good pairing if you spend meaningful time in the vault
   yourself (browsing, editing, asking Claude Code questions from inside it) rather than only
   through `second-brain-librarian`'s own handoffs.

## How it connects to the kit

Once you set `Second brain path` in `~/.claude/CLAUDE.md` (Phase 1 of the main setup guide), a
dedicated sixth agent from the kit, `second-brain-librarian`, owns this vault. `coder` and
`project-bootstrap` don't write here themselves — when they learn a reusable game mechanic or
device pattern during normal UEFN project work, they hand off to `second-brain-librarian` with a
short brief, and it updates `wiki/` following this file's conventions — see `~/.claude/CLAUDE.md`
rule 11 for exactly when and how.

You don't need to run this vault's own `compile` command for that handoff to happen. `compile`
is for when YOU drop raw material (PDFs, articles, notes) into `raw/` yourself — ask a Claude
Code session (inside this vault, or inside a UEFN project) to invoke `second-brain-librarian`
with the `compile` command, and it'll process `raw/` per this file's own workflow. The same
agent also answers queries against the KB and runs `audit`/`lint` when asked.

It also actively looks for connections between articles you didn't ask it to find — during
`compile`, a query, or `audit` — and keeps a running `wiki/meta/frontiere-conoscenza.md` of open
questions and promising-but-unformalized patterns. For a deliberate, whole-KB synthesis pass
(new higher-order articles combining existing ones), ask it to `evolve` or `sintetizza [topic]`
— it drafts proposals for your review rather than applying anything on its own. See the vault's
own `CLAUDE.md`, "Emergent synthesis and evolution," for the full mechanics.

## Automate the weekly UEFN release-notes sync (optional)

`second-brain-librarian` can also keep a running record of official UEFN release notes in
`wiki/note-di-rilascio-uefn/` — one article per release, backfilling everything the first time
it runs, then adding only newly published entries on every later run (it diffs against what's
already indexed, never re-creates or duplicates an entry). See its "UEFN release-notes sync"
workflow (mode 3) in `second-brain-librarian.md` for exactly how.

To run it once by hand, ask any Claude Code session with this kit installed: *"use
second-brain-librarian to sync UEFN release notes into the second brain."* The first run does
the full backfill; every run after that only adds what's new.

To run it automatically every Thursday, use `weekly-release-notes-sync.ps1` (Windows) or
`weekly-release-notes-sync.sh` (macOS/Linux) from this folder, wired into your OS's own
scheduler — Claude Code itself has no built-in weekly scheduler, so this is standard OS
automation, the same way the kit's own post-playtest hook is just a script Claude Code's hook
system calls. Two gotchas found on a real Windows run and already fixed in the script — worth
knowing if you ever edit it: `claude -p` (non-interactive/print mode) can't prompt for
permission, so it refuses to read/write outside its working directory unless that directory is
explicitly `cd`'d into and/or passed via `--add-dir`; and a prompt with embedded double quotes
gets silently truncated right at the first one when PowerShell hands it to an external `.exe` —
keep prompts passed this way free of nested double quotes.

**Test the script by hand before scheduling it** — run it once directly and confirm it reports a
sync result with no permission errors:
```
powershell -ExecutionPolicy Bypass -File C:\SecondBrainOssidian\weekly-release-notes-sync.ps1
```
Only wire it into Task Scheduler/cron once this works standalone.

**Windows (Task Scheduler, via `schtasks`)** — run once, from a terminal, adjusting the path if
your vault isn't at `C:\SecondBrainOssidian`:
```
schtasks /create /tn "SecondBrain-UEFN-ReleaseNotes" /sc weekly /d THU /st 09:00 ^
  /tr "powershell.exe -ExecutionPolicy Bypass -File C:\SecondBrainOssidian\weekly-release-notes-sync.ps1"
```
Verify it's registered: `schtasks /query /tn "SecondBrain-UEFN-ReleaseNotes"`. Remove it later
with `schtasks /delete /tn "SecondBrain-UEFN-ReleaseNotes" /f`.

**macOS/Linux (cron)** — `crontab -e`, then add (adjust the path to your vault):
```
0 9 * * 4 /bin/bash /path/to/your/vault/weekly-release-notes-sync.sh >> /tmp/second-brain-sync.log 2>&1
```
(`4` = Thursday in cron's day-of-week field.)

Either way, this only runs the release-notes sync — it does NOT run `compile` on your `raw/`
folder or touch anything else in the vault, and it never runs unattended UEFN project work.
