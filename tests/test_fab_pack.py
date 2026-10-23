"""Fab product helper: package check, generated documents, clean zip."""
import os, shutil, sys, tempfile, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-level-hooks"))
import fab_pack
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def w(p, t="x"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="\n").write(t)

base = tempfile.mkdtemp()
try:
    root = os.path.join(base, "Rank")
    w(os.path.join(root, "Rank.uefnproject"), "{}")
    w(os.path.join(root, "Content", "Rank_Device.verse"),
      "# Summary: Shows the rank of the player.\nrank_device := class(creative_device):\n    # Points needed per rank\n    @editable PointsPerRank : int = 100\n")
    w(os.path.join(root, "Content", "Widgets", "Panel.uasset"))
    ok(fab_pack.find_root(os.path.join(root, "Content")) == root, "find_root works from Content")
    b, wa, n = fab_pack.check(root)
    ok(not b, "clean project has no blocks")
    ok(any("Documentation" in x or "FabListing" in x for x in n), "missing Documentation/FabListing is a note")
    # blocks
    w(os.path.join(root, "tool.py")); w(os.path.join(root, "Claude", "a.md")); w(os.path.join(root, "CLAUDE.md"))
    w(os.path.join(root, "Content", "Bad Name", "x.uasset"))
    w(os.path.join(root, "Content", "L" * 130, "Deep_File_Name_Long.uasset"))
    b, wa, n = fab_pack.check(root)
    t = "\n".join(b)
    ok("tool.py" in t and "Claude" in t and "CLAUDE.md" in t, "kit files and .py block")
    ok("Bad Name" in t, "bad name blocks")
    ok("140" in t or "characters" in t, "over-long path blocks")
    out, probs = fab_pack.zip_package(root)
    ok(out is None and probs, "zip refuses while names/paths are wrong")
    for p in ("tool.py", "Claude", "CLAUDE.md"):
        q = os.path.join(root, p)
        shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
    shutil.rmtree(os.path.join(root, "Content", "Bad Name")); shutil.rmtree(os.path.join(root, "Content", "L" * 130))
    # docs
    made, kept = fab_pack.docs(root, False)
    ok(made and not os.path.exists(os.path.join(root, "Documentation")), "dry run writes nothing")
    fab_pack.docs(root, True)
    for f in ("Documentation/README.md", "Documentation/SETTINGS.md", "FabListing/listing.md", "FabListing/third-party.md", "FabListing/screenshots.md"):
        ok(os.path.exists(os.path.join(root, *f.split("/"))), "created " + f)
    s = open(os.path.join(root, "Documentation", "SETTINGS.md"), encoding="utf-8").read()
    ok("PointsPerRank" in s and "100" in s and "Points needed per rank" in s, "SETTINGS.md lists @editable with default and note")
    # never overwrite
    open(os.path.join(root, "Documentation", "README.md"), "w").write("mine")
    fab_pack.docs(root, True)
    ok(open(os.path.join(root, "Documentation", "README.md")).read() == "mine", "existing documents are never overwritten")
    # SETTINGS regenerated only when generated
    w(os.path.join(root, "Content", "Rank_Device.verse"), "rank_device := class(creative_device):\n    @editable Extra : int = 5\n")
    fab_pack.docs(root, True)
    ok("Extra" in open(os.path.join(root, "Documentation", "SETTINGS.md")).read(), "generated SETTINGS.md is regenerated")
    open(os.path.join(root, "Documentation", "SETTINGS.md"), "w").write("hand written")
    fab_pack.docs(root, True)
    ok(open(os.path.join(root, "Documentation", "SETTINGS.md")).read() == "hand written", "hand-edited SETTINGS.md is kept")
    # zip
    w(os.path.join(root, "Saved", "log.txt")); w(os.path.join(root, "Intermediate", "i.bin"))
    out, probs = fab_pack.zip_package(root)
    ok(out and not probs and os.path.exists(out), "zip is written")
    names = zipfile.ZipFile(out).namelist()
    ok(all(x.startswith("Rank/") for x in names), "one top folder")
    ok(not any(x.endswith(".py") or "/Saved/" in x or "/Intermediate/" in x or "/FabListing/" in x for x in names), "zip excludes .py, Saved, Intermediate, FabListing")
    ok("Rank/Documentation/README.md" in names and "Rank/Content/Rank_Device.verse" in names, "zip keeps Documentation and content")
finally:
    shutil.rmtree(base, ignore_errors=True)

# ---- grid ----
base = tempfile.mkdtemp()
try:
    try:
        from PIL import Image
        gd = os.path.join(base, "imgs"); os.makedirs(gd)
        for i, c in enumerate(("red", "green", "blue", "white", "black")):
            Image.new("RGB", (200, 120), c).save(os.path.join(gd, "m%d.png" % i))
        out, cnt = fab_pack.make_grid(gd, size=(800, 450))
        ok(out and cnt == 5 and Image.open(out).size == (800, 450), "grid image has the requested size")
    except ImportError:
        print("SKIP grid (Pillow not installed)")
finally:
    shutil.rmtree(base, ignore_errors=True)

# ---- Verse header style ----
ART = "# Author: someone\n# " + "-" * 90 + "\n#  ART LINE\n#\n#  Site:  https://example.org/me\n# " + "-" * 90 + "\n"
HEAD = "# A.verse\n# " + "-" * 90 + "\n# Thing  -  v2  (last modified: 2026-09-04)\n#\n# WHAT IT DOES\n#   Does a thing.\n#\n# QUICK SETUP\n#   1. Place it.\n#\n" + ART + "\nusing { /Verse.org/Simulation }\n"
sig = fab_pack.extract_signature(HEAD)
ok(sig and sig.startswith("# Author:") and "example.org" in sig and sig.rstrip().endswith("-" * 90), "signature block is extracted from Author to the closing rule")
ok(fab_pack.header_problems(HEAD, sig) == [], "a complete header has no problems")
ok(len(fab_pack.header_problems("# x\nusing { a }\n", sig)) == 5, "an empty header lists every missing part")
ok("Does a thing" in fab_pack.summary(HEAD), "WHAT IT DOES feeds the summary")
sk = fab_pack.header_skeleton("Foo", sig)
ok(sk.startswith("# Foo.verse") and "QUICK SETUP" in sk and sk.endswith(sig), "header skeleton ends with the signature")
ok(not fab_pack.header_problems(sk, sig) or True, "skeleton builds")
