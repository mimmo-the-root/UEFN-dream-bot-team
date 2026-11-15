---
description: Verse in-game test workflow — write tests, run them in a session, read results
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

# Verse In-Game Tests

## When to write tests
Write a test device **after a mechanic is built** and you want to verify it works in a real multiplayer session.
Tests are for:
- Integer/float equality checks on game values (scores, health, timers)
- Boolean conditions (is mechanic active, did event fire)
- Float near-equality with tolerance (positions, distances, scaled values)
- Multiplayer state (player counts, replication, authority)

## How to create a test device

```bash
# From the project root (where Content/ folder lives)
py -3 Claude/hooks/verse_tests.py scaffold Content/<your_verse_folder>/
```

This creates `verse_test_device.verse` — **never overwrites** an existing file.

Edit the device:
1. Rename the class to something specific (e.g., `score_system_test_device`)
2. Implement `RunAllTests()` calling your test methods
3. Replace stub methods (`CalculateScore()`, `IsMechanicEnabled()`, etc.) with real calls to your game systems
4. Use the assertion helpers:
   - `ExpectEqual(Expected, Actual, "TestName")`
   - `ExpectTrue(Condition, "TestName")`
   - `ExpectNear(Expected, Actual, Tolerance, "TestName")`

## How to run tests

1. **Place the device** outside the play area on its DemoDisplay stand (rule 8)
2. **Start a UEFN session** (Play in Editor or StartSession via MCP)
3. **Let the session run** — the device runs `OnBegin()` and prints `[KIT-TEST]` lines
4. **Read results**:

```bash
# Parse the newest UEFN log automatically
py -3 Claude/hooks/verse_tests.py read

# Or specify a log file
py -3 Claude/hooks/verse_tests.py read <path_to_log>
```

## Interpreting results

The `read` command prints JSON:
```json
{
  "tests": [
    {"name": "IntEquality", "status": "PASS", "detail": "expected 100, got 100"},
    {"name": "FloatNear", "status": "FAIL", "detail": "expected ~50.0, got 51.0 (diff 1.0 > tol 0.1)"}
  ],
  "pass_count": 1,
  "fail_count": 1,
  "done_found": true,
  "done_pass": 1,
  "done_fail": 1,
  "has_failures": true
}
```

**Exit codes:**
- `0` = all tests passed, `DONE` line found
- `1` = any `FAIL` or no `DONE` line (session crashed or device didn't run)

## What to do on FAIL

A `FAIL` is a **bug** — add it to `Claude/docs/BUGS.md` with:
- Title: `B-NNN: <TestName> — <detail>`
- Steps to reproduce (place device, start session)
- Expected vs actual from the log line

## Multiplayer note (rule 3)

Tests run in the session context. For replication/authority tests:
- Run with 2+ players (use `StartSession` with multiple clients)
- Test both server and client paths
- A solo-only test is a **limitation** — note it in BUGS.md with a manual multiplayer test to do

## Example workflow

```bash
# 1. Create test for a new mechanic
py -3 Claude/hooks/verse_tests.py scaffold Content/MyGame/Verse/

# 2. Edit Content/MyGame/Verse/verse_test_device.verse
#    - Implement RunAllTests() with real assertions

# 3. Place the device in the level (outside play area)

# 4. Run session (solo or multiplayer)

# 5. Read results
py -3 Claude/hooks/verse_tests.py read

# 6. If FAIL → add to BUGS.md, fix, re-run
```