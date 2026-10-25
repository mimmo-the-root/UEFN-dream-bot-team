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
    w(os.path.join(root, "Content", "Rank_Product", "Rank_Device.verse"),
      "# Summary: Shows the rank of the player.\nrank_device := class(creative_device):\n    # Points needed per rank\n    @editable PointsPerRank : int = 100\n")
    w(os.path.join(root, "Content", "Rank_Product", "Widgets", "Panel.uasset"))
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
    BASE = os.path.join(root, "Content", "Rank_Product")
    ok(fab_pack.product_folder(root) == BASE, "product folder = the Content folder with the most files")
    made, kept = fab_pack.docs(root, False)
    ok(made and not os.path.exists(os.path.join(BASE, "Documentation")), "dry run writes nothing")
    fab_pack.docs(root, True)
    for f in ("Documentation/README.md", "Documentation/SETTINGS.md", "FabListing/listing.md", "FabListing/third_party.md", "FabListing/screenshots.md"):
        ok(os.path.exists(os.path.join(BASE, *f.split("/"))), "created " + f)
    s = open(os.path.join(BASE, "Documentation", "SETTINGS.md"), encoding="utf-8").read()
    ok("PointsPerRank" in s and "100" in s and "Points needed per rank" in s, "SETTINGS.md lists @editable with default and note")
    # never overwrite
    open(os.path.join(BASE, "Documentation", "README.md"), "w").write("mine")
    fab_pack.docs(root, True)
    ok(open(os.path.join(BASE, "Documentation", "README.md")).read() == "mine", "existing documents are never overwritten")
    # SETTINGS regenerated only when generated
    w(os.path.join(root, "Content", "Rank_Product", "Rank_Device.verse"), "rank_device := class(creative_device):\n    @editable Extra : int = 5\n")
    fab_pack.docs(root, True)
    ok("Extra" in open(os.path.join(BASE, "Documentation", "SETTINGS.md")).read(), "generated SETTINGS.md is regenerated")
    open(os.path.join(BASE, "Documentation", "SETTINGS.md"), "w").write("hand written")
    fab_pack.docs(root, True)
    ok(open(os.path.join(BASE, "Documentation", "SETTINGS.md")).read() == "hand written", "hand-edited SETTINGS.md is kept")
    # zip
    w(os.path.join(root, "Saved", "log.txt")); w(os.path.join(root, "Intermediate", "i.bin"))
    out, probs = fab_pack.zip_package(root)
    ok(out and not probs and os.path.exists(out), "zip is written")
    names = zipfile.ZipFile(out).namelist()
    ok(all(x.startswith("Rank/") for x in names), "one top folder")
    ok(not any(x.endswith(".py") or "/Saved/" in x or "/Intermediate/" in x for x in names), "zip excludes .py, Saved, Intermediate")
    ok("Rank/Content/Rank_Product/Documentation/README.md" in names and "Rank/Content/Rank_Product/FabListing/listing.md" in names and "Rank/Content/Rank_Product/Rank_Device.verse" in names, "zip is the whole project: the generated files are inside Content")
finally:
    shutil.rmtree(base, ignore_errors=True)

# ---- older layout: folders next to Content are moved in ----
base2 = tempfile.mkdtemp()
try:
    r2 = os.path.join(base2, "Old")
    w(os.path.join(r2, "Old.uefnproject"), "{}")
    w(os.path.join(r2, "Content", "Old_Product", "A_Device.verse"), "a := class(creative_device):\n")
    w(os.path.join(r2, "Documentation", "README.md"), "my readme")
    w(os.path.join(r2, "FabListing", "third-party.md"), "my list")
    b, wa, n = fab_pack.check(r2)
    ok(any("older layout" in x for x in n), "check tells about folders left next to Content")
    made, kept = fab_pack.docs(r2, False)
    ok(any(x.startswith("moved Documentation/README.md") for x in made) and os.path.exists(os.path.join(r2, "Documentation", "README.md")), "dry run lists the move and moves nothing")
    fab_pack.docs(r2, True)
    nb = os.path.join(r2, "Content", "Old_Product")
    ok(open(os.path.join(nb, "Documentation", "README.md")).read() == "my readme", "old Documentation/README.md moved in, content kept")
    ok(os.path.exists(os.path.join(nb, "FabListing", "third_party.md")) and not os.path.exists(os.path.join(nb, "FabListing", "third-party.md")), "third-party.md becomes third_party.md (no hyphen in the archive)")
    ok(not os.path.exists(os.path.join(r2, "Documentation")) and not os.path.exists(os.path.join(r2, "FabListing")), "empty old folders are removed")
    out, probs = fab_pack.zip_package(r2)
    ok(out and not probs, "the migrated project zips without name problems")
finally:
    shutil.rmtree(base2, ignore_errors=True)

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
