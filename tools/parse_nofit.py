#!/usr/bin/env python3
"""Parse a NOFIT answer ('NOFIT: <reason> | SPLIT: <smaller packages>') from relay result text.

Usage: python tools/parse_nofit.py <result-file>
Prints JSON {"nofit": bool, "reason": str, "split": [str]}; always exits 0 on readable input.
"""
import json
import re
import sys

PATTERN = re.compile(r"^\s*NOFIT:\s*(?P<reason>.*?)\s*(?:\|\s*SPLIT:\s*(?P<split>.*))?$")


def parse_nofit(text):
    """Return a dict; a result without a NOFIT line is not-nofit."""
    for line in text.splitlines():
        m = PATTERN.match(line)
        if m:
            split = [s.strip() for s in re.split(r"[;,]", m.group("split") or "") if s.strip()]
            return {"nofit": True, "reason": m.group("reason"), "split": split}
    return {"nofit": False, "reason": "", "split": []}


def main(argv):
    if len(argv) != 2:
        print("usage: python tools/parse_nofit.py <result-file>")
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print("FAIL cannot read %s: %s" % (argv[1], e))
        return 2
    print(json.dumps(parse_nofit(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
