#!/usr/bin/env python3
"""bump_version.py - raises the kit version in every place at once, so no page ever shows an old one.

  python tool/bump_version.py X.Y.Z [--title "short title"]

Changes: project-template/Claude/KIT-VERSION, every agent-console*.html, README.md (the "What's new (v1.108 - vX.Y.Z)" heading), then rebuilds
the manual, the kit wiki, the kit stats and whats-new.json. Adds a "## vX.Y.Z - title" entry at the top of CHANGELOG.md when there is none
(with a title); write its notes by hand, one bullet per change, starting with [feature], [fix] or [other].
Run it whenever the kit changes in a way the owner can see. publish.ps1 refuses to publish when the versions disagree."""
import glob, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def rd(p):
    return open(p, encoding="utf-8").read()


def wr(p, s):
    open(p, "w", encoding="utf-8", newline="").write(s)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a or not re.match(r"^\d+\.\d+\.\d+$", a[0]):
        print(__doc__)
        return 2
    new = a[0]
    title = sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else ""
    vp = os.path.join(ROOT, "project-template", "Claude", "KIT-VERSION")
    old = rd(vp).strip()
    if old == new:
        print("already %s" % new)
    n = 0
    files = [vp] + sorted(glob.glob(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console*.html"))) + [os.path.join(ROOT, "README.md")]
    for p in files:
        s = rd(p)
        t = re.sub(r"(?<![\d.])" + re.escape(old) + r"(?![\d.])", new, s) if p != vp else new + ("\n" if s.endswith("\n") else "")
        if t != s:
            wr(p, t)
            n += 1
    log = os.path.join(ROOT, "CHANGELOG.md")
    c = rd(log)
    if not re.search(r"^## v" + re.escape(new) + r"\b", c, re.M):
        if not title:
            print("CHANGELOG.md has no entry for v%s: run again with --title \"...\" or add it by hand" % new)
        else:
            c = c.replace("# Changelog\n\n", "# Changelog\n\n## v%s — %s\n\n- [other] **Notes to write.** Replace this line.\n\n" % (new, title), 1)
            wr(log, c)
    print("version %s -> %s in %d file(s)" % (old, new, n))
    for tool in ("build_manual.py", "build_kit_wiki.py", "build_kit_stats.py", "build_whats_new.py"):
        subprocess.run([sys.executable, os.path.join(ROOT, "tool", tool)], cwd=ROOT, stdout=subprocess.DEVNULL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
