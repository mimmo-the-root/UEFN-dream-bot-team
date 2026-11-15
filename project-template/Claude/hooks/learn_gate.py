#!/usr/bin/env python3
"""learn_gate.py - learning runs ONCE at the end of a release, not after every change (v1.124.23).

Before, the kit re-read the changed Verse files, documents and devices at every session start and every 30 minutes of a
long session: the same files were read again and again while a release was still being built. Now the learning of an
already learned map waits until a release is closed (every task of that release Done in ROADMAP.md) and then runs once.

Always allowed: the first learning of a map (nothing learned yet) and the owner's Learn button on the console.
Switch back to the old behaviour with `learn: every-change` in Claude/LAB-PROJECT.txt or UEFN_KIT_LEARN=every-change.

  python Claude/hooks/learn_gate.py [project]      prints whether learning is due and why"""
import json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SKIP = {"", "later", "backlog", "-", "earlier"}


def _state_path(project):
    return os.path.join(project, "Claude", "logs", "learn-release.json")


def _read(project):
    try:
        with open(_state_path(project), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _write(project, st):
    p = _state_path(project)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)


def every_change(project):
    if os.environ.get("UEFN_KIT_LEARN", "").lower() == "every-change":
        return True
    try:
        with open(os.path.join(project, "Claude", "LAB-PROJECT.txt"), encoding="utf-8-sig") as f:
            return bool(re.search(r"(?im)^\s*learn\s*:\s*every-change\s*$", f.read()))
    except OSError:
        return False


def closed_releases(project):
    """Releases whose tasks are all Done (at least one task; the backlog never counts)."""
    try:
        import score
        ts = score.tasks(project)
    except Exception:
        return []
    by = {}
    for t in ts:
        rel = (t.get("rel") or "").strip()
        if rel.lower() in SKIP:
            continue
        by.setdefault(rel, []).append(bool(t.get("done")))
    return sorted(r for r, d in by.items() if d and all(d))


def due(project, first_pass=False):
    """(True/False, why). first_pass = the map has never been learned (always due)."""
    if first_pass:
        return True, "first learning of this map"
    if every_change(project):
        return True, "learn: every-change"
    st = _read(project)
    closed = closed_releases(project)
    if "known" not in st:   # first run of this rule: releases already closed before it are not learned again
        st = {"known": closed, "learned": closed, "since": time.strftime("%Y-%m-%d %H:%M")}
        _write(project, st)
    new = [r for r in closed if r not in st.get("learned", [])]
    if new:
        return True, "release %s closed" % ", ".join(new)
    return False, "waiting for the end of the release (changes are learned once, when its last task is Done)"


def mark_learned(project):
    """Called when nothing is pending any more: the closed releases count as learned."""
    st = _read(project)
    closed = closed_releases(project)
    st["known"] = sorted(set(st.get("known", [])) | set(closed))
    st["learned"] = sorted(set(st.get("learned", [])) | set(closed))
    st["at"] = time.strftime("%Y-%m-%d %H:%M")
    _write(project, st)


if __name__ == "__main__":
    pr = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(HERE))
    d, why = due(pr)
    print(("LEARN DUE: " if d else "LEARN WAITS: ") + why)
