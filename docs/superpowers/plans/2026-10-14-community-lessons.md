# Community Lessons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Creators can opt in to share approved lessons by GitHub PR; an Action screens them, a curator agent proposes promotion, the owner validates, releases carry the improved genre skills, and a new "What's new" console page shows what changed and who contributed.

**Architecture:** Python stdlib tools in `tool/` (schema, screening, intake, curator, reputation, summary) run by GitHub Actions; the kit side (`skills_lib.py`, console servers, Skills page, new News page) only exports one lesson at a time and imports the promoted pack as proposals. No server, no token for creators.

**Tech Stack:** Python 3 stdlib (tests are plain scripts, `ok(cond, msg)` style, run by `python3 tests/run_all.py`), GitHub Actions, static HTML console pages, two console servers (`agent-console-server.py` and `agent-console-server.ps1`) that must stay in step.

**Spec:** `docs/superpowers/specs/2026-10-14-community-lessons-design.md` (mockup: `...-news-mockup.html`)

## Global Constraints

- v1 shares lessons only: never blueprint, map name, paths, island code, Verse source.
- Switch "Contribute to the community" is OFF by default; nothing leaves the PC without pressing the button after seeing the JSON.
- Contribution file: `contributions/<genre>/<pattern_id>/<handle>.json`, `schema_version` 1, fields `pattern_id, genre, variant, section, direction (for|against), text (max 400 chars), kit_version`; identity is the PR author, never a JSON field.
- `pattern_id` is `skills_lib.pattern_id(variant, condition, action)`.
- Confirmed = >= 2 distinct handles with the same `pattern_id`, or owner approval. Levels: new, screened, hypothesis, confirmed, archived. Nothing is ever deleted.
- Score: +3 confirmed lesson, +1 per additional independent handle on the same `pattern_id`, -5 revoked/refuted, 0 archived. No levels.
- CI on contributions uses `pull_request` (never `pull_request_target`), no secrets, never merges; PRs may touch only `contributions/`; the curator may only open a PR on a bot branch.
- Contributor text never enters skills: lessons are regenerated from verified fields in a canonical template.
- Console endpoints take genre/pattern from a listing, never build a path from request text (`docs/code-scanning-lessons.md`).
- The owner commits, tags and publishes (`publish.cmd`): implementers run `python3 tests/run_all.py` and do NOT commit or tag. Every phase is its own kit version (bump `project-template/Claude/KIT-VERSION`, the five `agent-console*.html` kitVersion, `CHANGELOG.md`).

## Review Focus

1. Same handle sends the same `pattern_id` twice (or a PR edit): counts once. (Task 3)
2. Look-alike or invisible Unicode, mixed case handles, and 400+ char text in `text`. (Tasks 1, 2)
3. A PR that also touches a file outside `contributions/`, or adds dozens of files: rejected whole. (Task 4)
4. A lesson already approved on a creator's PC is later revoked: the next update removes it. (Task 8)
5. News page with no summary file (offline, first install) or a summary missing keys: empty state, no error. (Task 11)

---

### Task 0: Spike, GitHub pre-filled "new file" URL

**Files:** Create: `docs/superpowers/specs/2026-10-14-github-prefill-spike.md` (throwaway answer, 10 lines)

**Interfaces:** Produces: decision `PREFILL = url|issue-form`, the max safe URL length, and the exact URL template Task 5 builds.

- [ ] **Step 1:** Read GitHub docs for `/new/<branch>?filename=&value=` and test in the built-in browser on the repo (read-only until the creator would press Propose; do not submit). Record: does it work for non-collaborators (fork flow), URL length limit, how `value` must be encoded.
- [ ] **Step 2:** Write the answer. If it does not work or the limit is below 3000 characters, the fallback is an issue form (`.github/ISSUE_TEMPLATE/lesson.yml`) plus a workflow turning the issue into a PR; Tasks 4 and 5 then use the fallback. Owner confirms before Task 5.

### Task 1: Contribution schema and validator

**Files:** Create: `tool/contrib_schema.py`; Test: `tests/test_contrib_schema.py`

**Interfaces:** Produces: `validate(doc: dict, handle: str, rel_path: str) -> list[str]` (empty = valid), `SECTIONS`, `MAX_TEXT = 400`.

