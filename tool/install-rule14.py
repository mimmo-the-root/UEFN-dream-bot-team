import os, re, sys
src, dst = sys.argv[1], sys.argv[2]
new = open(src, encoding="utf-8").read().replace("\r\n", "\n").strip("\n")
if not os.path.isfile(dst):
    open(dst, "w", encoding="utf-8", newline="").write(new + "\n"); print("  created CLAUDE.md with rule 14"); sys.exit(0)
t = open(dst, encoding="utf-8", newline="").read(); nl = "\r\n" if "\r\n" in t else "\n"; t = t.replace("\r\n", "\n")
blk = re.compile(r"<!-- KIT:BEGIN kit-self-update -->.*?<!-- KIT:END kit-self-update -->", re.S)
old = re.compile(r"\n## 14\. Kit self-update.*?(?=\n## |\Z)", re.S)
if blk.search(t): t = blk.sub(lambda m: new, t, 1); msg = "rule 14 refreshed"
elif old.search(t): t = old.sub("\n" + new + "\n", t, 1); msg = "rule 14 replaced with new version"
else: t = t.rstrip("\n") + "\n\n" + new + "\n"; msg = "rule 14 added"
open(dst, "w", encoding="utf-8", newline="").write(t.replace("\n", nl)); print("  " + msg)
