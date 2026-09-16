# This folder is a seed, not live data

`docs-template/` holds pristine, empty copies of `SPEC.md`, `STATUS.md`, `ROADMAP.md`, `BUGS.md`,
`RETENTION-NOTES.md`, and `RELEASE-READINESS.md`. `Claude/SETUP-INSTRUCTIONS.md` (Phase 2, step 3)
copies these into the project's real `Claude/docs/` folder **once**, the first time a project is
set up — and only if `Claude/docs/` doesn't already exist.

**This is what makes it safe to bulk-copy `project-template/`'s update-safe parts over an existing
project to pick up a new kit version** (see SETUP-GUIDE.md's "Updating an existing project"
section): `docs-template/` never holds a project's real progress, so overwriting it changes
nothing that matters — the project's actual `Claude/docs/` (with its real SPEC/STATUS/ROADMAP/
BUGS/RETENTION-NOTES/RELEASE-READINESS content) lives at a different path and a kit update never
touches it.

Don't hand-edit these files expecting it to affect any existing project — it won't, they're
already past the point where they were seeded from here. If you want to change what a *brand
new* project starts with, edit the files in this folder; an existing project's own `Claude/docs/`
is edited directly instead.
