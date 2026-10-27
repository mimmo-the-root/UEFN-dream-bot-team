# A Fab product project

A **Fab product** is a small UEFN project whose components the customer adds to their own project. That changes what the kit may put in it.

## The rule: the kit installs nothing

The kit's own files (`Claude/`, `.claude/`, `CLAUDE.md`) must never be inside a Fab product. Epic's rules for an "UEFN Source" upload do not allow Python scripts (`.py`) in the archive, and the kit's hooks are Python. Even without that rule, the customer should receive your components, not our tooling.

So, in a new project, answer **Fab product** when the kit asks. It installs nothing and remembers your answer on your computer (outside the project), so it asks only once.

## What still works, and what does not

Works: the agents, skills and the connection to the open editor, because they live in your user profile, not in the project.

Also works: **learning**. A folder whose name has FAB as a word (for example `root_FAB_rainbow`) is a Fab product by itself, with no question. Press *Learn from this product* on the Skills page: the agent proposes lessons (mostly how things are done, not only errors) and prepares the recipes of your devices and mechanics, and you approve them in *To approve*. Fab recipes count as confirmed at once, because you check them in the editor. The kit installs nothing in the project, so it records your editor work in your profile instead (`~/.claude/fab-lab/<Product>/`): every MCP call, worked or failed, as in a map. `fab_lab.py status <project>` shows what was recorded, `fab_lab.py card <project>` writes a draft closing card for a finished material or mechanic (what changed, what failed, TODO for the final recipe and third-party assets), and `fab_lab.py console <project> --foreground` opens the Agent Console on that data (port 8766, so it does not clash with a map console; run it in your own PowerShell window and leave that window open, close it to stop the console). The console also shows the agents (for example `materials-expert`) working while they run. A card becomes a skill or recipe only with your yes. On the Skills page of the Fab console the section **FAB LAB** has a button "Learn from this product": it collects candidates from the failed calls and asks the agent (at the end of its next answer) for lessons; you edit, approve or reject them there, and approved ones are read by every Fab product at start. Recipes saved from a Fab product count as confirmed at once. Besides materials there is a **mechanics** recipe type for stand-alone devices, game mechanics and whole map templates: `fab_lab.py draft-recipe <project> "<name>"` drafts it from the product (Verse files with their code, the editor calls that worked), the agent fills in devices, settings, wiring, assets and how to verify, and saves it with `skills_lib.py recipe-add mechanics`. To rebuild one, ask for it by name or run `skills_lib.py recipes mechanics <keyword>`. The kit prepares these recipes by itself from the Verse code (for a Fab product when the console reads it, for a map at every session start). On the Skills page each learned recipe has **Share in the kit** or **Keep private**: only the ones you share are collected by `publish.ps1` (`tool/collect_recipes.py`, privacy checked) into the kit's official recipes, so every user gets them with the next update. A shared recipe is public, with its Verse code, under the kit's MIT license. Recipes also travel through the community like lessons: **Send to the community** opens a GitHub proposal you finish yourself; what others shared arrives with a kit update in an inbox on the Skills page, is checked again, and is used only after you approve it. Needs the profile update (`update-my-profile.cmd`) and a new session.

Does not work: the commands that come with the project scaffold (`/verse-check`, `/handoff`, `/devlog`, `/jam-check`, `/concept-card`) and the `Claude/docs/` memory between sessions. Those belong to a map.

## Names inside the assets

The editor remembers where a file was imported from, so a texture can carry a Windows user name or the name of another of your projects. Before every `check` and `zip` the kit replaces those names with asterisks of the same length (the file size does not change), keeps the original in your profile outside the project, and says what it cleaned; in its own reports the name is written `***anonymized***`. Nothing else in an asset is touched.

**Privacy rule (GDPR).** Regulation (EU) 2016/679 (the GDPR, in force in the European Union) asks to process only the personal data that is needed (data minimisation, Article 5(1)(c)); a Windows user name, an email address or a home folder path in a file that you share is personal data. In every text the kit writes (reports, listings, documents, logs, commit messages) a personal identifier is written `***anonymized***`. In your own binary assets, where the length of the text cannot change, the name is overwritten with asterisks of the same length (the file keeps its size). The rule applies ONLY to your own files: assets created by Epic (libraries, templates, Fortnite and Engine content) are never touched, to avoid problems with the editor and with Epic's validation. Anonymised data is outside the scope of the GDPR (Recital 26). This is not legal advice.

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

## The Checklist page

In the console of a Fab product a tab **Checklist** appears (other projects do not have it). It groups every check in seven stations: Project, Content, Build, Listing, Extra (memory calculation and a private release, one more round of validation), Zip and Submit. Each line says what the kit looked at and what to do; the label tells who checks it: the kit, the editor (a record from UEFN), you, or "extra" (a check added after a rejection). The verdict shows NOT READY while something blocks the upload, with a bar and the percentage of checks passed.

Lines only you can judge have a box: tick it when you have done the check. For the UEFN validation, run it in UEFN with **Skip Fix-up**, copy the output and paste it in the box of station 3; the kit counts errors and warnings and keeps the record. Start the page with `fab_lab.py console <project>`, as for the lessons. Nothing is written in the project.

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
- **`FabListing/`** (inside `Content/<Product>/` too: Fab takes the whole project, so the listing texts travel in the archive; copy them into the portal): `listing.md` (title, description, tags, technical details), `third_party.md` (assets and libraries to declare, for example Epic's Verse UI Kit). The listing images are made by hand.

Existing documents are never overwritten. Nothing is written without `--apply`.

### Images for the listing

Take the captures in the editor (the skill uses the proven recipes and the lab guard), keep them as PNG in `FabListing/images/`, then run `grid` to make the panoramic image. Epic gives no image sizes: check the current Fab pages before you choose `--size`.

### Not part of the kit

Shortening over-long paths and checking third-party licences are done by hand: `check` lists the paths over the limit and the third-party content, and you decide what to rename or declare.
