# Capturing markers for a brand not covered yet

Trigger: during `project-bootstrap`'s A1 (or any later session), you notice folders, placed
devices, or a project template name that clearly reference a real-world brand/franchise, but
`known-brand-markers.md` has no strong match for it (either it's missing entirely, or it's listed
there only as "weak confidence").

Don't guess the markers from memory or invent plausible-looking device names — capture them for
real, the same way the console's "unknown card" bug was only actually solved by a live payload
capture, not by theorizing from documentation.

## Step 1 — confirm it's worth a dedicated capture pass

A single oddly-named folder isn't enough to justify this. Worth it when there's a real cluster:
multiple devices/prefabs/folders that plausibly belong to the same named brand, or a project
template whose name matches (or closely resembles) an entry on [Epic's Game Collections
index](https://dev.epicgames.com/documentation/fortnite/game-collections-in-fortnite). If it's
just one ambiguous name, note it in `SPEC.md` as a loose observation and move on — don't spin up
analysis for a false lead.

## Step 2 — the actual capture

Read the real markers directly from this project, don't infer them:
- Content Browser: what folder(s) hold the brand-specific assets, and their exact name.
- Placed devices: their actual class/type names (via MCP Scene Graph reads if connected, or the
  Verse/device references in code), not just what they're labeled in the Outliner.
- The project's own template name, if it was created from a brand starter template.
- Anything distinctive about how the assets behave (e.g. LEGO's fixed half-scale, Fall Guys'
  Player-Spawner-instead-of-skydive convention) — behavioral quirks are markers too, not just names.

For a large or unfamiliar project where this spans multiple areas, this is a reasonable case for
`second-brain-trainer`'s parallel-analysis pattern (split by area, read-only clones, one
aggregated result) instead of one long sequential pass — same tool, different target (brand
markers instead of general reusable mechanics).

## Step 3 — write it down in TWO places

1. **This skill's own reference file**, `~/.claude/skills/brand-collections-uefn/references/known-brand-markers.md`
   — move the collection from "weak" to "strong" (or add a new entry if it wasn't there at all),
   with the exact markers just captured. This makes the recognition work immediately for every
   future project on this machine, with no vault required.
2. **The second brain vault, if configured** — hand off to `second-brain-librarian` with a brief
   (brand name, the markers captured, this project's name, today's date), asking it to create or
   update an article under `type: pattern` (the vault's existing frontmatter schema has no
   dedicated "brand" type — `pattern` is the closest fit: "how to recognize and build within the
   `<Brand>` Game Collection" is a reusable technical pattern, not a one-off device). Let
   `second-brain-librarian` decide the exact wiki/article placement per that vault's own
   `CLAUDE.md` conventions, same as any other handoff — don't prescribe a path here.

Both writes matter: the skill file is what actually gets read during `project-bootstrap`'s A1 (fast,
no vault dependency), the vault entry is what makes the same knowledge available on every other
machine/setup that shares that second brain.

## Step 4 — report it

Tell the owner plainly what was captured and where it was written (skill file, and vault article
if applicable) — this is exactly the kind of update worth surfacing, not silently filing away.
