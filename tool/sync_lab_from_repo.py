#!/usr/bin/env python3
"""sync_lab_from_repo.py - copy the kit's newest hooks and reference files from this repo into a lab project, before the release is published.

What it is: the same replacement kit_sync does from GitHub, but from the local repo, so the lab can run the next version while it is still unpublished.
Every replaced file is first saved under <Content>/Claude/logs/kit-backup/<stamp>/. Never touches local/, pack/ or caches, never the lab's own data
(logs, _spike, relay, docs). The editor is not involved.

    python tool/sync_lab_from_repo.py <project>/Content [--dry]
"""
import os, shutil, sys, time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude")
SKIP = {"local", "pack", "__pycache__"}


def same(a, b):
    try:
        with open(a, "rb") as x, open(b, "rb") as y:
            return x.read().replace(b"\r\n", b"\n") == y.read().replace(b"\r\n", b"\n")
    except OSError:
        return False


def main(argv):
    if not argv or not os.path.isdir(os.path.join(argv[0], "Claude")):
        print(__doc__)
        return 2
    lab = os.path.join(argv[0], "Claude")
    dry = "--dry" in argv
    stamp = time.strftime("%Y%m%d-%H%M%S")
    done = []
    for sub in ("hooks", "reference", "community"):   # community/ holds the data of the What is new page: left out, the lab kept the news of an old release
        for dp, dn, fn in os.walk(os.path.join(ROOT, sub)):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                src = os.path.join(dp, f)
                rel = os.path.relpath(src, ROOT)
                dst = os.path.join(lab, rel)
                if same(src, dst):
                    continue
                done.append(rel)
                if dry:
                    continue
                if os.path.isfile(dst):
                    bk = os.path.join(lab, "logs", "kit-backup", stamp, rel)
                    os.makedirs(os.path.dirname(bk), exist_ok=True)
                    shutil.copy2(dst, bk)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
    # the kit's own slash commands (.claude/commands/*.md of the kit_sync MANAGED list) live outside Claude/: the lab needs the new learn-map / learn-slice too
    sys.path.insert(0, os.path.join(ROOT, "hooks"))
    try:
        import kit_sync
        cmds = [m for m in kit_sync.MANAGED if m.startswith(".claude/commands/")]
    except Exception:
        cmds = []
    proj = argv[0]
    for rel in cmds:
        src, dst = os.path.join(ROOT, "..", rel), os.path.join(proj, rel)
        if not os.path.isfile(src) or same(src, dst):
            continue
        done.append(rel)
        if dry:
            continue
        if os.path.isfile(dst):
            bk = os.path.join(lab, "logs", "kit-backup", stamp, rel)
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            shutil.copy2(dst, bk)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    ver = os.path.join(ROOT, "KIT-VERSION")
    if os.path.isfile(ver) and not dry:
        shutil.copy2(ver, os.path.join(lab, "KIT-VERSION"))
    print("%s %d file(s)%s" % ("would copy" if dry else "copied", len(done), "" if dry else "; old ones in Claude/logs/kit-backup/" + stamp))
    for r in done[:60]:
        print("  " + r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
