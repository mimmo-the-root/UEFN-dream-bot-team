#!/usr/bin/env python3
"""
DO FIRST nudge injector hook.
Checks plan/NUDGE.md for a top line starting with '>>>'.
If present, prints 'DO THIS FIRST: <line>' and exits 0.
If missing or no '>>>' line, prints nothing and exits 0.
"""
import sys
from pathlib import Path

NUDGE_PATH = Path(__file__).parent.parent / "plan" / "NUDGE.md"


def nudge_inject(nudge_path: Path = NUDGE_PATH) -> str | None:
    """Read plan/NUDGE.md and return 'DO THIS FIRST: <line>' if top line starts with '>>>'."""
    if not nudge_path.exists():
        return None

    try:
        content = nudge_path.read_text(encoding="utf-8")
    except Exception:
        return None

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return None

    top_line = lines[0]
    if top_line.startswith(">>>"):
        directive = top_line[3:].strip()
        return f"DO THIS FIRST: {directive}"

    return None


def main():
    message = nudge_inject()
    if message:
        print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
