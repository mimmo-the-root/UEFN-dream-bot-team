#!/usr/bin/env python3
"""Traces of other projects in a map's assets (v1.110). Lives in ~/.claude/hooks. Never blocks anything.

Assets copied by hand between your projects keep the internal name of the project they came from, imports of assets that do not
exist here, and the Windows user name of the import paths. Epic's duplicate-island check (no multiple copies of the same island or
metadata) may look at such metadata. This only reports; it is a warning, not a block.

  map_trace.py [project folder]            print what the scan finds (writes nothing)
  map_trace.py [project folder] --apply    also record ONE bug row in Claude/docs/BUGS.md (Newly reported), once

A Fab product is skipped (fab_pack.py check does this scan for it). Reading only; the assets are never changed.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TITLE = "Assets keep traces of other projects"


def find_root(base):
    b = os.path.abspath(base)
    for _ in range(4):
        if os.path.isdir(os.path.join(b, "Content")) and any(f.endswith(".uefnproject") for f in os.listdir(b)):
            return b
        b = os.path.dirname(b)
    return None


def scan(root):
    """(findings, notes): every finding is a warning, even what a Fab package would block."""
    import fab_assets
    blocks, warns, notes = fab_assets.scan(root)
    return list(blocks) + list(warns), list(notes)


def _next_id(text):
    ids = [int(x) for x in re.findall(r"B-(\d{3})", text)]
    return "B-%03d" % ((max(ids) if ids else 0) + 1)


def record(root, findings):
    """One row in BUGS.md under 'Newly reported' (created if missing). Returns 'added', 'exists' or 'no-bugs-file'."""
    p = os.path.join(root, "Claude", "docs", "BUGS.md")
    if not os.path.isfile(p):
        return "no-bugs-file"
    with open(p, encoding="utf-8", newline="") as f:
        t = f.read()
    nl = "\r\n" if "\r\n" in t else "\n"
    t = t.replace("\r\n", "\n")
    for line in t.split("\n"):
        if TITLE in line and not re.search(r"\|\s*(Fixed|Closed)", line):
            return "exists"
    cause = "Copy and paste between projects: %d finding(s), for example %s" % (len(findings), findings[0][:160].replace("|", "/"))
    row = "| %s: %s | Content assets | minor | %s | Open |" % (_next_id(t), TITLE, cause)
    head = "| Title | Where | Severity | Probable cause | Status |\n|---|---|---|---|---|"
    m = re.search(r"^## Newly reported[^\n]*\n", t, re.M)
    if not m:
        t = t.rstrip("\n") + "\n\n## Newly reported (to be triaged)\n" + head + "\n" + row + "\n"
    else:
        rest = t[m.end():]
        n = re.search(r"^## ", rest, re.M)
        sec_end = m.end() + (n.start() if n else len(rest))
        sec = t[m.end():sec_end]
        if "| Title |" in sec:
            body = sec.rstrip("\n") + "\n" + row + "\n" + ("\n" if n else "")
        else:
            body = sec.rstrip("\n") + "\n" + head + "\n" + row + "\n" + ("\n" if n else "")
        t = t[:m.end()] + body + t[sec_end:]
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t.replace("\n", nl))
    return "added"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    root = find_root(args[0] if args else os.getcwd())
    if not root:
        print("not a UEFN project folder"); return 1
    try:
        import kit_install
        if kit_install.get_kind(root) == "fab":
            print("this is a Fab product: fab_pack.py check does this scan"); return 0
    except Exception:
        pass
    findings, notes = scan(root)
    if not findings:
        print("no traces of other projects found"); return 0
    for x in findings:
        print("WARNING %s" % x)
    for x in notes:
        print("note %s" % x)
    if "--apply" in argv:
        print("BUGS.md: %s" % record(root, findings))
    else:
        print("%d warning(s). Run again with --apply to record one bug row in Claude/docs/BUGS.md." % len(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
