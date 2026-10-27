# Constitution: Chicken Roundup

- Status: Approved
- Approved: yes

## Principles
- Devices before Verse: use a device that exists before writing a Verse one. Why: less code to break. Source: kit rule
- Every Verse file has the header with Summary, date and version. Why: it is the only description of the file. Source: kit rule
- One sample first: try one chicken before making the flock. Why: a wrong value costs a rebuild of the flock. Source: Epic farm example

## Forbidden
- leaderboard
- pvp

## Names and budget
- Folders and assets: letters, digits and underscore, paths of 140 characters at most.
- Performance: no per-frame loops.

## Scope limits
- One pen, one round length.

## Self-healing (minor bugs the kit may fix by itself)
- Mode: auto
- Minor: a Verse compile error with a clear cause; an old Verse header; an asset name outside the rules.
- Medium: logic that breaks an acceptance criterion.
- Major: an error in the requirement; any change to GAME-SPEC.md.
- Limits: 3 attempts per bug, 10 automatic fixes per session.

Version: 1
