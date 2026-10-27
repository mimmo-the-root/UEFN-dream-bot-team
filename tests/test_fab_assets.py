"""Fab asset scan: another project's names and imports inside .uasset files (synthetic packages, no real assets)."""
import os, shutil, struct, sys, tempfile
import tempfile as _tf
os.environ["UEFN_FAB_LAB_DIR"] = _tf.mkdtemp(prefix="fablab-test-")   # never write in the real ~/.claude/fab-lab
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-level-hooks"))
import fab_assets as FA, fab_pack
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def fstr(s):
    d = s.encode("utf-8") + b"\0"
    return struct.pack("<i", len(d)) + d

def package(names, imports):
    """Minimal UE5 package: summary + name table + import table (imports = package names; every one has outer 0, class Package)."""
    names = list(names)
    for n in ("Package", "/Script/CoreUObject"):
        if n not in names:
            names.append(n)
    for i in imports:
        if i not in names:
            names.append(i)
    idx = {n: k for k, n in enumerate(names)}
    head_fixed = struct.pack("<I", 0x9E2A83C1) + struct.pack("<i", -9) + struct.pack("<i", 0) + struct.pack("<i", 522) + struct.pack("<i", 1018) + struct.pack("<i", 0)
    def build(total, noff, ioff, eoff):
        b = head_fixed + b"\0" * 20 + struct.pack("<i", total) + struct.pack("<i", 0) + fstr("None") + struct.pack("<I", 0)
        b += struct.pack("<ii", len(names), noff) + struct.pack("<ii", 0, 0) + fstr("") + struct.pack("<ii", 0, 0)
        b += struct.pack("<iiii", 0, eoff, len(imports), ioff)
        return b
    probe = build(0, 0, 0, 0)
    noff = len(probe) + 64
    table = b"".join(fstr(n) + b"\0\0\0\0" for n in names)
    ioff = noff + len(table)
    imp = b"".join(struct.pack("<iiiiiii", idx["/Script/CoreUObject"], 0, idx["Package"], 0, 0, idx[i], 0) + b"\0" * 8 for i in imports)
    eoff = ioff + len(imp)
    b = build(eoff, noff, ioff, eoff)
    return b + b"\0" * (noff - len(b)) + table + imp

base = tempfile.mkdtemp()
try:
    root = os.path.join(base, "Proj")
    mine = "11111111-2222-3333-4444-555555555555"
    os.makedirs(os.path.join(root, "Content", "Prod", "Sound"))
    open(os.path.join(root, mine + ".uplugin"), "w").write("{}")
    open(os.path.join(root, "Proj.uefnproject"), "w").write("{}")
    def put(rel, own, imports=()):
        p = os.path.join(root, "Content", rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(package([own, own + "." + os.path.basename(own)], list(imports)))
    put("Prod/Sound/S_Point.uasset", "/" + mine + "/Prod/Sound/S_Point")
    put("Prod/Sound/SC_S.uasset", "/" + mine + "/Prod/Sound/SC_S", ["/" + mine + "/Prod/Sound/S_Point", "/Engine/EngineMaterials/X", "/CreativeCoreDevices/A/B"])
    names, imps = FA.parse(os.path.join(root, "Content", "Prod", "Sound", "SC_S.uasset"))
    ok(len(imps) == 3 and imps[0].endswith("S_Point"), "the import table is read")
    b, w, n = FA.scan(root)
    ok(not b and not w, "a clean project: nothing found (own mount, Engine and Epic libraries are fine)")
    put("Prod/Tex/T_Old.uasset", "/pilars/Rank_UI/T_Old")
    put("Prod/Sound/SC_S.uasset", "/pilars/HUD_WBP/UI/SC_S", ["/pilars/HUD_WBP/UI/S_Point"])
    b, w, n = FA.scan(root)
    ok(len(b) == 1 and "SC_S" in b[0] and "/pilars/HUD_WBP/UI/S_Point" in b[0] and "Disallowed reference" in b[0], "an import of another project's asset is a block")
    ok(any("internal name of another project" in x and "/pilars/" in x for x in w), "assets that still carry another project's name are a warning")
    pu = os.path.join(root, "Content", "Prod", "Tex", "T_User.uasset")
    open(pu, "wb").write(package(["/" + mine + "/Prod/Tex/T_User"], []) + b'{ "RelativeFilename" : "../../' + b"Us" + b'ers/jane.doe/Desktop/FAB UI Template/N.PNG" }')
    b, w, n = FA.scan(root)
    ok(any("Windows user" in x and "***anonymized***" in x and "jane.doe" not in x for x in w), "a Windows user name in an import path is reported, and never written out")
    open(pu, "wb").write(package(["/" + mine + "/Prod/Tex/T_User"], []) + b'{ "RelativeFilename" : "../../' + b"Us" + b'ers/********/Desktop/FAB UI Template/N.PNG" }')
    b, w, n = FA.scan(root)
    ok(not any("T_User" in x and "Windows user" in x for x in w), "a user name already replaced by asterisks is not reported again")
    os.remove(pu)
    put("Prod/Mat/MI_A.uasset", "/" + mine + "/Prod/Mat/MI_A", ["/MyOtherProject/Systems/M_Radial"])
    b, w, n = FA.scan(root)
    ok(any("/MyOtherProject/Systems/M_Radial" in x and "Reference Viewer" in x for x in w), "an unknown mount is a warning to check, not a block")
    bl, wa, no = fab_pack.check(root)
    ok(any("Disallowed reference" in x for x in bl), "fab_pack check reports the asset scan")
    open(os.path.join(root, "Content", "Prod", "Junk.uasset"), "wb").write(b"not a package at all" * 10)
    b, w, n = FA.scan(root)
    ok(any("not understood" in x for x in n), "a file the scan cannot read is a note, never an error")
    os.makedirs(os.path.join(root, ".lore")); open(os.path.join(root, ".lore", "x"), "w").write("x")
    for n in (".loreignore", ".urcignore", "Proj.code-workspace"):
        open(os.path.join(root, n), "w").write("x")
    os.remove(os.path.join(root, "Content", "Prod", "Junk.uasset"))
    out, probs = fab_pack.zip_package(root)
    import zipfile
    zn = zipfile.ZipFile(out).namelist() if out else []
    ok(out and not probs and not any(".lore" in n or ".urcignore" in n or "code-workspace" in n for n in zn) and any(n.endswith("Proj.uefnproject") for n in zn),
       "the archive leaves out lore, urc and code-workspace files and keeps the project")
    ok(FA.is_epic_mount("EntityFramework") and not FA.is_epic_mount("pilars"), "EntityFramework (Epic's own Verse module) is not reported as another project")
finally:
    shutil.rmtree(base, ignore_errors=True)
