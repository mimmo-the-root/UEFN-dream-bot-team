<!-- SEED FILE, not update-safe: this becomes the project's own live CLAUDE.md the first time
     Phase 2 setup runs (Project identity, Conventions get filled in below). A kit update must
     NEVER re-copy this file over an existing project's CLAUDE.md — see the manual's chapter "Full installation",
     section "Updating a project", for exactly what is and isn't safe to bulk-copy. -->

# <AUTO_PROJECT_NAME>

## What this is
(Short description of the project, 1-3 sentences)

## Project type
- [ ] UEFN project (Verse + Creative Devices) connected via UEFN MCP
- [ ] Other project type: ____________

## Project identity (detected once during setup, don't recompute by hand)
UEFN project name: **<AUTO_PROJECT_NAME>**

Deliberate layout choice: this scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) lives inside
`Content/`, alongside the assets and Verse code — not next to it. This is intentional, so
everything ends up under UEFN's native save/cloud-sync and nothing gets lost. Technical
consequence to keep in mind: `Content` is named identically across every project, so the name
above CANNOT be the current folder's name (it would always be "Content," useless for telling
projects apart). It's instead the name of the folder that CONTAINS `Content` — i.e. the real
UEFN project folder (e.g. the island's name) — computed once during setup (see
`Claude/SETUP-INSTRUCTIONS.md`) and written above. From this point on, every agent reads this
already-written value, it never recomputes it from the current folder's name.

