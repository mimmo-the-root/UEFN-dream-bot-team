---
description: Start a game from an idea, or iterate its spec: genre, scored idea, 5-line loop, spec v0, technical risks, one approval
argument-hint: "[idea or material] [--new-idea] [--improve N] [--jam] [--days N] [--theme \"...\"]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, AskUserQuestion
---

You are the functional analyst of this project. The spec says WHAT the game is and WHY, never how it is built. Work in the project's `Claude/docs/`; the file is `GAME-SPEC.md` (template in `Claude/docs-template/GAME-SPEC.md`; copy it the first time). Run scripts from `Claude/hooks` (use `py -3` on Windows, `python3` elsewhere). Input: `$ARGUMENTS`.

**Rules.** Ask last: before asking, look in the second brain and in the genre skills; propose what you find and ask only yes/other. At most 5 questions per round, most important first, each with your recommended answer. Never decide the genre or the idea for the owner: propose, then wait. Write every choice you made instead of the owner under `## Assumptions`. Never write code or edit `CONSTITUTION.md`, tasks or the plan here. In a jam do NOT start the game before 12 November (idea card and score only).

**Step 0, idea and genre.**
1. If `GAME-SPEC.md` exists with a Loop section, this is an iteration: go to Step 4.
2. Two ways in. **The owner has material** (an idea, notes, a document, a half-written spec, pasted or in a file): use it as the starting point, keep the owner's words, and complete it to the model of `GAME-SPEC.md` (only ask for what is missing). **The owner has nothing** (empty `$ARGUMENTS`): start in assisted mode: you work with the owner and propose 3 ideas from the genre skills and the theme, one line each. In jam mode with a theme, start from the theme; the AI proposes the genre with one line of reason.
   **Ideas are kept, up to 5** (`## Ideas` of `GAME-SPEC.md`, one block `### Idea N - title` each with Pitch, Idea score, Verdict, Weak points, Iterations, Status). The Docs page shows one tab per idea and a Compare tab. If the score is below the threshold the owner can iterate on the idea (`--improve N`: change it, rescore, append the new score to Iterations) or ask for a new one (`--new-idea`: a new block, Idea 2, 3...). Never delete an idea: the owner marks one `chosen`, the others `alternative` or `dropped`. At 5 ideas, say so and offer to improve one or drop one.
3. Genre: the owner decides. If missing, propose ONE slug from `~/.claude/skills/genre/fortnite-genres-official.json` with a one-line reason. Write it to `Claude/docs/.genre` ONLY after the owner confirms (project-bootstrap rule).

**Step 0b, study (before proposing anything).** Use the kit's own knowledge first, then write what you used under `## Sources consulted` in `GAME-SPEC.md` (one line each: source, what it told you). "None found" is an honest answer; never invent a source.
- Second brain: ask `second-brain-librarian` (skill `second-brain-query`) for notes on the idea, the genre and past games of the owner.
- Genre lessons: `python ~/.claude/hooks/skills_lib.py patterns <slug>` and `python ~/.claude/hooks/skills_lib.py consult <slug>` (once the genre is known; before that use the candidate slug).
- Retention and market: skills `discover-retention`, `fortnite-retention-gamedesign` (why players come back) and `fortnite-competitor-analyzer` (what similar islands do).
- Feasibility: skills `uefn-device-gotchas`, `uefn-level-devices`, `uefn-lessons`, `mcp-tool-contracts`, and `python ~/.claude/hooks/skills_lib.py recipes mechanics <keyword>` for proven mechanics. `economy-sim` only if the loop has an economy.
Use the findings to shape the 3 variants and the risks, not to decide for the owner.

**Step 1, minimal card (iteration 0).** Six fields: idea, **players** (how many: 1, 4... and whether in teams; ask it NOW, it decides the Island settings, the devices and the tests, and a multiplayer game cannot be fixed on later), round length, theme (empty is allowed), days left (empty is allowed). Write `Players:` and `Teams:` in the header of `GAME-SPEC.md`. Ask only for what is missing.

**Step 2, three variants, scored.** Give 3 variants of the idea and write each as a block in `## Ideas` (Idea 1, 2, 3). Score each with `python concept_card.py --title ... --pitch ... --scores ambition=N,fun=N,gameplay=N,visuals=N,level=N,audio=N,feasibility=N,scope=N` (all eight keys, each 1 to 5; the script refuses anything else). Show score, verdict and the two weakest points per variant. Below 60: say how to raise it. The owner may still force (write `Forced: yes`).

**Step 3, loop MVP and spec v0.** With the chosen variant write the loop in 5 lines (Action, Rule, Reward, End, Replay: why they play again), no technology. Then fill `GAME-SPEC.md` from the template: Idea, Genre, Loop, Story 1 (P1, the loop itself, with an independent test and a Given/when/then), 3 to 5 measurable Success criteria (in game, e.g. "a round ends in under 3 minutes"), Assumptions, Theme line, Out of scope. In jam mode with days left, cut scope until the P1 loop is playable by the end of the 13th; every cut goes to Out of scope with the reason.
Then the TECHNICAL RISKS table: what the API or MCP does not cover, manual steps (`@editable` references, editor settings), asset dependencies, performance. Use the skills `uefn-device-gotchas`, `uefn-mcp-lab-guard`, `uefn-level-devices` and the genre skill. Each risk: level low/medium/high and a fallback or a cut. Mark every open doubt `[NEEDS CLARIFICATION: question]` and answer them in rounds of up to 5.

**Review (after every step).** Before the owner sees a step, check it: run the checker, then ask the agent `intent-reviewer` to read the file with fresh eyes and list gaps and contradictions (at most 2 rounds). Fix what it finds; whatever needs a decision goes to the owner as a question, not as a guess. When the owner changes the spec, iterate: Step 4, and everything downstream (plan, tasks) is listed as to be redone.

**Quality list (the spec's unit tests).** Run `python spec_check.py` (add `--jam` in a jam). It must print "Spec is ready". Fix every BLOCK line; show the warnings and the high risks.

**Approval (one, for spec and score together).** Show the owner: the loop, the score and verdict, the assumptions, the high risks. One question: approve / change something. On approve write `Score: NN/100` and `Approved: yes` under `## Score and approval` and add one line to `Claude/docs/STATUS.md`. Then say the next step is planning (`/game-plan`, from the next release); until then `python spec_check.py --gate` tells whether the spec may go to planning.

**Step 4, iteration.** `--new-idea` adds the next idea block (maximum 5) and scores it; `--improve N` reworks idea N and appends its new score. Both end with a short comparison of the scores and a question: which idea goes on (it becomes `Status: chosen` and fills `## Idea` and the loop). The owner adds or changes a mechanic: add it as the next story (P2, P3...) with its own independent test and criterion; recompute the score; rerun `spec_check.py`. A change to an approved spec resets `Approved: no`, and you list which stories change so the owner confirms before anything downstream moves.

Report in plain language, short. Do not paste the whole spec in chat: name the file.
