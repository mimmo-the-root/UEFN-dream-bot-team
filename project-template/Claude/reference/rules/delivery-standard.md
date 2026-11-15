<!-- Full text of the project rule "Delivery standard". The short version is in this project's CLAUDE.md (KIT block delivery-standard); kit_sync keeps this file current. -->

# Delivery standard

- **Delivery standard** (planner-docs owns it; the console shows it): ROADMAP.md has a `## Phases` table (PH-0 MVP, PH-1 Launch, PH-2 Growth;
  one Active; each with exit criteria; Phase 0 exit = a playtest with up to 3 players completes the core loop with no blocking bug and the
  owner decides). Releases are `P<phase>-R<n>`; plan only the Active phase and the next one; everything else is Release `Later` (backlog).
  A request that arrives mid-release goes to the backlog unless the owner says what it replaces. EVERY bug is a row in BUGS.md before it is fixed;
  never deleted (Fixed, then Closed after verification). At most 2 tasks In progress. Done = acceptance criterion verified, compiles, bugs Fixed.
  **Audit findings always get their own release** (`P<phase>-R<n>`, theme `Audit fixes <date>`, tasks by severity), never mixed into a feature release.
  At release close planner-docs adds a 3-line release note and a 3-question retrospective to STATUS.md. Old project without `## Phases`:
  planner-docs adds it on its next planning pass.
  **A published map is past the MVP.** If `Claude/docs/.island-code` exists, the map is already live: Phase 0 is Done (the live version is the shipped release; write "Done - published before planning, island code present" in its Status) and the Active phase is Phase 1 (Launch/stable), with releases `P1-R1`, `P1-R2`... for the updates. Never ask the owner for a written decision to leave Phase 0, never plan an MVP for it. An old ROADMAP.md that still has PH-0 Active in such a project is corrected on the next planning pass: PH-0 Done, PH-1 Active, open Phase 0 tasks moved to `P1-R1`.
