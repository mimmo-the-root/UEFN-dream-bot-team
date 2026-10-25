# A Fab product project

A **Fab product** is a small UEFN project whose components the customer adds to their own project. That changes what the kit may put in it.

## The rule: the kit installs nothing

The kit's own files (`Claude/`, `.claude/`, `CLAUDE.md`) must never be inside a Fab product. Epic's rules for an "UEFN Source" upload do not allow Python scripts (`.py`) in the archive, and the kit's hooks are Python. Even without that rule, the customer should receive your components, not our tooling.

So, in a new project, answer **Fab product** when the kit asks. It installs nothing and remembers your answer on your computer (outside the project), so it asks only once.

## What still works, and what does not

Works: the agents, skills and the connection to the open editor, because they live in your user profile, not in the project.

Also works: **lessons**. The kit installs nothing in the project, so it records your editor work in your profile instead (`~/.claude/fab-lab/<Product>/`): every MCP call, worked or failed, as in a map. `fab_lab.py status <project>` shows what was recorded, `fab_lab.py card <project>` writes a draft closing card for a finished material or mechanic (what changed, what failed, TODO for the final recipe and third-party assets), and `fab_lab.py console <project> --foreground` opens the Agent Console on that data (port 8766, so it does not clash with a map console; run it in your own PowerShell window and leave that window open, close it to stop the console). The console also shows the agents (for example `materials-expert`) working while they run. A card becomes a skill or recipe only with your yes. Needs the profile update (`update-my-profile.cmd`) and a new session.

Does not work: the commands that come with the project scaffold (`/verse-check`, `/handoff`, `/devlog`, `/jam-check`, `/concept-card`) and the `Claude/docs/` memory between sessions. Those belong to a map.

## What Epic asks of a Fab upload

From Epic's Fab documentation: no Python scripts in the archive; asset and folder names with letters, digits and underscore only; paths no longer than 140 characters, counting the project's top-level folder; no `Saved` or `Intermediate` folders; test the package in a clean project; third-party software and assets declared in the listing; a title of about 30 characters or fewer. Epic gives no image sizes for the listing, so check the current Fab pages before you make images.

## Documents: map and Fab side by side

| | Map project | Fab product |
|---|---|---|
| Kit installed in the project | Yes | **No, never** |
| Project documents | `Claude/docs/` (spec, status, roadmap, bugs, map, handoff, dev log) | None today |
| Who the documents are for | You and the agents | The customer and the Fab listing |
| Verse headers | Summary, date, version; changes in the log | Same rule for the code you write |
| Python and kit files in the package | Harmless | **Forbidden** |

## The Fab helper (version 1.109)

Ask in the chat for the **fab-product** skill, or run the helper yourself. It lives in your profile (`~/.claude/hooks/fab_pack.py`), never in the project, and needs no kit in the project.

| Command | What it does |
|---|---|
| `python fab_pack.py check "<project>"` | Checks the package against Epic's rules and lists what blocks the upload, warnings and notes. Paths are counted as `<ProjectName>/Content/<path>`. |
| `python fab_pack.py docs "<project>"` | Shows which documents it would create. Add `--apply` to write them. |
| `python fab_pack.py grid "<images folder>" [out.png]` | Puts the images of a folder (the captures for the listing) in a panoramic grid on a plain background. Options `--cols`, `--size`, `--bg`. Needs Pillow. |
| `python fab_pack.py zip "<project>"` | Writes `<ProjectName>.zip` next to the project, one top folder, without `.py`, `Saved`, `Intermediate`, or kit files. It refuses while names or paths are wrong. |

### Verse file style

In a Fab product every Verse file starts with a manual header (what it does, why it is useful, quick setup, good to know, version and date) and ends the header with your signature block: author, ASCII art and links. Save the block once from a finished file with `python fab_pack.py signature save <file>` (it is kept in your profile, never in a project); `python fab_pack.py header <Name>` prints a new header with it, and `check` warns when a header misses a part or the signature. This applies to Fab products only, not to maps.

### Where the files go

Fab wants the **whole project zipped**, so every generated file lives inside `Content`, in the folder that holds the product's assets (`Content/<Product>/`). The helper picks the Content folder with the most files (never `Collections`, `Developers` or a third-party library such as `VerseUIKit`); use `--product NAME` to choose another. If an older version left `Documentation/` or `FabListing/` next to `Content`, `docs --apply` moves them in (nothing is overwritten) and renames `third-party.md` to `third_party.md`, because names inside the archive may not contain a hyphen.

### The two folders

- **`Documentation/`** (inside `Content/<Product>/`, travels with the product): `README.md` (setup and usage, with TODO fields for you), `SETTINGS.md` (generated from the `@editable` settings, their defaults and the `#` note above each, plus each Verse file's Summary; regenerated only while it still carries the generated marker, so your hand edits are kept).
- **`FabListing/`** (inside `Content/<Product>/` too: Fab takes the whole project, so the listing texts travel in the archive; copy them into the portal): `listing.md` (title, description, tags, technical details), `third_party.md` (assets and libraries to declare, for example Epic's Verse UI Kit) and `screenshots.md` (list of images to make).

Existing documents are never overwritten. Nothing is written without `--apply`.

### Images for the listing

Take the captures in the editor (the skill uses the proven recipes and the lab guard), keep them as PNG in `FabListing/images/`, then run `grid` to make the panoramic image. Epic gives no image sizes: check the current Fab pages before you choose `--size`.

### Not part of the kit

Shortening over-long paths and checking third-party licences are done by hand: `check` lists the paths over the limit and the third-party content, and you decide what to rename or declare.