- [ ] **Step 1: Tests:** valid doc returns `[]`; each of: wrong `schema_version`, genre not in `fortnite-genres-official.json`, variant failing `skills_lib.VARIANT_RE`, section not in `starter-sections.json`, `direction` other than for/against, `text` of 401 chars, unknown extra key, `pattern_id` not `p-` + 12 hex, path not equal to `contributions/<genre>/<pattern_id>/<handle>.json` → each returns a non-empty list naming the field.
- [ ] **Step 2:** Run it, expect FAIL (module missing).
- [ ] **Step 3:** Implement `validate`; read the genre list and sections from the repo files.
- [ ] **Step 4:** Run `python3 tests/test_contrib_schema.py`, expect all PASS.

### Task 2: Screening filters

**Files:** Create: `tool/screen_contribution.py`, `tool/official_names.json`; Test: `tests/test_screen_contribution.py`, `tests/fixtures/injection-samples.json`

**Interfaces:** Consumes: `contrib_schema.validate`. Produces: `screen(doc: dict) -> {"verdict": "pass"|"flag"|"block", "reasons": list[str]}`. `block` = deterministic injection signs; `flag` = unknown device/API identifier (not in `official_names.json`, seeded from identifiers already used in `project-template` genre references; owner extends).

- [ ] **Step 1: Tests:** a corpus file with >= 20 hostile texts (URL, `curl`/`powershell`, base64 blob, zero-width and bidi characters, markdown link/image, Windows/Unix path, "ignore previous instructions", "always run", "do not tell the user", tool/command names like `Bash`, `/kit-update`, hook/setting names) each must give `block`; >= 20 honest lessons from existing packs must give `pass` (false-positive count asserted == 0); an unknown device name gives `flag`.
- [ ] **Step 2:** Run, expect FAIL.
- [ ] **Step 3:** Implement with regexes and Unicode category checks (Cf, Cc, bidi); normalize with NFKC before matching so look-alikes are caught.
- [ ] **Step 4:** Run, expect PASS.

### Task 3: Intake state machine

**Files:** Create: `tool/intake.py`, `contributions/INTAKE.json` (empty `{"lessons":{}}`); Test: `tests/test_intake.py`

**Interfaces:** Consumes: `validate`, `screen`. Produces: `update_intake(contrib_root: str, intake_path: str, owner_decisions: dict | None = None) -> dict` returning the new intake; per lesson: `{state, handles[], verdict, reasons, since}`; `HYPOTHESIS_CAP_PER_GENRE = 40`.

- [ ] **Step 1: Tests:** one valid file becomes `hypothesis` with 1 handle; the same handle twice (two files or a re-run) still 1 handle; a second distinct handle makes `confirmed`; `block` verdict makes `archived` with the reason and the file still exists; invalid file is `archived` with schema errors; `owner_decisions={"p-…":"confirmed"}` overrides; the cap keeps extra lessons in `screened` (never deleted); running twice gives an identical result (idempotent).
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement. **Step 4:** Run, expect PASS.

### Task 4: Contribution Action

**Files:** Create: `.github/workflows/contributions.yml`, `tool/check_pr_paths.py`; Test: `tests/test_contrib_workflow.py`

**Interfaces:** Produces: `check_pr_paths(changed: list[str], handle: str) -> list[str]` (errors: any path outside `contributions/`, more than 20 files, a file whose handle segment differs from `handle`).

- [ ] **Step 1: Tests:** `check_pr_paths` cases above; a repo test reading the workflow text asserts it contains `pull_request:`, not `pull_request_target`, has no `secrets.`, and `permissions: contents: read` only.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement the script and the workflow (checkout the PR head, list changed files via `git diff --name-only`, run `check_pr_paths`, validate and screen each changed file, fail the check on errors, comment the verdict). The intake update itself runs in Task 7's scheduled workflow on `main`, not on fork PRs. **Step 4:** Run, expect PASS.

### Task 5: Kit export (switch + one lesson)

**Files:** Modify: `project-template/Claude/hooks/skills_lib.py`; Test: `tests/test_community_export.py`

