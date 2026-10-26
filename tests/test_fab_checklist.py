"""Fab checklist: stations, verdict, manual ticks, UEFN validation record, zip re-read, and the console endpoints (real server, temp profile)."""
import json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
UL = os.path.join(HERE, "..", "user-level-hooks")
sys.path.insert(0, UL)
os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(HERE, "..", "project-template")   # the kit files of this checkout, not the ones installed in the profile (CI has none)
import fab_checklist as FC
import fab_pack
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

base = tempfile.mkdtemp()
srv = None
try:
    root = os.path.join(base, "Prod_Pack")
    lab = os.path.join(base, "lab")
    os.makedirs(os.path.join(root, "Content", "Prod", "Verse"))
    os.makedirs(os.path.join(root, "Content", "Bad-Folder"))
    open(os.path.join(root, "Prod_Pack.uefnproject"), "w").write("{}")
    open(os.path.join(root, "11111111-2222-3333-4444-555555555555.uplugin"), "w").write("{}")
    open(os.path.join(root, "Content", "Prod", "Verse", "main.verse"), "w").write("using { /Verse.org/Simulation }\n")
    os.makedirs(lab)

    os.makedirs(os.path.join(root, "Content", "Collections")); os.makedirs(os.path.join(root, "Content", "Developers", "me", "Collections"))
    ok(not any("Collections" in w for w in FC.fab_pack.check(root)[1]), "the empty Collections folders the editor creates are not reported")
    d = FC.build(root, lab, FC.scan_state(root, lab))
    ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok([s["id"] for s in d["stations"]] == ["project", "content", "build", "listing", "extra", "zip", "submit"], "seven stations in order, the extra round (memory, private release) before the zip")
    ok(d["verdict"] == "NOT READY" and ids["b-valid"]["s"] == "todo" and "Run all checks" in ids["b-valid"]["fix"], "no validation yet: to do (never a guess), and it says to press Run all checks")
    ok("b-inv" not in ids, "the Custom Inventory item is gone")
    ok(ids["p-complete"]["s"] == "pass", "project, plugin and Content found")
    ok(ids["p-names"]["s"] == "fail" and "Bad-Folder" in ids["p-names"]["ev"] and ids["p-forbidden"]["s"] == "pass", "the pack rules are mapped to items (a bad folder name blocks)")
    ok(all(i["id"] != "s-send" for s in d["stations"] if s["id"] != "submit" for i in s["items"]) and d["total"] == sum(len([i for i in s["items"] if i["s"] != "na"]) for s in d["stations"] if s["id"] != "submit"), "the upload on the portal is not counted in the percentage")
    ok(0 <= d["pct"] <= 100 and d["total"] == sum(d["counts"][k] for k in ("pass", "fail", "warn", "todo", "manual")), "percent counts every live item")
    ok(not d["can_zip"], "the zip is locked while a station has a block")

    ok(FC.parse_validation("LogX: Error: Disallowed reference to /pilars/A\nLogX: Warning: foo")["errors"] == 1, "validation log: lines with an error are counted")
    ok(FC.parse_validation("Validation finished: 3 errors, 2 warnings")["errors"] == 3, "validation log: a summary line wins")
    ok(FC.parse_validation("0 errors, 0 warnings")["errors"] == 0, "validation log: zero errors")
    try:
        FC.save_validation(lab, "   ", True); ok(False, "an empty log is refused")
    except ValueError:
        ok(True, "an empty log is refused")
    ok(FC.latest_run(["[2026.10.25-10.00.00:000][1]UEFNValidation: Error: old", "[2026.10.25-12.00.00:000][2]UEFNValidation: Warning: new", "[2026.10.25-12.00.01:000][3]LogModelContextProtocol: Running tool GetLogEntries pattern UEFNValidation"]) == ["[2026.10.25-12.00.00:000][2]UEFNValidation: Warning: new"], "only the latest validation run counts, and the MCP call's own log line is ignored")
    class Fake:
        def __init__(self, text): self.text = text
        def call(self, name, args): return self.text
    pr = FC.read_editor_validation(root, lab, Fake(json.dumps(["[2026.10.25-12.00.00:000][2]UEFNValidation: Error: Disallowed reference to /pilars/X"])))
    ok(pr["reachable"] and pr["errors"] == 1 and json.load(open(os.path.join(lab, "validation.json")))["source"] == "editor log", "the validation is read from the editor log by itself: an error line is recorded")
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["b-valid"]["s"] == "fail", "an error in the editor log blocks")
    os.remove(os.path.join(lab, "validation.json"))
    pr = FC.read_editor_validation(root, lab, Fake("[]"))
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(pr["lines"] == 0 and ids["b-valid"]["s"] == "todo" and "no validation yet" in ids["b-valid"]["ev"], "no validation line in the log: to do (never a guess), with what to do")
    FC.read_editor_validation(root, lab, Fake("[2026.10.25-12.00.00:000][2]LogContentValidation: Display: Validation done"))
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["b-valid"]["s"] == "pass", "validation lines without error or warning: passed")
    os.remove(os.path.join(lab, "validation.json"))
    for res, st, txt in (({"state": "clean", "errors": 0, "warnings": 0}, "pass", "0 errors, 0 warnings"), ({"state": "clean", "errors": 0, "warnings": 2}, "warn", "2 warnings"),
                         ({"state": "errors", "errors": 3, "warnings": 0, "message": "boom"}, "fail", "3 errors"), ({"state": "not_analyzed", "reason": "UEFN not reachable"}, "todo", "not reachable")):
        FC.read_verse_build(lab, lambda r=res: r)
        d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
        ok(ids["b-verse"]["s"] == st and txt in ids["b-verse"]["ev"], "Verse build %s -> %s" % (res["state"], st))
    ok(FC.ensure_third_party(root) is False, "third_party.md is not recreated without a FabListing folder")
    os.makedirs(os.path.join(fab_pack.product_folder(root), "FabListing"))
    ok(FC.ensure_third_party(root) is True and FC.ensure_third_party(root) is False, "a missing third_party.md is recreated once and never overwritten")
    FC.save_validation(lab, "Validation finished: 2 errors, 0 warnings\nError: x", True)
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["b-valid"]["s"] == "fail" and "2 errors" in ids["b-valid"]["ev"], "a log with errors keeps the block and says how many")
    FC.save_validation(lab, "Validation finished: 0 errors, 0 warnings", True)
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["b-valid"]["s"] == "pass", "a clean log turns the validation green")

    before = d["counts"]["pass"]
    ok(ids["c-work"]["s"] == "manual" and ids["c-work"]["tickable"], "an item only you can judge is tickable")
    FC.set_tick(lab, "c-work", True)
    d = FC.build(root, lab); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["c-work"]["s"] == "pass" and d["counts"]["pass"] == before + 1, "ticking it counts as passed")
    ok(not ids["p-complete"]["tickable"], "a check done by the kit cannot be ticked by hand")
    FC.set_tick(lab, "c-work", False)
    ok(FC.build(root, lab)["counts"]["pass"] == before, "unticking puts it back")
    ok(all(os.path.commonpath([lab, p]) == lab for p in [os.path.join(lab, f) for f in os.listdir(lab)]) and not os.path.exists(os.path.join(root, "Claude")), "data stays in the lab folder, nothing in the project")

    shutil.rmtree(os.path.join(root, "Content", "Bad-Folder"))
    import fab_pack
    out, probs = fab_pack.zip_package(root)
    ok(out and not probs, "the kit makes the zip")
    out2, probs2 = fab_pack.zip_package(root)
    ok(out2 == out and sorted(f for f in os.listdir(base) if f.endswith(".zip") or f.endswith(".tmp")) == [os.path.basename(out)], "making the zip again replaces it: one file, one name")
    rec = FC.reread_zip(root, lab)
    ok(rec["ok"] and rec["zip"].endswith(".zip"), "the finished zip is unzipped in a temp folder and checked again")
    d = FC.build(root, lab, FC.scan_state(root, lab)); ids = {i["id"]: i for s in d["stations"] for i in s["items"]}
    ok(ids["z-make"]["s"] == "pass" and ids["z-reread"]["s"] == "pass", "the zip stations turn green")

    # ---- the console endpoints, real server with a temp profile -----------------
    home = os.path.join(base, "home")
    hk = os.path.join(home, ".claude", "hooks")
    os.makedirs(hk)
    for f in ("fab_checklist.py", "fab_pack.py", "fab_assets.py"):
        shutil.copy(os.path.join(UL, f), hk)
    json.dump({"name": "Prod_Pack", "project": root, "kind": "fab"}, open(os.path.join(lab, "product.json"), "w"))
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    server = os.path.join(HERE, "..", "project-template", "Claude", "hooks", "agent-console-server.py")
    env = dict(os.environ, HOME=home, USERPROFILE=home, UEFN_FAB_LAB=lab)
    srv = subprocess.Popen([sys.executable, server, str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=lab)
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = "http://127.0.0.1:%d" % port
    for _ in range(60):
        try:
            op.open(url + "/whoami", timeout=1).read(); break
        except Exception:
            time.sleep(0.25)
    who = json.loads(op.open(url + "/whoami").read())
    ok(who.get("fab") is True, "/whoami tells the pages this is a Fab product")
    data = json.loads(op.open(url + "/fab-data").read())
    ok(data.get("name") == "Prod_Pack" and data["stations"] and "verdict" in data, "/fab-data returns the checklist")
    page = op.open(url + "/checklist").read().decode("utf-8")
    sk = op.open(url + "/skills").read().decode("utf-8")
    ok('<a href="agent-console-fab.html">Checklist</a>' in sk, "the server adds the real Checklist link to the other pages of a Fab product (not only the script)")
    ok("Checklist" in page and "Epic" not in page, "the Checklist page is served and does not name Epic")
    import re as _re
    tabs = lambda t: len(_re.findall(r'<a\b[^>]*href="agent-console-fab\.html"[^>]*>Checklist</a>', t))
    ok(tabs(page) == 1 and tabs(sk) == 1, "the Checklist tab appears once on the Checklist page and once on the other pages (never twice)")

    def act(body, hdr=True):
        h = {"Content-Type": "application/json"}
        if hdr:
            h["X-Skills-Action"] = "1"
        try:
            r = op.open(urllib.request.Request(url + "/fab-act", json.dumps(body).encode(), h), timeout=20)
            return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
    ok(act({"action": "tick", "id": "c-audio", "on": True}, hdr=False)[0] == 403, "an action without the page header is refused")
    code, j = act({"action": "tick", "id": "c-audio", "on": True})
    ok(code == 200 and j["ok"], "a tick is accepted")
    data = json.loads(op.open(url + "/fab-data").read())
    ok({i["id"]: i for s in data["stations"] for i in s["items"]}["c-audio"]["s"] == "pass", "the tick shows in the next read")
    code, j = act({"action": "validation", "text": "0 errors, 0 warnings", "skip_fixup": True})
    ok(code == 200 and j["ok"], "a validation log is recorded")
    fl = data["listing"].get("files") or []
    ok([f["key"] for f in fl] == ["readme", "author", "settings", "listing", "third_party"], "the listing card lists the documents the kit creates (the signature file always, SETTINGS.md because this product has Verse)")
    fp = os.path.join(root, "Content", "Prod", "Documentation"); os.makedirs(fp, exist_ok=True)
    open(os.path.join(fp, "README.md"), "w", encoding="utf-8").write("# Hello\nsetup text")
    rd = json.loads(op.open(url + "/fab-file?key=readme").read())
    ok(rd.get("name") == "README.md" and "setup text" in rd["text"], "a document can be read from the console")
    ok("error" in json.loads(op.open(url + "/fab-file?key=../../x").read()), "an unknown file name is refused")
    ok(act({"action": "nonsense"})[0] == 400, "an unknown action is refused")
finally:
    if srv:
        srv.kill()
        srv.wait()
    shutil.rmtree(base, ignore_errors=True)
print("OK")
