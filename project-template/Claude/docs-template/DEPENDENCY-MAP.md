# Dependency map — <project or system>

> On-demand document: create it BEFORE any refactor or cross-cutting change (copy to `Claude/docs/DEPENDENCY-MAP.md`).
> Facts are labeled **[V]** verified (read in code or via the UEFN MCP tools) or **[I]** inferred (say from what).
> Never write "orphan" or "unused": write "no reference found in <sources searched>".
> Stale when the Verse files changed since `Generated`; regenerate before relying on it.

Generated: <YYYY-MM-DD> · Kit: <version> · Sources searched: <Verse files, MCP level scan, ...>

## 1. Verse files
| File | Lines | Role (one line) | Main class / device |
|---|---|---|---|

## 2. Dependencies per file
For each file: uses (calls / reads) · used by · `@editable` bindings · events in / out.

## 3. Coupling matrix and hubs
Rows = callers, columns = callees. Hubs = files with the most links in either direction.

## 4. Placed in the level vs referenced in code
| Device | Placed in level | Referenced in Verse | Notes |
|---|---|---|---|
Level-placed config and wiring are readable only through the coder's UEFN MCP tools; struct/array fields (e.g. `Levels[]`) may be unreadable → mark [I].

## 5. Impact on reduction candidates
| Candidate | Who depends on it | Risk if removed | Verdict |
|---|---|---|---|

## 6. Limits
What this map could not see (and why).