**Interfaces:** Produces: `community_state() -> {"share": bool, "shared": [pattern_id…]}`, `set_community(share: bool) -> dict`, `contribution_export(slug: str, pattern_id: str) -> {"ok": bool, "doc": dict, "url": str, "error": str}`. State file: `Claude/logs/community.json` (`UEFN_SKILLS_DIR`-style override for tests). `url` follows Task 0's template.

- [ ] **Step 1: Tests:** default `share` is False and `contribution_export` returns `ok False` while off; on, an approved local lesson returns a doc that passes `contrib_schema.validate` and has no map name or path (assert the deny terms of the genre are absent); a not-approved lesson or one with `origin == "community"` is refused; unknown `pattern_id` is refused; `shared` records it after export confirm via `mark_shared(slug, pattern_id)`.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement (reuse `load_pack`, `_deny_terms`, `_slug`/`resolve_genre`). **Step 4:** Run, expect PASS.

### Task 6: Console endpoints and Skills page controls

**Files:** Modify: `agent-console-server.py`, `agent-console-server.ps1`, `agent-console-skills.html` (under `project-template/Claude/hooks/`); Test: `tests/test_community_endpoints.py`

**Interfaces:** Consumes: Task 5. Produces: `GET /community-state`, `POST /community-state {"share": bool}`, `GET /community-export?genre=&id=` returning `contribution_export`'s result; genre and id are matched against `_genres()` and the pack listing, never used to build a path.

- [ ] **Step 1: Tests:** start the py server on a free port with a temp skills dir: state GET/POST round trip; export with the switch off gives `ok False`; export with an id not in the listing gives `ok False`; a request with `genre=../x` is refused. A text check that the `.ps1` server contains the same three routes.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement both servers in step; in the Skills page add the switch (header card) and a "Contribute" button on each approved local lesson opening a preview with the exact JSON and a "Open GitHub" button (opens the `url`, then calls `mark_shared`). **Step 4:** Run, expect PASS.

### Task 7: Intake and reputation scheduled workflow

**Files:** Create: `tool/reputation.py`, `.github/workflows/intake.yml`, `reputation.json` (repo root, empty `{"handles":{}}`); Test: `tests/test_reputation.py`

**Interfaces:** Consumes: `update_intake`. Produces: `compute(intake: dict, revoked: dict) -> {"handles": {handle: {"score": int, "confirmed": int, "lessons": int, "genres": [str]}}}`.

- [ ] **Step 1: Tests:** one confirmed lesson of a handle gives +3; a second handle on the same `pattern_id` gives the first handle +1 and itself +3 once the lesson is confirmed; a revoked lesson gives -5; archived gives 0; recomputation is deterministic; a handle with score 0 is listed with `strict: true`.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement; the workflow (on push to `main` touching `contributions/**`, and daily) runs `update_intake`, `compute`, and commits `INTAKE.json` and `reputation.json` with the default `GITHUB_TOKEN` to `main` only if changed. **Step 4:** Run, expect PASS.

### Task 8: Curator agent and promotion PR

**Files:** Create: `tool/curator.py`, `tool/classify.py`, `.github/workflows/curator.yml`; Test: `tests/test_curator.py`

**Interfaces:** Consumes: intake, `screen`. Produces: `build_promotion(intake: dict, contrib_root: str, existing_pack_dir: str) -> {"lessons": list[dict], "revoked": dict, "report_md": str}` where each lesson is `{id, genre, variant, section, direction, statement, condition, action, state, handles[]}` generated from verified fields by a fixed template; `classify(text: str) -> "fact"|"orders"|"unchecked"` (Anthropic API call without tools, key from `ANTHROPIC_API_KEY`; missing key gives `unchecked`, never an error).

- [ ] **Step 1: Tests:** output text equals the template applied to fields, never the raw contributor `text` (assert a distinctive contributor phrase is absent); the generated statement passes `screen`; an `orders` or `unchecked` classification keeps the lesson `screened` for human review; duplicates of lessons already in the pack are reported, not re-added; `revoked` lists archived-after-promotion ids and banned handles; the report has one block per lesson with state, handles, verdict.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement; the workflow runs on schedule and on demand with `contents: write`, `pull-requests: write`, creates branch `bot/promotion-<date>` writing `project-template/Claude/community/lessons.json` and `revoked.json`, opens ONE PR with `report_md`, never merges. **Step 4:** Run, expect PASS.