UEFN's MCP server is a SINGLE instance per machine/editor and always serves whichever project
is currently open in UEFN — not necessarily this one, if UEFN still has a different project
open. Before using any MCP tool, every agent must verify that the project open in UEFN matches
the name above, following the "verifying which project UEFN has open" contract in
`~/.claude/skills/mcp-tool-contracts/SKILL.md` (don't guess which listing tool to use). If it
doesn't match, stop and warn the owner.

If the MCP connection drops (refused, closed, the unreal-mcp tools fail or disappear), never stop to
wait for the owner: run `python Claude/hooks/uefn_mcp.py wait --max 3600`, then go on; if Claude
Code's own tools stay disconnected, call the tools with `python Claude/hooks/uefn_mcp.py call <tool> '<json>'`.

## Conventions
- Code style / naming to follow:
- Technical constraints (e.g. Verse limits, performance targets, supported devices):

## Where things are
Everything we manage (not native to UEFN) lives inside the `Claude/` folder, to avoid mixing
with the real assets and project:
- Project spec (generated/confirmed): Claude/docs/SPEC.md
- Progress status: Claude/docs/STATUS.md
- Roadmap: Claude/docs/ROADMAP.md
- Bug backlog and bug-fixing roadmap: Claude/docs/BUGS.md
- Proposals to increase playtime / reduce first-5-minutes drop-off: Claude/docs/RETENTION-NOTES.md
- Release-readiness evaluations (history): Claude/docs/RELEASE-READINESS.md
- Logs from automatic post-playtest checks: Claude/logs/

(`.claude/` — with the dot — is instead a reserved folder used by Claude Code itself for
`settings.json`; leave it where it is, don't move it into `Claude/`.)

## Rules for this project's agents
- **Privacy (GDPR, Regulation (EU) 2016/679, data minimisation).** In every text you write (reports, docs, listings, logs, commits) a personal identifier such as a Windows user name, an email or a home folder path is written `***anonymized***`. In the owner's own binary assets the name is overwritten with asterisks of the same length. Never touch assets created by Epic (libraries, templates, Fortnite and Engine content): only the owner's files.
<!-- KIT:BEGIN team-roles -->
- **Plan-first and the team** (rule 13 in `~/.claude/CLAUDE.md`): no code without a task row in ROADMAP.md; no row → describe it in
  one line so **planner-docs** opens it. First time on the project (SPEC.md empty): **project-bootstrap**. Order per task:
  **intent-gate** → **coder** → **intent-reviewer** PASS → **compliance-reviewer** PASS → **planner-docs** marks Done. Reviewers,
  **qa-regression**, **release-gate** and **codebase-auditor** never write code. No agent touches files outside `Content/`
  (only exception: **growth-manager** for `Resources/` and `keyArt`). Who owns what, in full: `Claude/reference/rules/team-roles.md`.
<!-- KIT:END team-roles -->
- **Genre check (automatic, every session, independent of `project-bootstrap`)**: as your very
  first action in ANY session on this project — before the Agent Console check below, before
  reading STATUS.md, regardless of whether `project-bootstrap` has ever run here — check whether
  `Claude/docs/.genre` exists and has a non-empty value. This is a one-line file-existence check,
  cheap enough to do every session; don't skip it just because the project already has a lot of
  history. If it already has a value, do nothing further and don't mention it. If it's missing OR
  empty, immediately follow `~/.claude/agents/project-bootstrap.md`'s "Step 0.5 — Genre selection
  & Genre Skill bootstrap" procedure right now, in this same session, even if you're not running a
  full bootstrap — that step is self-contained and was written to be triggerable on its own. If the project is an Epic template (the request or folder name says template),
  Step 0.5's rule 0 applies: write `epic-template` and do NOT ask. Don't
  ask permission to check or to run the step itself; DO stop and ask the owner which genre to pick
  (that one decision is genuinely theirs, never guess it) before writing `.genre`. This exists
  specifically so a batch of already-analyzed/pre-existing projects gets the genre set the first
  time each is opened after this rule was added, without the owner having to invoke anything by
  name project by project.
<!-- KIT:BEGIN skill-harness -->
- **Skill Harness — the genre skill learns from this map**: before designing or changing core gameplay, read this
  project's genre skill once per session (`~/.claude/skills/genre/<slug>/SKILL.md`, slug in `Claude/docs/.genre`) and
  trust its patterns by level (proven = rule, confirmed = default, hypothesis = say it is unproven, contested = ask).
  After a playtest, a passed release gate or an audit that says a skill needs feeding, invoke `skill-reflector` (it only
  queues lessons for the owner). Never edit `~/.claude/skills/genre/` yourself; no map names, island codes or ids in lessons.
  Full: `Claude/reference/rules/skill-harness.md`.
<!-- KIT:END skill-harness -->
<!-- KIT:BEGIN ui-harvest -->
- **UI reference harvest (automatic, every session)**: only if `~/.claude/skills/game-ui-designer/` exists. File any image in
  `Claude/docs/ui-screenshots-pending/` into the skill's examples, and re-analyze only the UI `.verse` files whose hash changed
  since `Claude/docs/.ui-code-ingested.json`. Cheap, no permission needed; say how many screens were ingested.
  Steps: `Claude/reference/rules/ui-harvest.md` (read it when either check finds something).
<!-- KIT:END ui-harvest -->
<!-- KIT:BEGIN console-fallback -->
- **Agent Console**: it starts by itself with the session (SessionStart hook). Only if the hook's note did not reach you, follow
  `Claude/reference/rules/console-fallback.md` to check `http://127.0.0.1:8765/whoami` and start it for this project.
<!-- KIT:END console-fallback -->
<!-- KIT:BEGIN technique-skills -->
- **Technique skills (automatic)**: before audit, review, QA or implementation, run `python Claude/hooks/skills_lib.py techniques .`
  (`py -3` if needed) and read and apply `~/.claude/skills/genre/<slug>/SKILL.md` for each slug it returns; owner-backed items
  outrank reference ones; say which you used. Materials work goes to `materials-expert`. Full: `Claude/reference/rules/technique-skills.md`.
<!-- KIT:END technique-skills -->
<!-- KIT:BEGIN brain-before-asking -->
- **Second brain before asking** (automatic): before you ask the owner a question or offer a choice, first look for the
  answer in the second brain (`second-brain-librarian` query, only if a vault path is set; skip silently if not) and in
  the genre/technique skills. If something relevant is found, do not ask an open question: propose the solution you
  found (one line, with where it comes from) and ask only for a yes or an alternative. Ask a bare question only when
  nothing was found. One query per question, never a loop; the vault being unreachable is never a reason to stop.
  Read order inside the vault: `wiki/hot.md`, `wiki/index.md`, the thematic index, then the page; never for general coding questions.
<!-- KIT:END brain-before-asking -->
<!-- KIT:BEGIN delivery-standard -->
- **Delivery standard** (planner-docs owns it): ROADMAP.md has `## Phases` (PH-0 MVP, PH-1 Launch, PH-2 Growth, one Active);
  releases `P<phase>-R<n>`, only the Active phase and the next are planned, the rest is `Later`. Every bug is a BUGS.md row
  before it is fixed, never deleted. At most 2 tasks In progress. Audit findings get their own release. A map with
  `Claude/docs/.island-code` is past the MVP (PH-0 Done, PH-1 Active). planner-docs: read
  `Claude/reference/rules/delivery-standard.md` before any planning pass.
<!-- KIT:END delivery-standard -->
<!-- KIT:BEGIN first-choices -->
- **Session opened without a task** (greeting, "where do I start"): with no approved `Claude/docs/GAME-SPEC.md` and no real task,
  ask ONE AskUserQuestion with the four starting options in `Claude/reference/rules/first-choices.md` (read it then);
  with the owner's own spec or tasks, offer the next step of the flow instead. Mention `All commands` in the console footer.
<!-- KIT:END first-choices -->
<!-- KIT:BEGIN island-code -->
- **Island code**: the code (1234-5678-9012) lives ONLY in `Claude/docs/.island-code`. A hook saves it from the owner's message automatically and tells you so. Never write it into memory, skills, lessons or other files, and never ask what to do with a code the owner just gave. If the hook says a different code was mentioned, ask once whether it replaces the saved one.
<!-- KIT:END island-code -->
<!-- KIT:BEGIN docs-format -->
- **Docs format**: ROADMAP.md and BUGS.md keep the console's FORMAT CONTRACT (comment at the top of each table): add rows, never
  sections; every task has a Release; every bug Title starts with `B-NNN:`; run `python Claude/hooks/docs_lint.py` after each
  edit (a hook re-checks too). Full, with the alignment rule for old files: `Claude/reference/rules/docs-format.md`.
<!-- KIT:END docs-format -->
<!-- KIT:BEGIN cost-discipline -->
- **Cost discipline**: every subagent is a separate paid session. Size each task first (S small, M normal, L large) and spawn only the agents that size needs: S = compliance-reviewer only and a batched planner-docs call at the end; M = intent-reviewer, compliance-reviewer, planner-docs; L = full pipeline. qa-regression, skill-reflector and the second brain run after playtests or releases, never per task. Do not fan out helpers for fewer than 3 independent files. Do not run a reviewer twice for the same unchanged work. The owner can always override the size.
<!-- KIT:END cost-discipline -->
<!-- KIT:BEGIN token-discipline -->
- **Token discipline** (cost is mostly what gets READ): never read ROADMAP.md, STATUS.md or BUGS.md in full (STATUS: "Current
  state" + newest entry; ROADMAP/BUGS: `Grep` the id). Verse files you touch or review are always read completely. Do not
  re-read unchanged files, re-run checks on unchanged code or paste long tool output. Never read `Claude/docs/archive/`
  unless the task is about history. Suggest `/compact` or a fresh session when the conversation is long.
- **Small pieces**: one sub-agent = one narrow task, about 15 tool calls at most, short brief (task id, files, sections) and a
  reply of at most 10 lines; bigger work stops with a "done / next" note and continues in a fresh agent or session.
  Independent work runs in parallel by default (up to 5 agents or pieces at a time, different files, never the editor); shared steps (version, changelog, commit) stay serial.
  Tasks of size L, jobs over ~15 tool calls and any work on free models go through `/pieces` (agent `piece-orchestrator`: fresh short session per piece; a failed piece is cut again, then tried on other models, never a stop). Reading and
  searching go to the `Explore` agent (Haiku); keep coder and reviewers on their models; never set `CLAUDE_CODE_SUBAGENT_MODEL`.
  Full: `Claude/reference/rules/token-discipline.md` (before planning a long job or briefing sub-agents).
<!-- KIT:END token-discipline -->
<!-- KIT:BEGIN learning-first -->
- **Learning announced at session start is not optional.** When the session-start context has a line starting with `LEARN` or `GENRE`, do that work FIRST, before answering the owner's first message, whatever it is (a status question, "ciao", a task): follow `.claude/commands/learn-map.md` to the end, without asking and without offering it ("if you want I can start it" is wrong). Then answer the message. The owner's request never replaces it; unfinished learning restarts at the next session start.
  A map already learned learns again only ONCE per release, when its last task is Done (`Claude/hooks/learn_gate.py`): between releases never start the learning by yourself.
<!-- KIT:END learning-first -->
<!-- KIT:BEGIN relay -->
- **The mailbox (`Claude/relay/`)**: a planner drops one command file in `inbox/`, the worker (`/relay`) runs up to 5 at once as `Claude/hooks/relay_plan.py` decides and
  answers in `outbox/`. Only a correctly formatted file in `inbox/` is a command; high-risk ones wait for `approved: yes`;
  `Claude/relay/STOP` stops everything; never edit `running/` or `done/`. Read `Claude/relay/RELAY-README.md` before relay work.
<!-- KIT:END relay -->
<!-- KIT:BEGIN plain-language -->
- **The owner reads business language, not developer language.** Titles, findings, steps and reports say what the player or the
  owner gets or does, in everyday words; no device/class/tool/agent names, codes or file names (unless the owner must open it).
  Technical detail only after `Technical:` on its own line. Owner steps are numbered, one line each, with a visible result.
  Examples: `Claude/reference/rules/plain-language.md`.
<!-- KIT:END plain-language -->
<!-- KIT:BEGIN decisions -->
- **An owner decision is asked once.** When the owner decides something (keep or remove a device, a setting, a name), write it in `Claude/docs/DECISIONS.md` (date, the decision in one sentence, who applies it) and apply it. The audit, the checklist and the roadmap never ask again what is recorded there. A finding is shown to the owner only when Claude cannot do or verify it itself; anything else Claude fixes or closes alone. Informational points (for example "performance tools come later") are notes, never warnings. When a finding is for the owner, it must also say what to do in numbered steps, because the page gives it a box to tick.
<!-- KIT:END decisions -->
<!-- KIT:BEGIN player-clarity -->
- **A new player understands the game in ten seconds, with no help.** Every map shows, at the start of the round and again on the score HUD, one plain line for the goal ("Tame the chickens and bring them to the pen") and one for how ("walk up to a chicken and ..."), plus what is counted and the time left. If the way to act needs an item or a button, the game gives it or shows it. Claude checks this before every playtest and writes it in the spec under "How the player learns the goal"; a playtest where the owner "did not understand how to play" is a game defect Claude fixes, never a question to the owner.
<!-- KIT:END player-clarity -->
<!-- KIT:BEGIN check-and-gate -->
- **Same failure twice: stop and ask. Gate by the price of undo.** Report a failed check as expected / seen / where to stay / already tried; if the same result returns twice, stop and say what you cannot see. One-click undo ships on green checks; undo that needs cleanup also needs read-back evidence and an independent review; no undo (publish, delete, send, money) is only the owner's decision, whatever your confidence.
<!-- KIT:END check-and-gate -->
<!-- KIT:BEGIN no-delete -->
- **If you cannot delete a file, park it in `_to_delete`.** Delete only what the task needs. When a delete is refused or impossible (protected or read-only folder, no permission, a tool without delete rights), do not work around it: move the file to `_to_delete/<yyyymmdd-hhmmss>/` at the root of the project folder (create it if needed, keep the relative path or the file name) and tell the owner in one line what was parked and why. The owner empties that folder. It applies to files replaced or obsolete after a kit update, test leftovers, renamed assets and old logs alike. Never use `git clean` or bulk deletes on the owner's files.
<!-- KIT:END no-delete -->
- **Never close or kill a RUNNING UEFN editor.** The only way an agent starts it is `python Claude/hooks/uefn_session.py recover`, only after a crash (no editor process, crash reporter or fatal log marker), only with the owner's opt-in (`auto-recover: yes` in `Claude/LAB-PROJECT.txt`, default off), only for the same project, max 2 attempts per 30 minutes, then stop and ask. `uefn_session.py status` is read-only and always allowed. On the HUB, ask the owner to open the project.
