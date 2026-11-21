#!/usr/bin/env python3
"""Print the short plan cache into session context. Read-only; at most 40 lines."""
import os
import sys

MAX_LINES = 40


def read_lines(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return [line.rstrip("\r\n") for line in handle]
    except OSError:
        return []


def do_first_line(lines):
    for raw in lines:
        text = raw.strip()
        if text.startswith("DO FIRST"):
            return text
        if text.startswith(">>>"):
            return "DO FIRST: " + text[3:].strip()
    return ""


def short_cache(project=None, limit=MAX_LINES):
    project = project or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    plan = os.path.join(project, "Claude", "plan")
    hot = read_lines(os.path.join(plan, "HOT.md"))
    directive = do_first_line(read_lines(os.path.join(plan, "NUDGE.md")))
    lines = []
    if hot:
        lines.append("--- plan/HOT.md ---")
        room = limit - (1 if directive else 0)
        lines.extend(hot[:max(0, room - 1)])
    if directive:
        lines.append(directive)
    lines = lines[:limit]
    return "\n".join(lines) + ("\n" if lines else "")


def main(argv=None):
    sys.stdout.write(short_cache())
    return 0


if __name__ == "__main__":
    sys.exit(main())
