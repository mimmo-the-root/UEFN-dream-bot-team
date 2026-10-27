#!/usr/bin/env python3
"""The _to_delete folder of a project: what the kit parked there, so the owner decides when to clean.
  python to_delete.py list  <project>                 # JSON: folders, files, sizes
  python to_delete.py park  <project> <path>...       # move files or folders into _to_delete/<timestamp>/ (never deletes)
  python to_delete.py open  <project>                 # opens the folder in the file manager
  python to_delete.py clean <project> <folder|--all>  # deletes one parked folder (name yyyymmdd-hhmmss) or all of them
Only paths inside <project>/_to_delete are ever deleted. Prints one JSON object. Exit 0."""
import json, os, re, shutil, subprocess, sys, time
NAME = re.compile(r"^\d{8}-\d{6}(-\d+)?$")

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
            if os.path.isdir(p) and NAME.match(n):
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
    r = root(project)
    if not os.path.isdir(r): return {"ok": True, "deleted": []}
    names = [n for n in os.listdir(r) if NAME.match(n)] if which == "--all" else ([which] if NAME.match(which or "") else [])
    if not names: return {"ok": True, "deleted": []} if which == "--all" else {"ok": False, "error": "unknown folder"}
    gone = []
    for n in names:
        p = os.path.join(r, n)
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
