"""Fab learning: candidates from the ledger, proposals the owner approves, the Stop hook and the console endpoints."""
import json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.error, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
UL = os.path.join(HERE, "..", "user-level-hooks")
sys.path.insert(0, UL)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
base = tempfile.mkdtemp()
srv = None
try:
    home = os.path.join(base, "home")
    os.makedirs(os.path.join(home, ".claude", "hooks"))
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(base, "labs")
    os.environ["UEFN_FAB_LESSONS"] = os.path.join(base, "fab-lessons.json")
    import fab_lab as FL
    root = os.path.join(base, "Prod")
    os.makedirs(os.path.join(root, "Content"))
    open(os.path.join(root, "Prod.uefnproject"), "w").write("{}")
    lab = FL.ensure_lab(root)
    with open(FL.ledger_path(root), "w", encoding="utf-8") as f:
        for _ in range(2):
            f.write(json.dumps({"d": "2026-10-25", "tool": "set_material_param", "r": "rejected", "why": "unknown parameter Colour"}) + "\n")
        f.write(json.dumps({"d": "2026-10-25", "tool": "create_asset", "r": "ok"}) + "\n")
        f.write(json.dumps({"d": "2026-10-25", "tool": "set_material_param", "r": "ok", "args": json.dumps({"arguments": {"asset": "M_X", "parameter_name": "Colour", "value": 1}})}) + "\n")
        for _ in range(3):
            f.write(json.dumps({"d": "2026-10-25", "tool": "create_widget", "r": "ok", "args": json.dumps({"arguments": {"path": "/x", "parent": "Canvas"}})}) + "\n")
    for bad in ("Keep files under C:\\Users\\me\\x because it helps a lot", "See https://example.com for how to do this well", "Fix B-012 by renaming the folder properly", "too short"):
        try:
            FL.propose(root, bad); ok(False, "refused: " + bad[:20])
        except ValueError:
            ok(True, "a lesson with a path, a link, a task id or too short is refused")
    r = FL.learn_request(root)
    ok(r["new_candidates"] == 3, "candidates without AI: the fix that worked, a tool that worked again and again, and the failure")
    txt = json.dumps(FL._jload(FL.proposals_path(root), []))
    ok("worked with the parameters asset, parameter_name, value" in txt and "create_widget worked 3 times" in txt and "M_X" not in txt, "the how-to lessons carry parameter names, never values")
    ok(FL.learn_request(root)["new_candidates"] == 0, "pressing Learn again does not duplicate it")
    pid = FL.propose(root, "Name the material parameters exactly as the master defines them before setting values.", when="setting material parameters", do="read the parameter names first")
    ok(pid and FL.propose(root, "Name the material parameters exactly as the master defines them before setting values.") is None, "an agent proposal is queued once")
    st = FL.learn_state(root)
    ok(len([x for x in st["proposals"] if x["status"] == "pending"]) == 4 and st["flag"]["state"] == "waiting", "four proposals wait for the owner, and the request waits for the agent")
    os.environ["CLAUDE_PROJECT_DIR"] = root
    ki = FL._ki(); ki.REGISTRY = os.path.join(base, "kit-projects.json")   # never write in the real ~/.claude/kit-projects.json
    ki.set_kind(root, "fab") if hasattr(ki, "set_kind") else None
    FL.fab_root = lambda b: root
    out = FL.stop_hook({"cwd": root})
    ok(out and out["decision"] == "block" and "fab_lab.py" in out["reason"] and "propose" in out["reason"], "the Stop hook asks the agent to finish the learning")
    ok(FL.stop_hook({"cwd": root}) is None and FL.stop_hook({"cwd": root, "stop_hook_active": True}) is None, "it asks once, never in a loop")
    FL.act(root, "approve", pid)
    ok("Name the material parameters" in FL.lessons_text(), "an approved lesson is read by every Fab product")
    for x in [x for x in FL.learn_state(root)["proposals"] if x["status"] == "pending"]:
        FL.act(root, "reject", x["id"])
    ok(not [x for x in FL.learn_state(root)["proposals"] if x["status"] == "pending"] and len(json.load(open(os.environ["UEFN_FAB_LESSONS"]))) == 1, "a rejected lesson is not kept")
    ok(not os.path.exists(os.path.join(root, "Claude")), "nothing is written in the project")

    # console endpoints (real server, temp profile)
    json.dump({"name": "Prod", "project": root, "kind": "fab"}, open(os.path.join(lab, "product.json"), "w"))
    shutil.copy(os.path.join(UL, "fab_lab.py"), os.path.join(home, ".claude", "hooks"))
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
    d = json.loads(op.open(url + "/fab-learn").read())
    ld = json.loads(op.open(url + "/learning-data").read())
    ok(ld.get("fab_product", {}).get("calls") == 7 and ld["fab_product"]["name"] == "Prod", "the Skills page gets the real data of the product, not an empty map view")
    ok("proposals" in d and d["calls"] == 7, "/fab-learn returns the state of the lab")
    def act(body, hdr=True):
        h = {"Content-Type": "application/json"}
        if hdr:
            h["X-Skills-Action"] = "1"
        try:
            r = op.open(urllib.request.Request(url + "/fab-learn-act", json.dumps(body).encode(), h), timeout=20)
            return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
    ok(act({"action": "request"}, hdr=False)[0] == 403, "an action without the page header is refused")
    code, j = act({"action": "request"})
    ok(code == 200 and j["ok"], "the Learn button is accepted")
    pid2 = FL.propose(root, "Check every asset path before creating it so the tool does not fail silently.")
    ok(act({"action": "approve", "id": pid2, "text": "Check every asset path before creating it so the tool never fails silently."})[1]["ok"], "an edited lesson is approved")
    ok("never fails silently" in FL.lessons_text(), "the edited wording is what is kept")
    sk = op.open(url + "/skills").read().decode("utf-8")
    ok("kLearnBox" in sk and "/fab-learn-act" in sk and "fabP()" in sk, "the Skills page carries the Learn block and the Fab lessons queue")
