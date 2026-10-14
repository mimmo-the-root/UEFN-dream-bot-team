# Community lessons: creators share, the kit learns for everyone

Status: approved by the owner and implemented in v1.99.0 (2026-10-14). Deviations from the first draft are listed in section 13.

## 1. Goal

UEFN creators who use the kit learn lessons from their own maps. Those lessons are approved by the creator on the
Skills page and stay on their PC. This feature lets a creator **voluntarily share approved lessons**, lets the kit
owner **collect and merge everything that arrives without throwing anything away**, and **release the improved genre
skills to all creators**. Success: genre skills get better as creators join, with no manual work on each lesson, with
no map code, names or numbers leaving the creator's PC, and with a malicious contribution unable to change what Claude
is told to do beyond one clearly marked, low-trust section.

## 2. Scope

In (v1):
- A switch "Contribute to the community" (off by default) and a "Contribute" button per approved lesson.
- Transport by GitHub Pull Request (no server, no token to maintain).
- Intake pipeline with levels (nothing is deleted), automatic screening against injection, owner promotion.
- Reputation: public signature (@handle) and a score computed from outcomes.
- A new console page "What's new" (mockup: `2026-10-14-community-lessons-news-mockup.html`).

Out (later): map blueprints (they carry numbers and structure of a map; v1 shares lessons only), reputation levels,
vouching, per-genre reputation, island-code verification, peer-confirmation button, any server or access control
(the code is public, so a client-side gate would be bypassed without creating value).

## 3. Actors and flow

1. Creator turns the switch on (Skills page). Setting stored in `Claude/logs/community.json` (`{"share": true}`).
2. On an approved lesson the creator presses **Contribute**. The console shows the exact JSON that will leave the PC
   (section 4) and, on confirm, opens the browser at a pre-filled GitHub "new file" page for the kit repository
   (`/new/main?filename=contributions/<genre>/<pattern_id>/<handle-placeholder>.json&value=<json>`). The creator only
   has to press "Propose new file" (GitHub forks and opens the PR). The kit never sends anything by itself.
3. An Action validates and screens the PR (section 5), labels it, and records it in the intake.
4. The **curator agent** (decided: agent + final human validation) groups contributions by `pattern_id`, rewrites
   accepted ones into canonical wording, checks conflicts with existing lessons, and opens ONE promotion PR against the
   genre skills with a short report per lesson (state, sources, screening verdict, what changed). It never merges and
   has no write access beyond that PR. The owner is the final validation: nothing reaches a release without his
   approval of that PR.
5. The release carries: the updated genre skills, `community-summary.json` (what the What's new page shows),
   `revoked.json`.
6. At the creator's PC the kit applies the update. Community lessons arrive as **proposals** the creator approves on
   the Skills page, as for their own; unconfirmed ones are marked "to verify".

## 4. Contribution format

One file per lesson per contributor: `contributions/<genre>/<pattern_id>/<handle>.json`. The handle in the file name
is checked against the PR author by the Action (the author is the identity; the JSON never claims an identity).

```json
{
  "schema_version": 1,
  "pattern_id": "<content hash, same function the kit already uses>",
  "genre": "<slug of fortnite-genres-official.json>",
  "variant": "<map type, canonical spelling>",
  "section": "<one of the starter sections>",
  "direction": "for | against",
  "text": "<generalized lesson, max 400 chars, no names/ids/links>",
  "kit_version": "1.99.0"
}
```

Not included: blueprint, map name, file paths, island code, Verse source, device names that are not in the official
device list. Two creators with the same `pattern_id` produce two files in the same folder: that is the support count,
with no merge conflicts.

## 5. Intake levels (nothing is deleted)

`new` (just arrived, invisible) -> `screened` (passed automatic checks) -> `hypothesis` (published in a separate
"to verify" block of the genre skill, one source is enough) -> `confirmed` (enters the rules) ; `archived` (rejected,
kept with the reason, never shown). Moves are recorded in `contributions/INTAKE.json` by the Action; a lesson is never
removed from the repository, only changed state.

Confirmed when: >= 2 distinct handles sent the same `pattern_id`, or the owner approves it. The owner can always
promote or archive by hand. Hypotheses are limited in number per genre so that a flood cannot grow the skill.

## 6. Injection defence (layers)

1. **Data, not prose.** Fixed schema; `text` limited by length and character set; `genre`, `variant`, `section` are
   enums/regexes; device and API names are checked against the official device list and the Verse digest names; an
   unknown identifier is a red flag (state stays `new`).
2. **Regenerate, do not trust.** The curator rebuilds the statement from condition and action in a fixed template (the contributor's own
   `statement` is never copied). Condition and action are still the contributor's words, so they pass a strict plain-English filter (printable
   ASCII and a few typographic marks only: no look-alike letters, combining marks, zero-width, bidi, control characters or newlines) and the
   screening, and the creator's kit applies the same character filter on import.
