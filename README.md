<p align="center"><img src="docs/images/logo.jpg" alt="Dream Bot Team for UEFN: AI agents for Fortnite maps" width="640"></p>

# UEFN Dream Bot Team: AI agents and MCP tools for Fortnite maps

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE) [![Latest release](https://img.shields.io/github/v/release/mimmo-the-root/UEFN-dream-bot-team?style=flat-square)](https://github.com/mimmo-the-root/UEFN-dream-bot-team/releases) [![Tests](https://img.shields.io/github/actions/workflow/status/mimmo-the-root/UEFN-dream-bot-team/tests.yml?branch=main&label=tests&style=flat-square)](https://github.com/mimmo-the-root/UEFN-dream-bot-team/actions/workflows/tests.yml) [![GitHub stars](https://img.shields.io/github/stars/mimmo-the-root/UEFN-dream-bot-team?style=flat-square)](https://github.com/mimmo-the-root/UEFN-dream-bot-team/stargazers)
![UEFN: Unreal Editor for Fortnite](https://img.shields.io/badge/UEFN-Unreal_Editor_for_Fortnite-blueviolet?style=flat-square&logo=fortnite&logoColor=white) ![Verse code](https://img.shields.io/badge/Verse-code-informational?style=flat-square) ![format: Agent Skills](https://img.shields.io/badge/format-Agent_Skills-0A7BBF?style=flat-square) ![last commit](https://img.shields.io/github/last-commit/mimmo-the-root/UEFN-dream-bot-team?style=flat-square) ![Claude Code kit](https://img.shields.io/badge/Claude_Code-kit-orange?style=flat-square) ![Fortnite maps](https://img.shields.io/badge/Fortnite-maps-blue?style=flat-square) [![Sitemap](https://img.shields.io/badge/sitemap-xml-lightgrey?style=flat-square)](https://mimmo-the-root.github.io/UEFN-dream-bot-team/sitemap.xml) [![Downloads](https://img.shields.io/github/downloads/mimmo-the-root/UEFN-dream-bot-team/total?style=flat-square&label=kit%20downloads&color=success)](https://github.com/mimmo-the-root/UEFN-dream-bot-team/releases)
![UEFN MCP tools mapped](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmimmo-the-root%2FUEFN-dream-bot-team%2Fmain%2Fdocs%2Fkit-stats.json&query=%24.mcp_tools&label=UEFN%20MCP%20tools%20mapped&color=informational&style=flat-square) ![proven UEFN MCP recipes](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmimmo-the-root%2FUEFN-dream-bot-team%2Fmain%2Fdocs%2Fkit-stats.json&query=%24.recipes_proven&label=proven%20MCP%20recipes&color=success&style=flat-square) ![AI agents](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmimmo-the-root%2FUEFN-dream-bot-team%2Fmain%2Fdocs%2Fkit-stats.json&query=%24.agents&label=AI%20agents&color=success&style=flat-square) ![skills](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmimmo-the-root%2FUEFN-dream-bot-team%2Fmain%2Fdocs%2Fkit-stats.json&query=%24.skills&label=skills&color=informational&style=flat-square) ![lessons](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmimmo-the-root%2FUEFN-dream-bot-team%2Fmain%2Fdocs%2Fkit-stats.json&query=%24.lessons&label=genre%20lessons&color=success&style=flat-square)


**Dream Bot Team** is a free, open-source Claude Code kit that builds, tests and improves **UEFN** (Unreal Editor for Fortnite) maps with a team of AI agents. You describe the game; the team plans it, builds it through the **UEFN MCP**, writes the **Verse** code, checks its own work with two independent reviewers, and stops to ask you whenever a step is yours. Nothing is deleted behind your back and nothing is published until you say so.

**[The idea behind it](docs/PHILOSOPHY.md)** (five minutes) | **[The story](docs/MANIFESTO.md)** | **[The manual](https://mimmo-the-root.github.io/UEFN-dream-bot-team/)**

v1.114 is the **first milestone**, not the end: the whole loop from an idea to a playable MVP, and a base to keep improving. We are not stopping here.

## What you get

- **Twenty-two agents, one job each** (seventeen team agents and five UEFN MCP sub-agents). The one that writes the code never reviews it.
- **A plan-first loop.** Idea, spec, plan, tasks, environment, build, audit, delivery. A task is done only when two independent reviewers agree, and a step that belongs to you is shown as "your turn", never as green.
- **The whole UEFN MCP mapped.** 388 tools, with arguments, prerequisites, cleanup and known traps; 387 recipes proven on a live editor.
- **An Agent Console.** A local dashboard: who is working, where the game stands, what needs you, what it cost, and a Score page that compares the game with its own plan.
- **It learns from your maps** and keeps your data on your computer. Sharing lessons is optional and private by default.
- **A Fab mode** for products you sell: the kit checks the package against Epic's rules and writes the listing and the user manual, and installs nothing in the product.
- **Free, MIT licensed**, for one island or fifty.

## What is proven, and what is not

We separate what ran on a real editor from what was only checked offline. Every release repeats this table.

| Part | Status |
|---|---|
| UEFN MCP recipes (387) | Proven on a live editor, each one run and read back |
| Chicken Roundup pilot map (built through the MCP, Verse compiles, references read back) | Built and read back from a real editor; a full round with players is being validated and this line changes when it has been played |
| Console pages, design rules, kit tests (80 steps) | Checked offline by tests and `ui_lint.py`; `tool/shoot_consoles.py` opens every page in a real browser |
| Fab checks, economy simulator, jam checks, static Verse check | Checked offline on sample projects |

## When you do NOT need this kit

- You are changing one device or one line of Verse. Ask Claude Code directly; the kit's plan, review and documents are overhead for a ten-minute fix.
- You already write Verse comfortably and one assistant is enough. The kit pays off when you juggle many maps or want an audit trail.
- Your project is not UEFN. The recipes, the MCP map and the agents are all about Unreal Editor for Fortnite.
- You do not use Claude Code, or you want no extra files in your project. A map project gets a `Claude/` folder and project rules (a Fab product gets none).
- You want the cheapest possible token use. Two reviewers and living documents cost tokens on purpose.

## From an idea to a playable game

| Step | You type | Claude writes | You decide |
|---|---|---|---|
| Idea, genre, spec | `/spec "your idea"` | `GAME-SPEC.md` (loop in 5 lines, stories, success criteria, risks, sources) | the genre, one approval |
| Principles and plan | `/game-plan` | `CONSTITUTION.md`, `PLAN.md` | one approval |
| Tasks | `/task-list` | the Tasks table in `ROADMAP.md` | nothing |
| Check | `/consistency` | a read-only report | what to fix first |
| Environment and playtest | `/environment`, `/environment --playtest` | the environment readout, `PLAYTEST.md` | the steps only you can do |
| Audit | `/audit` | `AUDIT.md`: small bugs fixed, serious ones listed | what to do with each serious one |
| Delivery | `/delivery` | `DELIVERY-GATE.md` | tick each box yourself, make the private release |

### Try the pilot demo

The kit ships Chicken Roundup: spec, plan, tasks and a playtest checklist. **Do not use your real map.** Make a new empty UEFN project, open Claude Code in its `Content` folder, run `/kit-update`, then `/demo` (with you) or `/demo --auto` (the AI approves every step). A stopwatch on the Docs page times the run. If it stops on red, do only what it says and continue.

## The Agent Console

One design system for every page: colour means status (green done, amber your turn, red blocked, cyan running, grey not started), only cheap motion, readable contrast, plain words. See [console design](docs/console/DESIGN.md) and [console product](docs/console/PRODUCT.md).

**Console**, the team at work (demo data):

![Agent Console](docs/images/agent-console.png)

**Docs**, from idea to delivery, with the next action and what is your turn:

![Docs page, Plan tab](docs/images/agent-console-docs-plan.png)

**Skills**, what waits for you and what the kit has learned:

![Skills page](docs/images/agent-console-skills.png)

**Flow**, the pipeline as a board, with tokens per agent:

![Flow page](docs/images/agent-console-flow-of-flows.png)

Also: **Stats** (time and tokens), **Score** (the game against its plan, criterion by criterion), **News** (what changed in the kit) and **Fab** (is the product package ready).

## What's new (v1.108 - v1.114.0)

- **v1.114, study and design.** `/spec` and `/game-plan` start from the kit's knowledge and write their sources; `/environment` lists what only you can do; one design system for all console pages (`console-ui` skill and `ui_lint.py`), lighter pulses, aligned numbers, no side stripes; the idea and philosophy in words and pictures.
- **v1.113, from spec to tasks.** `/game-plan`, `/task-list`, `/consistency`.
- **v1.112, start from an idea.** `/spec` with genre, three variants and measurable criteria.
- **v1.111, one workflow for everything you share.** Lessons, recipes, skills and MCP proof share states and buttons.
- **v1.110, Skills page by tabs, LEARN, Fab Checklist.**
- **v1.109, Fab products, economy simulator, safe editing** (editor lock, undo plan, static Verse check).
- **v1.108, ready for the jam and Score page**; the kit updates itself from GitHub.

Every version is in [CHANGELOG.md](CHANGELOG.md).

## Getting started

Read **[the manual](https://mimmo-the-root.github.io/UEFN-dream-bot-team/)**: a 15-minute quick start, the full setup (once per machine, then once per project), the team, the console page by page, and troubleshooting. The same manual runs inside the kit at `http://127.0.0.1:8765/manual/` while the console server is up. Setup has a few manual steps on purpose, so you see what is installed.

## Repo layout

```
project-template/       Files copied into each map project's Content/ folder (hooks, document
                         templates, the Agent Console, the project rules)
user-level-agents/       The 22 agent definitions, installed once into ~/.claude/agents/
user-level-memory/       Base rules loaded in every session
user-level-skills/       Shared skills, installed once into ~/.claude/skills/
second-brain-template/   Optional Obsidian vault for reusable mechanics
docs/                    The manual, the console design, the philosophy and manifesto, decisions
CHANGELOG.md             Version history
```

## Contributing

Issues and pull requests are welcome, see [`CONTRIBUTING.md`](CONTRIBUTING.md). If you hit a bug in the kit itself, open an issue with the agent or hook involved and what you expected versus what happened. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md); report security problems privately as described in [`SECURITY.md`](.github/SECURITY.md). Design ideas for the Skills mechanics are adapted from [tigerless-labs/autoharness](https://github.com/tigerless-labs/autoharness) (MIT, see `THIRD-PARTY-NOTICES.md`).

## License

MIT, see [`LICENSE`](LICENSE). Use it, fork it, ship it in your own team's setup.
