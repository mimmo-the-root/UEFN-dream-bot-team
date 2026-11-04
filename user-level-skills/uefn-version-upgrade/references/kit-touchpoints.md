# Where a UEFN release can touch the kit

Read the release notes against this table; open only the rows whose topic changed.

| Topic in the notes | Kit place to check | What to look for |
|---|---|---|
| MCP settings, startup, new toolsets, tool names | `Claude/SETUP-INSTRUCTIONS.md`, `env_check.py`, `mcp-tool-contracts/SKILL.md`, the Knowledge page (autodiscovery does the tool list by itself) | where it is enabled, how tools are named, how scripts run |
| Epic's own skills served by the MCP | `uefn-epic-skills/references/epic-skills-list.md` | new or removed skill names (compare with `ListSkills`) |
| Verse language and API | `uefn-verse-build`, `verse-patterns`, `uefn-lessons`, `verse_static.py` | renamed or deprecated members, new limits (for example `weak_map`), new classes |
| Experimental features | `release_gate.py` (compliance), `uefn-version-upgrade` list in the release file | what makes an island unpublishable |
| Memory budget and units | `release_gate.py`, `delivery.md`, `environment.md`, `performance-uefn-checklist` | percent or MB, the limit, when it is checked |
| Publishing requirements | `fortnite-thumbnail-pro`, `fortnite-title-description`, `growth-manager`, the delivery gate | image count and sizes, logo, video, rating |
| Devices and Creative | `uefn-level-devices`, `uefn-device-gotchas`, the device recipes | new or changed devices, new options |
| Progression, quests, persistence | `uefn-quests` (when it exists), the adventure-rpg genre, the `ordered objectives` recipe | what is publishable now |
| VS Code extension, Verse tooling | `docs/`, `CONTRIBUTING.md`, the manual install chapter | the name of the extension, file types |
| Fab and assets | `fab-product-project` chapter, Fab checklist | new product kinds, rules |

Not a touchpoint: art, lighting and gameplay features that no kit rule mentions.
