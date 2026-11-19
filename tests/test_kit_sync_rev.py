#!/usr/bin/env python3
"""Tests for the console revision guard in kit_sync.py (T-103): an older template page must not replace a newer project page."""
import importlib.util
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location("kit_sync", os.path.join(ROOT, "project-template", "Claude", "hooks", "kit_sync.py"))
ks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ks)
REL = "Claude/hooks/agent-console.html"


def page(rev, body="x"):
    return ("<html><head>\n<!-- kit-console-rev: %d -->\n</head><body>%s</body></html>" % (rev, body)) if rev else "<html><body>%s</body></html>" % body


def setup(tpl_rev, prj_rev):
    tmp = tempfile.mkdtemp()
    for side, rev in (("tpl", tpl_rev), ("prj", prj_rev)):
        path = os.path.join(tmp, side, *REL.split("/"))
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as f:
            f.write(page(rev, side))
    return os.path.join(tmp, "tpl"), os.path.join(tmp, "prj"), os.path.join(tmp, "prj", *REL.split("/"))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_older_template_does_not_overwrite():
    tpl, prj, dst = setup(2, 3)
    del ks.SKIPPED_OLDER[:]
    changed, added, _ = ks.sync_files(prj, tpl)
    assert "prj" in read(dst) and not changed, (changed, read(dst))
    assert REL in ks.SKIPPED_OLDER


def test_template_without_marker_does_not_overwrite_marked_page():
    tpl, prj, dst = setup(0, 3)
    changed, _, _ = ks.sync_files(prj, tpl)
    assert "prj" in read(dst) and not changed


def test_newer_template_overwrites():
    tpl, prj, dst = setup(4, 3)
    changed, _, _ = ks.sync_files(prj, tpl)
    assert "tpl" in read(dst) and REL in changed


def test_project_without_marker_keeps_old_behaviour():
    tpl, prj, dst = setup(3, 0)
    changed, _, _ = ks.sync_files(prj, tpl)
    assert "tpl" in read(dst) and REL in changed


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print("ok   %s" % name)
        except Exception as e:  # noqa: BLE001
            failed.append(name)
            print("FAIL %s: %s" % (name, e))
    if failed:
        print("\nFAILED: %s" % ", ".join(failed))
        return 1
    print("\nPASS kit_sync_rev: %d/%d cases" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
