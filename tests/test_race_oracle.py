#!/usr/bin/env python3
"""Tests for race_oracle.py (T-037). Fake model callables only, no network."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.race_oracle import race


def fake(out, delay=0.0, exc=None):
    def m(pkg):
        time.sleep(delay)
        if exc:
            raise exc
        return out
    return m


def oracle(out):
    return out == "good"


def test_fast_pass_wins_and_slow_is_not_waited():
    t0 = time.monotonic()
    r = race("pkg", {"a": fake("good", 0.01), "b": fake("good", 0.5)}, oracle)
    assert r["ok"] and r["winner"] == "a" and r["output"] == "good"
    assert r["losers"] == {"b": "not_finished"}
    assert r["latency"] < 0.3 and time.monotonic() - t0 < 0.3


def test_fast_fail_loses_to_slower_pass():
    r = race("pkg", {"a": fake("bad", 0.0), "b": fake("good", 0.05)}, oracle)
    assert r["winner"] == "b" and r["losers"] == {"a": "failed_oracle"}


def test_exception_loses():
    r = race("pkg", {"a": fake(None, 0.0, RuntimeError("boom")), "b": fake("good", 0.05)}, oracle)
    assert r["winner"] == "b" and r["losers"]["a"] == "error: boom"


def test_nobody_passes():
    r = race("pkg", {"a": fake("bad"), "b": fake("worse")}, oracle)
    assert not r["ok"] and r["winner"] is None and r["output"] is None
    assert r["losers"] == {"a": "failed_oracle", "b": "failed_oracle"}


def test_timeout_marks_not_finished():
    r = race("pkg", {"a": fake("good", 0.5)}, oracle, timeout=0.05)
    assert not r["ok"] and r["losers"] == {"a": "not_finished"}


def test_injected_clock_and_package_passed():
    seen = []
    ticks = iter([10.0, 12.5, 99.0])
    r = race("PKG", {"a": lambda p: (seen.append(p), "good")[1]}, oracle, clock=lambda: next(ticks))
    assert seen == ["PKG"] and r["latency"] == 2.5


def test_empty_models_raises():
    try:
        race("pkg", {}, oracle)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
