#!/usr/bin/env python3
"""check_pr_paths.py - a community PR may only add lesson files under contributions/<genre>/<pattern_id>/<its author>.json.

check_pr_paths(changed, handle) -> list of error strings. CLI: check_pr_paths.py <handle> < list of changed paths (one per line)."""
import re, sys

MAX_FILES = 20
OK_PATH = re.compile(r"contributions/(?:[a-z0-9-]+/p-[0-9a-f]{12}|recipes/[a-z0-9-]+/r-[0-9a-f]{12})/([A-Za-z0-9-]+)\.json")


def check_pr_paths(changed, handle):
    errs = []
    changed = [c for c in changed if c != ""]   # never strip: a name with a space or a newline must fail the pattern, not be cleaned into a valid one
    if not changed:
        return ["the pull request changes no file"]
    if len(changed) > MAX_FILES:
        errs.append("too many files (%d, the limit is %d)" % (len(changed), MAX_FILES))
    for c in changed:
        m = OK_PATH.fullmatch(c)
        if not m:
            errs.append("%s: outside contributions/<genre>/<pattern_id>/<handle>.json or contributions/recipes/<skill>/<recipe_id>/<handle>.json" % c)
        elif m.group(1).lower() != (handle or "").lower():
            errs.append("%s: the file name must be the author's GitHub handle (%s)" % (c, handle))
    return errs


if __name__ == "__main__":
    data = sys.stdin.read()
    names = data.split("\0") if "\0" in data else data.split("\n")   # git diff -z gives NUL separated names
    e = check_pr_paths(names, sys.argv[1] if len(sys.argv) > 1 else "")
    for m in e:
        print(m)
    sys.exit(1 if e else 0)
