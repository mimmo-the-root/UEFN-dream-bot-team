<!-- KIT:BEGIN second-brain-session -->
## 15. Second brain in a session (automatic, only when rule 11 has a real path)

While the "Second brain path" in rule 11 is still the placeholder, ignore this rule: the second brain is off.

When it is set, the project hook `Claude/hooks/brain_brief.py` prints `wiki/hot.md`, the read order and the pending-ingest count at the start of every session, and runs the free checks after every page written under `<vault>/wiki`. What you do:

- Read order: `wiki/hot.md`, then `wiki/index.md`, then the thematic `wiki-index.md`, then the page. Never read the vault for a general coding question.
- Before asking the owner a question, look for the answer in the vault (`second-brain-librarian` query) and in `wiki/kit/` (how the kit itself works); skip silently if nothing is found.
- If a hook reports a broken link or a quote that is not in its raw file, fix the page in the same turn: the checks cost no tokens.
- Only `second-brain-librarian` writes to the vault. `vault_check.py status` lists the raw sources still to ingest; `done raw/<file> wiki/<page>...` records one.
<!-- KIT:END second-brain-session -->
