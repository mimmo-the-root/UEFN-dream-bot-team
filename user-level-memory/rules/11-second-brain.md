<!-- Full text of base rule 11. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 11. Second brain (Obsidian) integration — optional

**Second brain path**: `<SECOND_BRAIN_PATH>` (replace it with the absolute path of your Obsidian
vault root — the folder containing `raw/`, `wiki/`, `output/`, and its own `CLAUDE.md`, see
`second-brain-template/` in this kit. While it stays the literal placeholder, this feature is off.)

`uefn-lessons` (rule 10 above) captures short, one-line tooling/syntax gotchas. This is a
different, complementary layer: a full Obsidian wiki of **game mechanics and Verse device
implementations**, kept current per device/mechanic so a pattern that already works on one
island can be reused by copying its up-to-date snippet, instead of rebuilt from scratch — see
`second-brain-template/CLAUDE.md` (or the copy already installed in your vault) for the full
article format and the update-in-place rule for device/mechanic articles.

A dedicated agent, `second-brain-librarian`, owns all reads/writes to this vault — it's the only
agent in this kit whose job is outside the current project's folder. Neither `coder` nor
`project-bootstrap` write to the vault directly; they hand off to it instead.

How a session reads it, and the hooks that check it, are in rule 15.

If `<SECOND_BRAIN_PATH>` is still the unfilled placeholder, skip this rule entirely — don't
invoke `second-brain-librarian`, don't mention it every session, it's simply off. If it's set:

- **When `coder` hands off**: after implementing or meaningfully changing a device or Verse
  pattern that's reusable beyond this one project (same bar as `uefn-lessons`: "would this help
  on a different island?" — but for a working implementation, not a one-line gotcha) — not for
  every small change, only ones worth having a snippet for. It invokes `second-brain-librarian`
  with a short brief (device/mechanic, what it does, what changed, this project's name, today's
  date) rather than writing to the vault itself.
- **When `project-bootstrap` hands off**: as a closing step after its initial analysis (its A6
  step — see `project-bootstrap.md`), for generalizable mechanics/devices it identified while
  mapping an existing project. Same handoff, not a direct write.
- **What `second-brain-librarian` does with a handoff**: reads `<SECOND_BRAIN_PATH>/CLAUDE.md`
  for that vault's actual current conventions (frontmatter fields, folder naming, the
  update-in-place rule for device/mechanic articles) rather than assuming any summary elsewhere
  is exhaustive — the owner may have adjusted their own vault's rules over time, and the vault's
  own `CLAUDE.md` is the authority. In short: finds or creates the matching wiki (e.g.
  `wiki/device/`, `wiki/meccaniche/`) and article, updates its `## Implementazione Verse (ultima
  versione)` section in place (bumps version/date, doesn't append a second snippet), cites the
  source as `conversazione: <date>, progetto <name>`, updates that wiki's `indice_wiki.md` (and
  `wiki/indice.md` if a new wiki was created).
- **This agent is also the one to invoke directly** for the vault's own `compile` (ingest
  `raw/` material), query, and `audit`/`lint` workflows — when the owner is working inside the
  vault itself rather than a UEFN project, or wants those run from within a project session.
- **The second brain isn't write-only.** `coder` also queries it (via `second-brain-librarian`)
  before implementing a common device/mechanic pattern from scratch, to check whether a
  ready, current Verse implementation already exists to adapt instead — see `coder.md` step 5.
  `project-bootstrap` queries it during its A4 retention step, to prefer proposals with a
  track record on other projects over purely theoretical ones — see `project-bootstrap.md`'s A4.
  Neither is required to query every time; it's a time-saver when the pattern is common enough
  to plausibly already be catalogued, not a mandatory step for every task.
- **Ask last.** Before asking the owner a question or offering a choice, query the second brain (and the
  genre/technique skills) first; if something relevant exists, propose that solution and ask only for a yes or an
  alternative. Ask a bare question only when nothing was found.
- **Never block on this.** If the vault path is unreachable (wrong path, drive not mounted,
  Obsidian vault moved), `second-brain-librarian` reports that and stops — `coder` and
  `project-bootstrap` treat a handoff exactly like a missing/misconfigured `uefn-lessons` file:
  note it once and move on, this is a nice-to-have layer on top of the actual UEFN work, never a
  reason to stop or fail a task.
- **Never write to `raw/` or `output/` in the vault** (beyond the `_COMPILED` rename `compile`
  itself does): those are the owner's own inbox and scratch space per that vault's `CLAUDE.md` —
  only `wiki/` (plus its indexes) is this integration's target.
