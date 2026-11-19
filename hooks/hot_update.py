#!/usr/bin/env python3
"""
HOT.md cache updater.
Writes plan/HOT.md (current release, tasks in flight, last decisions) after each task change.
Survives a session restart.
"""
import json
import os
import re
from pathlib import Path

# The project root is the current working directory (lab project: Content/)
REPO_ROOT = Path.cwd()
ROADMAP_PATH = REPO_ROOT / "Claude" / "docs" / "ROADMAP.md"
NUDGE_PATH = REPO_ROOT / "Claude" / "plan" / "NUDGE.md"
HOT_PATH = REPO_ROOT / "Claude" / "plan" / "HOT.md"


def get_current_release():
    """Extract the current release name from plan/NUDGE.md."""
    if not NUDGE_PATH.exists():
        return "unknown"
    try:
        content = NUDGE_PATH.read_text(encoding="utf-8")
    except Exception:
        return "unknown"
    # Look for pattern: "Release: <name>"
    m = re.search(r"Release:\s*([^\n]+)", content)
    if m:
        return m.group(1).strip()
    return "unknown"


def get_tasks_in_flight():
    """Extract tasks marked as 'In progress' from ROADMAP.md."""
    tasks = []
    if not ROADMAP_PATH.exists():
        return tasks
    try:
        content = ROADMAP_PATH.read_text(encoding="utf-8")
    except Exception:
        return tasks
    # Find all rows with 'In progress' status
    pattern = r"\|\s*T-(\d{3})\s*\|.*?\|\s*In progress\s*\|"
    for m in re.finditer(pattern, content):
        task_id = m.group(1)
        tasks.append(f"T-{task_id}")
    return tasks


def get_last_decisions():
    """Extract the last decision from plan/NUDGE.md."""
    if not NUDGE_PATH.exists():
        return []
    try:
        content = NUDGE_PATH.read_text(encoding="utf-8")
    except Exception:
        return []
    # Look for the last line that starts with "DECISION:"
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    for line in reversed(lines):
        if line.startswith("DECISION:"):
            return [line[9:].strip()]
    return []


def write_hot_file():
    """Write plan/HOT.md with current state."""
    # Create plan/ directory if it doesn't exist
    HOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    release = get_current_release()
    tasks = get_tasks_in_flight()
    decisions = get_last_decisions()

    hot_content = f"""# HOT.md — {release}

Current release: {release}

Tasks in flight:
{chr(10).join(f"  - {t}" for t in tasks) or "  - none"}

Last decisions:
{chr(10).join(f"  - {d}" for d in decisions) or "  - none"}
"""
    HOT_PATH.write_text(hot_content, encoding="utf-8")
    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Update HOT.md cache")
    parser.add_argument("--force", action="store_true", help="Force update even if no changes")
    args = parser.parse_args()

    return write_hot_file()


if __name__ == "__main__":
    raise SystemExit(main())