3. **Deterministic filters** on `text`: URLs, shell/PowerShell commands, base64-like blobs, zero-width and bidi
   Unicode, markdown links/images, file paths, tool or command names, phrases that address the assistant
   (ignore/always run/never tell/system/prompt...).
4. **Isolated classifier**: a model call with no tools and no secrets answering one question (describes a UEFN fact, or
   gives orders?). Only its verdict is used, never its text.
5. **Reputation** (section 7): score 0 accounts get stricter review and a daily limit.
6. **Blast radius**: PRs may only touch `contributions/` (renames and deletions count, symbolic links are refused); the check runs on
   `pull_request_target` so the PR cannot edit it, and is safe because it never executes PR content (scripts from the base commit, read-only
   token, no secrets); it never merges; contributions can never alter hooks, commands, settings or any code; promotion is a separate owner PR.
7. **Creator side**: the kit re-validates the schema on install, community lessons arrive as proposals to approve,
   hypotheses are worded "to verify against the map's code".
8. **Revocation**: `revoked.json` (pattern ids and handles) ships with each release; the kit removes matching lessons at
   the next update. Banning a handle revokes all of its lessons.

Known limit: a patient attacker can write a technical-looking but subtly wrong lesson that no filter tells from an
honest mistake. That is why single-source lessons stay hypotheses and rules need confirmation, and why revocation exists.

## 6b. Curator agent

Runs on a schedule (and on demand) as a GitHub Action with read access to `contributions/` and permission to open a
PR on a bot branch only. Input: `INTAKE.json` and the contribution files, treated strictly as data. Output: the
promotion PR (canonical lesson text from verified fields, section and variant, support list by handle, verdict of the
isolated classifier, conflicts/duplicates found with `similar`) and an updated `INTAKE.json` state proposal. Final
human validation: the owner reviews and merges the PR; he can reject single lessons (they become `archived` with the
reason). The agent's own output is screened by the same filters as contributions before it is proposed.

## 7. Reputation (v1: two levers)

- **Signature**: every published lesson carries "by @handle" (identity = GitHub PR author, mandatory by construction).
- **Score by outcome**, computed by an Action from the repository history into `reputation.json`: +3 when a lesson of
  the handle is confirmed (by another handle or by the owner), +1 for each additional independent handle that sends
  the same `pattern_id`, -5 when a lesson is revoked/refuted, 0 for archived. Weights are a starting point to tune.
  A handle with score 0 is under the stricter rules of section 6.5. No levels in v1.

## 7b. What's new page (console)

New page `agent-console-news.html` (new tab "What's new"). Shows: release summary from the changelog; skills new or
improved in the last release with lessons added/confirmed and contributors; top contributors (podium + table, the
owner highlighted); lessons confirmed on most maps; thanks; a "Submit an issue" link to the repository's issue chooser (`.../issues/new/choose`, shown in the last-release buttons and next to the thanks; it is also how a wrong community lesson is reported for revocation); "your part" card (switch state, lessons shared, score,
approved lessons not yet shared). Data comes from `Claude/community/community-summary.json` shipped with the kit update,
so the page works offline. Owner's personal numbers come from local `Claude/logs/community.json`. Mockup attached.

## 8. Components and files

- Kit (project-template): `skills_lib.py` (`contribution_export(slug, pattern_id)`, share state, apply `revoked.json`),
  `agent-console-skills.html` (switch + button + preview), `agent-console-news.html` (new), console server endpoints
  (`/community-state` GET/POST, `/community-export` GET) taking slug/pattern from a listing (no raw names into paths;
  see `docs/code-scanning-lessons.md`), `kit_sync.py` (install community pack as proposals), tests.
