#!/usr/bin/env python3
"""Tests for the server-side token ledger (T-105) in agent-console-server.py: pure functions, no network."""
import importlib.util
import os
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("console_server", os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-server.py"))
srv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(srv)


def state(paid_in, paid_out, free_in, free_out):
    return {"models": [
        {"provider": "claude-plan", "model": "opus", "input": paid_in, "output": paid_out, "requests": 1},
        {"provider": "groq", "model": "llama", "input": free_in, "output": free_out, "requests": 1},
    ]}


# delta computation + paid/free split
prev = srv.ledger_totals(state(100, 10, 50, 5)["models"])
cur = srv.ledger_totals(state(160, 20, 80, 9)["models"])
assert srv.ledger_deltas(prev, cur) == (70, 34), srv.ledger_deltas(prev, cur)

# a counter reset or a new model never gives negative numbers
assert srv.ledger_deltas(cur, srv.ledger_totals(state(5, 1, 0, 0)["models"])) == (0, 0)
assert srv.ledger_deltas({}, cur) == (0, 0)

# ledger accumulation per task, reset in the middle
led = {}
srv.ledger_apply(led, state(100, 10, 50, 5)["models"], "T-1")
srv.ledger_apply(led, state(160, 20, 80, 9)["models"], "T-1")
srv.ledger_apply(led, state(10, 0, 0, 0)["models"], "T-1")      # reset
srv.ledger_apply(led, state(30, 0, 10, 0)["models"], "T-2")
assert led["tasks"]["T-1"] == {"paid": 70, "free": 34}, led
assert led["tasks"]["T-2"] == {"paid": 20, "free": 10}, led
assert led["total"] == {"paid": 90, "free": 44}, led
assert all(v >= 0 for t in led["tasks"].values() for v in t.values())

# the file survives a restart: the second "process" continues from the saved baseline
path = os.path.join(tempfile.mkdtemp(), "logs", "token-ledger.json")
assert srv.ledger_poll_once(path, lambda: state(100, 0, 0, 0), "T-1")["total"] == {"paid": 0, "free": 0}
assert srv.ledger_poll_once(path, lambda: state(150, 0, 20, 0), "T-1")["total"] == {"paid": 50, "free": 20}
again = srv.ledger_poll_once(path, lambda: state(170, 0, 20, 0), "T-1")   # same file, fresh call
assert again["total"] == {"paid": 70, "free": 20} and again["tasks"]["T-1"]["paid"] == 70
assert srv.ledger_load(path)["tasks"]["T-1"]["paid"] == 70

# router down: no crash, no change
def boom():
    raise OSError("down")
assert srv.ledger_poll_once(path, boom, "T-1") is None
assert srv.ledger_load(path)["total"]["paid"] == 70
print("test_token_ledger: ok")