finally:
    if srv:
        srv.kill(); srv.wait()
    shutil.rmtree(base, ignore_errors=True)
print("OK")

# recipes learned in a Fab product are confirmed at once
_h = tempfile.mkdtemp()
os.environ["UEFN_SKILLS_DIR"] = os.path.join(_h, "skills")
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(_h, "fl")
os.makedirs(os.path.join(_h, "fl", "Prod_X"))
shutil.copytree(os.path.join(HERE, "..", "user-level-skills", "genre", "materials"), os.path.join(_h, "skills", "genre", "materials"))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
import skills_lib as _SL
_SL.recipe_add("materials", {"name": "r-fab", "parent": "M_X", "steps": ["a"]}, "Prod_X")
_SL.recipe_add("materials", {"name": "r-map", "parent": "M_X", "steps": ["a"]}, "Some Map")
_t_ = {r["name"]: r["tier"] for r in _SL.recipes_list("materials")["recipes"] if r.get("origin") == "owner"}
assert _t_ == {"r-fab": "confirmed", "r-map": "hypothesis"}, _t_
print("PASS Fab recipes are confirmed at once, a map recipe waits for a second map")
shutil.rmtree(_h, ignore_errors=True)

# mechanics recipes: draft from the product, save, list, rebuild fields kept
_h = tempfile.mkdtemp()
os.environ["UEFN_SKILLS_DIR"] = os.path.join(_h, "skills")
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(_h, "fl")
os.makedirs(os.path.join(_h, "fl", "RankSys"))
shutil.copytree(os.path.join(HERE, "..", "user-level-skills", "genre", "mechanics"), os.path.join(_h, "skills", "genre", "mechanics"))
import importlib; importlib.reload(_SL)
import fab_lab as _FL
_FL.lab_base = lambda: os.path.join(_h, "fl")
_proj = os.path.join(_h, "RankSys"); os.makedirs(os.path.join(_proj, "Content", "Rank", "Verse"))
open(os.path.join(_proj, "RankSys.uefnproject"), "w").write("{}")
open(os.path.join(_proj, "Content", "Rank", "Verse", "rank.verse"), "w").write("rank := class{}\n")
_FL.ensure_lab(_proj)
with open(_FL.ledger_path(_proj), "w", encoding="utf-8") as _f:
    _f.write(json.dumps({"tool": "spawn_device", "r": "ok", "args": json.dumps({"arguments": {"type": "x", "location": "y"}})}) + "\n")
