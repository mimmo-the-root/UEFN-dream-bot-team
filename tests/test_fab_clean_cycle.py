"""fab_clean_cycle: dry run reports editor state and assets to clean without touching anything."""
import os, subprocess, sys, tempfile, shutil
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
b = tempfile.mkdtemp()
try:
    r = os.path.join(b, "root_FAB_x"); os.makedirs(os.path.join(r, "Content", "P"))
    open(os.path.join(r, "root_FAB_x.uefnproject"), "w").write("{}")
    env = dict(os.environ, UEFN_FAB_LAB_DIR=os.path.join(b, "lab"), UEFN_KIT_TEMPLATE=os.path.join(ROOT, "project-template"))
    p = subprocess.run([sys.executable, os.path.join(ROOT, "user-level-hooks", "fab_clean_cycle.py"), r], capture_output=True, text=True, env=env)
    ok(p.returncode == 0 and "editor open: " in p.stdout and "assets to clean: 0" in p.stdout, "dry run reports state: " + p.stdout[-200:] + p.stderr[-300:])
    ok(subprocess.run([sys.executable, os.path.join(ROOT, "user-level-hooks", "fab_clean_cycle.py")], capture_output=True, text=True).returncode == 2, "no argument prints help")
finally:
    shutil.rmtree(b, ignore_errors=True)

# v1.111.1: Technical details are filled from the product; third-party authors survive the clean
sys.path.insert(0, os.path.join(ROOT, "user-level-hooks"))
b = tempfile.mkdtemp()
try:
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(b, "lab"); os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(ROOT, "project-template")
    import fab_pack, fab_assets
    r = os.path.join(b, "root_FAB_y"); os.makedirs(os.path.join(r, "Content", "Pack", "FabListing"))
    open(os.path.join(r, "root_FAB_y.uefnproject"), "w").write("{}")
    lp = os.path.join(r, "Content", "Pack", "FabListing", "listing.md")
    open(lp, "w").write("## Technical details\n\n- Modular / extensible: TODO (yes or no)\n- Code framework: TODO (x)\n- Projects: 3\n- Additional information: TODO\n")
    done = dict(fab_pack.fill_technical(r))
    t = open(lp).read()
    ok("TODO" not in t and "- Projects: 3" in t and done["Code framework"] == "Other", "technical details filled, a line the owner wrote is kept")
    tex = os.path.join(r, "Content", "Pack", "T_a.uasset")
    open(tex, "wb").write(b"xx C:/Us" b"ers/JanSmolders/Downloads/a.png xx")
    ok(fab_assets.source_authors(r) == ["JanSmolders"] and "JanSmolders" in fab_pack.third_party_md(r), "author of a texture is declared in third_party.md")
    fab_assets.clean(r, True, os.path.join(b, "bk"))
    ok("JanSmolders" in fab_pack.third_party_md(r), "the author stays declared after the clean erased the name")
finally:
    shutil.rmtree(b, ignore_errors=True)

b = tempfile.mkdtemp()
try:
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(b, "lab")
    r = os.path.join(b, "root_FAB_z"); d = os.path.join(r, "Content", "Pack"); os.makedirs(os.path.join(d, "Mats"))
    open(os.path.join(r, "root_FAB_z.uefnproject"), "w").write("{}")
    open(os.path.join(d, "Mats", "M_a.uasset"), "wb").write(b"x")
    fab_pack.docs(r, True)
    fab_pack.fill_readme(r)
    t = open(os.path.join(d, "Documentation", "README.md")).read()
    ok("SETTINGS.md" not in t and "Mats" in t and "TODO: copy" not in t, "README: no pointer to a missing SETTINGS.md, contents listed, setup steps filled")
    w = fab_pack.check(r)[1]
    ok(any("still has" in x and "README" in x for x in w), "check reports the TODO left in the documents")
finally:
    shutil.rmtree(b, ignore_errors=True)

b = tempfile.mkdtemp()
try:
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(b, "lab")
    r = os.path.join(b, "root_FAB_w"); d = os.path.join(r, "Content", "P"); os.makedirs(os.path.join(d, "FabListing"))
    open(os.path.join(r, "root_FAB_w.uefnproject"), "w").write("{}")
    open(os.path.join(d, "FabListing", "listing.md"), "w").write("Title: X\n\n## Description\n\nNice pack.\n\nThird-party content is declared in third_party.md.\n\n## Tags\n\nA\n")
    ok(any("names a file of the package" in x for x in fab_pack.check(r)[1]), "check flags a description that names a package file")
finally:
    shutil.rmtree(b, ignore_errors=True)
