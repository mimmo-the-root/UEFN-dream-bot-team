"""Prints the CHANGELOG.md entry of a version: first line = release title, then a blank line, then the notes.
Usage: python tool/release_notes.py v1.98.7   (used by .github/workflows/release.yml)"""
import re, sys
ver = sys.argv[1].lstrip("v")
log = open("CHANGELOG.md", encoding="utf-8").read()
m = re.search(r"(?ms)^## (v" + re.escape(ver) + r"\b[^\r\n]*)\r?\n(.*?)(?=^## |\Z)", log)
if not m:
    sys.exit("CHANGELOG.md has no '## v%s ...' entry" % ver)
sys.stdout.reconfigure(encoding="utf-8")
print(m.group(1).strip()); print(); print(m.group(2).strip())