_dp = _FL.draft_recipe(_proj, "Rank system")
_d = json.load(open(_dp, encoding="utf-8"))
assert _d["files"][0]["name"] == "rank.verse" and "rank := class" in _d["files"][0]["code"] and "spawn_device(location, type)" in _d["steps"][0], _d
_d.update(kind="device", use="Ranks players by score.", steps=["Place the manager", "Add rank.verse"], devices=["Manager: holds ranks"], verify="Score 10 and see the rank change")
r = _SL.recipe_add("mechanics", _d, "RankSys")
assert r["ok"], r
_rs = [x for x in _SL.recipes_list("mechanics")["recipes"] if x.get("origin") == "owner"]   # official recipes of the kit may share the name
assert _rs[0]["tier"] == "confirmed" and _rs[0]["files"][0]["name"] == "rank.verse" and _rs[0]["verify"], _rs
assert not _SL.recipe_add("mechanics", {"name": "x"}, "RankSys")["ok"]
print("PASS a mechanic recipe is drafted from the product, saved with its Verse code and confirmed at once")
shutil.rmtree(_h, ignore_errors=True)

# the kit prepares the mechanic recipe by itself from the product (no agent, no AI)
_h = tempfile.mkdtemp()
os.environ["UEFN_SKILLS_DIR"] = os.path.join(_h, "skills")
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(_h, "fl")
shutil.copytree(os.path.join(HERE, "..", "user-level-skills", "genre", "mechanics"), os.path.join(_h, "skills", "genre", "mechanics"))
importlib.reload(_SL)
import fab_lab as _FL2
_FL2.lab_base = lambda: os.path.join(_h, "fl")
_p = os.path.join(_h, "Rank_Sys"); os.makedirs(os.path.join(_p, "Content", "Rank", "Verse")); os.makedirs(os.path.join(_p, "Content", "Rank", "Documentation"))
open(os.path.join(_p, "Rank_Sys.uefnproject"), "w").write("{}")
open(os.path.join(_p, "Content", "Rank", "Verse", "rank.verse"), "w").write(
    "rank_device<public> := class(creative_device):\n    # Reports kills (required).\n    @editable\n    Elims : elimination_manager_device = elimination_manager_device{}\n    # Points per kill.\n    @editable PointsPerKill : int = 15\n")
open(os.path.join(_p, "Content", "Rank", "Documentation", "README.md"), "w").write("# Rank\n\nA rank system.\n\n## Setup\n\n1. Copy the folder.\n2. Place the device.\n\n## Usage\n\n- Players earn points per kill.\n")
_FL2.ensure_lab(_p)
_r = _FL2.ensure_auto_recipe(_p)
assert _r and _r["ok"], _r
assert _FL2.ensure_auto_recipe(_p) is None   # unchanged code: nothing to redo
_rec = [x for x in _SL.recipes_list("mechanics")["recipes"] if x.get("origin") == "owner"][0]
assert _rec["name"] == "rank sys" and _rec["kind"] == "device" and _rec["tier"] == "confirmed", _rec
assert any("Elims" in x and "elimination_manager_device" in x for x in _rec["devices"]) and any("PointsPerKill (int) = 15" in x for x in _rec["settings"]), _rec
assert _rec["steps"] == ["Copy the folder.", "Place the device."] and _rec["files"][0]["name"] == "rank.verse" and "earn points" in _rec["verify"], _rec
print("PASS the kit prepares the mechanic recipe by itself from the Verse code and the README")
shutil.rmtree(_h, ignore_errors=True)
