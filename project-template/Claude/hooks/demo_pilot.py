#!/usr/bin/env python3
"""Pilot demo (v1.114): the Chicken Roundup example shipped with the kit. Engine of /demo and of the Docs page button.

  python Claude/hooks/demo_pilot.py list
  python Claude/hooks/demo_pilot.py copy [Content folder]          # to Claude/docs/demo-chicken-roundup/  (your files are untouched)
  python Claude/hooks/demo_pilot.py load [Content folder]          # to Claude/docs/ of a NEW EMPTY test project (no game spec yet)

Never overwrites: a file that already exists is skipped and reported. `load` refuses when GAME-SPEC.md, PLAN.md or ROADMAP tasks exist."""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "reference", "demo-chicken-roundup")


def files():
    try:
        return sorted(f for f in os.listdir(SRC) if f.endswith(".md"))
    except OSError:
        return []


def docs(base):
    return os.path.join(base, "Claude", "docs") if os.path.isdir(os.path.join(base, "Claude")) else os.path.join(base, "docs")


def put(dest, names):
    os.makedirs(dest, exist_ok=True)
    done, skipped = [], []
    for n in names:
        t = os.path.join(dest, n)
        if os.path.exists(t):
            skipped.append(n)
        else:
            shutil.copyfile(os.path.join(SRC, n), t)
            done.append(n)
    return done, skipped


def started(d):
    for n in ("GAME-SPEC.md", "PLAN.md"):
        if os.path.isfile(os.path.join(d, n)):
            return n
    try:
        t = open(os.path.join(d, "ROADMAP.md"), encoding="utf-8").read()
    except OSError:
        return ""
    return "ROADMAP.md" if "| T-0" in t else ""


def main(argv):
    cmd = argv[0] if argv else "list"
    base = next((a for a in argv[1:] if not a.startswith("--")), os.getcwd())
    names = files()
    if not names:
        print("The demo files are missing: update the kit (/kit-update).")
        return 1
    if cmd == "list":
        print("Pilot demo: Chicken Roundup\n" + "\n".join("  " + n for n in names))
        return 0
    d = docs(base)
    if cmd == "copy":
        done, skipped = put(os.path.join(d, "demo-chicken-roundup"), names)
    elif cmd == "load":
        s = started(d)
        if s:
            print("This project already has %s: the demo is loaded only in an empty project (use `copy`)." % s)
            return 1
        done, skipped = put(d, [n for n in names if n != "README.md"])
    else:
        print(__doc__)
        return 2
    print("Copied: %s" % (", ".join(done) or "nothing"))
    if skipped:
        print("Skipped (already there): %s" % ", ".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
