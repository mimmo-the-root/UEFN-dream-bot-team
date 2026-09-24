# Known brand collection markers

Source: [Game Collections in Fortnite](https://dev.epicgames.com/documentation/fortnite/game-collections-in-fortnite)
(index) plus each collection's own detail page, read directly (2026-08). Confidence reflects what
was actually documented there, not a guess — "weak" means the public docs never named a folder,
device class, or template, only described the brand in marketing terms.

## Strong confidence — confirmed technical markers

**TMNT** (Teenage Mutant Ninja Turtles)
- Content Browser folder: `TMNT`
- In-game Creative inventory: `Brands > TMNT`
- Device classes: `TMNTCharacterSpawner`, `MouserNPC`, `TMNTDriftboardSpawner`,
  `TMNTSupplyDropSpawner`
- Prefab/template naming: `TMNT` prefix (e.g. "TMNT Sewer Gallery"), templates "Arcade,"
  "Dimension X Starter," "City Starter"

**LEGO®**
- Assets called "LEGO Elements": prefabs, devices, and primitives scaled at half Fortnite size
  (Minifigure scale), not resizable — that scale mismatch alone is a strong signal even without a
  folder name match
- Device classes: `Collectible` (awards LEGO studs), `Assembly` (LEGO Assembly device)
- Requires a separately-signed Creator Portal agreement (LEGO Brand Rules) — if a project has any
  reference to that agreement/program in its docs, treat as a strong signal too

**Fall Guys**
- Creative: dedicated **"Fall Guys" tab** in the console
- UEFN: assets under a **"Brand Templates"** section in the Project Browser
- Character class: **"Bean"** (Fall Guys' player character)
- Uses `Player Spawner` device instead of the normal skydive-in mechanic ("Beans don't skydive")
- Template naming: e.g. "Fall Guys Empty Grid," "Fall Guys Empty Large Grid"

## Weak confidence — name-level only, not yet confirmed against a real project

These collections are real and documented by Epic, but their public pages don't name a specific
folder, device class, or template — only marketing-level descriptions. Treat a match here as "the
project mentions this brand's name somewhere in its assets," worth flagging to the owner to
confirm, not a fact to state outright.

- **Star Wars™** — mentions of a `Conversation` device, "Vehicle Spawner" and "Cinematic
  Vehicles" devices reskinned for Star Wars content; no folder/class name published.
- **KPop Demon Hunters** — a "KPop Demon Hunters Starter Island template" is mentioned by name;
  no folder/device class published.
- **Squid Game** — two UEFN-only templates named "Minigame Mastery" and "Social Deduction"; no
  folder/device class published.
- **The Walking Dead Universe** — "Walker NPC" is the one named asset type, configured via a
  generic `NPC Spawner` device (not a TWDU-specific device class); no folder name published.
- **Rocket Racing** — documented as using "custom devices" without naming them; a full device
  list exists on a separate Epic page not covered in this pass. **Lifecycle note: Epic's own docs
  state Rocket Racing will be sunset in October** — a project matching this one may be on a
  collection that's being retired, worth flagging explicitly if found.

## Maintenance

This table needs to stay current two ways: Epic adds/retires collections over time (see the
Rocket Racing sunset note above — this table needs a re-check against [the index
page](https://dev.epicgames.com/documentation/fortnite/game-collections-in-fortnite) periodically,
the same way `second-brain-librarian`'s weekly UEFN release-notes sync already re-checks Epic's
"What's new" page — extending that same job to also glance at this index is the natural way to
keep it current without a separate manual chore), and every "weak" entry above should get
upgraded to "strong" the first time a real project confirms its actual markers — see
`first-use-recognition-procedure.md` for how that capture happens.
