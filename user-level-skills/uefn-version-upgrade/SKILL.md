---
name: uefn-version-upgrade
description: How to take in a new UEFN release (they come about every 15 days) and how to move a project to it: read the notes, diff the tools and the Verse digests, update the few places in the kit that hold version facts, and check a project before a publish. Use when the owner says a new UEFN version is out, update, upgrade, the build broke after updating, a feature is experimental, or before publishing from a project made on an older version.
kind: discipline
last_reviewed: 2026-11-03
sources: [Epic's UEFN release notes 42.20 to 43.00]
---

# Taking in a UEFN release

Epic ships a UEFN release about every 15 days. Most of it does not touch the kit; a few things do (a limit, a name, an MCP tool, a publishing rule). This skill is the routine that finds them without reading everything twice. What each release changed is kept in `references/releases/<version>.md`; the latest is `43.00.md`.

## When to use
- The owner says a new UEFN version is out, or the editor was just updated.
- A project that built yesterday breaks after an update.
- Before a publish from a project made on an older version.

**When not to use:** a normal Verse error in new code (use `uefn-verse-build`), a device that misbehaves (use `uefn-device-gotchas`).

## The routine (about an hour, once per release)
1. **Save the before.** Before updating the editor, copy the project's Verse digests (`Fortnite.digest.verse`, `UnrealEngine.digest.verse`, `Verse.digest.verse`) to `Claude/docs/digests/<old version>/`. After updating, copy them to `Claude/docs/digests/<new version>/`.
2. **Diff the Verse API.** `python Claude/hooks/digest_diff.py Claude/docs/digests/<old> Claude/docs/digests/<new>` lists what was added, removed or changed, and marks lines that mention experimental or deprecated. This is the part release notes always miss.
3. **Read what the tools learned by themselves.** The Knowledge page, "Editor tools", shows the new, renamed, reworded and removed MCP tools (autodiscovery) and the list of Epic's skills; `mcp_map.py --find WORDS` searches them. A silent update between releases shows there too.
4. **Read the release notes** (Epic Developer Community, "UEFN release notes"). Keep only what touches this kit: use the table in `references/kit-touchpoints.md`.
5. **Write the release file.** Copy `references/releases/TEMPLATE.md` to `references/releases/<version>.md` and fill it: what changed, what it breaks, what to check, and the numbers you confirmed in the editor (mark each number "confirmed" or "from the notes").
6. **Update the touchpoints** that the release changed, and nothing else. Run the tests.
7. **Set `last_reviewed`** of the skills you changed.

## Checking a project that moves to the new version
1. Build first and read the first error, not the last. Most breaks are a renamed member, a deprecated call or a new limit.
2. Search the Verse code for the words the release file lists under "what breaks"; fix only what the build or the search shows.
3. Look for experimental features in the Verse and in the level. An island that uses one cannot be published; tell the owner before building on it and offer the stable way.
4. Check the publish requirements in the Creator Portal (images, video, rating questionnaire) and the memory budget in the unit the editor shows.
5. Playtest once. If the Verse behaves oddly, try once with the new virtual machine switch on (when the release has it) and say what differs.

## Rules (symptom, cause, remedy)
- "It built yesterday": the update changed a name, a limit or a default, not your code. Read the first error.
- A fix that keeps a deprecated call: it works today and breaks later; replace it.
- Publishing blocked with no Verse error: look for an experimental feature in the level, not only in code.
- A number from the notes written as a fact: confirm it in the editor first, or label it "from the notes".
- Copying Epic's text into the kit: describe it in your own words and name the source.
- Everything at once: touch only the touchpoints the release changed.

Where version facts live in the kit: `references/kit-touchpoints.md`. Template: `references/releases/TEMPLATE.md`.
