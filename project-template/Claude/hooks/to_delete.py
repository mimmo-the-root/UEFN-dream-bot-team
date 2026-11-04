#!/usr/bin/env python3
"""The _to_delete folder of a project: what the kit parked there, so the owner decides when to clean.
  python to_delete.py list  <project>                 # JSON: folders, files, sizes
  python to_delete.py park  <project> <path>...       # move files or folders into _to_delete/<timestamp>/ (never deletes)
  python to_delete.py open  <project>                 # opens the folder in the file manager
  python to_delete.py clean <project> <folder|--all>  # deletes one parked folder (name yyyymmdd-hhmmss) or all of them
Only paths inside <project>/_to_delete are ever deleted. Prints one JSON object. Exit 0."""
import json, os, re, shutil, subprocess, sys, time
NAME = re.compile(r"\d{8}-\d{6}(-\d+)?")   # used with fullmatch: a trailing newline does not pass

def root(project):
    return os.path.join(project, "_to_delete")

def _size(p):
    if os.path.isfile(p): return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(p) for f in fs if os.path.isfile(os.path.join(a, f)))

def listing(project):
    r, out = root(project), []
    if os.path.isdir(r):
        for n in sorted(os.listdir(r), reverse=True):
            p = os.path.join(r, n)
            if os.path.isdir(p) and NAME.fullmatch(n):
                files = [os.path.relpath(os.path.join(a, f), p).replace("\\", "/") for a, _, fs in os.walk(p) for f in fs]
                out.append({"name": n, "files": files[:50], "count": len(files), "bytes": _size(p)})
    return {"ok": True, "folder": r, "folders": out, "total": sum(x["count"] for x in out), "bytes": sum(x["bytes"] for x in out)}

def park(project, paths, why=""):
    dest = os.path.join(root(project), time.strftime("%Y%m%d-%H%M%S"))
    moved = []
    for p in paths:
        ap = os.path.realpath(p)
        if not ap.startswith(os.path.realpath(project) + os.sep) or ap.startswith(os.path.realpath(root(project))) or not os.path.exists(ap):
            continue
        rel = os.path.relpath(ap, os.path.realpath(project))
        t = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(t), exist_ok=True)
        shutil.move(ap, t); moved.append(rel.replace("\\", "/"))
    return {"ok": True, "moved": moved, "folder": dest}

def open_folder(project):
    r = root(project); os.makedirs(r, exist_ok=True)
    try:
        if hasattr(os, "startfile"): os.startfile(r)
        elif sys.platform == "darwin": subprocess.Popen(["open", r])
        else: subprocess.Popen(["xdg-open", r])
        return {"ok": True, "folder": r}
    except Exception as e:
        return {"ok": False, "error": str(e), "folder": r}

def clean(project, which):
    """Deletes parked folders. The name comes from a request (the console) or the command line, so it is never joined into a path: a parked folder is
    picked from the directory listing by exact name, and the resolved path must still be a direct child of _to_delete (no link, no .. , no newline tricks)."""
    r = os.path.realpath(root(project))
    if not os.path.isdir(r): return {"ok": True, "deleted": []}
    which = which if isinstance(which, str) else ""
    if which != "--all" and not NAME.fullmatch(which): return {"ok": False, "error": "unknown folder"}
    names = [n for n in os.listdir(r) if NAME.fullmatch(n) and (which == "--all" or n == which)]
    if not names: return {"ok": True, "deleted": []}
    gone = []
    for n in names:
        p = os.path.realpath(os.path.join(r, n))
        if os.path.dirname(p) != r or not p.startswith(r + os.sep):
            continue   # a link or a path that leads out of _to_delete is never followed
        if os.path.isdir(p):
            try: shutil.rmtree(p); gone.append(n)
            except OSError as e: return {"ok": False, "error": str(e), "deleted": gone}
    return {"ok": True, "deleted": gone}

def main(a):
    if len(a) < 2: print(json.dumps({"ok": False, "error": "usage"})); return 0
    c, proj = a[0], os.path.abspath(a[1])
    res = listing(proj) if c == "list" else park(proj, a[2:]) if c == "park" else open_folder(proj) if c == "open" else clean(proj, a[2] if len(a) > 2 else "") if c == "clean" else {"ok": False, "error": "unknown command"}
    print(json.dumps(res)); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
