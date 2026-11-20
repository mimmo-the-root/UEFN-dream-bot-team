#!/usr/bin/env python3
"""Director's Cut helper (T-028): turn a proposal table into ROADMAP rows. Prints to stdout, never writes the roadmap.

Input: markdown table with the columns ID, Feature, Acceptance criteria, Priority, Release (any order, extra columns ignored).
Output: '| ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source |' rows.
Usage: python tools/dc_rows.py proposal.md [--source TEXT]
"""
import argparse
import re
import sys

NEEDED = ("id", "feature", "acceptance criteria", "priority", "release")


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(text):
    """Return a list of dicts (one per table data row) from the first table that has all needed columns."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        head = [c.lower() for c in split_row(line)]
        if not all(n in head for n in NEEDED):
            continue
        idx = {n: head.index(n) for n in NEEDED}
        out = []
        for row in lines[i + 1:]:
            if not row.lstrip().startswith("|"):
                break
            cells = split_row(row)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if len(cells) < len(head):
                raise ValueError("row has %d cells, header has %d: %s" % (len(cells), len(head), row[:60]))
            out.append({n: cells[k] for n, k in idx.items()})
        return out
    raise ValueError("no table with columns: " + ", ".join(NEEDED))


def format_rows(items, source="Director's Cut T-028"):
    rows = []
    for it in items:
        if not re.fullmatch(r"T-\d+", it["id"]):
            raise ValueError("bad id: " + it["id"])
        if not re.fullmatch(r"P[0-3]", it["priority"]):
            raise ValueError("bad priority for %s: %s" % (it["id"], it["priority"]))
        if not re.fullmatch(r"P0-R\d+[a-z]?", it["release"]):
            raise ValueError("bad release for %s: %s" % (it["id"], it["release"]))
        rows.append("| %s | %s | To do - Later | %s | %s | %s | feature | %s |" % (
            it["id"], it["feature"], it["acceptance criteria"], it["priority"], it["release"], source))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("table")
    ap.add_argument("--source", default="Director's Cut T-028")
    a = ap.parse_args(argv)
    with open(a.table, encoding="utf-8") as f:
        items = parse(f.read())
    print("\n".join(format_rows(items, a.source)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as e:
        print("dc_rows: " + str(e), file=sys.stderr)
        sys.exit(2)
