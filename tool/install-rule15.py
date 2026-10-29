"""Installs (or refreshes) the KIT block 'second-brain-session' (rule 15) in the user's ~/.claude/CLAUDE.md. Never touches anything outside the block.
usage: install-rule15.py <section file> <CLAUDE.md>"""
import os, re, sys
src, dst = sys.argv[1], sys.argv[2]
new = open(src, encoding="utf-8").read().replace("\r\n", "\n").strip("\n")
if not os.path.isfile(dst):
    open(dst, "w", encoding="utf-8", newline="").write(new + "\n"); print("  created CLAUDE.md with rule 15"); sys.exit(0)
t = open(dst, encoding="utf-8", newline="").read(); nl = "\r\n" if "\r\n" in t else "\n"; t = t.replace("\r\n", "\n")
blk = re.compile(r"<!-- KIT:BEGIN second-brain-session -->.*?<!-- KIT:END second-brain-session -->", re.S)
if blk.search(t): t = blk.sub(lambda m: new, t, 1); msg = "rule 15 refreshed"
else: t = t.rstrip("\n") + "\n\n" + new + "\n"; msg = "rule 15 added"
open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl)); print("  " + msg)
