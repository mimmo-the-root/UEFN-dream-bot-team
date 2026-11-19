# Package template — T-026 work-package contract

A work-package command file (`package-template`) is the single source of truth for one piece of
kit work shipped through a mailbox command. This document fixes its shape so every package can be
created, validated, and answered the same way.

## Command template fields

Every package command file MUST list exactly these seven fields (in this order):

- `id:`          the package id, e.g. `pkg-216`
- `title:`       one-line human-readable title for the work
- `risk:`        `low | medium | high` — shipping risk of the change
- `needs_owner:` `yes | no` — whether the package requires an owner decision before it can run
- `needs_mcp:`   `yes | no` — whether the package requires a live UEFN MCP editor connection
- `do:`          the imperative instruction text describing what to do (goal, files to read,
                 output path, acceptance command, max attempts, tier, token estimate, after)
- `report:`      what the result report must contain (e.g. "max 2 lines: output path, acceptance
                 result, PASS gate")

These optional fields follow:
- `approved:`    `yes | no` — whether the owner has approved this package to run
- `parallel:`    `yes | no` — whether this package may run in parallel with others
- `after:`       comma-separated list of package ids that must run before this one (empty allowed)
- `agent:`       which agent type should carry the package out

## Output path

A package's command template lives in `Claude/relay/inbox/<pkg-id>-<task-id>-work-package.md`
relative to the lab project. The validator (`tools/check_template.py`) checks the exact file given
to it.

## NOFIT answer format

When a package cannot be fitted (it cannot run as requested), the answer MUST be exactly:

```
NOFIT
<one-line reason>
```

No other framing is allowed. A package that can run never emits `NOFIT`.

## Acceptance

A package command file is accepted when `python tools/check_template.py <file>` exits 0.
Run `python tests/run_all.py` to run every acceptance test once.
