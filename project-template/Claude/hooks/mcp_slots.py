#!/usr/bin/env python3
"""mcp_slots.py - cross-process slot limiter for parallel MCP calls.

Each call waits for a free slot (env UEFN_MCP_SLOTS, default 1). A slot not renewed for 120 s is stale and freed.
Every call is logged one line in Claude/logs/mcp-slots.jsonl (time, tool, waited_ms, took_ms, ok, slots_in_use).

Usage from uefn_mcp.py:
    import sys, os, time
    sys.path.insert(0, os.path.dirname(__file__))
    from mcp_slots import acquire_slot, release_slot, get_slots_in_use

    waited_ms = acquire_slot(tool, timeout=300)
    try:
        took_ms = time.time() - start
        code, text = call(name, args)
        release_slot(ok=(code == 0), took_ms=took_ms)
        return code, text
    except Exception:
        release_slot(ok=False, took_ms=time.time() - start)
        raise

Slot file: Claude/logs/mcp-slots.lock (holds last_used timestamp per slot)."""

import json
import os
import sys
import time
from pathlib import Path

SLOTS_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "mcp-slots.lock")
DEFAULT_SLOTS = int(os.environ.get("UEFN_MCP_SLOTS", "1"))
STALE_SECONDS = 120
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "mcp-slots.jsonl")


def _load_slots():
    """Load slot timestamps from lock file. Returns dict slot_id -> last_used."""
    if not os.path.exists(SLOTS_FILE):
        return {}
    try:
        with open(SLOTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_slots(slots):
    """Save slot timestamps to lock file."""
    slots_dir = os.path.dirname(SLOTS_FILE)
    os.makedirs(slots_dir, exist_ok=True)
    with open(SLOTS_FILE, "w") as f:
        json.dump(slots, f, indent=None)


def _cleanup_stale(slots):
    """Remove slots not used for STALE_SECONDS. Returns count freed."""
    now = time.time()
    freed = sum(1 for t in slots.values() if now - t > STALE_SECONDS)
    if freed:
        for sid in list(slots.keys()):
            if now - slots[sid] > STALE_SECONDS:
                del slots[sid]
        _save_slots(slots)
    return freed


def acquire_slot(tool, timeout=300):
    """Wait for a free slot. Returns waited_ms (0 if free immediately) or raises TimeoutError."""
    slots = _load_slots()
    _cleanup_stale(slots)

    now = time.time()
    waited_ms = 0
    start_wait = now

    while True:
        # Find free slot
        for i in range(DEFAULT_SLOTS):
            sid = str(i)
            if sid not in slots or now - slots[sid] > STALE_SECONDS:
                # Use this slot
                slots[sid] = now
                _save_slots(slots)
                waited_ms = int((now - start_wait) * 1000)
                return waited_ms

        # All slots busy: wait
        if waited_ms >= timeout * 1000:
            raise TimeoutError(f"MCP slot limit ({DEFAULT_SLOTS}) reached, waited {waited_ms}ms")
        time.sleep(0.1)


def release_slot(ok=True, took_ms=0):
    """Mark the current slot as used (or freed). Takes took_ms for logging."""
    slots = _load_slots()
    now = time.time()
    for i in range(DEFAULT_SLOTS):
        sid = str(i)
        if sid in slots and now - slots[sid] < 0.1:  # Very recent slot
            slots[sid] = now
            _save_slots(slots)
            _log_entry(tool, took_ms, ok, slots_in_use=len(slots))
            break


def get_slots_in_use():
    """Return count of currently in-use slots."""
    slots = _load_slots()
    _cleanup_stale(slots)
    return len(slots)


def _log_entry(tool, took_ms, ok, slots_in_use):
    """Log one slot usage line to mcp-slots.jsonl."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "time": time.time(),
            "tool": tool,
            "waited_ms": took_ms,
            "took_ms": took_ms,
            "ok": ok,
            "slots_in_use": slots_in_use
        }) + "\n")


if __name__ == "__main__":
    # Simple test: spawn 6 threads, verify never 2 at once, stale slot recovered
    import threading

    def worker(thread_id):
        try:
            waited_ms = acquire_slot(f"test_tool_{thread_id}", timeout=10)
            print(f"Thread {thread_id}: acquired after {waited_ms}ms")
            time.sleep(2)  # Hold slot
            release_slot(ok=True, took_ms=2000)
            print(f"Thread {thread_id}: released")
        except TimeoutError as e:
            print(f"Thread {thread_id}: {e}")

    print(f"Testing with {DEFAULT_SLOTS} slot(s)...")
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Test done.")
    print(f"Slots in use: {get_slots_in_use()}")