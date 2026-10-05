#!/usr/bin/env python3
"""safety_net.py - restore points for a project's Verse code and docs. Zero AI tokens, never deletes anything.

  python Claude/hooks/safety_net.py snapshot [--why TEXT]   copy all .verse files (and Claude/docs/*.md) to a restore point
  python Claude/hooks/safety_net.py changes [--since ID] [--brief]   files added/modified/deleted since a restore point (default: newest)
  python Claude/hooks/safety_net.py list                    restore points, newest first
  python Claude/hooks/safety_net.py restore ID [--apply]    show (default) or perform the restore; first makes a restore point of the current state

Restore points live in Claude/logs/restore-points/<ID>/ and hold files as <name>.bak (UEFN compiles every .verse, so a copy
must never end in .verse). The newest KEEP points are kept; older ones are moved to Claude/logs/restore-points/_old/ (never deleted).
A restore overwrites modified/deleted files from the point; files ADDED after the point are left in place and listed.
"""
import hashlib, json, os, shutil, sys, time

KEEP, CAP_BYTES = 5, 300 * 1024 * 1024
RP = os.path.join("Claude", "logs", "restore-points")


def _files(project):
    for base, dirs, files in os.walk(project):
        rel_base = os.path.relpath(base, project).replace("\\", "/")
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__") and not (rel_base == "Claude" and d == "logs")]
        for f in files:
            rel = (rel_base + "/" + f).lstrip("./") if rel_base != "." else f
            if f.endswith(".verse") or (rel.startswith("Claude/docs/") and f.endswith(".md") and rel.count("/") == 2):
                yield rel


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def current(project):
    return {rel: _sha(os.path.join(project, rel)) for rel in _files(project)}


def points(project):
    root = os.path.join(project, RP)
    if not os.path.isdir(root):
        return []
    return sorted([d for d in os.listdir(root) if d != "_old" and os.path.isfile(os.path.join(root, d, "manifest.json"))], reverse=True)


def _manifest(project, pid):
    return json.load(open(os.path.join(project, RP, pid, "manifest.json"), encoding="utf-8"))


def snapshot(project, why=""):
    cur = current(project)
    total = sum(os.path.getsize(os.path.join(project, r)) for r in cur)
    if total > CAP_BYTES:
        raise ValueError("project text is %d MB, over the %d MB restore-point cap" % (total >> 20, CAP_BYTES >> 20))
    pts = points(project)
    if pts and _manifest(project, pts[0])["files"] == cur:
        return pts[0], False  # nothing changed since the newest point
    pid = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(project, RP, pid)
    for rel in cur:
        t = os.path.join(dest, "files", *rel.split("/")) + ".bak"
        os.makedirs(os.path.dirname(t), exist_ok=True)
        shutil.copy2(os.path.join(project, rel), t)
    json.dump({"id": pid, "why": why, "files": cur}, open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8"), indent=1)
    old = os.path.join(project, RP, "_old")
    for p in points(project)[KEEP:]:
        os.makedirs(old, exist_ok=True)
        shutil.move(os.path.join(project, RP, p), os.path.join(old, p))
    return pid, True


def diff(project, pid):
    base, cur = _manifest(project, pid)["files"], current(project)
    return (sorted(r for r in cur if r not in base), sorted(r for r in cur if r in base and cur[r] != base[r]), sorted(r for r in base if r not in cur))


def restore(project, pid, apply=False):
    added, modified, deleted = diff(project, pid)
    todo = modified + deleted
    if apply and todo:
        snapshot(project, "before restore of " + pid)
        for rel in todo:
            src = os.path.join(project, RP, pid, "files", *rel.split("/")) + ".bak"
            dst = os.path.join(project, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return todo, added


def main():
    a = sys.argv[1:]
    project = os.getcwd()
    if not a:
        print(__doc__); return 0
    cmd = a[0]
    opt = lambda k: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
    if cmd == "snapshot":
        pid, new = snapshot(project, opt("--why") or "")
        print(("Restore point %s created." if new else "No changes since restore point %s.") % pid)
    elif cmd == "list":
        for p in points(project):
            m = _manifest(project, p)
            print("%s  %d files  %s" % (p, len(m["files"]), m.get("why", "")))
    elif cmd == "changes":
        pts = points(project)
        pid = opt("--since") or (pts[0] if pts else None)
        if not pid:
            print("No restore point yet; run snapshot first."); return 0
        ad, mo, de = diff(project, pid)
        if "--brief" in a:
            print("Since restore point %s: %d modified, %d added, %d deleted." % (pid, len(mo), len(ad), len(de)))
        else:
            print("Since restore point %s:" % pid)
            for tag, lst in (("modified", mo), ("added", ad), ("deleted", de)):
                for r in lst:
                    print("  %-8s %s" % (tag, r))
            if not (ad or mo or de):
                print("  no changes")
    elif cmd == "restore":
        if len(a) < 2:
            print("usage: restore ID [--apply]"); return 1
        todo, added = restore(project, a[1], "--apply" in a)
        verb = "Restored" if "--apply" in a else "Would restore"
        print("%s %d file(s) from %s%s" % (verb, len(todo), a[1], "" if "--apply" in a else " (add --apply to do it)"))
        for r in todo[:30]:
            print("  " + r)
        if added:
            print("%d file(s) added since then were left in place (e.g. %s)." % (len(added), added[0]))
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("safety-net failed: %s" % e); sys.exit(1)
