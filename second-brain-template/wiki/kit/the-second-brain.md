---
tags: [kit, manual]
created: kit-1.114.0
updated: kit-1.114.0
sources: [docs/manual/the-second-brain.md]
type: kit
status: current
---
# The second brain

One folder of plain text files that every project reads and the helpers keep up to date. The next session starts where the last one stopped.

Every new chat starts blank. Plans, decisions and what worked last week are gone unless they live somewhere the helpers can read. The second brain is that place. It sits **outside any project**, so what one map teaches, the next map starts from. It is off until you give it a folder, and the kit works without it. With it, each map starts from what the kit already knows.

## What it holds

| Part | What is in it | Who writes it |
| --- | --- | --- |
| `raw/` | Sources: a project's spec and bugs, a Verse snippet, notes. Read, never edited | You, or a finished project |
| `wiki/` | Pages that link to each other: one page per mechanic, device, lesson, or chapter of the kit | One helper, the librarian (`second-brain-librarian`) |
| `wiki/hot.md` | A dozen lines: what you are working on, what changed last, what is open | The librarian, after every compile |
| `wiki/kit/` | This manual, written as wiki pages, so the kit can answer "how does the kit do this?" | Built by the kit on every release |
| `output/` | Answers and drafts that can be thrown away | Any helper |
| `CLAUDE.md` | The rules of the vault: page format, the update-in-place rule, the workflows | You, once (the kit gives you the template) |

The first things it holds are **mechanics** that worked (a pickup, a round timer, a score panel in Verse), what did **not** work (kept as counter-evidence), the **lessons** of every map, and the **kit's own knowledge**. A mechanic has one page, not one page per project: when something better is built, the old version moves to a dated history and a different but valid approach stays as a variant.

## Turn it on

Five steps, once. They are also in [[install|Install]].

1. Create a folder anywhere outside your UEFN projects, for example `C:\UEFN_Progetti\second-brain`, with `raw`, `wiki` and `output` inside.
2. Copy `second-brain-template/CLAUDE.md` of the kit to the root of that folder. Check the real file name in a terminal (`dir CLAUDE*`): it must be exactly `CLAUDE.md`.
3. Copy `second-brain-template/wiki/kit/` into the vault's `wiki/` folder, and create `wiki/index.md` with a line for it.
4. Run `update-my-profile.cmd` of the kit, then put the vault's full path in rule 11 ("Second brain path") of `~/.claude/CLAUDE.md`. The update also adds rule 15, the short rule that tells every session how to use it.
5. Restart your Claude session, then run `/kit-doctor`. It says whether the vault is found and what is still missing (usually only `wiki/hot.md`, which the librarian writes after its first compile).

> **Tip** You can ask Cod to do all of it: the relay command "turn the second brain on" does the five steps and proves each one with real output.

## What happens in a session

- **At the start**, a hook prints `wiki/hot.md`, the read order and how many raw sources wait to be ingested. It costs no AI tokens.
- **Before asking you a question**, a helper looks for the answer in the vault (and in the genre lessons). If it finds one, it proposes it and asks only for a yes.
- **The read order is always** `hot.md`, then `wiki/index.md`, then the index of the topic, then the page. A helper never reads the vault for a general coding question, which keeps it cheap.
- **When a helper builds something reusable**, it hands it to the librarian with a short brief. The librarian updates the one page for that mechanic and rewrites `hot.md`.
- **After every page written under `wiki/`**, a hook runs the free checks below. If a link is broken or a quote is not in its source, the problem comes back in the same turn and the page is fixed before the work moves on.

## The free checks

They are plain scripts (`vault_check.py` in the `second-brain-query` skill). No AI is involved, so they cost nothing and cannot be talked into agreeing with a mistake.

| Command | What it tells you |
| --- | --- |
| `status` | Which raw files are new, changed or deleted since the last ingest (by content, not by date), and which pages went stale. Example: `status: 2 pending (1 new, 1 changed, 0 deleted)` |
| `done raw/<file> wiki/<page>...` | Records that a source was ingested into those pages |
| `quotes` | Every quoted claim `> "exact text" - raw/<file>` must exist word for word in that raw file. Example: `quotes: 3 checked, 0 problem(s)` |
| `links` | Broken links between pages. Example: `links: 22 article file(s), 0 broken link(s)` |
| `stats`, `dups`, `names` | Missing fields or sections, possible duplicate pages, folder names (English and Italian vaults both work) |
| `hot` | Prints `wiki/hot.md` |

## Keeping it honest

The helper that writes a page must not be the only one that checks it: a model that reviews its own work tends to agree with itself. That is why the checks are scripts. A hard claim carries a quote line, and the script proves the quote is in the source. A source that was edited after it was ingested is flagged, with the pages that depend on it.

The checks prove that a page copies its source, not that the source is right. A wrong source makes a faithfully wrong page. So when sources disagree, the librarian writes both under *Counter-evidence* instead of smoothing it over, and the `audit` command looks for contradictions, orphans and stale pages when you ask.

## Where it is weak

- **It is empty at first.** With fewer than about fifty pages it behaves like a good search. It pays back over many maps.
- **Pages go stale.** Run the audit now and then. A wiki that only grows ends up contradicting itself.
- **It is only as good as what you feed it.** Keep private files, island codes and keys out of `raw/`. What the helpers read is sent to the model.
- **It is yours.** Plain files: open them in Obsidian, edit them, move them. Nothing is locked in.

## If something does not work

| You see | What it means |
| --- | --- |
| `/kit-doctor`: "second brain: off (placeholder)" | Rule 11 still has `<SECOND_BRAIN_PATH>`. Set the path (step 4) |
| "not a valid vault" | The folder needs `CLAUDE.md` and `wiki/` at its root |
| "the kit's own knowledge is not in the vault yet" | Copy `wiki/kit/` (step 3) |
| Nothing is printed at the start of a session | The project has no `brain_brief.py` hook yet: run `/kit-update` and restart the session |
| A page keeps failing `quotes` | The quote is not in the raw file word for word: copy it exactly, or remove the quote line |

## Related articles
- [[install|Full installation]]

## Sources
- The kit manual, chapter "The second brain" (docs/manual/the-second-brain.md), kit v1.114.0. Rebuilt on every kit release: do not edit this page, edit the manual.
