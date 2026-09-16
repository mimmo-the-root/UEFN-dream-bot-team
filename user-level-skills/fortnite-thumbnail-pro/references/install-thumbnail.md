# Installing a confirmed thumbnail into the project

Only once the owner has confirmed a final thumbnail (not for intermediate concepts/variants).
This is the one narrow exception in this kit to "agents don't touch files outside `Content/`" —
`Resources/` and the `.uefnproject` file both live at the real UEFN project root, one level
**above** `Content/`, not inside it.

## 1. Find the project root
`Content/CLAUDE.md`'s "Project identity" section has the project name already detected during
setup (never recompute it from the current folder — `Content` is named identically in every
project). The project root is the folder that *contains* `Content/`, i.e. one level up from
where this session is normally working — named after that same identity value (e.g. the island's
name).

## 2. Place the file
- `<project root>/Resources/` — create it if it doesn't exist yet.
- Save the confirmed image there. Match the key already used in the `.uefnproject` file if one is
  already set (see step 3) — if there's no existing convention, name it `Thumbnail.png`
  (converting to PNG first if the source is a different format; Epic's own limit is 1920x1080,
  max 5 MB, see the rules above).

## 3. Update `<ProjectName>.uefnproject`
This JSON file sits at the project root (same level as `Resources/`), named after the project
(e.g. `MyIsland.uefnproject`). It has a `"keyArt"` key pointing at the thumbnail, relative to the
project root:

```json
"keyArt": "Resources/Thumbnail.png",
```

- If the key already exists, update only its value — don't touch anything else in the file, and
  don't reformat/reorder the rest of the JSON.
- If the key is missing entirely, add it at the top level with the same shape as the example
  above; if you're not sure where Epic expects it in the schema, say so and ask rather than
  guessing at a nested location.
- Keep the path **relative** ("Resources/Thumbnail.png"), not absolute — an absolute path breaks
  the moment the project moves machines.

## 4. Confirm to the owner
State plainly what changed and where: the file's path under `Resources/`, and that `keyArt` in
the `.uefnproject` file now points at it. If UEFN was open while this happened, mention that a
restart (or reopening the project) may be needed for the editor to pick up the new key art —
this kit doesn't have an MCP call that refreshes it live.
