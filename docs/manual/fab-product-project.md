# A Fab product project

A **Fab product** is a small UEFN project whose components the customer adds to their own project. That changes what the kit may put in it.

## The rule: the kit installs nothing

The kit's own files (`Claude/`, `.claude/`, `CLAUDE.md`) must never be inside a Fab product. Epic's rules for an "UEFN Source" upload do not allow Python scripts (`.py`) in the archive, and the kit's hooks are Python. Even without that rule, the customer should receive your components, not our tooling.

So, in a new project, answer **Fab product** when the kit asks. It installs nothing and remembers your answer on your computer (outside the project), so it asks only once.

## What still works, and what does not

Works: the agents, skills and the connection to the open editor, because they live in your user profile, not in the project.

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

## Planned: the Fab documents (not built yet)

This is the plan for version 1.109, and it is a working hypothesis that will be confirmed before it is built. The kit would create only a small set of Markdown files:

- **`Documentation/`**: setup and usage instructions that travel with the product and become the customer's manual. Much of it can be generated from the code: the `@editable` settings with their defaults, and the summary at the top of each Verse file.
- **`FabListing/`**: the texts for the Fab portal (title, description, tags, technical details, declaration of third-party assets, what the product contains), kept outside the archive.

Alongside them: a light check of the package against the rules above, a helper to propose shorter names for paths that are too long (only with your approval), and screenshots for the listing.

Until then, the agents can help you write these texts on request, in the chat.
