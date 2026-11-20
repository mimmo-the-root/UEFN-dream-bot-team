#!/usr/bin/env python3
"""T-113: the pipeline remembers. Lessons go to V/wiki/hot.md (## Lessons, newest first, capped) and V/wiki/kit/lessons.md.

Usage:
  lessons.py add --vault V --text LINE [--source ID]
  lessons.py from-problems --lab LAB --vault V
  lessons.py seed --vault V
"""
import argparse
import json
import os
import re
import sys
from datetime import date

MAX_LEN = 200
HOT_CAP = 6000
SECTION = "## Lessons"
SEED = [
    "A status call takes 12 s: write the roadmap in one batch before long tests.",
    "The Claude Code classifier blocks some Cod commands: the planner or integrator does the git steps.",
    "The planner channel only fires when Cod ends a turn: Cod must never idle and loops with relay.",
    "Agent names must match exactly (learn-slicer).",
    "A test must never start the real integrator or the real suite.",
    "The vault is C:\\SecondBrainOssidian.",
]


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().replace("\r\n", "\n")
    except OSError:
        return ""


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()


def make_line(text, source="manual", day=None):
    """Return 'date | source | rule', total max MAX_LEN chars."""
    head = "%s | %s | " % (day or date.today().isoformat(), _clean(source) or "manual")
    rule = _clean(text)
    room = max(MAX_LEN - len(head), 0)
    if len(rule) > room:
        rule = rule[:max(room - 3, 0)].rstrip() + "..."
    return head + rule


def _rule(line):
    parts = line.split(" | ", 2)
    return (parts[2] if len(parts) == 3 else line).strip().lower()


def _split_hot(text):
    """Return (before, lesson_lines, after); lessons are '- ' bullets of the Lessons section."""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == SECTION), None)
    if start is None:
        return text, None, ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    items = [l[2:] for l in lines[start + 1:end] if l.startswith("- ")]
    return "\n".join(lines[:start]), items, "\n".join(lines[end:])


def _render_hot(before, items, after):
    out = (before.rstrip("\n") + "\n\n" if before.strip() else "") + SECTION + "\n"
    out += "".join("- %s\n" % i for i in items)
    if after.strip():
        out += "\n" + after.strip("\n") + "\n"
    return out


def add_lesson(vault, text, source="manual", day=None):
    """Add one lesson. Returns True if added, False if it was a duplicate."""
    line = make_line(text, source, day)
    hot_path = os.path.join(vault, "wiki", "hot.md")
    kit_path = os.path.join(vault, "wiki", "kit", "lessons.md")
    hot = _read(hot_path)
    before, items, after = _split_hot(hot)
    if items is None:
        before, items, after = hot, [], ""
    if any(_rule(i) == _rule(line) for i in items):
        return False
    items.insert(0, line)
    while len(_render_hot(before, items, after).encode("utf-8")) > HOT_CAP and len(items) > 1:
        items.pop()
    _write(hot_path, _render_hot(before, items, after))
    kit = _read(kit_path) or "# Kit lessons\n\n"
    if not any(_rule(l[2:]) == _rule(line) for l in kit.split("\n") if l.startswith("- ")):
        _write(kit_path, kit.rstrip("\n") + "\n- " + line + "\n")
    return True


def from_problems(lab, vault):
    """Turn new rows of LAB/plan/PROBLEMS-FROM-COD.md into lessons. Returns count added."""
    rows = _read(os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md")).splitlines()
    state_path = os.path.join(lab, "logs", "lessons-state.json")
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            done = int(json.load(f).get("last_line", 0))
    except (OSError, ValueError, AttributeError):
        done = 0
    added = 0
    for n in range(done, len(rows)):
        cols = [c.strip() for c in rows[n].strip().strip("|").split("|")]
        if len(cols) < 4 or cols[0].lower() == "time" or set(rows[n].strip()) <= set("|-: "):
            continue
        day = cols[0][:10] if re.match(r"\d{4}-\d{2}-\d{2}", cols[0]) else None
        if add_lesson(vault, "%s Fix: %s" % (cols[2], cols[3]), cols[1], day):
            added += 1
    _write(state_path, json.dumps({"last_line": len(rows)}))
    return added


def seed(vault):
    return sum(1 for t in reversed(SEED) if add_lesson(vault, t, "seed"))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--vault", required=True)
    a.add_argument("--text", required=True)
    a.add_argument("--source", default="manual")
    f = sub.add_parser("from-problems")
    f.add_argument("--lab", required=True)
    f.add_argument("--vault", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--vault", required=True)
    args = p.parse_args(argv)
    if args.cmd == "add":
        print("added" if add_lesson(args.vault, args.text, args.source) else "duplicate")
    elif args.cmd == "from-problems":
        print("added %d" % from_problems(args.lab, args.vault))
    else:
        print("added %d" % seed(args.vault))
    return 0


if __name__ == "__main__":
    sys.exit(main())