- Repo: `.github/workflows/contributions.yml` (validate, screen, label, update INTAKE and reputation),
  `tool/screen_contribution.py` (filters, name checks), `tool/community_summary.py` (builds
  `community-summary.json` at release), `contributions/`, `reputation.json`, `revoked.json`,
  `docs/community-contributions.md` (rules for contributors).
- Release: `tool/release_notes.py` unchanged; the release workflow also publishes `community-summary.json`.

## 9. Privacy and consent

Opt-in switch, off by default; nothing is sent without pressing the button and seeing the JSON; contributors accept
in `docs/community-contributions.md` that anonymized lessons become part of the kit under the repository licence;
their @handle is public. Turning the switch off hides every sharing control; it does not affect receiving the kit.

## 10. Testing

Schema tests (valid/invalid), screening tests with a corpus of injection samples and of honest lessons (false
positives tracked), `pattern_id` stability, state transitions of INTAKE, reputation arithmetic, revoked removal,
console endpoints (no path built from request text), What's new rendering with sample summary, and the existing
`python3 tests/run_all.py` stays green.

## 11. Open points for the owner

- Confirmation threshold (2 handles) and the hypothesis cap per genre.
- Score weights (3 / 1 / -5).
- The GitHub "new file" pre-fill URL must be verified against current GitHub behaviour (length limit, fork flow)
  before implementation; fallback is an issue form that an Action turns into a PR.

## 12. Rollout

1. Screening + schema + intake Action (nothing visible to creators). 2. Kit: switch, button, export. 3. Curator and
promotion PR. 4. What's new page and community-summary. 5. Reputation Action. Each phase ships as its own kit version.

## 13. Changes made while implementing (v1.99.0)

- **Contribution fields.** The kit's lessons already have `statement`, `condition`, `action` and an id that is the hash of variant + condition + action,
  so the file carries those three fields (limits 200/140/200) instead of one `text`, and the validator checks that the id matches the content.
- **Only published maps (owner constraint).** A lesson can be shared only if a map that supports it is published: the project has an island code
  (`Claude/docs/.island-code`) and Epic's API has public data for it. Cached in `Claude/logs/island-published.json` (only a hash of the code is kept),
  checked at session start (at most once a day); lessons of unpublished maps stay local and the Skills page says so. Each map remembers its project
  (`maps.json`). This is a barrier for honest use: with a tampered kit it can be bypassed, so the real defence stays in the Action and the owner's validation.
  Possible extension: put the island code in the contribution and let the Action verify it on Epic's API and weigh the reputation by the island's players.
- **Switch location.** The switch and the list of shared lessons live in `<skills dir>/community-share.json` (user level, like the skills).
- **Import** reuses the kit's existing community pack channel: the promoted lessons are written to `user-level-skills/genre/<genre>/community/community.json`
  and offered as ONE proposal per genre by `merge_pack` (origin community, tier hypothesis); `Claude/community-revoked.json` removes revoked lessons.
- **Curator** runs weekly as an Action, includes lessons the classifier could not check (marked `unchecked` in the report) because the owner validates the PR anyway, and holds back those it classifies as giving orders.
- **Issue link and form.** "Submit an issue" on the What's new page; `.github/ISSUE_TEMPLATE/wrong-lesson.yml` for a wrong community lesson.
- **Release.** One release (v1.99.0) carries all phases; `publish.ps1` regenerates `community-summary.json` before the tests.

## 14. Independent security review (2026-10-14) and what changed

A fresh reviewer tried to break the pipeline; confirmed problems were fixed, each with a test: look-alike letters, combining marks and spelled-out
phrases slipped past the screening (now a strict character allowlist, folding of spaced/leet text, more patterns); a rename could delete another
creator's file (`--no-renames`, NUL-separated names, no stripping of names); a symbolic link counted as a second handle (refused in CI and in the
intake); two handles confirmed a flagged lesson (now only clean lessons auto-confirm); a PR could edit its own check (now `pull_request_target`);
a revoked lesson could ship again (the curator prunes `community.json` and writes `community-revoked.json`, the kit filters revoked ids before import);
a revocation removed lessons your own map backs (now kept); the PR body took contributor text (code spans); `/community-state` had no CORS header.
Known limit: the screening is a blocklist plus an allowlist of characters; an attacker can still write a plain-English, keyword-free lesson that
is wrong or manipulative, which is why a single lesson stays a hypothesis, the owner validates every promotion, and revocation exists.
