"""T-048: the changelog draft exists and names every Done task id in the roadmap copy it receives. Temp dirs only."""
import os, re, shutil, sys, tempfile

root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
draft = os.path.join(root, "docs", "CHANGELOG-DRAFT-ibrido.md")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

ok(os.path.isfile(draft), "CHANGELOG-DRAFT-ibrido.md exists")

DONE = [
    "T-014", "T-019", "T-022", "T-023", "T-024", "T-025", "T-026", "T-028",
    "T-030", "T-035", "T-038", "T-040", "T-050", "T-051", "T-052", "T-053",
    "T-054", "T-055", "T-056", "T-057", "T-058", "T-059", "T-060", "T-061",
    "T-062", "T-063", "T-064", "T-065", "T-066", "T-067", "T-068", "T-069",
    "T-070", "T-072", "T-073", "T-074", "T-075", "T-076", "T-077", "T-078",
    "T-079", "T-080", "T-084", "T-085", "T-086", "T-087", "T-088", "T-089",
    "T-091", "T-093", "T-094", "T-098", "T-101", "T-103", "T-104", "T-105",
    "T-106", "T-107", "T-108", "T-109", "T-110", "T-111", "T-112", "T-113",
    "T-116", "T-118",
]


def check(draft_copy, roadmap_copy):
    raw = open(draft_copy, "rb").read()
    ok(b"\r" not in raw.replace(b"\r\n", b""), "draft has LF endings")
    text = raw.decode("utf-8")
    ok(len(re.findall(r"(?m)^## ", text)) >= 5, "draft is grouped by area")
    ok("ibrido-0" in text.lower(), "draft names the local slices")
    roadmap = open(roadmap_copy, encoding="utf-8").read()
    ids = []
    for line in roadmap.splitlines():
        row = re.match(r"\|\s*(T-\d{3})\s*\|[^|]*\|\s*Done\b", line)
        if row:
            ids.append(row.group(1))
    ok(ids == DONE, "roadmap copy has the Done rows (%d)" % len(ids))
    missing = [task for task in ids if task not in text]
    ok(not missing, "draft lists every Done id (%d checked)" % len(ids))


with tempfile.TemporaryDirectory() as d:
    roadmap_copy = os.path.join(d, "ROADMAP.md")
    with open(roadmap_copy, "w", encoding="utf-8", newline="\n") as f:
        f.write("| ID | Feature | Status | Acceptance criteria | Priority | Release | Kind | Source |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for task in DONE:
            f.write("| %s | Shipped work | Done - merged | criteria | P1 | P0-R3 | feature | owner |\n" % task)
    draft_copy = os.path.join(d, "CHANGELOG-DRAFT-ibrido.md")
    shutil.copyfile(draft, draft_copy)
    check(draft_copy, roadmap_copy)
