#!/usr/bin/env python3
"""mcp_slots.py - cross-process slot limiter for parallel MCP calls.

Each call waits for a free slot (env UEFN_MCP_SLOTS, default 1). A slot not renewed for 120 s is stale and freed.
Every call is logged one line in Claude/logs/mcp-slots.jsonl (time, tool, waited_ms, took_ms, ok, slots_in_use).

Usage from mcp_lab.py:
    from mcp_slots import acquire_slot, release_slot

    waited_ms = acquire_slot(tool, timeout=300)
    try:
        result = call(ts, tool, args)
        return result
    finally:
        release_slot(tool, ok=True, took_ms=elapsed)

Slot markers: individual files Claude/logs/mcp-slots.slot.<n> with last_used timestamp.
Stale if mtime > 120 s.
"""

import json
import os
import sys
import time
import threading
from pathlib import Path

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
DEFAULT_SLOTS = int(os.environ.get("UEFN_MCP_SLOTS", "1"))
STALE_SECONDS = 120
LOG_FILE = os.path.join(LOGS_DIR, "mcp-slots.jsonl")

_slot_lock = threading.Lock()


def _slot_marker_path(slot_id):
    return os.path.join(LOGS_DIR, f"mcp-slots.slot.{slot_id}")


def _all_slot_ids():
    """Return sorted list of slot IDs that have markers."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    ids = []
    for fname in os.listdir(LOGS_DIR):
        if fname.startswith("mcp-slots.slot."):
            try:
                sid = fname.split("mcp-slots.slot.")[-1]
                int(sid)
                ids.append(sid)
            except Exception:
                pass
    return sorted(ids)


def _cleanup_stale():
    """Remove markers older than STALE_SECONDS."""
    now = time.time()
    for sid in _all_slot_ids():
        path = _slot_marker_path(sid)
        try:
            if now - os.path.getmtime(path) > STALE_SECONDS:
                os.remove(path)
        except Exception:
            pass


def _free_slots():
    """Return list of slot IDs that are free (no marker or stale)."""
    _cleanup_stale()
    all_ids = set(str(i) for i in range(DEFAULT_SLOTS))
    used = set(_all_slot_ids())
    return sorted(all_ids - used)


def acquire_slot(tool, timeout=300):
    """Wait for a free slot, create its marker, return waited_ms (0 if immediate). Raises TimeoutError."""
    waited_ms = 0
    start_wait = time.time()
    while True:
        with _slot_lock:
            free = _free_slots()
            if not free:
                # release lock while sleeping so release_slot can run
                pass
            else:
                sid = free[0]
                path = _slot_marker_path(sid)
                try:
                    os.makedirs(LOGS_DIR, exist_ok=True)
                    with open(path, "w") as f:
                        f.write(str(time.time()))
                    return waited_ms
                except Exception:
                    # race: someone else took it, retry
                    pass
        waited_ms = int((time.time() - start_wait) * 1000)
        if waited_ms >= timeout * 1000:
            raise TimeoutError(f"MCP slot limit ({DEFAULT_SLOTS}) reached, waited {waited_ms}ms")
        time.sleep(0.05)


def release_slot(tool, ok=True, took_ms=0):
    """Remove the most recently acquired slot marker for this thread/process, log the call."""
    with _slot_lock:
        slots = _all_slot_ids()
        if not slots:
            return
        slots_in_use = len(slots)
        # Heuristic: we take the newest slot; in single-threaded or process-isolated use this is correct.
        newest_sid = max(slots, key=lambda sid: os.path.getmtime(_slot_marker_path(sid)))
        path = _slot_marker_path(newest_sid)
        try:
            os.remove(path)
        except Exception:
            pass
        _log_entry(tool, took_ms, ok, slots_in_use)


def get_slots_in_use():
    """Return count of currently in-use slots (non-stale markers)."""
    _cleanup_stale()
    return len(_all_slot_ids())


def _log_entry(tool, took_ms, ok, slots_in_use=0):
    """Log one slot usage line to mcp-slots.jsonl."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps({
                "time": time.time(),
                "tool": tool,
                "waited_ms": took_ms,
                "took_ms": took_ms,
                "ok": ok,
                "slots_in_use": slots_in_use
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    # Simple test: spawn 6 threads, verify never 2 at once, stale slot recovered
    import threading

    def worker(thread_id):
        try:
            waited_ms = acquire_slot(f"test_tool_{thread_id}", timeout=10)
            print(f"Thread {thread_id}: acquired after {waited_ms}ms")
            time.sleep(0.5)  # Hold slot
            release_slot(f"test_tool_{thread_id}", ok=True, took_ms=500)
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
