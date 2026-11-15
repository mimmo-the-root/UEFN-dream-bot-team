"""The release notes never carry the placeholder bump_version.py writes ("Notes to write. Replace this line.").
It was left under real notes in 5 releases and GitHub showed it. publish.ps1 runs the tests, so a release with the
placeholder cannot be published: write the notes (or delete the line when the notes are already there)."""
import os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
text = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
bad = []
ver = None
for line in text.splitlines():
    m = re.match(r"^## (v\d+\.\d+\.\d+)", line)
    if m:
        ver = m.group(1)
    elif re.match(r"^- \[other\] \*\*Notes to write\.\*\*", line):
        bad.append(ver or "?")
assert not bad, "CHANGELOG.md still has the placeholder 'Notes to write. Replace this line.' in %s: write the notes or delete the line" % ", ".join(bad)
print("ok changelog_notes")
