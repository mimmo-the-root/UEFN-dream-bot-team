#!/usr/bin/env python3
"""update_clock.py - when the kit looks for a newer release (v1.123.2).

The first session start after the computer was switched on checks at once; after that, every 6 hours. A check that could not finish (no network)
does not count: the next session start tries again, but not more often than every 15 minutes.

  due(home)      True when a check should start now
  attempt(home)  a check was started (throttles the retries)
  done(home)     a check finished (up to date, or the new release is in the profile): the 6 hours start here

Stamps live in the profile (~/.claude): kit-update-check.stamp (last finished check), kit-update-attempt.stamp (last start)."""
import os
import time

EVERY = 6 * 3600
RETRY = 15 * 60
CHECK, ATTEMPT = "kit-update-check.stamp", "kit-update-attempt.stamp"


def boot_time():
    """Epoch seconds of the last start of the computer; 0 when it cannot be told."""
    try:
        if os.name == "nt":
            import ctypes
            return time.time() - ctypes.windll.kernel32.GetTickCount64() / 1000.0
        with open("/proc/uptime", encoding="utf-8") as f:
            return time.time() - float(f.read().split()[0])
    except Exception:  # noqa: BLE001
        return 0.0


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


def _touch(p):
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def due(home, now=None, boot=None):
    now = time.time() if now is None else now
    att = _mtime(os.path.join(home, ATTEMPT))
    if att is not None and now - att < RETRY:
        return False
    ok = _mtime(os.path.join(home, CHECK))
    if ok is None:
        return True
    boot = boot_time() if boot is None else boot
    return now - ok >= EVERY or ok < boot


def attempt(home):
    _touch(os.path.join(home, ATTEMPT))


def done(home):
    _touch(os.path.join(home, CHECK))
