#!/usr/bin/env python3
"""Install the kit into a NEW UEFN map, and remember whether a project is a map or a Fab product (v1.108).

Lives in ~/.claude/hooks. The kit template is ~/.claude/kit-template (a copy of project-template).

  python kit_install.py <Content folder or UEFN project root> --dry-run   # list what would be copied
  python kit_install.py <Content folder or UEFN project root> --apply     # copy it (never overwrites a file)
  python kit_install.py --kind <UEFN project root> map|fab                # remember the answer
  python kit_install.py --status <UEFN project root>                      # what is known about it

Rules: the kit is installed ONLY in a map. A Fab product is a small UEFN project whose components are
added to the customer's project later, so project-template is NEVER put in it. The answer
("map" or "fab") is kept in ~/.claude/kit-projects.json, outside the project, so the question is
asked once. Existing files are never overwritten; Claude/docs is never touched. Nothing is deleted.
"""
import re, json, os, shutil, sys

HOME = os.path.join(os.path.expanduser("~"), ".claude")
REGISTRY = os.path.join(HOME, "kit-projects.json")
SKIP_NAMES = {"KIT-VERSION.tmp", "__pycache__", ".git"}
SKIP_TOP = {"logs"}  # per-project data, created by the hooks


def template_dir():
    return os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(HOME, "kit-template")


def _norm(p):
    return os.path.normcase(os.path.abspath(p))


def find_uefn_root(base):
    """(root, content) for a folder that is a UEFN project root, its Content folder, or None."""
    base = os.path.abspath(base)
    for cand in (base, os.path.dirname(base)):
        try:
            if any(n.endswith(".uefnproject") for n in os.listdir(cand)):
                return cand, os.path.join(cand, "Content")
        except OSError:
            pass
    return None


def load_registry():
    try:
        return json.load(open(REGISTRY, encoding="utf-8"))
    except Exception:
        return {}


def name_looks_fab(root):
    """True when the project folder name has FAB as a word (root_FAB_rainbow, Fab-Pack, my.fab)."""
    return bool(re.search(r"(^|[^a-z0-9])fab([^a-z0-9]|$)", os.path.basename(os.path.abspath(root)), re.I))


def registered_kind(root):
    return load_registry().get(_norm(root), {}).get("kind")


def get_kind(root):
    """map / fab as the owner chose it; when nothing was chosen, a folder called ..._FAB_... counts as a Fab product."""
    return registered_kind(root) or ("fab" if name_looks_fab(root) else None)


def set_kind(root, kind):
    if kind not in ("map", "fab"):
        raise ValueError("kind must be map or fab")
    reg = load_registry()
    reg[_norm(root)] = {"kind": kind, "name": os.path.basename(os.path.abspath(root))}
    os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
    json.dump(reg, open(REGISTRY, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def kit_installed(content):
    return os.path.isfile(os.path.join(content, "Claude", "hooks", "kit_sync.py")) and os.path.isfile(os.path.join(content, "CLAUDE.md"))


def plan(content, tpl=None):
    """Files of the template that are missing in `content` (relative paths)."""
    tpl = tpl or template_dir()
    out = []
    for base, dirs, files in os.walk(tpl):
        rel_base = os.path.relpath(base, tpl)
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES and not (rel_base == "Claude" and d in SKIP_TOP)]
        for f in files:
            if f in SKIP_NAMES:
                continue
            rel = os.path.normpath(os.path.join(rel_base, f))
            if not os.path.exists(os.path.join(content, rel)):
                out.append(rel)
    return sorted(out)


def apply(content, tpl=None):
    tpl = tpl or template_dir()
    done = []
    for rel in plan(content, tpl):
        dst = os.path.join(content, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(tpl, rel), dst)  # copy only, never replaces an existing file (plan() skips those)
        done.append(rel)
    return done


def main(argv):
    if not argv:
        print(__doc__); return 2
    if argv[0] == "--kind":
        if len(argv) < 3:
            print("usage: --kind <UEFN project root> map|fab"); return 2
        set_kind(argv[1], argv[2]); print("remembered: %s = %s" % (argv[1], argv[2])); return 0
    if argv[0] == "--status":
        r = find_uefn_root(argv[1]) if len(argv) > 1 else None
        if not r:
            print("not a UEFN project"); return 1
        print("root=%s kind=%s kit_installed=%s" % (r[0], get_kind(r[0]) or "unknown", kit_installed(r[1]))); return 0
    r = find_uefn_root(argv[0])
    if not r:
        print("not a UEFN project folder (no .uefnproject next to Content)"); return 1
    root, content = r
    if get_kind(root) == "fab":
        print("this is a Fab product: the kit is NOT installed in it (components get added to the customer's project)"); return 3
    if not os.path.isdir(os.path.join(os.path.expanduser("~"), ".claude")) or not os.path.isdir(template_dir()):
        print("kit template not found: run update-my-profile.cmd from the kit first"); return 4
    os.makedirs(content, exist_ok=True)
    files = plan(content)
    if "--apply" in argv:
        done = apply(content)
        set_kind(root, "map")
        print("installed %d file(s) into %s; next: read Claude/SETUP-INSTRUCTIONS.md and run it" % (len(done), content)); return 0
    print("dry-run: %d file(s) would be copied into %s (nothing written)" % (len(files), content))
    for f in files[:12]:
        print("  " + f.replace(os.sep, "/"))
    if len(files) > 12:
        print("  ... and %d more" % (len(files) - 12))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
