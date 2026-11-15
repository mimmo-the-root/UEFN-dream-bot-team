---
description: Be the worker of the mailbox: poll Claude/relay/inbox, run up to 5 commands in parallel (relay_plan.py), answer in outbox (or show the state with `status`)
argument-hint: "[status | stop]"
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*), Read, Write, Edit, Agent
---

Input: `$ARGUMENTS`. The mailbox is `Claude/relay/` (from the project's `Content` folder); the full protocol is `Claude/relay/RELAY-README.md`. Read it first and follow it exactly.

- No argument: start the polling loop now in dynamic mode (`/loop`): every 120 seconds when idle, every 30 seconds right after a command, 300 seconds while the MCP is not connected. Write `outbox/HEARTBEAT.md` at every poll. At EVERY poll run `python Claude/hooks/relay_plan.py` and do exactly what it prints: close the finished ones first, then start ALL the `start` commands in one message as background agents (up to 5 running), then run `run_now` yourself. Do not wait to be asked to parallelize: the plan decides. Never stop on your own: only `Claude/relay/STOP` or `/relay stop` ends the loop.
- `status`: print HEARTBEAT, the files in `inbox/`, `running/` and the last three results. Change nothing.
- `stop`: create `Claude/relay/STOP`, write HEARTBEAT `stopped`, end the loop.

Check the MCP before the first command; it connects at session start, so if it is not connected, say in one line that the owner must reconnect it or restart this session. Short report: the state and what you did, no file contents.