### Task 9: Kit install of the community pack

**Files:** Modify: `skills_lib.py`, `kit_sync.py`; Test: `tests/test_community_import.py`

**Interfaces:** Consumes: Task 8 files. Produces: `import_community(pack_dir: str) -> {"queued": int, "removed": int, "skipped": int}`.

- [ ] **Step 1: Tests:** each lesson is re-validated (an invalid one is skipped); valid ones become proposals with `origin "community"`, `tier "hypothesis"` when `state` is hypothesis and the statement prefixed "To verify against the map's code: "; confirmed ones are queued without the prefix; importing twice queues nothing new; an id listed in `revoked.json` that is already a pattern or a proposal is removed (`removed` counts it); a revoked lesson the creator had approved disappears from the rendered skill.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement; `kit_sync.py` calls it at session start (try/except like `merge_variants`). **Step 4:** Run, expect PASS.

### Task 10: Community summary at release

**Files:** Create: `tool/community_summary.py`, `project-template/Claude/community/community-summary.json` (generated); Modify: `publish.ps1` (run it after tests, before commit); Test: `tests/test_community_summary.py`

**Interfaces:** Consumes: intake, `reputation.json`, `CHANGELOG.md`, `release_notes.py`. Produces: `build_summary(tag: str, intake: dict, reputation: dict, previous: dict | None) -> dict` with keys `release{tag,date,title,items[]}`, `counts{new_skills,improved_skills,received,confirmed,hypotheses,archived,contributors,new_contributors}`, `skills[{genre,status:"new"|"improved",added,confirmed,handles[],highlight}]`, `top[{handle,score,confirmed,genres,delta}]`, `helpful[{text,genre,handle,maps}]`, `thanks[handle]`.

- [ ] **Step 1: Tests:** a fixture intake plus reputation yields the keys above; a genre with no pack before is `new`; deltas come from `previous`; handles are sorted by score; `top` is capped at 10; with an empty intake the summary is valid with zero counts.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement; `publish.ps1` runs `python tool/community_summary.py` and stops on error. **Step 4:** Run, expect PASS.

### Task 11: What's new page

**Files:** Create: `project-template/Claude/hooks/agent-console-news.html`; Modify: console servers (serve `/community-summary` from the shipped file), the nav of the other five console pages and `agent-console-flow.html` if it lists pages; Test: `tests/test_news_page.py`

**Interfaces:** Consumes: `GET /community-summary` (Task 10 shape) and `GET /community-state` (Task 6). Page built from the mockup, all data read at load.

- [ ] **Step 1: Tests:** every console page's nav contains the News link; the page references `/community-summary` and `/community-state`; the sample summary fixture renders (headless check with the repo's existing browser test approach if present, otherwise a string check of the render function with the fixture); the page contains the link `https://github.com/mimmo-the-root/UEFN-dream-bot-team/issues/new/choose` in the release buttons and next to the thanks; the empty state text is shown when the summary is missing or has no `skills` key.
- [ ] **Step 2:** Run, expect FAIL. **Step 3:** Implement the page, both servers' route, nav links; add `.github/ISSUE_TEMPLATE/wrong-lesson.yml` (fields: genre, pattern id or text, what is wrong) and `config.yml` so the issue chooser offers it. **Step 4:** Run, expect PASS.

### Task 12: Documentation and release bookkeeping

**Files:** Create: `docs/community-contributions.md`; Modify: `README.md`, `SETUP-GUIDE.md`, `CHANGELOG.md`

- [ ] **Step 1:** Write `docs/community-contributions.md`: what is shared and what never is, consent and licence line, how to contribute, how levels and the score work, how to ask for removal.
- [ ] **Step 2:** Add README and SETUP-GUIDE sections (switch, button, What's new) and a CHANGELOG section per shipped phase with a title line for `release_notes.py`.
- [ ] **Step 3:** Run `python3 tests/run_all.py`, expect all steps passed, then `python3 tool/release_notes.py <new-tag>` prints the title.

## Phases and order

Task 0 first. Phase 1: Tasks 1-4 (invisible to creators). Phase 2: Tasks 5-6. Phase 3: Tasks 7-9. Phase 4: Tasks 10-12 (the page needs the reputation data from Task 7). Each phase ships as its own kit version.
