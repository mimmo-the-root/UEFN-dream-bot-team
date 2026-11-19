#!/usr/bin/env python3
"""
Swap task releases.
A new idea must name the task that leaves the release; it edits the Release column of both rows
and logs the swap. Works on ROADMAP.md table rows.
Usage: python tools/swap_task.py <task_enters> <task_leaves> <new_release> [--from-release <from_release>]
"""
import re
import sys
from pathlib import Path

ROADMAP_PATH = Path("docs") / "ROADMAP.md"


def swap_tasks(task_enters: str, task_leaves: str, new_release: str, from_release: str | None = None):
    """
    Swap two task releases: task_enters gets new_release, task_leaves leaves its release.
    If from_release is not given, task_leaves is set to empty (becomes backlog/Later).
    Returns True if both rows were found and updated.
    """
    if not ROADMAP_PATH.exists():
        raise FileNotFoundError(f"Roadmap not found: {ROADMAP_PATH}")

    with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    # Find rows matching | T-NNN | ... | Release | ...
    # Column order: ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source
    task_enters_row = None
    task_leaves_row = None

    for i, line in enumerate(lines):
        if line.startswith("| T-"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 6:
                task_id = cells[0]
                if task_id == task_enters:
                    task_enters_row = i
                elif task_id == task_leaves:
                    task_leaves_row = i

    if task_enters_row is None:
        raise ValueError(f"Task row not found: {task_enters}")
    if task_leaves_row is None:
        raise ValueError(f"Task row not found: {task_leaves}")

    # Update the Release column (index 5) of both rows
    def update_release(line, new_release_val):
        cells = line.split("|")
        cells[6] = f" {new_release_val} "  # index 6 = Release column (6th cell after ID)
        return "|".join(cells)

    lines[task_enters_row] = update_release(lines[task_enters_row], new_release)
    lines[task_leaves_row] = update_release(lines[task_leaves_row], from_release or "")

    content = "\n".join(lines)

    with open(ROADMAP_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # Log the swap
    swap_log = Path("plan") / "SWAP-LOG.md"
    swap_log.parent.mkdir(parents=True, exist_ok=True)
    with open(swap_log, "a", encoding="utf-8") as f:
        f.write(f"- {task_leaves} -> {new_release}; {task_enters} -> {from_release or 'Later'}\n")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Swap task releases in ROADMAP.md")
    parser.add_argument("task_enters", help="Task ID that enters the release")
    parser.add_argument("task_leaves", help="Task ID that leaves the release")
    parser.add_argument("new_release", help="New release value for task_enters")
    parser.add_argument("--from-release", help="Release for task_leaves (default: empty/Later)")

    args = parser.parse_args()

    try:
        swap_tasks(args.task_enters, task_leaves=args.task_leaves, new_release=args.new_release,
                   from_release=args.from_release)
    except (FileNotFoundError, ValueError) as e:
        print(f"swap_task: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
