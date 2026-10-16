#!/usr/bin/env python3
"""The small release chores that were forgotten once: the README "What's new" must name the current version,
CHANGELOG's first entry must be the current version, and the manual's console chapter must explain each page."""
import os, re, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def read(*p):
    with open(os.path.join(root, *p), encoding="utf-8") as f:
        return f.read()
ver = read("project-template", "Claude", "KIT-VERSION").strip()
major, minor = ver.split(".")[:2]
fails = []
heads = [l for l in read("README.md").splitlines() if l.startswith("## What's new")]
if not any(re.search(r"v%s\.%s\b" % (major, minor), h) for h in heads):
    fails.append("README.md: no '## What's new (...)' heading names v%s.%s (add this release to the README)" % (major, minor))
m = re.search(r"^## v(\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M)
if not m or m.group(1) != ver:
    fails.append("CHANGELOG.md: first entry is %s, KIT-VERSION is %s" % (m.group(1) if m else "missing", ver))
con = read("docs", "manual", "the-console.md")
for page in ("Console", "Stats", "Docs", "Flow", "Skills", "What's new"):
    sec = re.search(r"^## %s\n(.*?)(?=^## |\Z)" % re.escape(page), con, re.M | re.S)
    if not sec or "Why it is there" not in sec.group(1):
        fails.append("docs/manual/the-console.md: page '%s' has no 'Why it is there' paragraph" % page)
if fails:
    print("\n".join(fails)); sys.exit(1)
print("release docs ok")
