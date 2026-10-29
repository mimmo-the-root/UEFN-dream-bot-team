---
tags: [kit, manual]
created: kit-1.115.0
updated: kit-1.115.0
sources: [docs/manual/install.md]
type: kit
status: current
---
# Full installation

The [[quick-start|quick start]] is the short path. This chapter adds everything it leaves out: the Unreal Engine skills plugin, upgrading an old install, the optional extras, what the first session does, and how to update a project without losing anything.

## Two phases, two folders

Mixing the phases up is the most common source of confusion, so keep this table in mind.

| | Phase 1: environment | Phase 2: project |
|---|---|---|
| How often | Once per computer | Once per UEFN project |
| You start `claude` from | The UEFN **installation** folder (on Windows usually `C:\Program Files\Epic Games\Fortnite`) | The project's own `Content/` folder |
| What it does | Gets the MCP server running and registers it with Claude | Installs the project scaffold and connects it to that project |

## Phase 1 in detail

The steps of the [[quick-start|quick start]] (the `.mcp.json` file, *Auto Start Server*, copying agents and skills, registering the server) are Phase 1. These are the parts it does not repeat.

### Check that the server listens

The default port is 8000. On Windows run `netstat -ano | findstr :8000`; on macOS or Linux run `lsof -i :8000`. A line that names the port as listening means it worked. No output at all means it did not: check that `.mcp.json` is in the right folder, that UEFN was restarted **after** the file was created, and that *Auto Start Server* is really on.

### Upgrading from an older kit: delete the retired agents

Copying `user-level-agents/` into `~/.claude/agents/` only adds or replaces files. An agent the kit has since renamed or retired stays on disk and can still be called by habit. In the console it shows up as an agent that is not in the roster. Before you copy a new version, compare the file list with what is in `~/.claude/agents/` and delete everything that is not one of the 17 agents listed in [[your-team|Your team]].

### Install Anthropic's Unreal Engine skills plugin

It is a separate plugin, maintained by Anthropic, and it complements this kit. It needs Git on your computer ([Git for Windows](https://gitforwindows.org/) on Windows).

> **Warning** If Claude Code was already running in PowerShell when you installed Git, that window does not see the new `git` command. Close the window and open a new one before you continue, or the plugin install fails with "Git is missing".

Then run this inside Claude Code:

```
/plugin install unreal-engine-skills-for-claude-code@claude-plugins-official
```

### Optional: a second brain in Obsidian

A separate wiki, outside any project, kept by the `second-brain-librarian` agent. Reusable mechanics, lessons and the kit's own knowledge are written there once and found again in every project. It is off until you give it a folder: skip this step and the kit works, but each map starts from zero. [[how-the-kit-thinks|How the kit thinks]] explains what it holds and how the helpers use it.

1. Create a vault anywhere on your computer (not inside a UEFN project) with the `raw/`, `wiki/` and `output/` folders, and copy `second-brain-template/CLAUDE.md` to the vault's root.
2. Check the file name from a terminal (`dir CLAUDE*` on Windows, `ls CLAUDE*` elsewhere). It must be exactly `CLAUDE.md`.
3. Copy `second-brain-template/wiki/kit/` into the vault's `wiki/` folder and add a line for it to `wiki/index.md`. It holds the kit manual as wiki pages, so the helpers can answer "how does the kit do this?" from the second brain.
4. Open `~/.claude/CLAUDE.md` and set the vault's full path as the "Second brain path" in rule 11. From the next session a hook prints `wiki/hot.md` and the number of raw sources still to ingest, and another runs the free checks (broken links, quotes not found in `raw/`) after each page the librarian writes.

> **Warning** File Explorer hides known extensions, so a file can be saved as `CLAUDE.MD.md` and look identical to the right name. Only the terminal tells you the truth.

### Optional: shorter replies

The third-party `caveman` plugin makes Claude's replies much shorter and saves output tokens. It is not part of the kit and not required. The kit's own cost rules (cheap models, small/medium/large task sizing, history trimming) already do most of the saving.

## Phase 2 in detail

Before the first session, in UEFN, open **Project Settings** for this project and enable *Python Editor Scripting* and *UEFN MCP Toolsets*. This is per project and cannot be skipped.

Copy the **contents** of `project-template/` into the project's `Content/` folder, open a terminal there, start `claude` and say: *Read Claude/SETUP-INSTRUCTIONS.md and set up this project.* The agent then:

1. reads the real project name from the folder above `Content/` and writes it into `CLAUDE.md`;
2. checks that the MCP connection really answers from this folder;
3. asks you what the project is, its type and any conventions;
4. lists the available MCP tools and sets up the post-playtest hook;
5. checks that the project open in UEFN is the right one;
6. only then runs `project-bootstrap` for the first analysis.

You can leave `SETUP-INSTRUCTIONS.md` in place afterwards; it does no harm.

> **Note** The MCP server always serves the project that is **open in UEFN**, not the folder where you started Claude. Open the project in UEFN first, then start the session. Every agent that uses the server checks this before it touches anything.

## Updating a project

> **Note** If you installed the kit **before v1.108.3**, update it by hand once: run `/kit-update --fetch` in a session (or `update-my-profile.cmd` from the repo folder), then open a new session. Older kits never look at GitHub, so they cannot find the new version alone. From v1.108.3 on, a background check at session start (at most every 6 hours) downloads new releases by itself, and every project follows at its next session. To switch it off, create an empty file `~/.claude/kit-auto-update.off`.

The easy way is described in [[troubleshooting|Troubleshooting]]: with `~/.claude/kit-template/` in place, each session updates the kit files of the project you open. If you prefer to do it by hand, this is the rule.

**Safe to overwrite at any time:** `Claude/hooks/` (the console, its server and every hook), `Claude/reference/`, `Claude/community/`, `Claude/SETUP-INSTRUCTIONS.md`, and `.claude/settings.json` (diff it first if you edited a hook matcher).

**Never copy over:** `Claude/docs/` (SPEC, STATUS, ROADMAP, BUGS: the project's whole history), your `CLAUDE.md`, and `Claude/logs/`. They are the project's own data. The agents' per-project memory lives outside the folder entirely and is not touched either way.

After an update, hard-refresh the console tab. The old page may still be in the browser.

## A project on a second computer

Registration of the MCP server is stored per computer, so a project you set up on computer A shows no MCP tools the first time you open it on computer B. That does not mean it needs a new setup. Do Phase 1 on computer B once; the agents register the server themselves when they notice it is missing.

## Two files called settings.json

Your computer has two folders named `.claude`, each with its own `settings.json`, and they are never merged by hand.

| | `~/.claude/settings.json` | `<project>/.claude/settings.json` |
|---|---|---|
| Where | In your user folder, one per computer | In every project, one per project |
| Created by | Claude Code itself | The kit, copied from `project-template/` |
| Contains | Your personal preferences (theme, update channel) | That project's post-playtest hook and permissions |
| What to do | Do not touch it | Copy it with the rest of `project-template/` |

Claude Code reads both and layers the project's on top of yours.

## Related articles
- [[quick-start|Quick start]]
- [[your-team|Your team]]
- [[how-the-kit-thinks|How the kit thinks]]
- [[troubleshooting|Troubleshooting]]

## Sources
- The kit manual, chapter "Full installation" (docs/manual/install.md), kit v1.115.0. Rebuilt on every kit release: do not edit this page, edit the manual.
