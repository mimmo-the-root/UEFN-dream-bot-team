#!/usr/bin/env python3
"""brain_hot.py - copy newer kit second-brain hooks into the profile without a restart.

Usage: python brain_hot.py [--home DIR] [--kit DIR]

Called by the pipeline guardian every cycle and by ensure-brain.ps1 at session start.
"""
import argparse
import os
import shutil
import sys

NAMES = ("brain_brief.py", "brain_upkeep.py")


def profile_home(home=None):
    return os.path.abspath(home or os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude"))


def kit_hooks(home=None, kit=None):
    if kit:
        return os.path.abspath(kit)
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = (
        os.path.join(home, "kit-template", "Claude", "hooks"),
        os.path.abspath(os.path.join(here, "..", "project-template", "Claude", "hooks")),
        here,
    )
    for path in candidates:
        if os.path.isfile(os.path.join(path, "brain_brief.py")):
            return path
    return candidates[0]


def brain_hot_update(home=None, kit=None, names=NAMES):
    home = profile_home(home)
    source_dir = kit_hooks(home, kit)
    target_dir = os.path.join(home, "hooks")
    copied = []
    for name in names:
        source = os.path.join(source_dir, name)
        if not os.path.isfile(source):
            continue
        target = os.path.join(target_dir, name)
        if os.path.normcase(os.path.abspath(source)) == os.path.normcase(os.path.abspath(target)):
            continue
        if os.path.isfile(target) and os.path.getmtime(source) <= os.path.getmtime(target):
            continue
        try:
            os.makedirs(target_dir, exist_ok=True)
            if os.path.isfile(target):
                shutil.copyfile(target, target + ".old")
            shutil.copy2(source, target)
            copied.append(name)
        except OSError:
            continue
    return copied


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hot-update the profile's second-brain hooks")
    parser.add_argument("--home")
    parser.add_argument("--kit")
    args = parser.parse_args(argv)
    copied = brain_hot_update(args.home, args.kit)
    if os.environ.get("BRAIN_HOT_VERBOSE") == "1":
        print("brain hot update: " + (", ".join(copied) if copied else "up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
