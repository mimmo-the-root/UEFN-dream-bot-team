# Changelog

## v1.79.11

- Added a "Recent roadmap tasks" card to the Docs & Status console
  (`agent-console-docs.html`), same readable-list treatment as the existing "Recent bug backlog"
  card: code — description, with a status badge (Done/In progress/Blocked/To do/Out of scope,
  reusing the existing `statusBucket()` bucketing) and a priority pill (MVP/nice-to-have/backlog/
  out of scope, normalized from ROADMAP.md's free-text Priority column the same way
  `bugSeverityPill()` already normalizes BUGS.md's Severity column). Still-outstanding tasks
  (in progress/blocked, then to-do) surface first, done and out-of-scope rows sink to the bottom;
  shows up to 10 rows with a link to the full ROADMAP.md. Previously the roadmap card only ever
  showed a progress ring and counts, never the individual tasks themselves.

## v1.79.10

- **Root cause found and fixed** for the Control Tower token gauge showing a stale active
  agent/station (e.g. "QA-REGRESSION") while the header above it correctly said "idle".
  `agent-console.html` (main console) has always pruned `active` stack entries whose `start`
  event never got a matching `stop` within 45 minutes (`STALE_ACTIVE_MS`, in `tickTimers()`) —
  this handles a session/subagent that crashed or was killed before its `SubagentStop` hook
  fired, which otherwise leaves a permanent orphaned entry. `agent-console-flow.html` never had
  this pruning, so a single orphaned start from days earlier could pin its gauge/truck/station
  rows to that agent indefinitely. Confirmed against the real project's `agent-console.jsonl`:
  several `start` events (qa-regression, verse-reviewer, intent-reviewer, an "unknown"-agent
  entry) going back to Sep 5 had no matching `stop` anywhere in the log. Added the same
  `STALE_ACTIVE_MS` (45 min) pruning to `agent-console-flow.html`, run every tick.
- Also fixed the stop-event matching in `agent-console-flow.html` to close the *most recent*
  unmatched start for an agent (LIFO) instead of the oldest (`findIndex` → manual reverse scan) —
  matters once stale/orphaned entries can coexist with a fresh, genuinely-running call for the
  same agent id.

## v1.79.9

- Added a visible version tag next to the title on the Flow of Flows console
  (`agent-console-flow.html`), matching the main console's existing one. The user reported the
  token gauge still showing a stale reading after 6 hard refreshes even though the v1.79.8 fix
  was confirmed correct and present on disk — with no version tag on this page, there was no way
  to tell whether the browser tab was actually loading the fixed file or a stale
  server/browser-cache copy. This tag makes that a glance, not a guess (see the main console's
  own header comment on why this exists).

## v1.79.8 — Control Tower gauge stuck showing a stale "current" reading at idle

Found by the owner comparing a live screenshot against `agent-console-flow.html`'s Control Tower
card: the header correctly read "CONTROL TOWER — idle" / "no active task" (green LED), but the
token-usage gauge directly below it still showed a non-zero needle, "65122.0K tok" and station
"QA-REGRESSION" — implying that station was actively burning tokens right now, contradicting the
header one line above it.

Root cause, in `pollTokensGauge()`: the needle angle, station label, and pulse glow were already
correctly gated on `topAgent` (the same `active.length ? active[active.length-1].agent : null`
check `refreshStations()` uses to drive the header), and correctly went to their idle state when
`topAgent` was falsy. But `readout.textContent = (t.total/1000).toFixed(1) + 'K tok'` ran
*unconditionally*, before that idle branch — so once any station had run and pushed a real token
total, the numeric readout kept displaying that last-seen total forever, never resetting, no
matter how long the system had been idle. It wasn't a stale-cache bug; it simply never had a code
path that cleared it.

Fix: moved the readout update inside the same `if (topAgent) { … } else { … }` branch already
driving the needle/station/pulse, using the exact same idle signal the header consumes — no new or
duplicate "is anything active" check was introduced. When idle, the readout now shows `0 tok` and
the station shows `idle`, matching the header directly above it. `sessionMaxTokens` (the
`maxRecorded`-style running max used to scale the needle's swing) is untouched by this fix and is
never reset on idle — it's explicitly a persistent scaling reference, not a live reading, and the
`tg-max` "session total" label keeps showing it across idle periods, exactly as intended.

Also bumped `KIT_VERSION` in `agent-console.html` (unrelated file, same kit) to keep the kit-wide
version number in step with this fix.

## v1.79.7 — Bug backlog card: overlong free-text Severity broke row layout

Found by the owner comparing a live screenshot against `renderBugBacklog()`'s output on the real
`root_harrow_TWD` `BUGS.md`: the bottom 4 rows (B-007..B-004) rendered a consistent one-line
`[severity pill] [status badge] [title]` layout, but the top 2 rows (B-009, B-008) showed an
overlong pill wrapping the title onto its own line below. The row template's HTML is identical and
unconditional for every row — this was not a structural markup difference, purely content-driven
wrap: the pill used to dump the raw `Severity` cell straight in (lowercased, otherwise unmodified).
Most rows have a clean one-word Severity (`Major`, `Minor`, `Non-blocking`), but on a real
long-running project that column is sometimes free text blurring severity and status together, e.g.
B-009's real cell is `Major (was reopened 2026-09-09; RESOLVED 2026-09-10)` and B-008's is `Was
blocking (sole remaining open item on T-028 — part (b) PASSed 2026-09-08)` — both far too long for a
pill, and B-008's even reads as a status phrase rather than a severity word. **Fix**: added
`bugSeverityPill()`, a keyword-match bucketer (same approach as the existing `bugStatusBadge()`) that
maps anything containing "block" (but not "non-block") to `blocking`, "major" to `major`, "minor" to
`minor`, "non-block" to `non-blocking`, empty to `unspecified`, and anything else to its first word
as a short fallback — the extra parenthetical context is dropped from the pill (it's redundant with
"Probable cause"/the full BUGS.md) and kept only in the pill's `title` tooltip. Verified against the
real B-004..B-009 rows: B-004/B-005/B-006/B-007 = `Non-blocking` → pill "non-blocking" (grey);
B-008 = `Was blocking (...)` → pill "blocking" (red); B-009 = `Major (...)` → pill "major" (amber).
All six rows' Status column is `Closed` → green "Resolved" badge in every case, and all six now
render the identical `pill → badge → title` single-line layout regardless of Severity cell length.

## v1.79.6 — Four real-project parser/UX bugs found by hand-verifying against a live ROADMAP.md/STATUS.md/BUGS.md

All four found by the owner testing `agent-console-docs.html` live against a real, long-running
project (`root_harrow_TWD`) and hand-counting the ground truth from the real docs.

**1. Task count was off by one, and "remaining" silently included Out-of-scope rows.**
`parseTableAfterHeading()`'s `looksLikeRowStart()` used to require the row's OWN opening line to
both start AND end with `|` (`/^\|.*\|\s*$/`), on the assumption a row always fits on one physical
line. A row whose last cell is itself long enough to contain real line breaks (long acceptance-
criteria prose, same shape the continuation-line handling already supports) opens with `| T-053 |
...` but that first physical line does not end with `|` — the closing `|` only appears several
lines later. That made the row's own first line fail the check and fall into the "continuation of
the previous row" branch instead, silently merging all of T-053 into T-052's last cell and dropping
it from the table entirely (confirmed against the real file: 64 real task rows parsed as only 63,
missing exactly T-053; not a T-005-shaped "the row doesn't exist" situation). **Fix**: row starts
are now recognized purely from the opening `| <ID>` shape (`/^\|\s*[A-Za-z]{1,4}-\d+\b/`), no
longer requiring the same physical line to also close with `|`. Separately, `statusBucket()` only
recognized done/active/blocked and defaulted everything else (including a deliberate "Out of
scope"/"Fuori scope" status) to "todo", so the hero card's "X remaining" summed Da fare + Out of
scope into one bucket. `statusBucket()` now returns a dedicated `"outOfScope"` bucket, and the
"remaining" count in `renderHeroInner()` only sums todo + active + blocked. Verified against the
real ROADMAP.md: 64 rows total, 53 Fatto, 6 Da fare, 5 Out of scope (53 + 6 + 5 = 64) — the card
now reads "53 of 64 tasks Done" / "6 tasks remaining" instead of "52 of 63 Done, 11 remaining".

**2. "Last update" showed a stale, months-old "In progress" line instead of the current one.**
The "In progress:" extraction used to run `/\*\*In progress:\*\*\s*([^\n]+)/i` against the WHOLE
`status.content`, requiring a BOLD `**In progress:**` label. A real STATUS.md's `## Current state`
section — documented in the file's own header comment as "REPLACED on every update", i.e. the only
authoritative snapshot — writes this as a plain, unbolded `In progress: ...` line, so the regex
never matched there and instead matched the first BOLD `**In progress:**` occurrence anywhere later
in the file, typically a stale dated Log entry near the bottom (confirmed: a real file's Log
contained `**In progress:** none — T-011 closed Fatto ... No task currently "In corso.")_`, which
the console was surfacing as if it were current). **Fix**: the extraction now first locates the
`## Current state` heading, scopes the search to that section only (bounded by the next `##`
heading), and matches `In progress:` with or without bold markers.

**3. "0 open bugs" showed "No bugs logged yet." even when bugs exist and are simply all resolved.**
`renderHeroInner()`'s open-bugs breakdown used the same fallback copy for "BUGS.md has no rows at
all" and "BUGS.md has rows but none are currently open" — misleading in the (common, healthy) case
where a project's backlog is fully resolved. **Fix**: the fallback now checks the unfiltered
backlog row count separately and shows "No open bugs right now — all logged bugs are currently
resolved." when bugs exist but none are open, reserving "No bugs logged yet." for a genuinely empty
Backlog table.

**4. Bug backlog card showed the oldest bugs (file order), not the most relevant/recent ones.**
`renderBugBacklog()` used to be `rows.slice(0, 6)` — literally the first 6 rows in file order,
i.e. the oldest bugs by id, regardless of how many newer or still-open bugs existed further down a
real BUGS.md. **Fix**: rows are now sorted before slicing — Open/Blocked bugs first (reusing the
existing `bugStatusBadge()` bucketing), "No status"/"In progress" next, Resolved last, and within
the same bucket the higher bug number (a safe structural proxy for "more recent", since ids are
assigned sequentially) sorts first, rather than parsing dates out of free-text Status/Probable
cause prose. On the real BUGS.md (10 rows, all Resolved) this changes the displayed set from
B-001..B-005/B-004b to B-004..B-009 — the six most recently-numbered bugs.

`KIT_VERSION` bumped to `v1.79.6` in both `agent-console.html` copies (`root_harrow_TWD`'s deployed
copy and the kit template, kept in sync); `agent-console-docs.html` fixes applied identically to
both copies (verified byte-identical after the change).

## v1.79.5 — Bug backlog: added a status badge alongside the severity pill

The "Recent bug backlog" card (`agent-console-docs.html`) showed only a severity pill (blocking/
major/minor/non-blocking) per bug — no indication of whether the bug was resolved, still open, or
in progress, even though the real `## Backlog` table already has a `Status` column and
`parseTableAfterHeading()` was already capturing it generically into `row.status` (via its
header-driven `row[header] = cell` parsing) — `renderBugBacklog()` just never displayed it.

Real Status cells are free text the project owner writes, not a fixed enum (mixed English/
Italian, e.g. "Closed — RISOLTO 2026-09-17, re-verified not re-fixed", "Open — coder adds on next
touch of this file", "Was blocking (sole remaining open item on T-028 — part (b) PASSed
2026-09-08)"). **Fix**: new `bugStatusBadge()` buckets a raw Status cell into a small badge,
checked in this order: (1) starts with "Closed" or contains "Risolto"/"Resolved" → green
"Resolved" (checked first so "...; T-028 has no other open item" isn't misread as still-open just
because "open" appears later in the text); (2) starts with "Open" → amber "Open"; (3) contains
"blocking" but not "non-blocking" (e.g. old "Was blocking (...)" rows with no leading Closed/Open
marker) → red "Blocked"; (4) anything else (or empty) → grey, showing the first few words of the
raw cell instead of hiding it. The badge (small dot + label, rounded-rect shape) renders right
after the existing round severity pill on the same line so the two are never visually confused;
`.bugrow` gained `flex-wrap:wrap` so long titles don't get cramped. Only `parseBugsBacklog()`'s
`## Backlog` table rows are affected — the separate "Newly reported (to be triaged)" free-text
section (not parsed into rows at all) is untouched. `KIT_VERSION` bumped to `v1.79.5`.

## v1.79.4 — Docs & Status console: three real parsing bugs found in live testing against a large real project

Real user bug report from live testing the Docs & Status console (`agent-console-docs.html`)
against `root_harrow_TWD`'s actual `Claude/docs/ROADMAP.md` (151KB, 63 real task rows) and
`STATUS.md` (256KB, real log history) — three concrete wrong-numbers/wrong-data issues, page
still loaded fine, nothing crashed:

**1. "Roadmap progress" showed "0 of 24 tasks Done"** while the timeline below correctly showed
most tasks as done. Root cause: the done/in-progress/todo counting logic (`t.status.toLowerCase()
=== "done"`) matched the literal English word only — this real project's rows use the Italian
status word "Fatto" (also "In corso" / "Da fare" / "Bloccato"), which is the PROJECT OWNER's own
data, not something we should force-translate. **Fix**: new `statusBucket()` helper buckets a raw
Status cell into done/active/blocked/todo case-insensitively, recognizing English and Italian
variants at minimum ("Done"/"Fatto", "In progress"/"In corso", "To do"/"Da fare",
"Blocked"/"Bloccato"); used everywhere a status was being compared (progress ring/count, timeline
dot color, current-task detection).

**2. Timeline stopped at T-025** even though real tasks go to T-065+. Root cause, two compounding
issues in `parseTableAfterHeading()`: (a) it stopped at the first blank line, but this real
ROADMAP.md has blank lines between rows (the owner groups rows visually by MVP/Nice-to-have/etc.
— still one continuous markdown table); (b) after fixing (a), a single very-long row (T-053's
acceptance-criteria cell) turned out to contain real embedded newlines instead of staying on one
markdown line, which also looked like "end of table" to the old strict per-line row matcher.
**Fix**: the parser now skips blank lines, recognizes a new row only when a line's first cell
looks like a real id (`T-053`, `B-001: …`), and treats any other non-heading line as a
continuation of the previous row's last cell — the table now only ends at a real heading or a
genuinely blank tail. Verified this reaches all 63 real rows through T-065. On top of that, the
timeline no longer dumps every parsed task unwindowed: `renderTimeline()` now shows a ~12-task
window centered on the current (In corso/In progress) task — a handful of done tasks leading up
to it, the current task, and a few upcoming ones — with a small note when the view is windowed,
since the strip itself already scrolls horizontally.

**3. "Last update" showed a stale/wrong entry** instead of STATUS.md's real newest log entry.
Root cause: the `_(updated: ...)_ ` regex required an exact `)_` right after the date to close
markdown italics, which this real project's long "Current state" prose (its own parentheses
inside) doesn't reliably produce — it silently returned `null` and fell back to a *file-wide*,
non-anchored `###` search with no guarantee it was even inside the `## Log` section. Per
STATUS.md's own documented convention ("New entry AT THE TOP on every update. Don't delete
history."), the correct source is the **first** `### YYYY-MM-DD` heading inside the `## Log`
section specifically — not the "Current state" snapshot block above it, and not any other `###`
occurrence. **Fix**: explicitly locate `## Log` first, then take the first dated heading after it.

All three fixes are in `Claude/hooks/agent-console-docs.html` (kit `project-template/` copy and
`root_harrow_TWD`'s deployed copy, kept in sync); `KIT_VERSION` bumped to `v1.79.4` in both
`agent-console.html` copies.

## v1.79.2 — Docs & Status console: fixed the real infinite-loading bug and removed all remaining mockup data

Real user bug report (live testing with screenshots) of the Docs & Status console
(`agent-console-docs.html`), two issues:

**1. "loading…" that could hang forever.** `fetchDoc()`'s `fetch("/doc?name=...")` had no bounded
timeout — a `try/catch` covered a thrown/rejected fetch, but nothing covered a request that just
never resolves (server mid-restart, stalled connection, etc.), which is a real gap even though it
did not reproduce in either of the two hypotheses named in the report: the server's `/doc` route
itself was already correct for every key including `spec` (whitelist lookup, always returns `200`
+ JSON, never hangs), and opening the page via `file://` already failed fast with a clear
"could not reach the local server" message rather than hanging — both verified with Playwright
before and after this fix. **Root cause actually found**: the markdown-table parser's separator-row
regex, `/^\|[\s:-]+\|\s*$/`, only matched a single-column separator like `|---|`, not a real
multi-column one like `|---|---|---|---|---|` (the `|` inside a character class only matched a
literal pipe once, not "one or more pipe-delimited groups"). Every doc's table (ROADMAP.md's Tasks
table, BUGS.md's Backlog table) silently failed to render as a table in `mdToHtml`, and once the
same parser was reused (below) to drive the hero/timeline/bug-backlog cards, those came back
empty. **Fix**: broadened the regex to `/^\|[\s:|-]+\|\s*$/` (both places it's used), and added a
6-second `AbortController` timeout to `fetchDoc()` so no fetch anywhere on this page can leave a
card on "loading…" indefinitely regardless of cause — success, honest-empty ("not created yet"),
and error ("could not reach the local server") are now the only three end states, all reachable
within a couple of seconds.

**2. Hardcoded mockup data still displayed as real.** Found and removed every one of these
leftover sample values, none of which were ever wired to a real file:
- "Recent bug backlog": `Storm collider not deactivating at round end`, `Respawn point duplicated
  in Zone 2`, `Missing logger in 3 custom files`, `DemoDisplay stand misaligned`
- Roadmap progress ring: hardcoded `68%`, `17 of 25 tasks Done`, `MVP release: 3 tasks remaining`
- Open bugs hero card: hardcoded `4` / `🔴1 blocking · 🟠2 major · 🟡1 minor`
- Last update hero card: hardcoded `Today, 14:20` / `planner-docs · T-017 marked Done`
- Roadmap task timeline: hardcoded nodes `T-013`…`T-020` with fake feature names ("Elimination
  Manager", "Player Spawner", "Item Granter", "Respawn cooldown UI", "Storm Controller",
  "DemoDisplay")

All five are now driven by real parsing of `Claude/docs/ROADMAP.md`'s Tasks table and
`Claude/docs/BUGS.md`'s Backlog table via the same `/doc?name=` mechanism the doc-card previews
already used (`renderHero()`, `renderTimeline()`, `renderBugBacklog()`). Each shows an honest
empty state ("ROADMAP.md has not been created yet" / "No bugs logged yet") when the file doesn't
exist or has no rows yet — never sample content.

**Verified with Playwright (chromium)** against the real running `agent-console-server.py`:
- Fresh project, no `Claude/docs/*.md` at all: every card/section shows its honest empty state
  within ~2.5s, zero `pageerror`/console errors.
- Populated project with distinctive test data (`ROADMAP.md` with tasks `T-101`–`T-106`, 3 Done /
  1 In progress / 2 To do; `BUGS.md` with `TESTBUG-Widget alignment off by 4px` (blocking),
  `TESTBUG-Save button unresponsive` (major), `TESTBUG-Tooltip wraps oddly` (minor); `STATUS.md`,
  `SPEC.md`, `RETENTION-NOTES.md`, `RELEASE-READINESS.md` each with a distinctive `TEST*-marker`
  string): the progress ring showed `50%` / `3 of 6 tasks Done`, open bugs showed `3` /
  `🔴1 blocking · 🟠1 major · 🟡1 minor`, the timeline rendered all 6 real task IDs with correct
  Done/In progress/To do dots, the bug backlog listed all 3 real `TESTBUG-` entries with correct
  severity pills, and all 6 doc-card preview modals (including SPEC.md) opened and rendered the
  real marker text within ~1.2s — no stuck loading anywhere, matching the test data exactly.
- `file://` (no server running): every card and the preview modal show
  "Could not reach the local server" / "disconnected — is agent-console-server running?" within
  seconds, not indefinite "loading…".

`KIT_VERSION` bumped to v1.79.2.

## v1.79.1 — Fixed Cost of Asking's halt→resume wait time (was measuring the wrong thing)

Independent QA re-verification of v1.79.0 found that the "Cost of Asking" card's average wait
time was silently wrong. It used "the next log entry of any kind after a halt" as the resume
signal, but that's not actually a safe signal: every agent's own `SubagentStop` hook logs a
`stop` line a moment after that agent finishes producing its halt verdict, as it exits — this is
the halting agent wrapping up its own invocation, not the owner responding. In a full simulated
run (intent-gate pass → coder → qa-regression reject → coder retry → qa-regression pass →
compliance-reviewer halt → **47-minute real gap** → coder resumes → compliance-reviewer pass →
release-gate pass), the card showed "~0.5 min/time" instead of the real ~47 minutes, because it
was measuring time-to-own-stop-hook, not time-to-owner-response.

**Fix**: the resume signal is now the next genuine `start` event (any agent) after the halt,
since a new invocation can only begin once the owner (or a scheduled resume) has actually acted —
falling back to the next entry only if the log ends right after the halt with no later start at
all. Re-verified against the same simulated run: now correctly shows "~47.0 min/time".

Also independently re-verified against a fresh/empty project (all 4 cards show their honest empty
states, zero console errors, zero unhandled 404s), against malformed/edge-case log lines (an
orphaned `verdict` with no matching `start`, an out-of-order-appended event, and a `verdict` with
an unparseable `ts`) — the UI degrades gracefully in all three cases, no crash, no silent
miscounting of the well-formed data — and against all 6 updated agent `.md` files, whose logging
instructions use one consistent event schema each with no duplicate/conflicting logging step.

`KIT_VERSION` bumped to v1.79.1.

## v1.79.0 — Flow console's 4 bottom cards now real, not sample layouts

v1.78.0 wired the Flow console's truck/gauge/Control Tower to real `/log`/`/tokens`/`/active-task`
data but left the 4 bottom cards (Decision Log, Model Tiers, Cost of Asking, Gate Outcomes) as
explicitly-labeled "(sample layout)" placeholders, because no agent logged the verdict/model-tier
data those cards need. This release adds that real data and wires the cards to it.

**New log event types** (appended to `Claude/logs/agent-console.jsonl`, same append-only
JSON-lines file and mechanism `agent-console-log.sh`/`.ps1` already use for `start`/`stop`):
- `{"agent":...,"event":"verdict","result":"pass"|"reject"|"halt","task":"<id>","ts":...,"detail":"..."}`
  — now logged by `intent-gate` (CLEAR→pass, AMBIGUOUS→halt), `intent-reviewer` (PASS→pass,
  REJECTED→reject, 5th-attempt escalation→halt), `compliance-reviewer` (same pattern as
  intent-reviewer), `qa-regression` (pass/reject based on whether it found blocking/major
  problems), and `release-gate` (READY[/WITH RESERVATIONS]→pass, NOT READY→reject). See each
  agent's own `.md` under `user-level-agents/` for the exact logging step added.
- `{"agent":"coder","event":"model_tier","tier":"from-scratch"|"second-brain"|"verse-patterns","task":"<id>","ts":...}`
  — logged once per task by `coder`, right after it settles on an implementation approach in its
  existing Step 0.5 (reused this kit's own existing vocabulary — second-brain query, verse-patterns
  reference, or neither — instead of inventing a generic cheap/mid/frontier scale).

**Flow console (`agent-console-flow.html`)** — all 4 cards now read real events from `/log`:
- **Decision Log**: the most recent real `verdict` events, colored by result (pass=green,
  reject=red, halt=magenta), same keyword styling as before. Empty state: "No decisions logged
  yet".
- **Model Tiers**: real percentage breakdown of `coder`'s logged `model_tier` events. Empty state:
  "No model-tier data yet".
- **Cost of Asking**: real halt count from `verdict` events with `result:"halt"`, and a real
  average wait time computed halt→resume, where "resume" is the kit's natural existing signal (the
  next log entry of any kind after a halt, since nothing else happens while the pipeline is
  genuinely waiting on the owner) — no dedicated resume event was added because none was needed.
  Empty state: "No halts recorded yet — nothing has required your input".
- **Gate Outcomes**: real pass/reject/halt counts aggregated across all gate/reviewer agents.
  Empty state: "No gate verdicts logged yet".
- The "(sample layout)" labels and the disclaimer text saying this data doesn't exist are gone;
  replaced with a comment describing the real data source for future maintainers.

**Audit of the rest of the console system (agent-console.html, -stats.html, -docs.html,
-flow.html)** for other fake/decorative elements: found none beyond what's already fixed. The
remaining `Math.random()` uses (missile-launch particle bursts, explosion-arc curvature) are
explicitly-documented cosmetic effects triggered only by real start/stop/verdict events, not stand-
ins for unavailable data, so they were left as-is.

`KIT_VERSION` bumped to v1.79.0.

## v1.78.0 — Docs & Flow consoles wired to real project data (they were mockups)

The two new consoles (`agent-console-docs.html`, `agent-console-flow.html`) looked finished but
never actually read anything real — every number and animation was hardcoded sample data or a
timer loop. This release wires both to the exact same real data sources
`agent-console.html` already uses (`/log`, `/tokens`, `/active-task`, and a new `/doc` endpoint),
instead of inventing a separate mechanism.

**Docs & Status console:**
- "Recent status" now shows the real "## Current state" section parsed out of the project's
  actual `Claude/docs/STATUS.md` (was: three hardcoded lines that never changed).
- Fixed SPEC.md, RETENTION-NOTES.md and RELEASE-READINESS.md not opening at all — they had no
  click handler and no data entry in the old hardcoded `DOCS` object, so clicking them did
  nothing. All six docs now fetch their real content from the new `/doc?name=<key>` server
  endpoint (added to both `agent-console-server.py` and `.ps1`) and render it (a small built-in
  markdown→HTML pass, plus the existing raw-markdown tab). A doc that genuinely doesn't exist yet
  in a fresh project (no SPEC.md until an agent writes one, for example) now shows a clear "not
  created yet" state instead of silently doing nothing — the doc-grid cards also dim and relabel
  themselves the same way on load.
- Removed the left icon-rail: every icon but "Status" was a dead, non-functional button. The main
  docs table/grid is now centered in the page with the freed-up width instead of sitting
  left-aligned next to empty space.

**Flow of Flows console:**
- The truck no longer animates on a fixed timer regardless of real activity. It now polls `/log`
  every second (same event stream and `active`-stack logic `agent-console.html` uses) and sits
  parked at the start of the belt, with every build/gate/ship machine effect dark, whenever no
  real agent in the 5-stage pipeline (`intent-gate → coder → intent-reviewer →
  compliance-reviewer → planner-docs`, matching the main console's own `MINIFLOW_PIPELINE`) is
  actually active. It only moves to, and animates, whichever real stage is currently running.
- The Control Tower's station-row highlighting no longer cycles through stations on a timer. It
  now reflects whichever real agent is topmost in the live `active` stack — genuine idle (no
  highlighted station, no cycling) when nothing is running.
- The token-usage gauge no longer performs a canned sweep with random numbers. It now reads the
  same `/tokens` session-cumulative total the main console's "Tokens this session" stat uses, and
  only shows a needle position/pulse while a real agent is active; at idle it sits flat at zero
  with "no usage data yet" / "idle" rather than implying false activity. **Honest limitation:**
  this kit does not currently log token usage per-agent or per-task, only a session-wide total —
  so the gauge shows the real session total scaled against its own session-high, not a genuine
  per-station breakdown. Real per-agent token metering would need a new logging hook (e.g. tagging
  `agent-console-tokens.ps1`/`.sh`'s writes with whichever agent is topmost in `/log`'s `active`
  stack at that moment) — left as documented future work rather than faked here.
- The four "Decision log / Model tiers / Cost of asking / Gate outcomes" cards and the top
  shipped/steps/decisions/sent-to-you counters remain illustrative sample layouts, labeled as such
  in the page: this kit does not yet log a structured per-decision audit trail or model-tier
  choices anywhere, so there's no real data to wire them to yet.

`KIT_VERSION` bumped to v1.78.0.

## v1.77.2

- Fixed: Docs and Flow console tabs did not open — nav wiring bug. The main console and Stats
  page nav used server-root-absolute hrefs (`/`, `/stats`, `/docs`, `/flow`), which resolve to a
  nonexistent local path when `agent-console.html` is opened directly (`file://`) instead of
  through `agent-console-server.py` — clicking Docs/Flow silently failed with
  `ERR_FILE_NOT_FOUND`. Also, the reverse links on the new Docs/Flow pages (plain relative
  filenames like `agent-console-stats.html`) fell through the server's catch-all route and
  rendered the wrong page when served over `http://`. Both are now unified: every console page's
  nav uses plain relative filenames, and `agent-console-server.py`'s `do_GET` explicitly maps both
  the short routes (`/stats`, `/docs`, `/flow`) and the filename routes
  (`agent-console-stats.html`, `agent-console-docs.html`, `agent-console-flow.html`) to the correct
  file, so navigation works identically via `file://` and via the local server. Also found and
  fixed `agent-console-server.ps1` (the Windows/PowerShell server), which never received `/docs`
  and `/flow` routes when those pages were added — only `/stats` existed there; both routes (and
  their filename aliases) are now added, matching the Python server. `KIT_VERSION` bumped to
  v1.77.2.

## v1.77.1 — Full Italian-to-English translation pass

Completed full Italian-to-English translation across the kit, including previously-intentional
status vocabulary (`Da fare`/`In corso`/`Bloccato`/`Fatto` → `To do`/`In progress`/`Blocked`/`Done`;
`CHIARO`/`AMBIGUO` → `CLEAR`/`AMBIGUOUS`) per explicit user request ("TRADUCI TUTTO" — translate
everything, no exceptions). This supersedes the v1.77.0 judgment call to leave that vocabulary
alone as an "intentional shared convention" — the owner's instruction here is total and overrides
that reasoning.

- Updated `ROADMAP.md`/`STATUS.md` templates, `CLAUDE.md`, `user-level-memory/CLAUDE.md`, and every
  agent file (`coder.md`, `intent-gate.md`, `intent-reviewer.md`, `planner-docs.md`,
  `project-bootstrap.md`, `release-gate.md`) that referenced the old Italian status/verdict labels
  as literal strings, so the enum values stay consistent everywhere they're written, compared, or
  displayed.
- Fully translated several `user-level-skills/*/SKILL.md` files that were still entirely in
  Italian (`fortnite-marketing-launch`, `fortnite-competitor-analyzer`, `fortnite-retention-
  gamedesign`, `fortnite-social-trailer`, `fortnite-thumbnail-pro`, `fortnite-title-description`,
  `fortnite-update-writer`, `fortnite-analytics-coach`), including their `description:` frontmatter
  and "Parla in italiano" style instructions (now "Speak in English").
- Translated the `genre/roguelike/` and `genre/survival/` skill trees (`SKILL.md`, `references/
  variants.md`, `references/evidence-shared.md`, and every `variants/*/evidence.md` file), and
  `genre/fortnite-tags-known.json`'s Italian internal notes/mechanism fields.
- Translated `second-brain-template/CLAUDE.md` in full, including its prescribed article section
  headers (`## Punti chiave` → `## Key points`, `## Connessioni e potenziali` → `## Connections
  and potential`, `## Fonti` → `## Sources`, etc.), frontmatter field names (`fonti` → `sources`,
  `visto_su` → `seen_on`, `data_creazione`/`data_aggiornamento` → `date_created`/`date_updated`,
  `versione_implementazione` → `implementation_version`), file names (`indice.md` → `index.md`,
  `indice_wiki.md` → `wiki-index.md`, `frontiere-conoscenza.md` → `knowledge-frontiers.md`,
  `evoluzione-kb.md` → `kb-evolution.md`), and the `sintetizza` command alias (now `synthesize`) —
  with matching updates in `second-brain-template/README.md`, the release-notes sync scripts, and
  `second-brain-librarian.md` so every cross-reference stays in sync.
- Fixed remaining stray Italian strings in `agent-console-stats.html` (chart title/empty-state
  text) and a couple of quoted owner remarks and file-path examples elsewhere.
- `KIT_VERSION` bumped to v1.77.1.

## v1.77.0 — Two new Agent Console views: Docs & Status navigator, Flow of Flows pipeline

Two new console pages, approved across many mockup rounds in `/tmp/console-mockups/` and
`/tmp/flow-jev/conveyor-5.html`, are now real files in `Claude/hooks/`, wired into the same
`view-switch` nav pattern and `agent-console-server.py` routing as the existing Console/Stats
pages. Also fixed stray Italian UI text the owner spotted on the Stats page.

**What changed:**
- New `Claude/hooks/agent-console-docs.html` ("Docs & Status Console"): icon rail, hero cards (SVG
  roadmap-progress ring, open-bug count, last update), a horizontal timeline of ROADMAP.md tasks
  with hover tooltips, a bug-backlog card, and a docs grid over `Claude/docs/*.md`
  (STATUS.md/ROADMAP.md/BUGS.md/SPEC.md/RETENTION-NOTES.md/RELEASE-READINESS.md, matching
  `planner-docs`'s real file ownership) with a raw-markdown vs. rendered-HTML preview toggle.
  The rendered-HTML view is a snapshot: it regenerates when a task starts, not live on every page
  open and not only when `planner-docs` writes — see the new Step 0 item 6 in
  `user-level-agents/coder.md`, added right after it writes `Claude/docs/.active-task`.
- New `Claude/hooks/agent-console-flow.html` ("Flow of Flows Console"): the assembly-line conveyor
  pipeline (only the approved "Assembly line" variant — the mockup file held 5 switchable
  concepts, only one shipped), 4 color-coded zones (INTAKE/BUILD/GATE/SHIP) with the kit's real
  per-agent icons/colors (matches the registry in `agent-console.html`: coder alone in BUILD with
  a 🏭 factory + welding sparks, compliance pre-check/MCP place gate/qa-regression/intent-
  reviewer/compliance-reviewer clustered in GATE, planner-docs in SHIP with a sealed-crate ✅), a
  nose-forward truck that travels the belt and pauses at whichever station is active, a Control
  Tower (chief-of-staff hub + token-usage gauge scaled to the max token value recorded so far per
  station, a scrollable per-station status list, decision history), and the Decision
  Log/Model Tiers/Cost of Asking/Gate Outcomes 4-card grid.
- Both new pages linked from the main console's and Stats page's `view-switch` header nav
  (`Console · Stats · Docs · Flow`), and `agent-console-server.py` gained matching `/docs` and
  `/flow` routes alongside the existing `/` and `/stats`.
- Italian-to-English cleanup: `agent-console-stats.html` had leftover Italian UI copy the owner
  flagged ("Nessun codice isola trovato...", "Salva il codice della tua isola...", a tooltip
  reading "Genere assegnato al progetto...", plus the surrounding code comments) — all translated
  to English. Audited `agent-console.html` and both new console files with the same pass; none of
  the kit's intentional status vocabulary (`To do`/`In progress`/`Blocked`/`Done`,
  `CLEAR`/`AMBIGUOUS`) was touched — that's the kit's own tracked convention, not stray text.
- `KIT_VERSION` bumped to v1.77.0.

## v1.76.1 — `second-brain-trainer` verifies findings before they reach the shared vault

Owner asked for a review against best practices for dynamic multi-agent orchestration (fan-out
vs. pipeline, adversarial/claim-level verification before a high-stakes write). Checked the kit's
own parallel-fan-out agent, `second-brain-trainer`, against that: its Step 1-3 fan-out-and-
synthesize (dispatch `second-brain-scout` clones per area in parallel waves, merge duplicates)
already matches the pattern well. The gap was verification — merged findings went straight to
`second-brain-librarian` for writing into the vault with no re-check, and this is a higher-stakes
write than most in the kit: a mistaken pattern here doesn't just cost the current project, every
future project that queries the second brain inherits it.

**What changed:**
- `user-level-agents/second-brain-trainer.md`: new Step 3.5 — every aggregated finding is
  re-opened against its actual file/device and confirmed to (1) genuinely work as described and
  (2) actually be reusable across projects, not secretly dependent on this project's own setup,
  before `second-brain-librarian` ever sees it. Findings that don't hold up are dropped, not
  softened. Step 5's report now also states how many were dropped at this step.
- `codebase-auditor` (v1.75.1) and `second-brain-trainer` now share the same verify-before-write
  discipline — the two places in this kit where an agent's own findings become a permanent
  artifact someone else acts on without re-reading the source.

## v1.76.0 — Skill-design best-practice pass: sharper trigger phrases + a growth "lessons" KB

Owner asked for a review of the kit's skills against published best practices for writing Claude
Skills (description field written for model decision-making with concrete trigger phrases;
gotchas as the highest-value content, continuously updated from real outcomes). Checked every
skill in the kit against those; the "system" skills (`genre`, `uefn-lessons`, `verse-patterns`,
`mcp-tool-contracts`, `discover-retention`) already did this well — hooked to a specific agent
step, already accumulate real lessons. The real gap was the 8 `fortnite-*` growth/marketing
skills: short, generic, human-summary-style descriptions with no concrete trigger phrases, and no
equivalent of `uefn-lessons` capturing what actually worked vs. flopped across real projects.

**What changed:**
- All 8 `fortnite-*` skill descriptions (`analytics-coach`, `competitor-analyzer`,
  `marketing-launch`, `retention-gamedesign`, `social-trailer`, `thumbnail-pro`,
  `title-description`, `update-writer`): rewritten to include concrete phrases an owner would
  actually type ("fammi una copertina," "perché il CTR è basso," "scrivi le patch notes," and
  similar), written for the model's own routing decision rather than as a human-readable summary.
- New `user-level-skills/fortnite-growth-lessons/SKILL.md`: cross-project knowledge base for
  growth/marketing, mirroring `uefn-lessons`'s exact convention but for measured outcomes
  (thumbnail/title/trailer/launch/patch-note approaches that demonstrably over- or under-performed)
  instead of code gotchas — explicitly gated on a real signal (a number, a direct reaction), never
  filed just because an asset was produced.
- `user-level-agents/growth-manager.md`: reads this new skill before routing to any of the 8, and
  now has an explicit "feed outcomes back" step — whenever a real result becomes known during a
  session (owner reports updated metrics, reacts to a launch, comments on a patch note's tone),
  file it as a lesson without waiting to be asked, the same discipline `coder`/`second-brain-
  librarian` already apply on the code side.

## v1.75.1 — `codebase-auditor` now verifies its own findings before handing them off

Owner asked for a best-practice pass over the kit. Reviewed against current guidance on
large/agentic work (delegating audits with evidence verification, in particular) and checked it
against what's actually in this kit's agent files — most of it was already covered (task lists in
ROADMAP.md/STATUS.md, pre-human review gates via intent-reviewer/compliance-reviewer, no
"think step by step"-style redundant prompting anywhere in the kit). One real gap found:
`codebase-auditor` produced findings and hands them straight to `planner-docs` with no re-check
against the actual files — a hallucinated or stale finding could turn into a real ROADMAP task.

**What changed:**
- `user-level-agents/codebase-auditor.md`: new Step 2.5 — every finding gets re-opened against
  its actual file/line/device and rechecked before it's allowed into the report; findings that
  don't hold up on re-check are dropped, not softened. Findings that can't be fully confirmed via
  static analysis alone are now labeled as such (vs. directly-confirmed ones), so `planner-docs`/
  the owner can tell "confirmed" from "worth checking at the next playtest" at a glance. Also
  notes that a large project's audit can be split across parallel passes per category, but the
  verification step always runs against the real files afterward regardless.

## v1.75.0 — Broke the chicken-and-egg loop: UI learning no longer depends on a `coder` task

Owner pointed out the real gap: they design UI screens BY HAND, directly in the project, not via
`coder` — that's precisely why they wanted this skill (`coder` can't design good screens yet
without examples). Every feeding mechanism up to v1.74.3 was tied to `coder` finishing a tracked
task, so hand-authored screens never fed the skill at all — a genuine dead end, since the one
source of real examples (the owner's own hand-drawn work) had no path in.

**What changed:**
- `project-template/CLAUDE.md`'s "UI reference harvest" rule now also runs a per-session **UI
  code drift check**, independent of the task workflow entirely: on every session start, it hashes
  every real UI/widget file found in the project and compares against
  `Claude/docs/.ui-code-ingested.json` (new per-project state file, file path → last-ingested
  hash). Anything new or changed since last time — regardless of who wrote it or whether it was
  ever a tracked task — gets analyzed via `game-ui-designer`'s source-code analysis and filed into
  `code-derived.md`/`manifest.md`/`UI-STYLE-NOTES.md` automatically, then its hash is recorded so
  it isn't re-analyzed until it changes again.
- `user-level-skills/game-ui-designer/SKILL.md`: documents this as mechanism 5, explicitly framed
  as the primary feeding path for hand-authored screens — the `coder`-task-close mechanisms (1-3)
  become the secondary loop once `coder` itself starts generating screens FROM the accumulated
  style guide, closing the full circle (hand-made screens teach the skill → skill lets `coder`
  generate consistent new screens → those get fed back too).

Net effect: the owner can keep designing UI entirely by hand, and every screen still gets learned
automatically the next time the project is opened in Claude Code — no task, no screenshot, no
explicit request.

## v1.74.3 — `coder` self-feeds `game-ui-designer` from every new/edited screen, no screenshot needed

Owner asked the natural follow-up to v1.74.2: while actively working on a project and building or
editing a UI screen, what actually happens automatically? Until now the day-to-day feeding path
(`coder.md` step 8 / `planner-docs.md` step 5) still expected a screenshot as the primary input,
with code-derived analysis only wired in as the one-time bootstrap backfill and an on-demand ask.
That meant ordinary day-to-day UI work wasn't feeding the skill at all unless a screenshot showed
up — inconsistent with the fact that the code itself (the widget file `coder` just wrote) is
always available and doesn't need the owner to do anything.

**What changed:**
- `user-level-agents/coder.md` step 8: after finishing ANY UI screen (new or edited), `coder` now
  runs `game-ui-designer`'s source-code analysis on the file(s) it just wrote as the DEFAULT path
  — always available, no screenshot dependency — and includes the extracted facts in its
  fixed-shape closing report. A screenshot, if one also happens to exist, is added on top, never
  a substitute or a blocker.
- `user-level-agents/planner-docs.md` step 5: files the code-derived facts from `coder`'s report
  into `references/examples/code-derived.md` + `manifest.md` at every task close (falls back to
  extracting them itself if an older-format report didn't include the block). Dropped the
  "pending screenshot marker" fallback since a code-derived entry now always exists regardless of
  whether an image does — a screenshot is purely additive from here on, not something to chase.

Net effect: every UI screen built or modified through this kit from now on automatically becomes
a reference example the moment its task closes — nothing to remember, nothing to attach.

## v1.74.2 — `game-ui-designer` can learn directly from real UI code, not just screenshots

Owner clarified: their existing project has real UMG/Verse widget implementation files for its
UI screens, not exported screenshots — the screenshot-only pipeline from v1.74.0/v1.74.1 had no
path for that.

**What changed:**
- `user-level-skills/game-ui-designer/SKILL.md`: new 4th feeding mechanism, "Direct source-code
  analysis" — reads real widget/UI Verse files directly, extracts concrete facts only (widget
  types/nesting, literal colors, corner-radius/padding, currency asset references, layout
  structure), writes one entry per screen to a new `references/examples/code-derived.md` plus a
  `manifest.md` row sourced to the real file path, and feeds the same per-project
  `Claude/docs/UI-STYLE-NOTES.md` the screenshot path already feeds. Explicitly runs on demand
  when the owner points at real code, not only via the scheduled hooks.
- `user-level-agents/project-bootstrap.md`: the one-time existing-UI backfill (Branch A) now
  checks for real UI code files first — this is the common case for an existing UEFN project —
  falling back to image screenshots only if code isn't found or doesn't apply.

## v1.74.1 — `game-ui-designer` self-feeding made fully automatic (no per-task question)

Owner pushed back on v1.74.0's "ask once whether to save a screenshot" mechanism: same lesson as
the earlier genre-check gap — a step that only fires when manually invoked, or that requires
answering a question every single task, doesn't actually self-maintain. Reworked the whole
feeding pipeline to be automatic in the same three places the rest of this kit already automates
mechanical bookkeeping (task close, every-session check, one-time project bootstrap):

**What changed:**
- `user-level-agents/coder.md` step 8: after finishing a UI screen, stages any available
  screenshot into `Claude/docs/ui-screenshots-pending/` instead of asking whether to keep it —
  purely mechanical, no owner-facing question.
- `user-level-agents/planner-docs.md`: new closing step 5 (renumbering old 5-9 → 6-10, and fixing
  a pre-existing duplicate step-9 numbering along the way) — on closing a UI-related task,
  automatically files any staged screenshot into `~/.claude/skills/game-ui-designer/references/
  examples/<archetype>/`, logs it in that skill's `manifest.md`, and records the concrete style
  choices made into the project's `Claude/docs/UI-STYLE-NOTES.md`; if no screenshot was staged yet,
  leaves a one-line pending marker instead of asking again next session.
- `project-template/CLAUDE.md`: new "UI reference harvest" bullet, same automatic-every-session
  pattern as the genre check — scans `Claude/docs/ui-screenshots-pending/` on every session start
  and files anything a previous task close didn't have an image for yet.
- `user-level-agents/project-bootstrap.md` (Branch A, existing-project analysis): new one-time
  backfill step — scans a pre-existing project for screenshots of UI screens that already exist,
  so projects analyzed for the first time under this skill aren't stuck empty just because they
  predate it.
- `user-level-skills/game-ui-designer/SKILL.md`: self-learning section rewritten to describe the
  3 automatic feeding paths above plus the two things that stay genuinely manual (adding an
  external, non-UEFN inspiration image; periodically reviewing whether `style-guide.md` itself
  needs updating as real examples accumulate).

## v1.74.0 — New skill: `game-ui-designer` (learns the owner's in-game UI style over time)

Owner wanted a way to design new UEFN in-game UI screens (stores, shops, missions/quests,
teleporter, rewards, inventory) that stay visually consistent with examples they've made by
hand, and to be able to feed it images to keep improving — an explicitly self-learning skill,
not a one-shot style dump.

**What was added:**
- `user-level-skills/game-ui-designer/SKILL.md`: new user-level skill (lives at
  `~/.claude/skills/game-ui-designer/`, same convention as `genre/`, `uefn-lessons/`, etc.).
  Covers panel anatomy, item-card recipe, currency display, progress/reward patterns, and what
  NOT to copy directly from reference art (third-party icons/branding).
- `references/style-guide.md`: distilled rules extracted from the owner's first 9 reference
  images (Roblox-sourced, given explicitly as aesthetic reference only, not UEFN screenshots or
  literal assets to reuse).
- `references/examples/<archetype>/*.png` + `manifest.md`: the starting example set, organized
  by UI archetype (store, shop, missions-quests, teleporter, rewards, inventory).
- **Self-learning loop**: the skill instructs itself to (1) save any new reference image the
  owner shares into the matching archetype folder and log it in `manifest.md`; (2) after
  finishing a real screen, ask once whether to save a screenshot of the *finished, owner-approved*
  result back into the examples — this is what gradually shifts the example set from "generic
  Roblox inspiration" to "this owner's own established UEFN style"; (3) periodically re-check
  `style-guide.md` against the accumulated real examples and propose updates if they've drifted.
  Promotion to `mature` follows the same discipline as Genre Skills: 3+ distinct projects with an
  owner-approved finished screenshot each, not just a raw example count.
- `user-level-agents/coder.md`: new step 8 (old step 8→9) — when a task involves building or
  reworking a UI/menu screen, read this skill first (and the project's own
  `Claude/docs/UI-STYLE-NOTES.md` if one already exists, which wins over the generic guide), and
  offer to save a screenshot of the finished result afterward.

## v1.73.3 — Fixed truncated reject-count badge on the last miniflow stage

Owner reported a minor but real display bug in the main Agent Console: the small red "×N" reject
badge on an agent avatar (spotted on `planner-docs`, the rightmost stage in the miniflow rail) was
visually cut off horizontally, unreadable.

**Root cause:** `.mf-reject-badge` is `position:absolute; right:6px` relative to its 96px-wide
`.mf-node`. The rail (`.miniflow-rail`) scrolls horizontally but had no right-side padding, so the
rightmost node sat flush against the rail's own clipped edge — the badge's rendered box extended
past that edge and got cut off. Reproduced with a Playwright script forcing the badge visible on
the last pipeline stage (`planner-docs`) and confirmed visually against the owner's screenshot
before making any change.

**What changed:**
- `agent-console.html`: `.miniflow-rail` now has right-side padding (`padding:6px 14px 2px 0`) so
  the last stage's badge has clearance instead of sitting at the hard scroll edge; `.mf-reject-badge`
  changed from `right:6px` to `right:-2px` (compensates for the node's own edge) with
  `white-space:nowrap` and `z-index:2` added so the badge text never wraps/gets clipped regardless
  of which stage it's on.
- Verified with a Playwright screenshot forcing `×12` on the `planner-docs` badge: fully readable,
  no truncation, no console errors (before/after comparison).

## v1.73.2 — Show the project's assigned genre on the Stats tab (owner spotted the gap)

Owner noticed that the Stats page showed tags and a "Genre Rank" card saying "in Survival", but
never showed the genre actually assigned to the project via `Claude/docs/.genre` — those are two
different sources (one is what the creator chose/confirmed for the project, the other is what
Epic's live API reports for the published island) that usually agree but could in principle
diverge, and the page never surfaced the first one at all.

**What changed:**
- `agent-console-server.py` / `.ps1`: new `/project-genre` endpoint, serving
  `Claude/docs/.genre` verbatim (same plain-text pattern as the existing `/active-task`).
- `agent-console-stats.html`: new green "genre" badge next to the island title, visually distinct
  from the grey tag badges, with a tooltip explaining it's the project-assigned genre — separate
  from whatever genre the Genre Rank card's live API data reports.
- Verified with a mock server returning `survival` from `/project-genre` alongside real tag data:
  Playwright screenshot confirms the badge renders correctly, zero console errors.

## v1.73.1 — Genre check decoupled from project-bootstrap (runs automatically every session)

Fixed a real usability gap the owner hit immediately: the genre-selection step (v1.73.0's Step
0.5) only lived inside `project-bootstrap`, which by design runs ONCE EVER and only on projects
that haven't already been bootstrapped — so it would never fire on any of the owner's existing,
already-analyzed projects, forcing a manual per-project invocation for every one of them.

Moved the trigger to `CLAUDE.md` (project rules), same automatic-every-session pattern already
used for the Agent Console check: as the very first action of any session, check whether
`Claude/docs/.genre` exists — a one-line file check, cheap enough to run every time — and if not,
follow `project-bootstrap.md`'s Step 0.5 procedure directly (that step was already self-contained,
just needed a trigger not gated behind "bootstrap never ran here before"). No permission needed to
run the check itself; the genre choice itself still always stops and asks the owner, same as
before. This means opening any pre-existing project — even ones analyzed long before this feature
existed — now sets its genre and bootstraps its Genre Skill automatically, without the owner
invoking anything by name project by project.

## v1.73.0 — Genre Skills architecture (real code, not just design) + tag badges on Stats

Turns the Genre Skills design discussed with the owner into actual wired-in behavior, plus
closes the loop on official genre/tag data.

**Genre Skills bootstrap and lifecycle, wired into the real agent workflow:**
- `project-bootstrap.md` (Step 0.5, new): the first time a project has no `Claude/docs/.genre`,
  proposes the closed genre list (`~/.claude/skills/genre/fortnite-genres-official.json`), saves
  the owner's choice, and bootstraps an empty `~/.claude/skills/genre/<slug>/SKILL.md` (status
  `draft`) if that genre has no skill yet — deliberately empty, no invented patterns.
- `coder.md` (new step): reads the project's Genre Skill before gameplay/design tasks, one-way
  dependency only (never edits it).
- `planner-docs.md` (new step, on task close): appends a dated observation to the matching
  variant's `evidence.md`, checks the promotion rule (3+ maps with entries and at least one
  pattern — reproducible in 2+, plausible cause, actionable — repeated across them), flips
  `draft` → `mature` and updates `SKILL.md` when it's met, and only then checks 2+ mature
  variants for genuine cross-variant convergence into `references/evidence-shared.md` (staying
  empty is a legitimate outcome, not a gap to force).
- Genre Skills moved to the USER level (`~/.claude/skills/genre/`), matching every other skill in
  this kit (`fortnite-analytics-coach`, `uefn-lessons`, etc.) — shared across every project
  instead of duplicated per-project. Shipped with two prototype genres (Survival, Roguelike),
  each with a first set of variants as empty, honest starting points.

**Official genre + tag lists, now complete from real sources.** The genre list
(`fortnite-genres-official.json`) was previously missing 3 of 13 genres (only 10 were confirmed
via a real `GET /genres` capture). Fetched Epic's own documentation
(dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite) to fill the gap:
Adventure & RPG, Battle Royale, Deathrun & Platformer — their display names are doc-confirmed,
their `slug` values are inferred from the same pattern as the 10 API-confirmed ones and marked
`slugSource: "docs-inferred"` rather than presented as equally certain. Also fetched Epic's Game
Tags documentation (dev.epicgames.com/documentation/fortnite/games-and-game-tags-in-fortnite-creative)
for the full 149-tag official closed list (`fortnite-tags-known.json`) — previously shipped
empty, waiting to be built up tag-by-tag from real captures; now ships pre-populated with Epic's
own list, with a separate `observedOnIslands` array for tracking which tags actually show up on
real islands over time (see below).

**Tag badges on the Stats tab, from real data already being fetched.** `agent-console-server.py`
/ `.ps1`: every `/island-info` call now also updates `~/.claude/skills/genre/fortnite-tags-known.json`'s
`observedOnIslands` with the island's real `tags` field (first/last seen, times observed, which
islands) — best-effort, never breaks the info endpoint on failure. `agent-console-stats.html`:
renders the island's current tags as small badges next to the title, using data already being
fetched for the title itself (no new network calls). Verified with a mock `/island-info` response
carrying 5 tags and a direct call to the tracking function against a real copy of
`fortnite-tags-known.json` — confirmed same-day re-observation doesn't double-count
`timesObserved`, and a Playwright screenshot confirmed the badges render with zero console errors.

## v1.72.0 — Genre Rank card on the Stats tab

Added a "Genre Rank" panel to `agent-console-stats.html`, showing where the island currently
ranks within its genre plus a 7-day rank trend (best/worst/average).

**A winding but honest path to the real endpoint.** The feature was first requested from a
reference screenshot the owner had; it was initially mis-assumed to come from a third-party site
(Fortnite.gg), and a capture prompt was drafted around that premise before the owner corrected
it with a screenshot of the *official* Swagger "Genres" section — missed earlier because that
Swagger page is JS-rendered and unreadable by automated fetch (same limitation noted in v1.71.0).
A first real sample from `GET /genres/{slug}/rankings` didn't match the reference screenshot's
genre or rank range, which turned out to be the wrong endpoint — that one ranks a genre overall,
not one island. The owner then shared the full Swagger endpoint list, which surfaced the actually
relevant one: `GET /islands/{code}/rankings`.

**Confirmed via real capture (2026-09-19).** With no `from`/`to`, the endpoint returns only the
latest single hourly snapshot. With `from`/`to` set to a 7-day window it returns an
HOURLY-granularity series — 167 points observed for the real island tested — each shaped
`{timestamp, genres:[{genreSlug, genre, rank}]}`; `genres` had exactly one element in every real
record (this island carries a single genre tag). Lower rank number = better. A `to` in the future
produces a real `400 Bad Request`, so — same pattern as the metrics endpoint — `to` is always
clamped server-side to "now".

**What changed:**
- `agent-console-server.py` / `.ps1`: new `_get_island_rankings()` / `Get-IslandRankingsJson`,
  same memory+disk cache pattern (5-min TTL) as the metrics endpoint, served at
  `GET /island-rankings`.
- `agent-console-stats.html`: new rank card above the KPI tiles — current rank, best/worst/average
  over the window, and an inverted-axis line chart (lower rank number maps to the smaller y, near
  the top, so "up" reads as "improving" — the opposite convention from every other chart on this
  page, called out explicitly in the code). Best-effort: any error or empty payload just hides the
  card instead of blocking the rest of the page.
- Verified against the owner's own real captured sample: the rendered numbers (#378 current,
  #320 best, #876 worst, #531.5 average) matched the reference screenshot exactly.

## v1.71.1 — Two real chart bugs: silent window compression, wrong date axis

Both found through the owner actually using v1.71.0, not through testing here.

**Bug 1 — a 7-day window rendering as if it were 2 days.** `renderChart()` filtered out `null`
values (days with insufficient traffic — Epic's own floor is 5+ unique players) *before* laying
out the x-axis, so when most days in the window had no data, the few real points got stretched to
fill the whole chart width. Owner report: "in the chart I only see two days even though it says 7,
is that right?". Fixed by keeping every point for layout purposes and grouping only *contiguous*
non-null runs for drawing, so a real gap now shows as a visible break in the line (or a lone dot)
instead of being silently absorbed into the axis.

**Bug 2 (deeper) — the axis itself was wrong.** Even after fixing bug 1, the x-axis still just
spanned however many entries the API happened to return for the window — and it turns out the API
*omits* days with insufficient data from the array entirely rather than padding them with `null`.
A real case (data on only 2 of the last 7 calendar days) rendered those 2 dates as if they were
"the 7-day window", while the actual current date was days later. Owner report (mid-session):
"it's giving me 12/09 and 13/9, today is 18/09". Fixed with a new `padToSevenDayGrid()` that builds a true
7-calendar-day grid ending at the browser's own "today" (UTC-date matched), mapping real points
onto it and leaving an explicit `null` for any day genuinely absent from the API's response — now
the single source of truth for "the window" used by both the KPI tiles and the chart. Verified
against a reproduction of the exact real scenario (data only on 2026-09-12/13, system date
2026-09-18).

## v1.71.0 — Real island stats: a "Stats" tab on the Agent Console, backed by the Fortnite Ecosystem API

New feature, requested after the two v1.70.5 bug fixes: a second page alongside the console,
showing the island's real performance data instead of pipeline/agent activity.

**Layout chosen after a 4-mockup review** (KPI row + a big chart with a metric selector — the
other three explored a small-multiples grid, a sidebar + single chart, and a record-strip +
normalized comparison chart, kept as reference but not built).

**Real API schema, not guessed.** Before writing any of this, `coder` was sent to make a real
call against `api.fortnite.com/ecosystem/v1` and capture the actual response — the public Swagger
page is JS-rendered and unreadable by an automated fetch, so this followed the kit's usual
real-payload-capture discipline instead of inventing field names. Confirmed: the API needs no API
key/OAuth despite `securitySchemes` listing one in its OpenAPI doc (unused by any actual
endpoint); the real path is `GET /islands/{code}/metrics/{interval}` (`day`/`hour`/`minute` as a
path segment, not a query param) with optional `from`/`to` ISO 8601 query params (7-day lookback
needs them passed explicitly — the default window is much shorter); field names are camelCase and
not 1:1 with the human labels (`recommendations`, not `recommends`; `averageMinutesPerPlayer`);
`retention` is a separate array shaped `{d1, d7, timestamp}`, not folded into the other metrics;
values can be `null` on a day with too little traffic (Epic's stated floor: 5+ unique players);
and a documented `429` exists for rate limiting with no published threshold.

**New/changed files:**
- `agent-console-stats.html` — the new page. Same design tokens as `agent-console.html` (this is
  a tab of the same console, not a separate product). Nine KPI tiles (the metric definitions
  above), click a tile to plot it in the chart below, real hover crosshair + tooltip snapping to
  the nearest day, a 7-day max badge per tile, and a friendly empty state when no island code is
  configured yet instead of a blank/broken page.
- `agent-console.html` — added a small Console/Stats view-switch pill in the header (a plain
  `<a href>`, not client-side routing — each view is its own static file on the same local
  server).
- `agent-console-server.py` / `agent-console-server.ps1` — two new endpoints: `/island-metrics`
  (proxies the 7-day daily-granularity call above) and `/island-info` (island title/tags, for the
  page header). Both cache server-side — 5 min for metrics, 1 hour for info, memory + a
  `Claude/logs/fortnite-*-cache.json` fallback file — so a page reload, or a real `429`, still
  shows the last good data instead of an empty page. `/stats` now serves the new HTML file the
  same way `/` serves the console.
- `Claude/docs/.island-code` — new per-project file, same pattern as `.active-task`: a single
  line with the island code (e.g. `1234-5678-9012`), read by both server scripts. Nothing writes
  this automatically yet — set it once per project and the Stats tab picks it up.

Verified with a mock local API server standing in for Epic's endpoint (network to the real one
isn't available from this dev sandbox): metric fetch, the 429-with-stale-cache fallback, and the
missing-island-code case all confirmed server-side; the actual page verified in a real browser via
Playwright against that mock server — KPI tiles, chart, hover tooltip, and switching the plotted
metric by clicking a different tile, zero console/page errors.

## v1.70.5 — Two real Agent Console bugs fixed: stale-entry misattribution, wrong task ID on the miniflow

Both surfaced from real usage after the open-source release, diagnosed locally with the exact log
evidence before any fix was written.

1. **Orphaned queue entries with no expiry corrupted attribution.** When a real `SubagentStop`
   event was lost (session crash/restart, or a phantom orchestrator-poll stop consuming it), the
   matching `start` entry in `agent-console-active.json` sat forever with no expiry. A real log
   capture showed a 7-day-old orphaned `qa-regression` start get "resumed" by the next real stop of
   that type, stamping a week-old description on the just-finished task — and when several such
   stale entries got auto-cleared together on a reload, they all showed the same timestamp, looking
   like a coincidence but actually just one replay tick. Fixed in both the PowerShell and bash hook
   pairs (`agent-console-log.ps1`/`.sh`, `agent-console-stop.ps1`/`.sh`): every queue entry now
   carries its own `ts`, and anything older than 45 minutes (same threshold as the client-side
   `STALE_ACTIVE_MS`) is pruned before a new entry is pushed or matched.

2. **The miniflow header showed the previous task's ID.** `.active-task` (written only by `coder`)
   and the miniflow's active stage (derived live from the `active` stack) are two independent
   sources. A task entering `intent-gate` — which runs before `coder` — advanced the stage
   immediately while the on-disk task-ID label stayed frozen on the previous task until `coder`
   eventually overwrote it, so the header could read e.g. "MINIFLOW — T-050" with `intent-gate`
   active while the real work was already on T-051. Fixed in `agent-console.html`:
   `resetMiniflowCycle()` now clears the task-ID label the instant a new cycle starts, instead of
   leaving the stale id visible until the next poll happens to catch up.

3. **macOS/Linux hook pair brought up to parity.** `agent-console-stop.sh` previously never read
   the `SubagentStop` payload at all — it blindly popped queue index 0, i.e. it still had the
   attribution bug the PowerShell side had already fixed in v1.69, on top of the orphaned-entry bug
   above. Rewritten to match the PowerShell logic (skip phantom/empty `agent_type` events, match the
   oldest queued entry of the same type, prune expired entries, serialize the queue read-modify-write
   with `flock` the way the PowerShell side uses a named Mutex). Verified with a real sandbox
   repro — phantom stop ignored, correct desc attributed with two agent types queued at once, and a
   1-hour-old orphaned entry correctly dropped rather than resumed — before shipping.

## v1.70.4 — Loud warning when launched from the wrong folder (silent hook failures, root cause of the last incident)

Root cause of the "logs stopped, console stopped animating" incident: the session had been
launched from the UEFN project's outer root instead of from inside `Content/`, where this kit's
scaffold actually lives. Every hook in `.claude/settings.json` builds its script path from
`CLAUDE_PROJECT_DIR`, so from the wrong folder every one of them points at a `Claude/hooks/` that
doesn't exist — they fail silently, one at a time, with nothing visibly wrong until you notice the
console is stale. The owner asked for a warning so this is caught immediately instead of
discovered later through cold logs.

**`session-start-reminder.ps1`/`.sh`** (fires on every fresh `claude` launch, matcher `"startup"`)
now checks, before anything else: if `Claude/hooks/agent-console.html` isn't found at
`CLAUDE_PROJECT_DIR` but IS found one level down at `Content/Claude/hooks/agent-console.html`,
that's this exact mistake — emit a loud, explicit `additionalContext` warning telling the owner,
in Claude's very first reply, to close the session and relaunch from inside `Content/`. This can't
silently fail the same way the thing it's warning about does: it only depends on `Test-Path`/
`[ -f ]` file checks, no server, no network call, so it still runs even when every other hook in
this file would be broken by the same wrong-folder mistake it's catching.

Tested directly (bash version): simulated both the wrong-folder case (warning fires, correct
`additionalContext` JSON) and the correct-folder case (no false positive, existing "console
started" message unaffected) — both confirmed via `bash -n` syntax check and running the script
with `CLAUDE_PROJECT_DIR` pointed at each location in turn.

## v1.70.3 — Migration/troubleshooting notes from real-world v1.70 upgrade feedback (root cause corrected)

Docs-only patch, no agent/console logic changed. Three things surfaced testing the v1.70 upgrade on
a real project:

1. **A stale `verse-reviewer` entry surfaced in the console after upgrading — root cause corrected.**
   First suspicion was a leftover `verse-reviewer.md` still installed in `~/.claude/agents/` (this
   kit only ever adds/updates agent files on copy, never deletes retired ones) — but the owner
   confirmed that file was already removed before this happened, so that wasn't it. The actual cause:
   `Claude/logs/agent-console.jsonl` **persists across restarts by design** (see
   `agent-console-server.py`'s own header comment — it's meant to keep activity history, not get
   wiped on every session). A `verse-reviewer` start event logged before the v1.69 rename, with no
   matching stop event, was still sitting in that file; the console's 45-minute stale-cleanup (see
   its own `STALE_ACTIVE_MS` check) surfaced and auto-cleared it exactly as designed — same as it
   would for any genuinely-abandoned entry. Nothing was broken and no fix was needed: it's expected,
   one-time noise from history predating the rename, not a recurring issue. **SETUP-GUIDE.md** Phase
   1 keeps its "delete agent files no longer on the roster before upgrading" step regardless — it's
   still good practice for the general case where an old file WOULD stay invokable — but it wasn't
   what caused this specific incident.
2. **`Content/Claude/docs/` vs `Claude/docs/` confusion.** Confirmed NOT a regression — this kit's
   scaffold has always lived inside the project's `Content/` folder by design (see SETUP-GUIDE
   section 1 and `project-template/CLAUDE.md`), so `Content/Claude/docs/STATUS.md` is the correct,
   intended path. A search from the wrong working directory (project root instead of `Content/`)
   will miss it — worth remembering when troubleshooting, not a path to fix.
3. **Two new troubleshooting entries added to SETUP-GUIDE.md's Agent Console section**: Claude
   Code's own permission prompt pausing before it starts the server / opens the console (this is
   Claude Code's standard tool-permission system reacting to a `Bash` command and/or a browser
   action, not something the kit or the console page itself triggers — approve it, or check
   `.claude/settings.json`'s `permissions` block if it keeps re-prompting every session instead of
   being allow-listed once), and a cosmetic mojibake in MCP log labels (`argumentsâ€¦` instead of
   `arguments…`, a UTF-8/Windows-1252 re-interpretation in `agent-console-mcp.ps1`'s truncation —
   harmless, the underlying event data is intact).

   *(Correction: an earlier draft of this note misattributed the permission prompt to a browser/OS
   security dialog — it's Claude Code's own permission system, corrected above.)*

## v1.70 — Bounded review cycles, fixed report contracts, a durable verdict log, cheaper models on structural-check agents

Follow-through on a "graph engineering" gap audit the owner asked for after sharing an article on
node/edge contracts, bounded cycles, and model tiering. The audit ran as six parallel evaluation
passes over the kit against those principles, then one synthesis pass; six things already matched
the vision (bounded-contract nodes, `.active-task` as a real data-contract edge, structural runtime
routing via CLEAR/AMBIGUOUS and PASS/REJECTED, independent verifiers on the review edges, no
unnecessary node isolation, pipeline-first topology). Seven trivial/low-effort gaps closed:

1. **Bounded REJECTED cycles.** The `intent-reviewer`/`compliance-reviewer` fix-and-resubmit loop
   had no attempt cap, unlike `coder`'s own compile-fix loop (capped at 5). Both reviewers and
   `coder.md` now share the same 5-consecutive-attempt cap: past that, stop, write the unresolved
   items to `Claude/docs/BUGS.md`, and ask the owner — exactly like a stuck compile error.
2. **Fixed report contract for closing a task.** `coder`'s hand-off to `planner-docs` was free
   prose ("a concise summary of what changed"). It's now a fixed shape: Task ID, Files/devices
   touched, both reviewers' verdicts with attempt numbers, second-brain interaction, one-line
   summary.
3. **Fixed output lines for `planner-docs`.** Both of its modes (opening a task, closing a task/
   end-of-session update) now report back in a fixed shape instead of freeform recap prose.
4. **Honesty fix in `compliance-reviewer`.** Two of its checks (naming/Outliner state, DemoDisplay
   stand positions) claimed "if MCP is available, verify live" — but its frontmatter tools are
   `Read, Grep, Glob` only, no MCP access at all. Reworded to check what's actually verifiable from
   files and explicitly say when a claim rests on `coder`'s report rather than independent
   confirmation, instead of implying a live check that can't happen.
5. **`.task-verdicts` (new durable log).** Both reviewers now append one line per verdict
   (`timestamp reviewer task-id verdict attempt-n`) to `Claude/docs/.task-verdicts`, append-only,
   same single-writer/independent-reader pattern as `.active-task`. `planner-docs` cross-checks it
   before marking a task Done, so "both reviewers PASSed" is independently checkable instead of
   resting on `coder`'s prose relay.
6. **Model tiering on structural-check agents.** `intent-gate` and `compliance-reviewer` moved from
   `sonnet` to `haiku` — both are bounded, checklist-shaped checks (ambiguity naming, mechanical
   rule conformance against a fixed list), not open-ended judgment calls, so a cheaper model fits
   the actual cost/latency lever the audit called out as underused. `intent-reviewer` (spec-adherence
   judgment) and `coder` stay on `sonnet`.

Deliberately not done this round, flagged instead for a separate decision: `codebase-auditor`'s
five audit lenses (structural, duplication, performance, maintainability, long-session risk) are a
genuine parallel fan-out/fan-in diamond currently run serially in prose — real opportunity, but
medium effort and an architecture change, proposed rather than applied unprompted. `release-gate`
and `planner-docs` model-tier changes were left alone too — lower-confidence, "pilot only" per the
audit's own caution, worth revisiting only after the two changes above are validated in practice.

No changes to `agent-console.html`'s JS logic — only its `KIT_VERSION` string was bumped to
`"v1.70"` to match; none of the fixes above touch the console's rendering or polling code, so the
full Playwright verification pass wasn't needed this round.

## v1.69 — Structural pipeline hardening: split the review gate, add intent-gate, a single MCP-tool source of truth, and a task-lock file; Agent Console miniflow rail

Follow-through on a flow audit the owner asked for after three separate incidents (v1.65-v1.67)
turned out to share one root cause: an agent judging its own readiness/correctness, or the same
instruction duplicated in prose across multiple files where it could quietly diverge. Four
structural changes, all confirmed by the owner, implemented together:

1. **`intent-gate` (new agent)** — runs BEFORE `coder` writes anything. Independently checks
   whether a task's acceptance criteria (and any owner-supplied base code) are concrete enough to
   implement without guessing, and returns CLEAR or AMBIGUOUS. Moves the "is this actually clear"
   judgment out of `coder`'s own Step 0.5 self-check and into an agent with no stake in getting to
   start the work.
2. **`verse-reviewer` split into `intent-reviewer` + `compliance-reviewer`.** `intent-reviewer`
   checks only spec adherence (the old check 1) and must PASS before `compliance-reviewer` — the
   eight mechanical checks (logger, naming, header, DemoDisplay, deprecated APIs, multiplayer
   authority, state machine, second-brain compliance) — is even invoked. This makes the ordering
   structural instead of a convention inside one agent's single-pass checklist: the incident this
   split responds to was a combined reviewer PASSing a guessed integration because spec adherence
   was one item among nine, not the precondition for the rest.
3. **`~/.claude/skills/mcp-tool-contracts/SKILL.md` (new skill)** — single source of truth for
   "which exact MCP tool does X," starting with the project-identity check
   (`ValkyrieToolset.VerseToolset.ListFiles`, not `AssetTools.find_assets`). `coder.md`,
   `qa-regression.md`, and `project-bootstrap.md` now reference this file by name instead of each
   restating the check in its own words — the exact pattern that let the v1.67 incident happen
   (the same generic instruction, worded slightly differently, in three places at once).
4. **`Claude/docs/.active-task` (new lightweight file)** — `coder` writes the task ID here when it
   flips a task to In progress; `intent-reviewer`/`compliance-reviewer` cross-check the ID `coder`
   reports against this file instead of trusting the report alone.

Agents removed: `verse-reviewer.md`. Agents added: `intent-gate.md`, `intent-reviewer.md`,
`compliance-reviewer.md`. Net: eleven → fourteen agent files installed (two new internal-helper
files were already excluded from that count; the public-facing roster goes from eleven to twelve
directly-invokable agents). Updated for the new gate names/order: `coder.md` (Step 0 writes
`.active-task`, new Step 0.4 invokes `intent-gate`, compliance gate now two sequential PASSes),
`planner-docs.md`, `release-gate.md`, `codebase-auditor.md`, `project-template/CLAUDE.md`,
`user-level-memory/CLAUDE.md` (new rule 13a), `docs-template/ROADMAP.md`, `SETUP-GUIDE.md`.

**Agent Console**: added a miniflow rail (the owner picked "V1" of three mockups presented) above
the orbit — a horizontal row of ring-progress nodes tracking where the CURRENT task sits in
intent-gate → coder → intent-reviewer → compliance-reviewer → planner-docs, derived purely from
the same `/log` event stream already driving the orbit (no new server plumbing required for the
rail itself). A stage shows a live mm:ss timer while active, and a small red "×N" badge if the
task was ever sent backward through it (detected as a regression: an earlier pipeline stage going
active again after a later one was already reached) — the one signal specifically meant to make it
visible, at a glance, when the review gates are actually catching something rather than rubber-
stamping. Added a best-effort `/active-task` endpoint to both `agent-console-server.py` and `.ps1`,
serving `Claude/docs/.active-task`'s content for the rail's task-ID label (the rail still works
fully without it). New node colors `indigo`/`lime` added (all ten previous slots were already
taken); `KIT_VERSION` bumped to v1.69; header text "ten agents"/"ten bots" → "twelve agents"/
"twelve bots". Verified: extracted `<script>` block passes `node --check`; scratch server + seeded
`agent-console.jsonl` + Playwright screenshot confirms the rail renders correctly mid-pipeline
(two stages done, one active with a live timer, task ID shown, zero `pageerror` events) before
cleanup.

## v1.68 — Added `codebase-auditor`: an independent, whole-codebase quality audit

Requested directly: an audit role independent from `coder` itself, styled as a senior developer
who just joined the team — understands architecture/data flow first, then hunts for structural
problems, duplicated code, performance bottlenecks, and maintainability risk, with a specific eye
on what only breaks after a long, uninterrupted play session (a growing collection never cleared,
event bindings stacking up round after round, per-player state never cleaned up on leave) rather
than what a short playtest would catch. Feeds findings to `planner-docs` to queue as ROADMAP
tasks instead of queuing them itself.

Added `user-level-agents/codebase-auditor.md` (model: sonnet). Deliberately distinct from what's
already in the kit: `verse-reviewer` gates one task's compliance right after `coder` finishes;
`qa-regression` hunts regressions from an actual play-session's logs; `project-bootstrap`'s A3
step is a one-time static pass before `SPEC.md` exists. `codebase-auditor` is the repeatable,
whole-codebase second opinion the owner runs on demand at any project stage — never writes code,
never touches devices or documentation files itself.

`planner-docs.md` updated: its task-opening procedure now explicitly covers a batch of findings
handed off from `codebase-auditor` (one ROADMAP task per finding worth tracking, small ones routed
to BUGS.md instead — `planner-docs` makes the final call, `codebase-auditor` only suggests).
`project-template/CLAUDE.md` and SETUP-GUIDE.md updated (ten agents now, install file count
eleven → twelve). Agent Console: new `codebase-auditor` node (🕵️), reusing `red` as a second
regular-node color (added a plain `.node[data-color="red"]` CSS rule alongside the existing
`.node.special[data-color="red"]` used by YOU — every other defined color was already assigned to
a different agent), `KIT_VERSION` bumped to v1.68, header text "nine agents"/"nine bots" → "ten
agents"/"ten bots". Verified with a scratch server + Playwright screenshot: zero `pageerror`
events, 10/10 idle, new node renders correctly on the shared ring.

## v1.67 — New uefn-lessons entry: use ValkyrieToolset.VerseToolset.ListFiles, not AssetTools.find_assets

Root-caused by the owner directly, on a case that had already needed a rollback: `coder.md`
only ever said, generically, "read/list a couple of Verse files or assets through the MCP tools"
for its project-identity safety check — it never named which toolset to use. `coder` picked
`AssetTools.find_assets` on `/Game`, the intuitive choice for "search for assets," without
knowing that in this kit's MCP/UEFN setup that path never surfaces the project's actual custom
content, even with the right project open — it fails silently (empty result, no error), which
reads exactly like "MCP has the wrong project open" and sends debugging in the wrong direction.
The owner verified directly that `ValkyrieToolset.VerseToolset.ListFiles` is the toolset that
actually works.

Added to `~/.claude/skills/uefn-lessons/SKILL.md` under "MCP / tooling quirks" — this is a
property of the MCP/UEFN configuration itself, not this one project, so it belongs in the shared
cross-project lessons file rather than per-project memory (same bar as every other entry there:
"would this help on a different island?"). Also fixed at the source in the three agents that ran
the same generic, toolset-unspecified safety check and would have hit the identical trap:
`coder.md`, `qa-regression.md`, and `project-bootstrap.md` all now name
`ValkyrieToolset.VerseToolset.ListFiles` explicitly and warn against `AssetTools.find_assets` for
this purpose, instead of leaving the toolset choice to intuition.

## v1.66 — No invention: coder must read/restate/ask, verse-reviewer must check the spec was followed

Reported directly, a concrete failure: the owner gave `coder` ready-made base code plus a spec to
integrate with an existing device; `coder` interpreted an unclear point instead of asking,
producing a wrong implementation that needed a rollback — and `verse-reviewer` PASSed it anyway,
because it was only checking rule mechanics (logger, naming, DemoDisplay), never whether the
implementation actually matched what was asked.

**`coder.md`** gains a new mandatory **Step 0.5 — Understand before you touch. Never invent,
never interpret.**: read an unfamiliar device's actual current implementation/config before
touching it (no more guessing from a device's name/type); treat a gap in the task's acceptance
criteria as a blocker to ask about, not a decision to make; when handed ready-made base code,
read it fully and restate the intended integration back to the owner in concrete terms before
editing anything; treat spec ambiguity with the same weight as an unresolvable compile error —
never proceed on a guess "to keep moving."

**`verse-reviewer.md`** gains a new check 1, **Spec adherence — no invention**, checked first,
before every mechanical rule: compares the implementation against the task's acceptance criteria
line by line, and treats a silently-interpreted ambiguity as a REJECTED finding even when the
resulting code is otherwise clean and every other rule passes — compliant code built on a guess
is still wrong. Its "Why this agent exists" section now documents this failure mode directly, and
its description/frontmatter lead with spec adherence instead of burying it among the mechanical
checks.

## v1.65 — Templates physically separated from live project data, safe to bulk-update

Asked directly: "can I overwrite the whole project folder to update everything, without losing
data?" The honest answer before this release was no — `project-template/Claude/docs/` held the
SPEC/STATUS/ROADMAP/BUGS/RETENTION-NOTES/RELEASE-READINESS templates at the *same path* a real
project's live, populated versions of those files live at, so re-copying `project-template/` over
an existing project (to pick up hook/agent fixes from a newer kit version) would have silently
wiped a project's entire tracked history — every task, every log entry, every bug.

Fixed by construction, not by a warning to remember: renamed `project-template/Claude/docs/` to
**`Claude/docs-template/`** (added its own `README.md` explaining it's a seed, never live data).
`Claude/SETUP-INSTRUCTIONS.md` gained step 3b: seed a brand-new project's real `Claude/docs/` from
`docs-template/`, but only if `Claude/docs/` doesn't already exist yet — every step in that file is
now explicitly documented as safe to re-run after an update. `project-template/CLAUDE.md` got a
header comment flagging it as a seed file too (it becomes the project's own live `CLAUDE.md`,
identity and conventions filled in, the first time Phase 2 runs).

Added a new **"Updating an existing project to a new kit version"** section in SETUP-GUIDE.md with
the exact two lists — update-safe (`Claude/hooks/`, `Claude/reference/`,
`Claude/SETUP-INSTRUCTIONS.md`, `Claude/docs-template/`, `.claude/settings.json`) vs. never-bulk-
copy (`Claude/docs/`, project-root `CLAUDE.md`, `Claude/logs/`, per-agent persistent memory) — plus
copy commands (`rsync`/`robocopy`) for the safe subset. This replaces answering "what do I update"
ad hoc after every release with a standing, mechanical procedure.

## v1.64 — Plan-first workflow: no code without a tracked, ID'd task

Requested directly, after a from-scratch project surfaced a bigger structural gap than any single
bug: nothing in the kit stopped `coder` from writing code before specs/status were updated, and
reopening a project after time away didn't make "what's in progress / what's next / what's done"
immediately obvious. This release restructures the documentation flow around one rule
(`~/.claude/CLAUDE.md`, new **rule 13**): every task is a row in `Claude/docs/ROADMAP.md`'s
`Tasks` table (ID, Feature, Status, Acceptance criteria, Priority) before any code gets written
against it, and it's only marked **Done** after `verse-reviewer` PASSes it.

**Orchestrator decision (asked for explicitly, decided against a new agent):** the alternative
considered was a dedicated `orchestrator` subagent enforcing Request → task → code → review →
close. Rejected: a Task-tool subagent is a stateless dispatch, not a supervisor of the main
session's own tool-call sequence — it can't actually intercept "coder is about to start without a
task" from outside. The main Claude Code session already *is* the orchestrator; what it needed
was an unambiguous rule loaded into every session (rule 13) plus `planner-docs` actually enforcing
it as gatekeeper — not one more hand-off hop, which would have worked against this same release's
other goal of cutting down on loops.

**Templates rewritten**: `ROADMAP.md` now has a `Tasks` table plus a "Current MVP / release
target" line `release-gate` reads. `STATUS.md` now opens with a **Current state** block (In
progress / Planned next / Done so far / Recommended next step) that's replaced on every update,
sitting above the existing append-only dated log.

**Agents updated**: `coder` gets a mandatory Step 0 plan-first gate (find the task ID or stop and
ask; flip Status to In progress itself — the one narrow exception to not touching ROADMAP.md — never
Done) and now closes a task by handing off to `planner-docs` after a `verse-reviewer` PASS,
instead of just reporting done. `coder-prep` explicitly never touches these files at all — the
gate and the closing hand-off are `coder`'s job once per wave. `planner-docs` is rewritten as the
two-mode gatekeeper (opening a task / closing one) instead of an end-of-session-only recap agent.
`verse-reviewer` now expects and reports a task ID for traceability. `release-gate` gets an
explicit ROADMAP-completeness criterion (every current-release task Done, and Done tasks
actually backed by a recorded PASS). `project-bootstrap` (both branches) now seeds real `T-<3
digits>` tasks with acceptance criteria instead of a prose "planned features" list or a vague
"next step" line.

**Skills reviewed against the new flow**: all sixteen (`uefn-lessons`, `verse-patterns`,
`uefn-device-gotchas`, `performance-uefn-checklist`, `discover-retention`, `second-brain-query`,
`token-aware-coding`, `brand-collections-uefn`, the eight `fortnite-*`) — none contradicted
plan-first (none of them touch ROADMAP/STATUS or tell an agent to start coding directly), so only
one needed a change: `token-aware-coding` gained a line about grepping one task row instead of
reading the whole ROADMAP.md once it grows across releases. Deliberately did NOT add a padding
entry to `uefn-lessons` just to check a box — this release's gap was process, not a Verse/UEFN/MCP
gotcha, and that skill's own stated bar ("would this help on a different island?") doesn't apply
to something documented directly in rule 13 instead.

`project-template/CLAUDE.md`'s per-project rules list and `SETUP-GUIDE.md` (new section **2b**,
with a full worked example of a feature request end to end) updated to match.

## v1.63 — Added `verse-reviewer`, a compliance gate before a task counts as done

Reported directly by the owner on a from-scratch project: devices shipped without the mandatory
logger, devices with class/configuration problems because the second brain was never consulted,
and reusable patterns that only ever reached a project's own memory instead of the shared vault.
Nothing in the kit caught this — `qa-regression` looks for runtime/gameplay regressions at
playtest, not rule conformance right after a task; `release-gate` looks at whole-project
readiness before a release, not one task right after it's written.

Added `user-level-agents/verse-reviewer.md` (model: sonnet) — the functional-analyst role: never
writes code or touches devices, only checks `coder`'s own output against this kit's mandatory
rules (logger, naming/organization, `DemoDisplay` presence and accuracy, deprecated APIs,
multiplayer authority, state machine) and, when the second brain is configured, cross-checks in
query mode whether a reusable pattern actually reached the vault instead of only living in project
memory. Returns PASS or an itemized REJECTED list; `coder` fixes and resubmits.

`coder.md` updated with a mandatory compliance gate: before reporting any task done, invoke
`verse-reviewer` and only report "done" after a PASS — for a `coder-prep` wave, this runs once for
the whole wave, same reasoning as the existing single-writer second-brain handoff. This keeps the
kit's "one agent owns the task" rule intact: `coder` is still sole owner of implementation and of
deciding when work is finished, it just no longer grades its own compliance.

Also updated: `project-template/CLAUDE.md`'s per-project agent rules list; SETUP-GUIDE.md (agent
count seven→eight→nine across this and the prior two releases, install file count ten→eleven,
section 2's roster); and the Agent Console — new `verse-reviewer` node (🛡️, a new `yellow`
regular-node color variant added to CSS since every other defined color was already assigned),
`KIT_VERSION` bumped to v1.63, header text "eight agents" → "nine agents"/"nine bots". Verified
with a scratch server + Playwright screenshot: zero `pageerror` events, 9/9 idle, new node
renders correctly on the shared ring.

## v1.62 — `fortnite-title-description` rebuilt into a full publishing package

Rebuilt `fortnite-title-description` per direct spec from the owner: it now produces the whole
Discover publishing package in one pass — Title (max 40 characters), Description (max 500
characters), one Main genre proposal, 4 Discover tags, and 3 how-to-play instruction lines (max
150 characters each) — everything in English, with explicit instructions to actually count
characters per field (and show the count, e.g. "37/40") rather than estimate or truncate
mid-sentence to fit. Added a second, distinct deliverable — the **community blog presentation**
(an extended description and a short one), aimed explicitly at getting readers to go play, in
whatever language the owner asks for (the five publishing fields stay English regardless).
Updated `growth-manager.md` and `SETUP-GUIDE.md` section 3e's description of this skill to match
the new scope.

## v1.61 — Agent Console updated for growth-manager

Caught by the owner asking directly ("did you update the console too?") after v1.59 added the
`growth-manager` agent without touching `agent-console.html` — it was still showing the old
seven-agent roster. Added `growth-manager` to the `AGENTS` array (📈, orange — the one color slot
already defined in CSS but unused by any agent), bumped `KIT_VERSION` to v1.61, and updated the
static "seven agents"/"seven bots" header text to eight. Nothing else needed changing: node
layout, angle spacing, and the legend/footer counts all derive from `AGENTS.length` dynamically
(confirmed in code, no hardcoded "7" anywhere else), so the new node slotted in on the shared ring
automatically. Verified with a scratch server + Playwright screenshot against a throwaway copy of
`project-template` — zero `pageerror` events, new node renders correctly at 8/8 idle.

## v1.60 — Confirmed thumbnails now get installed into the project (Resources/ + keyArt)

Requested directly: once a thumbnail from `fortnite-thumbnail-pro` is confirmed, it needs to
land in the project itself, not just be handed over as an image. Added
`references/install-thumbnail.md` to `fortnite-thumbnail-pro` with the exact procedure: create
`Resources/` at the project root if missing (the root is the folder that *contains* `Content/`,
named per `CLAUDE.md`'s "Project identity" — never the current folder, always literally
`Content`), save the confirmed file there, and update the `"keyArt"` key in
`<ProjectName>.uefnproject` (also at the project root) to point at it, e.g.
`"keyArt": "Resources/Thumbnail.png"` — editing only that key, not reformatting the rest of the
JSON. `growth-manager` (v1.59) now owns actually doing this when a thumbnail is confirmed
through it. This is a deliberate, narrow exception to the kit's standing "no agent touches files
outside `Content/`" rule, called out explicitly both in `growth-manager.md` and in
`project-template/CLAUDE.md`'s per-project rules list, scoped to exactly `Resources/` and the
`keyArt` key — nothing else at the project root.

## v1.59 — Added `growth-manager`, a dedicated agent for the eight marketing skills

v1.58 added the eight `fortnite-*` growth/marketing skills but left them relying entirely on
Claude Code's own description-based matching, with no agent owning them — inconsistent with
every other skill-cluster in the kit (`coder` reads `verse-patterns`, `project-bootstrap` reads
`discover-retention`/`brand-collections-uefn`, etc.). Added `user-level-agents/growth-manager.md`
(model: sonnet) as the dedicated owner: a single entry point the owner can talk to in plain
language, which routes to the matching `fortnite-*` skill(s) — one for most requests, several in
sequence for a full launch push — instead of the owner needing to know or name any of the eight
skills. It explicitly stays out of Verse/device work (that's `coder`) and doesn't write
`STATUS.md`/`ROADMAP.md`/`BUGS.md` itself (that's `planner-docs`) — it summarizes for
`planner-docs` instead when something it produced should be recorded there. SETUP-GUIDE.md
updated: agent count (seven → eight agents, section 2), Phase 1 install file count (nine → ten,
section 5), and section 3e rewritten to describe `growth-manager` as the normal way to reach
these skills, with direct skill-matching/naming kept as a fallback.

## v1.58 — Added eight growth/marketing skills (analytics, competitors, launch, retention, trailer, thumbnail, title/description, update writer)

The kit so far only covered building the island (`coder`, `qa-regression`, and the dev-side
`user-level-skills/`). Added eight new skills under `user-level-skills/fortnite-*` covering the
other half of running a map: `fortnite-analytics-coach` (Creator Portal + public-tracker
analysis), `fortnite-competitor-analyzer` (genre/competitor research), `fortnite-marketing-launch`
(launch/growth plans), `fortnite-retention-gamedesign` (session-length/retention game design),
`fortnite-social-trailer` (trailer scripts, TikTok/Shorts hooks), `fortnite-thumbnail-pro`
(high-CTR thumbnail concepts + prompts), `fortnite-title-description` (Discover-optimized
titles/descriptions), and `fortnite-update-writer` (patch notes/announcements).

Unlike the dev-side skills, none of these are read by a fixed step in an agent — there's no
"marketing agent" in this kit to dispatch them from. They rely on Claude Code's own
description-based skill selection instead (same mechanism as `discover-retention` and
`brand-collections-uefn`), so SETUP-GUIDE.md's new section 3e is explicit about how to fall back
to naming the skill directly ("use the fortnite-thumbnail-pro skill") if a request doesn't get
matched automatically. Install step in Phase 1 (section 5) updated to include all eight folders.

## v1.57 — Fixed the footer line disagreeing with the "Agents" legend box

Found immediately after checking the new v1.56 version tag actually worked — it did (confirmed
"v1.56" in the screenshot), but the footer sentence at the bottom of the ring ("1 working, 6
idle...") and the "Agents" legend box at the top ("working 0, broken 1") disagreed about the
exact same agent at the exact same moment.

- **Root cause**: the footer line had its own much older, separate counting logic
  (`activeCount = active.length`) left over from before the broken/waiting distinction existed —
  it only ever knew "in the active stack" vs. "not," with no idea an entry could be flagged
  broken or waiting. The legend box's newer four-state logic was never wired back into it.
- **Fix**: extracted the legend's counting logic into one shared `computeAgentCounts()`, now used
  by both the legend box and the footer line. The footer's wording adapts too — it stays the
  familiar "N working, M idle" when nothing's flagged, and adds "broken"/"waiting" segments only
  when their count is above zero, so it doesn't get more cluttered than it needs to be on a
  normal day.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  20-minute-old `coder` call (well past the 15-minute broken threshold) now shows "0 working, 1
  broken, 6 idle" in BOTH the footer and the legend box.
- `KIT_VERSION` bumped to v1.57.

## v1.56 — Version tag next to the title, to kill a whole class of "did the fix actually apply" confusion

Prompted directly by the last two rounds of troubleshooting in this changelog: a real fix (v1.55)
looked like it hadn't worked, and the actual cause was almost certainly a browser tab left open
from before the file was replaced — this is a single-page app, so a tab doesn't notice its own
HTML file changing on disk until it's reloaded.

- **New `KIT_VERSION` constant** near the top of the page's script, rendered as a small tag right
  after the title (e.g. "v1.56"). Checking it is now the first troubleshooting step: if it still
  shows an old version after replacing the file, the fix is a hard refresh (Ctrl/Cmd+Shift+R), not
  more debugging of the actual feature.
- **This constant must be bumped on every release that touches `agent-console.html`**, matching
  `CHANGELOG.md`'s top heading — said plainly in a comment right above the constant itself as a
  standing reminder, since the whole point only holds if it never drifts out of sync.
- `SETUP-GUIDE.md` updated with a matching troubleshooting note, right at the top of the Agent
  Console section where it'll actually get read before someone goes looking for a phantom bug.
- Verified with the same headless-browser screenshot test as previous releases: confirms the tag
  renders next to the title with no layout shift and no JS errors.

## v1.55 — Auto-clear thresholds were too aggressive for real long-running background work

Found immediately after v1.54, from another live report on the same pre-fix session: the console
showed ALL agents idle while Claude Code's own session view confirmed two real `coder` calls
genuinely still running (9m49s and 25m8s, both climbing) — worse than v1.54's "broken"
misattribution, since now it looked like nothing was happening at all. Root cause: the hard
auto-clear (`STALE_ACTIVE_MS`, 20 minutes) force-removed both entries from tracking entirely, and
the log showed "⚠ auto-cleared 'coder' — no stop event arrived after 20 min" twice at the same
timestamp. Both thresholds were tuned for an older, more conservative assumption about how long a
subagent call normally runs — one this kit's own new parallel-work features (`coder-prep`,
`second-brain-trainer`'s waves, background `coder` calls) have since made outdated:

- **`STALE_ACTIVE_MS` raised from 20 to 45 minutes.** Still a real safety net for a truly
  orphaned entry (a lost `SubagentStop`), just far less likely to fire on legitimate long
  background work.
- **`LED_SOFT_WARN_MS` raised from 6 to 15 minutes**, same reasoning — 6 minutes was flagging
  completely normal memory-heavy reads as "broken" far too eagerly.
- **Real bug fixed in the auto-clear loop itself**: it force-marked a card idle unconditionally,
  without checking whether another concurrent call to the same agent id (see v1.54's "×N" badge)
  was still legitimately active — so clearing one stale sibling could wrongly hide a fresh,
  genuinely-running one. Now uses the same "only if no sibling remains" guard the normal
  stop-event path already used.
- Auto-clear log message updated to say plainly that it does NOT necessarily mean anything broke.
- Verified with the same headless-browser screenshot test as previous releases, this time
  replaying the exact reported timestamps (one `coder` call 25m8s old, one 9m49s old): both now
  correctly show "working ×2" instead of being cleared to idle.

## v1.54 — Fixed a real status-misattribution bug for concurrent same-agent calls, added a "×N" concurrency badge

Found from a live report: the console showed "1 broken" while two real `coder` calls were
running at once (one ~14 minutes old in the background, one fresh) — and the owner couldn't tell
who the second one even was, since the ring only ever showed one `coder` card.

- **Real bug fixed**: `refreshLeds()` and `updateLegendCounts()` both used `Array.find()` to look
  up a named agent's current activity in the `active` stack — which returns the FIRST matching
  entry, i.e. the OLDEST of any concurrent same-id calls. So the card's "broken" (stuck/overdue)
  check was silently keyed off however long the oldest concurrent instance had been running, even
  while a much fresher call to the same agent was the one actually active — exactly what produced
  "1 broken" while the fresh `coder` call was working normally. New `latestEntryFor()` uses the
  MOST RECENT matching entry instead, so the card reflects what's actually current.
- **New "×N" concurrency badge**, via `getConcurrency()`: when 2+ concurrent calls to the same
  named agent share one card (unavoidable — Claude Code gives no per-call id to split them), the
  card now visibly says so instead of the second (or third) instance being entirely invisible.
- **Documented, not fixed (can't be, with the data available)**: which exact stop event pairs
  with which concurrent start is inherently ambiguous without a real call-stack id — the console
  assumes first-started/first-finished (FIFO), a reasonable default, not a guarantee.
  `SETUP-GUIDE.md` now says this plainly, alongside a direct answer to "should broken agents get
  killed": the console is read-only telemetry, it has no way to stop/cancel/kill anything — a
  stuck call has to be handled at the Claude Code session level itself.
- Verified with the same headless-browser screenshot test as previous releases: two synthetic
  concurrent `coder` starts (one 14 minutes old, one fresh) confirm "working 1, broken 0" (was
  "broken 1" before the fix) and the "×2" badge on the shared card.

## v1.53 — Generic "fork" clones now get a "<parent> clone" label and disappear when done

Prompted by the owner spotting a plain "fork" node in the console after `coder` spawned a
background clone, and asking for two things: make it obviously coder's own child, and have it
leave the ring once it's finished instead of sitting there idle forever.

- **New `KNOWN_IDS`/`ephemeralIds` tracking.** The fixed roster (seven bots, Vault, YOU, MCP) is
  captured once at init; anything NOT in it — a generic `subagent_type: "fork"` dispatch being the
  common case — is now treated as ephemeral.
- **`ensureNode()` now takes the parent id** (whoever was on top of the active stack when the
  fork started — the same heuristic `pulseLink()` already used for handoff pulses). An ephemeral
  node gets a 🧬 icon, the parent's own color, a "\<parent name\> clone" label instead of the raw
  `"fork"` string, and its spoke now points at the parent instead of at the hub.
- **New `removeEphemeralNode()`**, called from `setIdle()` instead of the normal idle-in-place
  path whenever the node is ephemeral: removes the DOM node, its spoke, and every tracking
  structure it was registered in (`nodeEls`, `spokeEls`, `counts`, `BLURBS`,
  `SPOKE_TARGET_OVERRIDE`, `ALL_NODES`), then re-runs `recomputeAngles()` so the ring closes the
  gap immediately instead of leaving a dead idle slot.
- Known remaining limitation, unchanged: `subagent_type` is still the only id Claude Code reports
  for a fork, so two genuinely concurrent forks under the same parent still share one node — this
  matters far less now that a single fork (the common case) behaves correctly and cleans up after
  itself.
- Verified with the same headless-browser screenshot test as previous releases: a synthetic
  `coder` → `fork` start/stop sequence confirms the "coder clone" label, parent-colored spoke, and
  full removal from the ring on stop, with zero JS errors.

## v1.52 — `coder` can now parallelize across independent devices/areas, via a new `coder-prep` helper

Prompted by the owner asking why `coder` stayed one-device-at-a-time even on tasks that obviously
split into unrelated pieces. The real reason: UEFN exposes exactly one MCP server per editor,
serving whichever project is open, and a Verse compile is a whole-project build, not an isolated
per-file one — two concurrent device placements or compiles wouldn't fail safely, they'd race
against that one shared live editor state. That part was never going to be safe to parallelize.
But most of `coder`'s actual time/cost per device is the part BEFORE any MCP call — reading
context, writing the Verse itself — and for genuinely independent areas, that part has nothing
shared to race against:

- **New agent**: `user-level-agents/coder-prep.md` — `model: sonnet` (real implementation work,
  not a lightweight scan, so no model downgrade here unlike `second-brain-scout`). Writes the
  actual Verse for ONE area, following every one of `coder`'s own conventions, but never touches
  MCP and never compiles — it reports back exactly what needs placing/configuring so `coder` can
  apply it afterward.
- **`coder.md`** gained a new "Splitting work across genuinely independent devices/areas" section:
  when a task splits cleanly, dispatch one `coder-prep` per area in parallel (capped ~6-8 per
  wave, same as `second-brain-trainer`), then apply every area's plan yourself, serially — MCP
  placement, `DemoDisplay`, compile-fix loop, one area at a time. Second-brain handoffs from the
  wave get combined into a single `second-brain-librarian` call at the end, same single-writer
  discipline as `second-brain-trainer` already uses. Skip all of this for a task that isn't
  genuinely independent-by-area, or one too small to be worth splitting.
- Nine agent files to install now, not eight — `SETUP-GUIDE.md` updated (install step, agent
  list, and a new explainer paragraph in section 3c). `coder-prep` doesn't get its own Agent
  Console node any more than `second-brain-scout` does — the console's existing fallback-node
  logic for an unrecognized `agent_type` already covers it.

## v1.51 — Documented the community `obsidian-skills` Claude Code plugin as an optional pairing

Not a kit feature — a documentation-only addition, at the owner's request, pointing to a
community Claude Code plugin marketplace worth knowing about if you spend time in the second-brain
vault yourself:

- **`second-brain-template/README.md`**: new step 5 in "Set up the vault (once)" — installing the
  `obsidian-skills` marketplace (by kepano, an Obsidian team member) teaches Claude Code better
  Obsidian-specific conventions (formatting, linking, front matter) on top of whatever
  `second-brain-librarian` already does. Explicitly marked as independent of this kit — not
  shipped or maintained by it, just a good pairing.
- **`SETUP-GUIDE.md`**, Phase 1 step 7 (connect an Obsidian second brain): same note added as a
  final optional bullet, with the same two commands:
  ```
  /plugin marketplace add kepano/obsidian-skills
  /plugin install obsidian@obsidian-skills
  ```

## v1.50 — Project name in the Agents stat box, and a real hub-LED gap fixed

Requested addition plus a real logic gap the owner spotted from a live screenshot (MCP Server node
glowing "working" while the Chief of Staff hub sat grey):

- **Project name in the "Agents" stat box.** A new line, "PROJECT: <name>", now sits above the
  agent-count/legend rows in that box — same project name `pollWhoami()` already fetches for the
  Activity Log panel's header, just also shown here since that box is more prominent.
- **Chief of Staff hub LED gap fixed.** The hub's own LED used to go green ONLY when a subagent
  was in the `active` stack (`active.length > 0`) — so when the main session did something
  directly without delegating to a subagent (e.g. calling the UEFN MCP server itself), the hub
  stayed grey/idle even though it was genuinely working, which is exactly what a live screenshot
  showed (MCP Server node glowing "working", hub LED grey). The hub LED now also turns green
  whenever the main session itself is active, via the same `/session` polling that already drives
  the YOU node's LED (`sessionActive`, kept in sync by `pollSession()`, consumed by
  `refreshLeds()`); `pollSession()` now also calls `refreshLeds()` immediately instead of waiting
  up to a second for the next tick.
- The YOU node's own LED was already correctly session-driven (green while the main session is
  actively working, grey once it's yielded back to you) — audited per the owner's request, no
  change needed there.
- Verified with the same headless-browser screenshot test as previous releases, this time seeding
  a synthetic `agent-console-session.json` with `active:true` and zero running subagents to
  confirm both YOU and the hub go green together in that specific case.

## v1.49 — New `second-brain-scout` helper: cheaper-model clones for second-brain-trainer's parallel analysis

Prompted by a real "Claude usage" report showing 38% of usage coming from unnamed/"fork" subagent
dispatches — almost certainly `second-brain-trainer`'s own parallel analysis clones, which
previously ran as generic unnamed Task dispatches (inheriting the session's default model, e.g.
Sonnet) with no way to configure them more cheaply, since a model override in this kit's design
only applies to a NAMED custom agent (one with its own `model:` frontmatter field), not a
generic/unnamed clone:

- **New agent**: `user-level-agents/second-brain-scout.md` — `model: haiku`. Analyzes exactly one
  project area, read-only, no vault access at all, and reports candidate reusable patterns in the
  same format the old generic clones used. You never invoke it yourself.
- **`second-brain-trainer` Step 2 updated** to dispatch `second-brain-scout` (one per area, per
  wave, still genuinely parallel) instead of a generic/unnamed clone — same behavior and output
  format, cheaper model for a step that's read-only and low-judgment by design.
- Eight agent files to install now, not seven (`SETUP-GUIDE.md` updated) — `second-brain-scout`
  doesn't count toward the kit's "seven agents" branding since it only ever runs as
  `second-brain-trainer`'s own dispatch, never on its own; it doesn't get an Agent Console node of
  its own either — the console's existing fallback-node logic for an unrecognized `agent_type`
  already covers it with no console changes needed.
- Also recommended to the owner, not kit changes: `/compact` mid-task and `/clear` between
  unrelated tasks (65% of usage came from >150k-context sessions), and disabling the `unreal-mcp`
  server when not actively playtesting (39% of usage) — MCP tool results stay in context for the
  rest of the session.

## v1.48 — Reverted the second ring: Obsidian Vault, YOU and MCP Server now share one ring with the bots

The v1.45 "second, further-out ring" for Obsidian Vault/YOU/MCP Server didn't land well visually
— reverted. All ten nodes (seven bots + the three special ones) now orbit on a single shared
ring at one radius, with one dashed guide circle instead of two:

- `OUTER_RING_IDS` and the separate outer-radius/second-guide-circle logic are gone from
  `layoutOrbit()`; every node uses the same `radius` (`halfDim * 0.72`, slightly larger than the
  old inner-ring radius since it's now the only ring).
- `recomputeAngles()` still special-cases Obsidian Vault's own angle — it's placed at the angular
  midpoint between `second-brain-librarian` and `second-brain-trainer` (the v1.47 fix, kept),
  it's just that midpoint is now a slot on the *one* ring instead of a separate outer one. Every
  other node (the six remaining bots, YOU, MCP Server) is spaced evenly around the rest of the
  circle in array order, and the Vault simply slots into the gap between its two second-brain
  neighbors without disturbing anyone else.
- Verified with the same headless-browser screenshot test used for the last few releases —
  confirms all ten nodes on one ring, Vault still between its two second-brain neighbors.

## v1.47 — Obsidian Vault repositioned between its two second-brain agents

Small but requested fix to `recomputeAngles()`: the outer ring used to space Obsidian Vault, YOU,
and MCP Server evenly by array order alone, which happened to land the Vault right next to
`project-bootstrap` — visually unrelated to it. The Vault is now placed at the angular midpoint
between `second-brain-librarian` and `second-brain-trainer` on the inner ring (the two agents it
actually draws spokes to and reacts to), computed via the shortest arc between their two angles;
YOU and MCP Server are then spaced evenly around the rest of the circle relative to that fixed
Vault angle, so nothing else shifts if more inner-ring agents are ever added. Verified with the
same headless-browser screenshot test used for the last two releases.

## v1.46 — Agent Console header/layout compaction: merged title row, new agent status legend, matched panel heights

Requested space-saving pass on `agent-console.html`'s header and layout, live-tested with the same
headless-browser + synthetic-event pattern used for v1.45 before packaging:

- **Merged header row.** The tagline ("seven agents. one chief of staff...") and the connection
  status line used to sit stacked below the title as two extra rows; they now sit to the right of
  the title on the same row (`.termlines` is a single flex row, `.termlines-side` stacks them
  right-aligned) — recovers two lines of vertical space.
- **Title changed to all-caps**: "DREAM BOT TEAM AGENT CONSOLE FOR UEFN" (title bar and `<title>`
  tag both updated; the blinking `_` cursor is kept).
- **Removed the decorative `.termbar`** (the three macOS-style red/yellow/green window-chrome
  dots) — recovers a third line. Those exact three colors aren't wasted: they're reused as the
  semantic colors in the new legend below (plus grey for idle).
- **Tokens stat box narrowed** (`.stat.compact`, `flex:0.65`) — it's a single number, it didn't
  need as much room as the other stat boxes.
- **New "Agents" stat box.** Shows the total agent count (7) plus a live idle/working/broken/
  waiting breakdown with a colored-dot legend (grey=idle, green=working, red=broken,
  yellow=waiting), computed by a new `updateLegendCounts()` call inside `refreshLeds()` so the
  numbers and the individual node LEDs can never disagree.
- **Four-state LED model.** The node LED heuristic used to have three states (idle / active /
  waiting, with "waiting" rendered red for both "blocked on a delegated child" and "stuck /
  running suspiciously long"). Those two very different meanings are now split: **yellow** =
  blocked waiting on a delegated child (not top of the active stack), **red** = the top-of-stack
  entry itself has been running past `LED_SOFT_WARN_MS` (likely stuck/erroring — "broken"). Green
  (working) and grey (idle) are unchanged.
- **Activity Log panel height now matches the orbit-ring panel.** `.main-grid` switched from
  `align-items:start` to `align-items:stretch`, and `.orbit-wrap` centers its ring vertically in
  whatever extra room that leaves — previously the two side-by-side panels could end up visibly
  different heights.

## v1.45 — Agent Console visual pass: second ring, vault "contested" effect, bot rays, regression missiles, fountains, project name

A full set of requested visual additions to `agent-console.html`, live-tested with a headless
browser (screenshots + a synthetic event stream) before packaging:

- **Second virtual ring.** Obsidian Vault, YOU, and MCP Server now orbit on a further-out ring
  (`OUTER_RING_IDS`), visually separate from the seven working-bot agents on the inner ring — a
  faint dashed guide circle marks each ring. `recomputeAngles()` now spaces the two rings
  independently so a node added to one never crowds the other.
- **Obsidian Vault "connected to both brains."** The vault now draws two spokes — one to
  `second-brain-librarian` (purple, existing), one to `second-brain-trainer` (new, teal) — and
  pulses (`vaultPulse`) whenever either is active, with a stronger oscillating "tug" animation
  (`.contested`, `vaultContested`) when BOTH are active at once, as if pulled from two directions.
  A floating "💭 Thinking" indicator with an animated ellipsis shows above it while active.
- **Bot ray bursts.** Every inner-ring agent gets a small, colored ripple-ring burst around its
  own icon while active (`.node-ray`) — the same idea as the hub's own ripple, scaled down and
  colored per-agent, so a working bot visibly radiates too, just far less dramatically.
- **Regression missiles.** When a `qa-regression` stop event's own description matches
  `/regression/i` (optionally with a count, e.g. "3 regressions" → up to 4 staggered launches), a
  small 🚀 flies from `qa-regression` to `coder` along an arced path and ends in a mini particle
  explosion (`spawnExplosion`) on arrival.
- **Fountains.** Obsidian Vault spawns a small stream of 💎 while active; `planner-docs` spawns a
  small stream of 📄 while active — both plain arc-and-fade particles (`spawnFountainParticle`),
  keyed by node id so start/stop is idempotent.
- **Project name in the activity log panel.** The right-hand panel's title now shows "📁
  <project folder name>" (from `/whoami`'s `project` field, already polled for the Session-running
  timer) so it's obvious at a glance which project's console you're looking at.
- Footer explanation text rewritten to document all of the above.

## v1.44 — Fixed "Session running for" showing hours/days right after a genuine server restart

Real bug, found from a live report ("the server isn't being restarted... it's been up 5 hours!!")
that turned out to be a display problem, not a restart problem — the v1.40 kill+restart mechanism
was working correctly, but the console's own "Session running for" stat made it look otherwise:

- **Root cause**: that stat was computed client-side from the OLDEST line in
  `Claude/logs/agent-console.jsonl`. That file deliberately persists across server
  restarts/sessions (it's the activity history — "delete it for a clean slate" is documented,
  intentional behavior). So once you'd used the kit across a few sessions, the stat kept showing
  hours/days of elapsed time no matter how recently the server had actually restarted — it was
  reading accumulated history, not server uptime.
- **Fix**: `agent-console-server.ps1`/`.py` now record their own real process-start time at
  launch and serve it from `/whoami` as a new `started_at` field (alongside the existing
  `project` field from v1.40). The console page polls `/whoami` every 5 seconds and prefers that
  real start time for "Session running for" — it now genuinely resets to zero the moment the
  server restarts, and also self-corrects mid-session if the server underneath the open tab gets
  restarted (project switch, kit update). Falls back to the old earliest-log-line behavior only
  against a server build that predates the `started_at` field, so an old server + new page combo
  degrades gracefully instead of showing nothing.
- `agent-console.jsonl`'s own persistence is untouched — this only changes what feeds the timer
  stat, not the activity log/history.
- SETUP-GUIDE.md's "Session timer" paragraph rewritten, plus a new troubleshooting entry for
  exactly this symptom.

## v1.43 — Console auto-opens in the browser; new brand-collections-uefn skill; console diagnostics confirmed clean

Three things landed together, per the owner's request to batch them into one update after two
rounds of diagnostics:

- **Console diagnostics: no code bugs found, only documentation gaps.** A live payload capture
  confirmed the console's "fork" background-agent dispatch (`● fork(...)` in the transcript) was
  already correctly tracked all along — it's the same `Agent`/`Task` tool the console already
  listens for, just with `subagent_type: "fork"`, not a different tool name needing a matcher
  fix. The only real finding: every fork shares one generic fallback node (🤖) instead of one per
  task, because the fallback keys off `subagent_type`, identical for every fork regardless of what
  each one does — a deliberate limitation of the generic-node mechanism, not a bug. Documented in
  SETUP-GUIDE.md's troubleshooting section instead of leaving it implying a matcher fix was
  needed. Likewise, the v1.40 stale-cross-project-server fix was independently re-confirmed
  working exactly as designed (kill+restart via `/whoami` happens automatically, before Claude's
  first reply) — the only gap was that nothing opened a browser tab, which is the next item.
- **The console now opens itself in your default browser, automatically, every session** — an
  explicit owner preference (previously the hook only started the server and mentioned the URL,
  leaving opening the tab up to you). `session-start-reminder.ps1` uses `Start-Process`; `.sh`
  tries `open` (macOS) then `xdg-open` (Linux), doing nothing on a headless box rather than
  failing the hook. `CLAUDE.md`'s fallback section and `.claude/settings.json`'s comment updated
  to match.
- **New optional skill: `brand-collections-uefn`.** Recognizes which official Fortnite Game
  Collection (brand island — TMNT, LEGO, Fall Guys, Star Wars, KPop Demon Hunters, Squid Game,
  The Walking Dead Universe, Rocket Racing) a project is built on, from real Content Browser
  folder names, device classes, and template names — not guesswork. Ships with a marker table
  researched directly from Epic's own Game Collections documentation: strong, confirmed technical
  markers for TMNT/LEGO/Fall Guys; name-only "weak" entries for the other five, since Epic's
  public pages for those don't publish folder/class-level detail. Includes a capture procedure
  for upgrading a "weak" entry (or adding a brand missing entirely) straight from a real project —
  writes to the skill's own reference file (works immediately, no vault needed) and, if the
  second brain is configured, to a `type: pattern` article via `second-brain-librarian` for
  cross-machine reuse; large projects can lean on `second-brain-trainer`'s parallel-analysis
  pattern for the capture pass itself. Wired into `project-bootstrap`'s A1 step and as a new rule
  12 in `user-level-memory/CLAUDE.md`. Install step 5 now copies seven skill folders instead of
  six.

## v1.42 — Agent Console: added the second-brain-trainer node

The console's `AGENTS` list still only had six entries after v1.41 added the seventh agent — it
now has its own node, so a training-sweep run is actually visible instead of falling back to a
generic/unknown node:

- New node for `second-brain-trainer` (🐝, a new `teal` color — every other slot in the existing
  8-color palette was already taken by another node) added to `agent-console.html`'s `AGENTS`
  array, with matching CSS rules (blob border/glow, name color, pill color) for the new `teal`
  `data-color`.
- The header tagline ("six agents. one chief of staff...") updated to "seven agents." The
  "N idle" footer counter was already computed dynamically from `AGENTS.length`, so it picks up
  the new total automatically — no fix needed there.
- No hook/server changes needed for this: `second-brain-trainer` dispatches its own parallel
  analysis clones and its one `second-brain-librarian` handoff exactly like any other agent-to-
  agent invocation the console already tracks (start/stop, FIFO attribution, comet/pulse) — this
  update only adds the node it lights up on the ring.

## v1.41 — New optional agent: second-brain-trainer (parallelized vault training pass)

New seventh agent, `second-brain-trainer`, for owners who want to backfill the Obsidian second
brain from a large or unfamiliar project faster than the normal one-thing-at-a-time flow:

- Splits the current project into areas (owner-given, or inferred from `Claude/docs/SPEC.md`'s
  project-structure section and the Outliner's own grouping) and dispatches one read-only
  analysis clone per area **in parallel** (batched in waves of ~6-8 if there are more areas than
  that) — genuinely concurrent subagents, visible as multiple simultaneous nodes if the Agent
  Console is open.
- Keeps the vault's single-writer rule intact: the parallel clones never touch the vault
  themselves, only gather findings; `second-brain-trainer` aggregates every clone's results and
  hands them to `second-brain-librarian` in exactly ONE call at the end. The vault is plain
  markdown with no locking, so this avoids the corrupted/lost-content risk of two writers
  touching it around the same time — parallelizing the reading is safe, the writing stays
  strictly single-threaded either way.
- Only useful when `second-brain-librarian` (and its vault) is already configured; skips itself
  with a clear message if it isn't. Owner-invoked only — not something the other agents call on
  their own.
- `user-level-agents/second-brain-trainer.md` added (Phase 1 install step 5 now copies seven
  agent files instead of six). SETUP-GUIDE.md updated: section 2's agent list, section 3c's
  second-brain writeup, and the intro's feature list and agent count.

## v1.40 — Agent Console: deterministic, per-project auto-start (no more asking, no more stale cross-project server)

Fixes a real bug the owner hit switching UEFN maps/projects, plus the matching feature request —
start the console with the very first command of a session, not after a round of asking:

- **Bug fixed: stale cross-project server.** Every project used the same fixed port (8765), and
  the old `SessionStart` hook only checked "is *something* listening on 8765" before deciding
  whether to start a new one — so switching to a different UEFN project while a previous
  project's server was still bound left you looking at the *wrong* project's console, since it
  looked "already running" from the outside. Fixed by giving every server instance a new
  `/whoami` route reporting which project folder it's actually serving; the session-start hook
  now compares that against the current project before deciding anything.
- **No more asking.** `session-start-reminder.ps1`/`.sh` no longer prompts Claude to ask whether
  you want the console open. It now deterministically: (1) checks `/whoami` on port 8765; (2) if
  it's already serving THIS project, leaves it alone; (3) otherwise kills whatever's bound to the
  port — only if it looks like one of this kit's own server processes (powershell/pwsh/python),
  never an unrelated program — and starts a fresh one scoped to the current project, in the
  background. Claude just mentions the URL in its first reply; there's nothing to answer.
- `agent-console-server.ps1` and `.py` both gained the `/whoami` route (`{"project": "<this
  project's folder>"}`), computed once at server startup from the script's own location — this is
  the mechanism the fix above relies on.
- `CLAUDE.md`'s fallback "Rules for this project's agents" section rewritten to match: describes
  the same deterministic check-and-replace behavior instead of "ask, then start if nothing's
  listening," for the rare case the hook's own context note doesn't reach an older Claude Code
  build.
- `.claude/settings.json`'s `SessionStart` block comment updated to describe the new behavior.
- SETUP-GUIDE.md section 5b rewritten (the "how it starts" paragraph and the troubleshooting
  entry) to match — including a new note for the specific symptom "it's showing a different
  project's data."
- No change needed for the very-first-ever-bootstrap case the owner also asked about:
  `Claude/hooks/agent-console.html` already ships as part of this kit's project template, so it's
  present from the very first session on a project regardless of whether `project-bootstrap` has
  ever been run — the deterministic auto-start above already covers it with no special-casing.

## v1.39 — Agent Console: new MCP Server node, YOU session-active LED

Two feature requests, implemented and live-tested by the owner's own Claude Code session (with
synthetic events for the MCP node, to avoid actually touching the UEFN editor during testing),
then backported into the kit source (including authoring the missing `.sh`/`.py` equivalents for
parity, since only the `.ps1` versions were provided):

- **New "MCP Server" node** (🛰️, orange), fed by a new pair of hooks,
  `agent-console-mcp.ps1`/`.sh`, wired on both `PreToolUse` and `PostToolUse` for the
  `mcp__unreal-mcp__call_tool` matcher (added as a second, independent command alongside
  `after-playtest.ps1`/`.sh` on that same matcher — not a replacement). It writes to its own log,
  `Claude/logs/agent-console-mcp.jsonl`, served from a new `/mcp` route. The node lights up (LED,
  "working" pill, call counter, tooltip with a best-effort label of what was called) while a call
  is in flight, and returns to idle on stop. When a bot made the call, a pulse animates from that
  bot's node to the MCP node so you can see *who's* talking to the editor; a direct call from the
  main session just shows the node connected to the hub.
- **YOU node now shows a session-active LED**: green while the main Claude Code session is
  actively working, grey once it's yielded back and is waiting on your next message — independent
  of the existing red "approval required" alert (still tied to `release-gate`, unchanged). Fed by
  `agent-console-tokens.ps1`/`.sh` (already firing on every tool call — now also writes
  `Claude/logs/agent-console-session.json` with `active:true`) and a new
  `agent-console-session-stop.ps1`/`.sh`, added as a second command on the existing `Stop` hook,
  which writes `active:false` at the exact moment the main session yields back to you. Served
  from a new `/session` route.
- Fixed a bug caught during testing: the MCP Server node's pill showed "undefined" instead of
  "idle" on first load (a special node with no `pillOff` defined had no fallback).
- `agent-console-server.ps1` gained the two new routes (already done upstream); backported the
  same `/mcp` and `/session` routes into `agent-console-server.py` for parity, since the uploaded
  copy was still the three-route version.
- `.claude/settings.json` updated: new `PreToolUse` block for `agent-console-mcp.ps1`, a second
  `PostToolUse` command on the existing `mcp__unreal-mcp__call_tool` block, and a second `Stop`
  command for `agent-console-session-stop.ps1`.
- New SETUP-GUIDE.md paragraphs documenting both features under section 5b.

## v1.38 — Agent Console: per-agent + hub status LEDs, comet moved fully outside the ring

The owner's own Claude Code session made further live-tested improvements directly to
`agent-console.html` (verified both with overlapping real subagents and by injecting synthetic
states into the page to check the logic deterministically, since real timings were too fast to
screenshot at the right millisecond):

- **Dynamic status LED on every agent card**, replacing the old fixed-green "online" dot:
  - grey = idle
  - green (pulsing) = genuinely working right now (top of the active-invocation stack)
  - red (blinking) = either waiting on a delegated task to finish (it's active but not on top of
    the stack — e.g. `coder` that just handed off to `second-brain-librarian`), or has been
    running longer than 6 minutes with no stop, a likely-stuck signal distinct from (and earlier
    than) the 20-minute hard auto-clear added in v1.36.
  Verified with 3 overlapping invocations: only the most-recently-started one shows green, the
  rest show red — the intended parent/child-delegation reading.
- **Chief of Staff hub** now has its own status LED too (green while supervising at least one
  active agent, grey when everything's idle), correctly positioned on the hub's own edge.
- **Comet orbit radius increased** from ~30px (effectively glued to the 32px blob edge) to ~46px,
  so it now clearly orbits outside the icon instead of riding along its border glow. Also added a
  real fading tail — a gradient arc trailing the comet's head — instead of just a glowing dot.
- Confirmed no "unknown" card remains in the current log history from the v1.37 fix; if one
  reappears after a hard refresh on `http://127.0.0.1:8765/`, it's worth a fresh capture with the
  same method used for the v1.37 diagnosis rather than assuming it's the same already-fixed bug.

## v1.37 — Agent Console: the real "unknown"/stuck-card root cause, found and fixed

The owner ran the diagnostic prompt from v1.36 in their own Claude Code session against a live
capture of `SubagentStop` payloads (2 real subagents dispatched overlapping) and found the actual
bug — the v1.36 auto-clear safety net was masking the symptom, not fixing it. Two real,
independent findings, backported into `agent-console-log.ps1`/`.sh` and
`agent-console-stop.ps1`/`.sh`:

- **`SubagentStop` fires for more than just a real subagent finishing.** Of 5 captured events,
  only 2 were real completions (a populated `agent_type` whose `agent_id` matched a prior
  dispatch); the other 3 were internal orchestrator-session events with `agent_type:""` and an
  `agent_id` never seen in any start event (one even carried the session's own scheduled-wakeup
  id). The old script treated every SubagentStop as a real stop and always popped the FIFO
  queue's oldest entry — so a ghost event would consume a real agent's queue entry, permanently
  desyncing every attribution after it. That's what actually produced the "unknown" cards and
  real cards (e.g. `coder`) staying stuck on WORKING — not a simple ordering race.
  `agent-console-stop.ps1`/`.sh` now reads the payload's own `agent_type` directly; if it's
  empty, the script exits immediately without touching the queue or logging anything. The queue
  is now used only to recover the matching `desc`, by searching for the oldest entry whose
  `agent` matches the real `agent_type` — not by blindly popping index 0 — which also fixes
  attribution when two different agent types are active at once and finish out of order.
- **A PowerShell 5.1 parsing gotcha**, found once the above was fixed and `desc` was still coming
  back empty: `@(Get-Content -Raw | ConvertFrom-Json)` — the outer `@(...)` around the pipe —
  double-nests the result once the queue has more than one element (`Object[1]{ Object[N]{ ... }
  }` instead of a flat `Object[N]`), silently breaking the agent-match search. Queue parsing in
  both `.ps1` scripts now normalizes explicitly ($null / already-an-array / single-object) with
  no outer `@(pipe)` wrap. The `.sh` scripts use `jq` and were never subject to this specific
  gotcha, but got the `agent_type`-based ghost-event fix ported over regardless, since that part
  is about hook payload behavior, not the shell.
- Confirmed end-to-end with `coder` + `qa-regression` dispatched overlapping and finishing in
  reversed order: correct `desc` on both, no `unknown`, and the queue back to `[]` clean.
- v1.36's 20-minute auto-clear safety net stays in place as a front-end fallback (still worth
  having in case a future Claude Code version changes these field names again — see the updated
  SETUP-GUIDE troubleshooting entry), but is no longer expected to be the thing doing the actual
  work here.
- Rewrote the SETUP-GUIDE.md troubleshooting entry for stuck/misattributed/"unknown" cards to
  describe the real mechanism instead of the earlier (incorrect) FIFO-ordering theory.

## v1.36 — Agent Console: fixed stuck animations, ring overlap, hub icon, vault connector

Direct feedback from a live run that surfaced a real "unknown" card in the console (see the new
SETUP-GUIDE troubleshooting entry) plus three follow-on asks:

- **Comet/pulse animations no longer run forever.** Root cause of the underlying symptom (a
  card's comet/pulse staying "active" after the real work finished): a `stop` event can get
  misattributed to a phantom `"unknown"` agent when the FIFO attribution queue
  (`agent-console-active.json`) is popped while already empty, which "eats" a stop that belonged
  to a real, still-active card. As a front-end safety net (independent of fixing the hook-side
  race, which needs a live capture to pin down per-setup), a card with no matching stop event
  after 20 minutes is now auto-cleared — its comet/pulse/glow turn off and the activity log gets
  an explicit "⚠ auto-cleared" note explaining why, instead of spinning indefinitely.
- **Ring layout no longer overlaps when a new node appears at runtime.** A dynamically-added
  fallback node (e.g. that same `"unknown"` card) used to keep the *original* even-spacing angle
  math from before it existed, so it could land right on top of an existing node instead of the
  ring re-spacing itself. All node angles are now recomputed whenever a new node is added.
- **Chief of Staff hub icon**: replaced the abstract coral starburst mark (read as "a little
  flower") with the same 🤖 robot glyph used for an unrecognized/fallback agent card, per direct
  feedback — same visual language, not a separate abstract mark.
- **Obsidian Vault's connector** now points at `second-brain-librarian` instead of at the hub —
  it isn't a bot the Chief of Staff talks to directly, it's the storage that
  `second-brain-librarian` actually writes into, so the line now reflects that relationship
  instead of implying a direct hub connection.
- Added a matching SETUP-GUIDE.md troubleshooting entry for the "unknown" node specifically,
  since it's a distinct enough symptom from the older generic stuck-card entry to deserve its own
  explanation and remedy.

## v1.35 — Agent Console: vivid colors, gem icon for Obsidian Vault, Claude-style hub mark

Follow-up to v1.34's redesign, based on direct feedback that the first pass looked too washed
out compared to the reference image (bright neon rings on a dark background, not muted glass):

- Removed the `grayscale`/`opacity` filter that was desaturating every idle node's ring and
  icon — that was the actual cause of the "muted" look, since it was graying out the
  already-correct per-agent border color. Every node's colored ring, glow, and label now render
  at full saturation all the time; only the glow intensity and a scale bump change between
  idle and active.
- Node shape switched from the organic "blob" to a clean circle with a thicker (3px) glowing
  ring, closer to the reference's neon-circle look; each node also got a small pulsing green
  "online" dot in the corner, and its name label is now colored to match its own ring instead of
  plain gray.
- **Obsidian Vault** now uses a gem icon (💎) instead of a folder, echoing the amethyst-crystal
  icon in the reference image.
- **Chief of Staff hub**: replaced the placeholder text glyph with a small custom inline-SVG
  mark (three overlapping coral-orange rounded bars radiating from a center dot) instead of a
  generic icon — a distinct, Claude-toned identity for the hub specifically, not the same icon
  reused for every other node. The hub's ring, glow, and ripple rings were retinted to match
  (coral / amber / magenta instead of blue / purple / cyan).

## v1.34 — Agent Console visual redesign: "Dream Bot Team AGENT CONSOLE_"

Cosmetic/UX redesign of `agent-console.html` only — no changes to the hooks, the FIFO queue, the
server, or the token/timer logic behind it. Two design passes in a row, both from live reference
images the owner supplied:

- Renamed the console's title to **"Dream Bot Team AGENT CONSOLE_"** (matches the existing
  blinking-cursor convention already used elsewhere in the file).
- Replaced the old two-column hex layout with a radial layout: a central **"chief of staff"** hub
  (a Claude-style glyph in a circular core) with three staggered expanding ripple rings
  (`@keyframes ripple`) so it reads as "alive" even at rest.
  Six agent nodes plus two new special nodes are arranged evenly around it and slowly orbit
  (~0.9°/s, one lap roughly every 6.5 minutes) via a `requestAnimationFrame` loop that recomputes
  each node's position, its SVG spoke back to the hub, and any in-flight pulse dot every frame.
- Distinct color per agent, reinforced (same six-color palette as before, now driving glow color,
  border color, and the new comet color together).
- Agent icons are now glassmorphic "blobs" — `backdrop-filter: blur()`, translucent gradient
  fill, an organic asymmetric `border-radius` loosely inspired by the Fortnite sprite gallery the
  owner referenced (not a literal copy — a from-scratch shape in that spirit, since the request
  left the exact execution up to me).
- Spokes now carry a **continuous traveling pulse** while an agent is active (not just on
  handoff) — a small dot flowing along the spoke toward the hub, in the agent's own color, so
  "this agent is working" is visible at a glance without reading the pill text.
- Added a small **comet**: a half-circle dot that orbits an agent's icon (`@keyframes
  spinComet`), shown only while that agent is `.active`, colored to match the agent.
- Added two new special, non-subagent nodes on the same ring:
  - **Obsidian Vault** ("shared memory") — lights up whenever `second-brain-librarian` is active,
    since that's the real agent that writes to the vault.
  - **YOU** ("approvals only") — turns red and pulses whenever `release-gate` is active. This is
    a **heuristic proxy**, called out explicitly in the footer: there's no dedicated
    "approval requested" hook in this kit yet, so `release-gate` running is used as the closest
    available signal that a real decision is waiting on a human. A matching red "⚠ approval
    required" stat card lights up in the top stats row at the same time, and the hub itself gets a
    red glow.
- Moved the activity/terminal log to the right-hand column (`.main-grid`, a two-column grid that
  collapses to one column under 960px) instead of full-width below the layout.
- `SETUP-GUIDE.md` section 5b's screenshots/description of the console's look are now stale and
  should be refreshed to match, next time that section is touched — not done in this pass since it
  was purely visual and no behavior changed.

## v1.33 — two more real bugs found testing the token/timer update, both fixed

The owner tested v1.32 live (guided by a diagnostic prompt) and found two genuine bugs, not
hypothetical ones:

- **Stale server process**: the running `agent-console-server.ps1` had been started before the
  updated files were copied in — it had already loaded the old `agent-console.html` and doesn't
  re-read routes/files after startup, so `/tokens` looked broken when the real cause was an old
  process still serving old content. Not a code bug, but common enough to call out explicitly:
  `SETUP-GUIDE.md` section 5b now has a dedicated note to restart the server after updating any
  `agent-console-*` file.
- **Real race condition**: `agent-console-log.ps1` and `agent-console-stop.ps1` both
  read-modify-write `Claude/logs/agent-console-active.json` (the FIFO attribution queue), and
  overlapping subagent invocations can run both at the same instant. Confirmed via a live test:
  concurrent unsynchronized writes corrupted a queue entry (a field serialized as a 2-element
  array instead of a plain string), which then threw uncaught inside `agent-console.html`'s
  render loop before `lastCount` advanced past the bad entry — permanently wedging the
  connection indicator on "🔴 DISCONNECTED" every poll thereafter, plus a stuck "WORKING" card
  and a stray ghost card, despite the server and network being completely fine. Fixed two ways:
  a named Mutex (`Local\AgentConsoleQueueMutex`, shared between both scripts) now serializes the
  read-modify-write section so the queue file can't be corrupted in the first place, and
  `agent-console.html`'s `processEntries()` now defensively skips any log entry whose
  `agent`/`desc` fields aren't plain strings instead of throwing — so even a future corrupted
  entry from some other cause degrades to "one skipped row," not a permanently broken console.

## v1.32 — session timer and approximate token counter in the Agent Console

- **Session timer**: a "Session running for" readout, ticking live every second, computed
  client-side from the earliest event already loaded — no new hook needed. Each active agent
  card also now shows its own live elapsed time (`⏱ 1:24`) while it's working.
- **Tokens this session (experimental/best-effort)**: a new stat showing a rough running total
  of token activity, summed from the session transcript Claude Code writes to disk. New hook
  `Claude/hooks/agent-console-tokens.ps1`/`.sh`, wired as a `PostToolUse` hook with no matcher
  (fires on every tool call, not just subagent ones), reads the transcript incrementally
  (tracked byte offset, so it stays cheap on a long session) and writes a cumulative snapshot to
  `Claude/logs/agent-console-tokens.json`. `agent-console-server.ps1`/`.py` gained a `/tokens`
  endpoint serving that file; the page polls it alongside `/log`.
- Explicitly documented as approximate: the total sums `input + output + cache_read +
  cache_creation` tokens across every assistant turn — a proxy for activity, not a billing
  figure, since prompt-caching pricing and per-turn full-context `input_tokens` aren't adjusted
  for. There's no documented API for this — it's inferred from the transcript's on-disk shape,
  which could change between Claude Code versions; `SETUP-GUIDE.md` section 5b has a
  troubleshooting entry (and a debug-capture switch in the script) for when it doesn't.
- `.claude/settings.json` updated with the new no-matcher `PostToolUse` block.

## v1.31 — fixed premature "finished" on backgrounded subagents

Found live: the owner dispatched `coder` to fix three bugs at once, Claude Code ran it in the
background ("Waiting for 1 background agent to finish"), and the console showed "finished" two
seconds after "started" while the agent was still genuinely working.

- **Root cause**: "stop" was logged from `PostToolUse` on the subagent-dispatch tool
  (`Task`/`Agent`) — but for a backgrounded dispatch, that tool call returns (firing
  `PostToolUse`) the instant the work is handed off, not when it's actually done. Foreground
  dispatches happened to look right by coincidence; background ones didn't.
- **Fix**: "stop" now comes from the `SubagentStop` hook instead — the hook Claude Code fires on
  a subagent's real completion, foreground or background. `agent-console-log.ps1`/`.sh` now only
  logs "start" (on `PreToolUse`, unchanged); a new `agent-console-stop.ps1`/`.sh` handles "stop"
  on the new `SubagentStop` hook.
- Since `SubagentStop`'s payload doesn't reliably say which agent just finished,
  attribution goes through a new small FIFO queue file, `Claude/logs/agent-console-active.json`:
  the start hook pushes an entry, the stop hook pops the oldest one and uses its
  agent/description. Best-effort (documented as such), correct for the common case.
  `.claude/settings.json` updated: removed the old stop-logging `PostToolUse` "Task|Agent"
  block, added a `SubagentStop` block.
- `SETUP-GUIDE.md` section 5b rewritten to describe the new two-hook/queue mechanism, plus a new
  troubleshooting entry for a card stuck on "WORKING" or a wrong attribution (delete
  `agent-console-active.json` to reset).

## v1.30 — real root cause found: the subagent tool isn't always named "Task"

The owner diagnosed this live (guided debug: uncommented the raw-payload capture, temporarily
widened the hook matcher to `.*`, invoked `coder` explicitly, inspected the captured payload).
Confirmed cause of the console staying at 0/IDLE even with a correct `.claude/settings.json`:
on this build, Claude Code's internal subagent-dispatch tool is named `"Agent"`, not `"Task"` —
every event was being filtered out before it ever reached the log. All other field names
(`hook_event_name`, `tool_input.subagent_type`, `tool_input.description`) were already correct.

- `agent-console-log.ps1`/`.sh` now accept **both** `"Task"` and `"Agent"` as the tool name,
  since it's been observed to vary by Claude Code build/version — future-proofs the console
  against needing this same diagnosis again on a different setup.
- `.claude/settings.json`'s two matchers changed from `"Task"` to the regex `"Task|Agent"`.
- `SETUP-GUIDE.md` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly, and the
  troubleshooting section now says explicitly what to do if a future version renames the tool to
  something else again (add it to both the script check and the matcher, same pattern).

## v1.29 — fixes from a real test of the Agent Console automation

Two problems found live-testing v1.28: the automatic session-start question never fired, and the
console stayed at 0/IDLE even after opening it manually.

- **Root cause of the silent prompt**: `session-start-reminder.ps1`/`.sh` printed plain text to
  stdout, which isn't reliably read as an instruction by Claude Code. Rewrote both to emit
  proper hook-output JSON (`hookSpecificOutput.additionalContext`), the documented way to inject
  context Claude actually sees at session start.
- **Guaranteed fallback added**: the same reminder now also lives as plain prose in
  `project-template/CLAUDE.md`'s "Rules for this project's agents" section — CLAUDE.md always
  loads regardless of any hook-output quirk in a given Claude Code version, so the console
  question surfaces even if the hook JSON approach doesn't land on some setup.
- **Clarified why cards can stay at 0/IDLE**: the console only reacts to a genuine `Task` tool
  dispatch to a named subagent — general conversation or an inline edit Claude does without
  delegating doesn't produce one, and isn't a bug. `SETUP-GUIDE.md` section 5b now says this
  explicitly, plus an expanded troubleshooting checklist covering the most likely real cause:
  `.claude/settings.json` needs to be fully replaced on an existing project, not just the new
  hook script files copied in.

## v1.28 — Agent Console asks to open itself, automatically

- New `Claude/hooks/session-start-reminder.ps1`/`.sh`, wired into `.claude/settings.json` as a
  `SessionStart` hook (matcher `startup`, so it fires when you launch `claude` fresh, not on
  every `/clear`/`/compact`). If the project has the Agent Console installed, it reminds Claude
  at the very start of the session to ask the owner whether they want it open — if yes, Claude
  checks port 8765 and, if nothing's listening, starts `agent-console-server.ps1`/`.py` itself
  in the background (detached, doesn't block the session) and tells the owner to open
  `http://127.0.0.1:8765/`. Says no once, doesn't ask again that session.
- `SETUP-GUIDE.md` section 5b and `Claude/SETUP-INSTRUCTIONS.md` step 9 updated to describe the
  automatic prompt as the default way to open the console, with manual startup kept as an
  alternative for anyone who'd rather run it in their own terminal.

## v1.27 — real-time Agent Console

A local, arcade-style dashboard that shows the team of agents actually working in real time —
which one is active, on what, and when one hands off to another — instead of only seeing the
finished output in `STATUS.md`/`BUGS.md`.

- New `Claude/hooks/agent-console.html`: a self-contained page with a card per agent (glows in
  that agent's own color and shows the current task while active), a scrolling activity log, and
  an animated pulse between two cards when one agent invokes another mid-task.
- New `Claude/hooks/agent-console-log.ps1`/`.sh`: wired into `.claude/settings.json` as
  `PreToolUse`/`PostToolUse` hooks matched on the `Task` tool (what Claude Code uses internally
  for every subagent invocation) — appends a start/stop line to
  `Claude/logs/agent-console.jsonl` per event, already configured in the scaffold, nothing to
  set up per project.
- New `Claude/hooks/agent-console-server.ps1` (PowerShell, no dependencies) and
  `agent-console-server.py` (Python, cross-platform): a small local web server serving the page
  and the live log — run manually, in its own terminal, kept open while working; not started
  automatically.
- `.claude/settings.json` and `Claude/SETUP-INSTRUCTIONS.md` updated accordingly;
  `SETUP-GUIDE.md` gets a new section 5b documenting setup, usage, and troubleshooting (same
  debug-payload pattern as the existing post-playtest hook).
- Entirely optional and safe to ignore/remove — nothing else in the kit depends on it.

## v1.26 — token-consumption reduction: six progressive-disclosure skills

Based on a set of recommendations the owner got analyzing the kit's token usage (same
adapt-don't-paste-verbatim approach as prior externally-sourced proposals):

- **Six new skills**, all following the progressive-disclosure shape (short `description`,
  dense body, `references/` loaded only on demand): `verse-patterns` (reusable Verse code
  idioms — multiplayer authority, state machines, logging/timers, item pool/round progression),
  `uefn-device-gotchas` (device-TYPE-specific quirks — DemoDisplay sizing/orientation,
  Elimination Manager/Item Granter timing, Storm Controller/Player Spawner position-critical
  behavior), `performance-uefn-checklist` (the static red-flag checklist), `discover-retention`
  (Discover signal facts plus a growing validated-proposal log, superseding `uefn-lessons`'
  "Discover / retention signals" category), `second-brain-query` (rules for asking the second
  brain narrowly), and `token-aware-coding` (general token-efficient habits — targeted search
  over full reads, precise `@file` mentions, periodic summarization).
- **`~/.claude/CLAUDE.md` rule 7 (DemoDisplay) trimmed**: the detailed sizing/orientation math
  and the `get_actor_bounds` gotcha moved to `uefn-device-gotchas/references/
  demodisplay-sizing.md`; CLAUDE.md now keeps only the always-needed core rule (one stand per
  Verse device, function-grouped) and the safety-critical gameplay-position exception, with a
  pointer to the skill for the rest — this file loads in every session, on every project, so
  trimming it has the largest leverage of any change in this pass.
- **`uefn-lessons/SKILL.md` de-duplicated**: its "Discover / retention signals" category now
  points to `discover-retention` instead of repeating the same facts; its "Device behavior
  surprises" category now points to `uefn-device-gotchas` for device-specific quirks, keeping
  the two skills' scopes non-overlapping (uefn-lessons = generic Verse/UEFN/MCP tooling,
  uefn-device-gotchas = per-device-type behavior).
- **Agent files wired to the new skills** rather than duplicating their content inline:
  `coder.md`'s pre-work checklist now points to `verse-patterns`/`uefn-device-gotchas`/
  `second-brain-query` at the relevant steps, and its DemoDisplay bullet points to the sizing
  reference instead of restating the math; `project-bootstrap.md`'s A3 now reads
  `performance-uefn-checklist` instead of inlining the checklist, and A4 reads
  `discover-retention` instead of `uefn-lessons`' (now-removed) Discover category;
  `qa-regression.md` references `performance-uefn-checklist` for what to watch at playtest.
- `SETUP-GUIDE.md` Phase 1 step 5 now lists all six new skill folders for installation, and a
  new section 3d explains what each one covers and why the progressive-disclosure shape matters
  for token usage.

## v1.25 — synthesis behavior applied consistently across every sync, not just `evolve`

Follow-up refinement (second round of feedback the owner got on v1.24, adapted rather than
applied verbatim):

- **Sync mode now checks for lateral synthesis too**: after `coder`/`project-bootstrap` hand off
  something to capture, `second-brain-librarian` checks related articles for a newly-surfaced
  connection (Level 1: update their "Connessioni e potenziali" directly) and adds a
  `wiki/meta/frontiere-conoscenza.md` entry when the sync reinforces or creates a genuinely
  interesting combination (Level 1 for a note, Level 2 to propose a new synthesis article) — so
  every ordinary sync feeds the KB's evolution, not only an explicit `evolve` run. Its report now
  says explicitly whether it touched other articles' connections or the frontier file.
- **"Connessioni e potenziali" got a concrete four-line template** (formalized links, latent
  links, synthesis candidates, open questions) instead of being described only abstractly —
  makes it actually consistent across articles and checkable by `audit`.
- `type: synthesis` articles now list their component concepts as a scannable inline
  `componenti: [[...]]` line under "Componenti combinati," for quick Dataview/graph use.
- **Query now prefers citing a synthesis article over its isolated components**, when one exists
  — the actual value-add of a second brain over flat search — applying whether the query comes
  from the owner or from `coder`/`project-bootstrap` asking before their own work.
- Release-notes sync (mode 3) now also updates a tracked device/mechanic article's "Connessioni e
  potenziali" (or adds a frontier entry) when a release note affects it, instead of leaving the
  conflict only inside the release-notes article itself.
- Step 0's near-miss-filename handling now gives the exact rename command, not just the
  diagnosis.
- Index-update steps now also remind to update any `moc-*.md` for a touched wiki, if one exists.
- Added an optional `wiki/meta/log-sessioni-sintesi.md` (a lightweight running tally of `evolve`
  runs), created only once `evolve` has actually run a few times, distinct from the narrative
  `evoluzione-kb.md`.
- The `second-brain-librarian.md` ↔ vault `CLAUDE.md` cross-reference on proactive-synthesis
  behavior is now stated as a direct instruction ("apply Level 1 immediately, propose Level 2")
  rather than just pointing at the other file.

Deliberately NOT added, per the owner's own judgment on the proposal: autonomous `evolve`
triggering, automatic versioning of the vault's `CLAUDE.md` itself, automatic Canvas/diagram
generation, or additional mandatory frontmatter fields — all flagged as premature/out of scope
for now.

## v1.24 — emergent synthesis and evolution for the second brain

Significant rewrite of `second-brain-template/CLAUDE.md`, incorporating and adapting a set of
proposals the owner got from another AI assistant, integrated to fit the existing architecture
rather than pasted verbatim:

- New **"Emergent synthesis and evolution"** section: `second-brain-librarian` now actively
  looks for connections between articles it wasn't explicitly asked to find — during `compile`,
  a query, or `audit` — not just when told to. Three levels of autonomy: apply directly (update
  an article, add a missing wikilink), propose-then-confirm (new synthesis article, merge, new
  wiki), and a dedicated Level 3 pass only on explicit command. Five named reasoning moves
  (structural analogy, generalization, composition, inversion, cross-domain transfer) to use
  when actively looking for a connection, with the "why" documented in 1-2 dense sentences.
- New **`evolve`/`sintetizza [topic]`** workflow (Level 3): a deliberate whole-KB (or scoped)
  synthesis pass — finds under-connected clusters, drafts 3-7 emergent ideas in
  `output/sintesi-YYYY-MM-DD.md`, and presents them for review. Never applies anything
  unconfirmed, same rule as `audit`.
- New `wiki/meta/` living files, created on demand (not pre-created empty):
  `frontiere-conoscenza.md` (open questions, untested hypotheses, patterns seen on 2+ projects
  without an article yet), `evoluzione-kb.md` (dated log of significant syntheses/reorganizations),
  `principi-design-second-brain.md` (observations about how this KB itself is working — a wiki
  article for the owner to read, explicitly NOT a mechanism for the agent to rewrite its own
  `CLAUDE.md` autonomously; structural changes to this file stay the owner's call).
- Richer, Dataview/graph-friendly frontmatter (`aliases`, `status`, `type`, `visto_su`,
  `versione_implementazione` — all optional, added where they genuinely apply), a new required
  `## Connessioni e potenziali` section on most articles, and a dedicated four-section structure
  for `type: synthesis` articles.
- `audit` gained four categories: under-synthesized clusters, weak connections, dormant ideas,
  stagnant evolution (a device/mechanic-specific case of staleness, called out because it
  directly hurts reuse value).
- `compile` gained a step 9 (synthesis side effect) and `query` a closing self-check, both
  tying back into the same "notice connections proactively" behavior.

`second-brain-librarian.md` updated to recognize `evolve`/`sintetizza` as a fourth direct
command alongside `compile`/query/`audit`, and to note the proactive-connection behavior applies
during ordinary work too, not only when `evolve` is explicitly invoked.

## v1.23 — "How I Want Claude to Help Me" section in the vault's CLAUDE.md

Added a new section to `second-brain-template/CLAUDE.md`: connect ideas between notes the owner
may have missed — while compiling, writing, or answering a query, `second-brain-librarian`
should actively look for related-but-unlinked existing articles (even across different thematic
wikis) and surface the connection (add the `[[wiki link]]`, mention it in the summary/answer),
not just handle the immediate task and move on.

## v1.22 — fixed two real bugs in the release-notes sync script

Found on a real Windows test run of `weekly-release-notes-sync.ps1`:

1. **Permission error reading the vault's `CLAUDE.md`.** The script never `cd`'d into the vault
   before calling `claude -p`; non-interactive/print mode can't prompt for confirmation, so it
   refused to touch anything outside its working directory. Fixed by `Set-Location` into the
   vault plus passing `--add-dir` as a belt-and-suspenders measure. Applied the same fix to the
   `.sh` version for consistency, even though bash's quoting doesn't hit the next bug.
2. **Prompt silently truncated mid-sentence.** The prompt had embedded double quotes (`"UEFN
   release-notes sync"`); when PowerShell hands a string like that to an external `.exe`,
   Windows' native argument parsing treats the embedded quote as closing the argument early —
   this is exactly what happened, the agent received the prompt cut off right before the quoted
   phrase. Fixed by removing all embedded double quotes from the prompt text.

`second-brain-template/README.md` now documents both gotchas and recommends testing the script
by hand once before wiring it into Task Scheduler/cron.

## v1.21 — weekly UEFN release-notes sync

`second-brain-librarian` gets a fourth mode, "UEFN release-notes sync" (added `WebFetch` to its
tool list): fetches
[Epic's "What's new in UEFN" page](https://dev.epicgames.com/documentation/fortnite/whats-new-in-unreal-editor-for-fortnite)
and keeps `wiki/note-di-rilascio-uefn/` current — one article per release. First run ever
backfills every entry found on the page; every run after that diffs against what's already
indexed and adds only newly published entries, never re-creating or duplicating one already
captured. Flags anything that looks like it deprecates something already noted elsewhere in the
KB (an `uefn-lessons` entry, a project's `BUGS.md`, an existing device article's snippet).

Added `second-brain-template/weekly-release-notes-sync.ps1` and `.sh` to actually run this on a
schedule, plus README instructions for wiring either into Windows Task Scheduler (`schtasks`,
Thursdays) or cron (macOS/Linux) — Claude Code itself has no built-in weekly scheduler, so this
is standard OS automation, the same pattern as the kit's own post-playtest hook. Can also be run
once by hand by asking any session to "use second-brain-librarian to sync UEFN release notes."

`note-di-rilascio-uefn/` added to the vault's suggested starting wikis in
`second-brain-template/CLAUDE.md`; setup guide's section 3c documents the new mode and the
automation setup.

## v1.20 — Windows hidden-extension gotcha on the vault's CLAUDE.md

Found on a real setup: saving/renaming `CLAUDE.md` through Windows File Explorer with
extensions hidden (the default) can silently produce `CLAUDE.MD.md` instead of `CLAUDE.md` —
Explorer hides the trailing `.md` because it's a "known" extension, so the wrong filename looks
identical to the correct one in the file list, and `second-brain-librarian` correctly reported
the vault as unconfigured (it reads the real filesystem, not Explorer's display) while the owner
saw what looked like the right file.

Fixes:
- `second-brain-template/README.md` and `SETUP-GUIDE.md` (Phase 1 step 7) now tell you to verify
  the vault's `CLAUDE.md` from a terminal (`dir CLAUDE*` / `ls CLAUDE*`) instead of trusting
  Explorer's file list, with the exact rename if it's wrong.
- `second-brain-librarian` now names the exact wrong filename (or missing folder) it actually
  found on disk when the vault looks misconfigured, instead of a generic "not configured" — so a
  five-second rename doesn't get reported the same way as an actually broken setup.

## v1.19 — second brain becomes read-write, not just write-only

Until now `coder` and `project-bootstrap` only fed the Obsidian second brain, never consulted
it — a project could reimplement something already catalogued from scratch without ever
checking. Fixed:

- **`coder`** (new step 5) queries `second-brain-librarian` before implementing a common
  device/mechanic pattern (respawn, item pool, round progression, elimination handling, and
  similar) from scratch, and adapts the existing snippet instead of reinventing it when a
  current implementation is already catalogued. Not mandatory on every task — only when the
  pattern is common enough to plausibly already exist.
- **`project-bootstrap`**'s A4 (retention proposals) now also queries the second brain for
  proposals already tried on other projects and their actual outcome, preferring a
  track-recorded proposal over a purely theoretical one when both apply.
- `second-brain-librarian`'s "direct vault commands" section now explicitly covers being queried
  by `coder`/`project-bootstrap` this way, not just by the owner.

Documented in `~/.claude/CLAUDE.md` rule 11, the setup guide's section 3c, and item 7 of "What
this kit does."

## v1.18 — second brain path set to `C:\SecondBrainOssidian`

`~/.claude/CLAUDE.md` rule 11's "Second brain path" now defaults to `C:\SecondBrainOssidian`
instead of the `<SECOND_BRAIN_PATH>` placeholder, so `second-brain-librarian` picks it up
automatically — no manual edit needed on this machine. Also updated as the worked example in the
setup guide's Phase 1 step 7 and in `second-brain-template/README.md`. Reusing this kit on a
different machine or vault location: replace the path with your own, or with the literal
`<SECOND_BRAIN_PATH>` placeholder to turn the feature off.

## v1.17 — dedicated second-brain-librarian agent

Added a sixth agent, `second-brain-librarian` — the only agent in this kit whose work happens
outside the current UEFN project's folder. It's now the sole owner of reads/writes to the
Obsidian second brain vault added in v1.16:

- `coder` and `project-bootstrap` no longer write to the vault themselves. When they identify a
  reusable device/mechanic worth capturing, they hand off to `second-brain-librarian` with a
  short brief (device/mechanic, what changed, project name, date) instead — keeping the vault's
  actual conventions in one place rather than duplicated (and potentially drifting) across every
  agent that might touch it.
- `second-brain-librarian` also runs the vault's own `compile` (ingest `raw/` material the owner
  drops in directly), query, and `audit`/`lint` workflows when invoked directly, exactly as
  defined in the vault's own `CLAUDE.md`.
- It always reads `<SECOND_BRAIN_PATH>/CLAUDE.md` before acting, since the vault's conventions
  are the authority and may be customized by the owner over time — nothing about the vault's
  structure is hardcoded into this agent beyond finding it and the handoff format.
- Never blocks UEFN work: if the vault is unreachable or unconfigured, it reports that and
  stops; `coder`/`project-bootstrap` treat a handoff exactly like a missing `uefn-lessons` file.

`~/.claude/CLAUDE.md` rule 11, the setup guide (Phase 1 step 7, section 2's agent list, section
3c), and `second-brain-template/README.md` all updated to describe the handoff model instead of
direct writes.

## v1.16 — optional Obsidian second brain for reusable mechanics

Added `second-brain-template/` (`CLAUDE.md` + `README.md`) — a separate, optional Obsidian vault
(not inside any UEFN project) that accumulates game-mechanic and Verse device implementations
across every project, kept current per device/mechanic rather than as a pile of snapshots, so a
working pattern can be reused by copying an up-to-date wiki snippet instead of rebuilding it.

New `~/.claude/CLAUDE.md` rule 11 ("Second brain (Obsidian) integration — optional") holds the
vault's path (`<SECOND_BRAIN_PATH>` placeholder, filled in once per machine, off by default) and
the writing rules: `coder` writes/updates an article after implementing a reusable device/
mechanic pattern; `project-bootstrap` does the same as a new closing step (A6) after its initial
analysis of an existing project. Both read the vault's own `CLAUDE.md` for its current
conventions before writing (it may be customized over time) rather than hardcoding assumptions
here. Never blocks a UEFN task: skipped silently if the path is unset or unreachable.

Setup guide: new optional Phase 1 step 7 (vault creation + path configuration), new section 3c
explaining the feature and how it differs from `uefn-lessons` (short tooling gotchas vs. full
wiki articles on reusable implementations), "What this kit does" item 7, and base-rules summary
item 9. Phase 1's later steps (register/verify) shifted from 7-9 to 8-10; a numbering gap
introduced in v1.13 (step 7 missing between 6 and 8) is also fixed by this renumbering.

## v1.15 — self-heal MCP registration on a new machine

Fixed a real gap: MCP server registration lives in `~/.claude.json`, per machine — it never
travels with the project (Git, cloud sync, a new computer), so a project already fully set up on
one machine showed no MCP tools the first time it was opened on another, with nothing telling
`coder`/`qa-regression`/`project-bootstrap` this was expected rather than a broken project.

All three MCP-using agents now check for this explicitly, before their existing identity-match
safety check: if `claude mcp list` doesn't show `unreal-mcp` but `CLAUDE.md`'s "Project identity"
is already filled in (proof this project was set up with MCP before), they treat it as a
new-machine first run — not a project problem — and register the server themselves (same
auto-find-and-register routine `Claude/SETUP-INSTRUCTIONS.md` step 2 already used for first-time
setup: check port 8000, then `claude mcp add ... --scope user` if missing). No manual step or
re-run of `Claude/SETUP-INSTRUCTIONS.md` needed on the new machine for this specifically.

Documented in the setup guide under "Why the MCP server is set up this way," with a reminder
that Phase 1's UEFN-side setup (`.mcp.json`, *Auto Start Server*, the kit's user-level files, the
Unreal Engine skills plugin) still needs to be done once on the new machine — this self-heal only
covers the Claude Code registration step, not UEFN's own server config.

## v1.14 — deprecated-API detection, a three-track roadmap, and Discover-grounded retention proposals

`project-bootstrap`'s A3 quality check now produces three separate, priority-ordered tracks in
`Claude/docs/BUGS.md` instead of one undifferentiated bug list:
- **Bugs**, ordered by severity (as before).
- **Deprecated functions**: calls to deprecated/soon-to-be-removed Verse/UEFN APIs or device
  features, each with its replacement if known from Epic's official docs. `coder` (rule 4 in
  `~/.claude/CLAUDE.md`) doesn't introduce new calls to something already flagged, and migrates
  one opportunistically when already touching that code. `qa-regression` flags any it comes
  across too.
- **Performance issues** (static review, added in v1.12), now explicitly its own track with its
  own impact-ordered roadmap rather than mixed into the bug list.

A4 (retention proposals) is now grounded in how Fortnite's **Discover** surfacing actually
measures engagement — average playtime, bounce rate (the concrete reason a 5-minute session
threshold matters for visibility, not just player experience), player retention, and Qualified
Play-Through Rate — sourced from
[Epic's official documentation](https://dev.epicgames.com/documentation/fortnite/how-discover-works-in-fortnite)
and added as a new curated "Discover / retention signals" category in
`user-level-skills/uefn-lessons/SKILL.md`, so proposals can name which specific signal they
target instead of offering generic playtime advice.

## v1.13 — Unreal Engine skills plugin is now required, with its Git prerequisite

Phase 1's plugin install step is no longer optional: `/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official` is now a required part of
environment setup (renumbered to step 6, shifting the later registration steps to 8-10). Added
its prerequisite: Git must be installed first ([Git for Windows](https://gitforwindows.org/) on
Windows), plus a Windows-specific gotcha — if Claude Code is already running in a PowerShell
session when Git gets installed, that session won't see the new `git` command until it's closed
and reopened (PowerShell only reads `PATH` at startup), which otherwise looks like a failed Git
install even though it succeeded.

## v1.12 — static performance review during bug identification

`project-bootstrap`'s A3 quality check (existing-project bug identification) now also does a
static performance review of the code, flagging patterns likely to cost FPS at runtime: per-tick
work that could run less often or on events instead, unbounded/growing loops or collections,
expensive calls (spawns, MCP/device queries, distance/trace checks) inside a loop or per-tick
path instead of throttled/cached, per-player work that scales badly with player count, and heavy
logic left running after it's no longer needed. Each finding becomes its own `BUGS.md` entry,
marked as a static finding for `qa-regression` to confirm at actual playtest — this doesn't
replace `qa-regression`'s existing runtime performance checks (rule 4 in `~/.claude/CLAUDE.md`),
it catches likely issues earlier, before the first playtest even happens.

## v1.11

Phase 1, step 5 of the setup guide now mentions, as an optional extra, installing Anthropic's
official Unreal Engine skills plugin (`/plugin install
unreal-engine-skills-for-claude-code@claude-plugins-official`) alongside this kit's own
user-level files — a separate plugin with its own Unreal Engine/Verse skills, complementary to
this kit rather than a replacement for it.

## v1.10 — DemoDisplay rule refined with real placement/sizing details

Replaced the v1.9 DemoDisplay/support-device rules (`~/.claude/CLAUDE.md` rules 7-8, `coder.md`,
`project-bootstrap.md`) with a much more precise version, based on hands-on testing on a real
project:
- **Grouping by function**: one `DemoDisplay` stand per Verse device, containing every device
  that Verse device configures — not one stand per connected device.
- **Sizing**: resize via the `DemoDisplay`'s own `width`/`depth`/`height` properties (through
  `ObjectTools`), never actor Scale (stays `1,1,1`). Documented the actual numeric relationships
  (`width=6/depth=5/height=4` defaults ≈ 500×633uu; `+1 width` ≈ `+100uu` on Y; `width=8-10`
  typically fits 5-6 grouped devices).
- **Orientation**: yaw=0 → front=+X, right=+Y, with a note to always check yaw before assuming
  an axis — a real attempt got this backwards.
- **`get_actor_bounds` gotcha**: asymmetric components (e.g. a spotlight cone) can skew the
  bounding box on one side; compute the real footprint from the set `width`/`depth`/`height`
  instead, and only use `get_actor_bounds` to check the side expected to be symmetric.
- **Placement on the stand**: devices go inside the stand's X/Y footprint at the same Z as its
  base — no Z stacking, no fixed-spacing rows, freely grouped within the footprint.
- **Gameplay-critical-position exception**: devices whose position IS functional gameplay data
  (Storm Controller/Beacon = storm circle center, Player Spawner = spawn point, etc.) are never
  physically moved onto a stand — they stay in place and are only referenced by name in the
  `DemoDisplay`'s description. `coder` and `project-bootstrap` now both check this before moving
  or flagging any device for relocation.

Also seeded two real entries into `user-level-skills/uefn-lessons/SKILL.md` ("Device behavior
surprises" and "MCP / tooling quirks") with the width/Scale and `get_actor_bounds` gotchas above,
replacing two of the placeholder examples.

## v1.9

Added two new base rules (`~/.claude/CLAUDE.md`, rules 7-8; older rule 7 shifted to 9, rule 8
to 10 — check cross-references if you customized the file):
- **DemoDisplay for every Verse device**: every custom Verse device gets a dedicated
  `DemoDisplay` device documenting what it does and what it's connected to, created or updated
  on every touch, not just at creation. `coder` maintains it going forward; `project-bootstrap`
  flags existing devices with a missing or stale one as a non-blocking BUGS.md entry.
- **Support devices outside the play area**: logic/support devices (Item Granter, Timer,
  Elimination Manager, `DemoDisplay`, etc.) must be placed outside the playable area so players
  never see or reach them — devices players are meant to encounter (Player Spawner, a central
  display case) are the explicit exception. `project-bootstrap` flags misplaced support devices
  it finds on existing projects rather than moving them itself.

## v1.8

Removed the packaging-warning notes ("verify `Claude/` and `.claude/` don't end up in the
released experience") from `CLAUDE.md`, `SETUP-GUIDE.md`, and `Claude/SETUP-INSTRUCTIONS.md`
(step 7bis). It's intentional that they ship with the release — the whole point of installing
the scaffold inside `Content/` is that it rides along as a backup, covered by UEFN's own
save/cloud-sync, not something to strip out before release.

## v1.7 — cross-project learning

Added `user-level-skills/uefn-lessons/SKILL.md`, a shared knowledge base installed once
(Phase 1) that persists across every project, unlike `coder`/`qa-regression`'s existing
per-project memory which resets on every new island. `coder` and `qa-regression` now read it
before starting work and add a short entry to it — instead of to their per-project memory —
whenever they hit a lesson that's about Verse/UEFN/MCP itself rather than something specific to
the current project's own devices or design. This is the mechanism for actually getting better
at UEFN development the more projects use this kit, instead of every new island starting from
the same blind spots. Documented in the setup guide as new section 3b, and in
`~/.claude/CLAUDE.md` rule 8 alongside the existing per-project memory rule.

## v1.6

Added Outliner (Scene Graph) organization and device naming to the naming/organization base
rule — previously it only covered the Content Browser's folders and files:
- Devices should be grouped in the Outliner into folders matching the experience's actual
  areas/systems (e.g. `Lobby`, `Game Area 1`, `Devices`), not left flat.
- Devices should be renamed `<DeviceType>_<Function>` (e.g. `teleport_lobby`) instead of kept
  at their default auto-generated name, so what a device does is clear without opening it.
- `coder` follows this when placing/configuring devices going forward.
- `project-bootstrap` now also reviews existing projects' Outliner organization during its
  quality check and, if it's disorganized, proposes a reorganization plan (folders + a
  current-name → suggested-name list) in `SPEC.md` for the owner to review — it doesn't rename
  devices on its own, since a blind rename can break Verse references bound to a device's name.

## v1.5

`Claude/SETUP-INSTRUCTIONS.md` step 2e now covers the most common false alarm: if the owner
just enabled *Python Editor Scripting* / *UEFN MCP Toolsets* while the project was already open
in UEFN, those settings don't take effect until the project is reloaded. The instructions now
tell the owner to close and reopen the project in UEFN (not necessarily quit UEFN) before
re-checking, instead of leaving them to guess why a setting they just enabled still isn't
working.

## v1.4

`Claude/SETUP-INSTRUCTIONS.md` step 2 now finds and registers the MCP server on its own instead
of just checking whether Phase 1 already did it: it probes port 8000 directly (`netstat`/
`lsof`), and if the server is up but not yet registered in Claude Code, registers it
automatically at user scope — no manual `claude mcp add` required from the owner. This makes
per-project setup self-sufficient: whichever project you set up first also does the one-time
registration, and every later project just finds it already there. Phase 1 in the setup guide
now marks its own registration steps (6-8) as optional — useful as an early sanity check, but
no longer required before setting up your first project.

## v1.3

Added an "About the author" section at the top of the setup guide (Mimmo_the_root — creator
code ROOT, Discord, socials) and a note on why some setup steps are left manual on purpose
(transparency: see and understand what's installed, rather than hide it behind a one-click
installer).

## v1.2 — Two-phase setup restructure

Fixed a real ordering/confusion problem, verified against Epic's official UEFN MCP docs and
against a real working setup tested on multiple projects:

- Setup is now explicitly split into **Phase 1 (environment setup, once per machine)** and
  **Phase 2 (per-project setup, repeated for every project)** — with a table up front spelling
  out the two different folders you launch `claude` from in each phase, since that was the
  actual source of confusion.
- Phase 1 now correctly sequences: create `.mcp.json` inside the **UEFN installation folder**
  → (re)start UEFN → enable *Auto Start Server* → verify the port is listening (`netstat`/
  `lsof`) → install the kit's user-level agents/CLAUDE.md → launch `claude` from that same
  installation folder → register the server once at Claude Code user scope → verify. Previously
  these steps were scattered across a "prerequisites checklist" and two later sections, in an
  order that didn't match how it actually needs to be done.
- Per-project `Claude/SETUP-INSTRUCTIONS.md` step 2 is now a lightweight double-check (assumes
  Phase 1 already ran) instead of repeating full registration instructions.
- Note: Epic's own documentation describes a different, per-project `.mcp.json` approach
  (created in each project's root folder). This kit deliberately uses the machine-level
  approach in Phase 1 instead — tested and working across multiple real projects — and says so
  explicitly in the guide's sources section, so readers comparing against Epic's page aren't
  thrown off by the difference.

## v1.1

Clarified the MCP server prerequisites, which were previously conflated into a single
per-project checklist: split *Auto Start Server* (once per machine) from *Python Editor
Scripting* / *UEFN MCP Toolsets* (once per project), and added a port-listening check
(`netstat`/`lsof`) as the first diagnostic step. Superseded by the fuller restructure in v1.2
above.

## v1.0 — Community edition (English)

First public release. Five user-scope Claude Code subagents (project-bootstrap, coder,
qa-regression, planner-docs, release-gate) plus a per-project scaffold for developing UEFN
projects at scale without mixing them up. Key design decisions baked into this release:

- The scaffold (`CLAUDE.md`, `.claude/`, `Claude/`) is installed **inside** each project's
  `Content/` folder on purpose, so it's covered by UEFN's own save/cloud-sync. Since `Content`
  is named identically in every project, the project's identity is read from the parent folder
  name once during setup and stored in `CLAUDE.md`, never recomputed from the current folder.
- The MCP server is registered once at Claude Code **user scope**, so every project on the
  machine sees it automatically — no per-project `.mcp.json`.
- The `unreal-mcp` server exposes a single generic dispatcher tool for all actions; the
  post-playtest hook filters on the call's JSON payload rather than the tool name.
- `Claude/reference/logger-template.verse.txt` uses a `.verse.txt` extension on purpose — UEFN
  compiles every `.verse` file under `Content/`, and this template isn't a valid standalone
  Verse module.
