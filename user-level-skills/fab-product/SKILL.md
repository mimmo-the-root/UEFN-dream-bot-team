---
name: fab-product
description: Preparing an UEFN project to be sold on Fab (a Fab product, not a map). Read it when the project is registered as a Fab product, when the owner talks about Fab, a listing, the UEFN Source archive, screenshots for the listing or the product's documentation.
last_reviewed: 2026-10-23
sources: [official-docs]
---

# Fab product (UEFN Source)

A Fab product is a small UEFN project whose components the customer adds to their own project. The kit installs NOTHING in it (no `Claude/`, `.claude/`, `CLAUDE.md`, no Python): Epic does not allow `.py` files in an UEFN Source archive. Everything here works from your profile, with `~/.claude/hooks/fab_pack.py`.

## Epic's rules for the archive (Fab documentation, "Upload UEFN source to Fab")
- The archive is the complete project folder zipped: exactly one project, with project file, plugin file and all content; not encrypted.
- No Python scripts; no `Saved` or `Intermediate` folders.
- Every asset path 140 characters or fewer, including the top-level folder name. Count it as `<ProjectName>/Content/...`.
- English letters, digits and underscore only in folder and file names; clear names, not generic ones such as `Assets` or `NewFolder`; no unused folders.
- Declare third-party software and assets in the listing. Test the package in a clean project.

## The helper (run it, do not recount by hand)
- `python ~/.claude/hooks/fab_pack.py check <project>`: what blocks the upload (exit 1), warnings (empty folders, third-party content such as VerseUIKit, `.lore`), notes.
- `python ~/.claude/hooks/fab_pack.py docs <project> [--apply]`: dry run first, then writes, INSIDE Content in the folder that holds the product's assets (`Content/<Product>/`), `Documentation/` (README.md, SETTINGS.md) and `FabListing/` (listing.md, third_party.md, screenshots.md). It never overwrites; `Documentation/SETTINGS.md` is regenerated from the code (the `@editable` settings with defaults and each file's Summary) until the owner edits it.
- `python ~/.claude/hooks/fab_pack.py zip <project>`: writes `<ProjectName>.zip` next to the project: the WHOLE project (Fab wants it all), without `.py`, `Saved`, `Intermediate` and kit files; it refuses when names or paths still break the rules.

## How to work
1. Run `check`. Report the blocks in plain words; never rename or move assets without the owner's yes (a rename must keep references working: use the editor's move/rename, not the file system).
2. Run `docs` (dry run), tell the owner what would be created, then `--apply`.
3. Fill the TODO fields from what the code and level really contain; do not invent features, prices or licences. Anything you do not know stays TODO and goes in the reply.
4. Third-party content: check the licence of each item (VerseUIKit is Epic's library: confirm its terms before including it) and fill `FabListing/third_party.md`.
5. Verse code the customer receives keeps the header rule: Summary, real date, version; changes are not listed in the file.
6. Materials: when the owner confirms a material works, save its recipe (`skills_lib.py recipe-add materials <file.json> "<product name>"`, run from `~/.claude/kit-template/Claude/hooks/`); that is what the materials skill learns from. Say it in the reply, with the recipe name.
7. Lessons: your UEFN MCP calls are recorded outside the project (`fab_lab.py`, folder `~/.claude/fab-lab/<Product>/`). When a material or mechanic is finished, run `python fab_lab.py card <project>`, fill the TODO parts of the draft (goal, final recipe, traps, third-party assets) and ask the owner whether to promote it into a skill or recipe. Never write lesson files in the project.
8. Before saying "ready": `check` has no blocks, no TODO is left in `FabListing/listing.md`, then `zip`, and the owner tests the zip in a clean project.

## Verse files of a Fab product (this style only here, never in maps)
Every `.verse` file the customer receives is written as a small manual. Header, in this order, all `#` lines between dashed rules:
1. `# <Name>.verse`, then `# Title  -  vN  (last modified: YYYY-MM-DD)` with the real date; raise N at every substantial change (the change history is not kept in the file).
2. `WHAT IT DOES`, `WHY IT IS USEFUL`, `QUICK SETUP` (numbered, one line per setting of the Details panel, ending with the DebugLoggingEnabled hint), `GOOD TO KNOW` (limits and surprises).
3. `Author:` and then the owner's signature block (ASCII art and links). Never write it from memory: it is saved once with `python ~/.claude/hooks/fab_pack.py signature save <a finished verse file>` and printed with `header <Name>` (layout plus signature). If none is saved, ask the owner for a finished file; do not invent links.
Body: numbered section comments (`# --- 1. TAG DEFINITIONS ---`), a comment above every class, every `@editable` and every function saying what it is for in the customer's words, and short comments on the non-obvious lines. `check` warns when a header misses a part or the saved signature.

Images for the listing: Epic gives no sizes; check the current Fab pages first. Take the captures in the editor with the proven recipes (`uefn-editor-logs`: SetCameraTransform, CaptureViewport; always the lab guard, and restore the camera afterwards), save them as PNG in `FabListing/images/`, then build the panoramic grid on a plain background:
`python ~/.claude/hooks/fab_pack.py grid <Content/<Product>/FabListing/images> [out.png] [--cols N] [--size 1920x1080] [--bg #1a1a1a]` (needs Pillow; it writes `grid.png` there and leaves the originals alone). Update `FabListing/screenshots.md` with what each picture shows.
