"""install-lean-profile.py - v1.124.19: replace the long base rules 1-13 in ~/.claude/CLAUDE.md with the short
version (KIT block base-rules) and install the full texts in ~/.claude/kit-rules/.

  python tool/install-lean-profile.py <kit user-level-memory folder> <~/.claude folder>

Safe: a backup CLAUDE.md.before-lean-<timestamp> is written first; the owner's second brain path is kept;
sections the owner added (headings that are not base rules 1-13) and every KIT block are kept untouched.
Running it again only refreshes the block."""
import os, re, shutil, sys, time

src, dst = sys.argv[1], sys.argv[2]
core_src = open(os.path.join(src, "CLAUDE.md"), encoding="utf-8").read().replace("\r\n", "\n")
block = re.search(r"<!-- KIT:BEGIN base-rules -->.*?<!-- KIT:END base-rules -->", core_src, re.S).group(0)
intro = core_src[:core_src.index("<!-- KIT:BEGIN base-rules -->")]

rules_dst = os.path.join(dst, "kit-rules")
os.makedirs(rules_dst, exist_ok=True)
for n in sorted(os.listdir(os.path.join(src, "rules"))):
    if n.endswith(".md"):
        shutil.copyfile(os.path.join(src, "rules", n), os.path.join(rules_dst, n))

path = os.path.join(dst, "CLAUDE.md")
if not os.path.isfile(path):
    open(path, "w", encoding="utf-8").write(core_src); print("  created CLAUDE.md (short base rules)"); sys.exit(0)
raw = open(path, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
t = raw.replace("\r\n", "\n")

m = re.search(r"\*\*Second brain path\*\*:\s*`([^`]*)`", t)
brain = m.group(1) if m else "<SECOND_BRAIN_PATH>"
blk = block.replace("`<SECOND_BRAIN_PATH>`", "`%s`" % brain) if brain != "<SECOND_BRAIN_PATH>" else block

cur = re.search(r"<!-- KIT:BEGIN base-rules -->.*?<!-- KIT:END base-rules -->", t, re.S)
if cur:
    if cur.group(0) == blk:
        print("  short base rules already current"); sys.exit(0)
    out, msg = t[:cur.start()] + blk + t[cur.end():], "short base rules refreshed"
else:
    first_kit = t.find("<!-- KIT:BEGIN")
    region_end = first_kit if first_kit >= 0 else len(t)
    region, rest = t[:region_end], t[region_end:]
    sections = re.split(r"(?m)^(?=## )", region)
    base = re.compile(r"## (?:[1-9]|1[0-3])\. ")
    kept = [s for s in sections[1:] if not base.match(s)]
    found = len(sections) - 1 - len(kept)
    if found == 0:
        out, msg = blk + "\n\n" + t, "short base rules added at the top (no old base rules found)"
    else:
        out = intro + blk + "\n\n" + "".join(kept) + rest
        msg = "base rules 1-13 (%d sections) replaced with the short version; %d own section(s) kept" % (found, len(kept))
    bak = path + ".before-lean-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(path, bak)
    msg += "; backup " + os.path.basename(bak)
open(path, "w", encoding="utf-8", newline="").write(out.replace("\n", nl))
print("  " + msg + (" (second brain path kept)" if brain != "<SECOND_BRAIN_PATH>" else ""))
