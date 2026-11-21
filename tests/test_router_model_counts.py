import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "user-level-hooks")):
    if os.path.isfile(os.path.join(p, "dream_router.py")):
        sys.path.insert(0, p)
HOME = tempfile.mkdtemp()
SCANS = os.path.join(HOME, "scans")
os.makedirs(SCANS)
os.environ["DREAM_ROUTER_HOME"] = HOME
import dream_router as dr
dr.HOME = HOME

CHAIN = ["okprov", "badprov", "untestedprov", "failedprov", "unknownprov"]
SETTINGS = {"chain": CHAIN, "scan_dir": SCANS}
dr.settings = lambda: dict(SETTINGS)
dr.keys = lambda: {"FAKE_KEY": "fake-key-123456"}
dr.providers = lambda: {n: {"key": "FAKE_KEY", "label": n, "signup": "https://example.invalid", "base": "https://example.invalid/v1"} for n in CHAIN}
dr.provider_key = lambda prov, ks: "fake-key-123456"
dr.available = lambda name: True
dr.recent_errors = lambda: []
dr.recent_models = lambda: []
dr.plan_available = lambda: True
dr.size_summary = lambda: None
dr._read_json = lambda name, default, keep=False: default

with open(os.path.join(SCANS, "provider-scan-okprov.json"), "w", encoding="utf-8") as f:
    json.dump({"models": [
        {"model": "good", "status": "error"},
        {"model": "badperf", "status": "working"},
        {"model": "scan-good", "status": "working"},
        {"model": "scan-good", "status": "working"},
        {"model": "scan-conflict", "status": "error"},
        {"model": "scan-bad", "status": "auth_failed"},
        {"model": "scan-err", "status": "error"},
        {"status": "working"},
        "not-a-model"]}, f)
with open(os.path.join(SCANS, "provider-scan-badprov.json"), "w", encoding="utf-8") as f:
    f.write("{broken")

dr.STATE = {
    "cooldown": {}, "breaker": {}, "checked": {n: 1 for n in CHAIN}, "models": {},
    "bad": {"failedprov": "key rejected"},
    "counts": {"okprov": 10, "badprov": 4, "untestedprov": 3, "failedprov": 6, "unknownprov": None},
    "perf": {
        "okprov/good": {"ok": 2, "fail": 0},
        "okprov/mostly": {"ok": 3, "fail": 1},
        "okprov/deep/nested/v2": {"ok": 1, "fail": 0},
        "okprov/badperf": {"ok": 0, "fail": 2},
        "okprov/scan-conflict": {"ok": 0, "fail": 2},
        "badprov/bad1": {"ok": 0, "fail": 3},
        "badprov/bad2": {"ok": 0, "fail": 1},
        "failedprov/once-good": {"ok": 2, "fail": 0},
        "unknownprov/a": {"ok": 1, "fail": 0},
        "unknownprov/b": {"ok": 0, "fail": 1},
        "otherprov/model": {"ok": 5, "fail": 0}},
    "last": None, "started": 0}

assert dr.DEFAULT_SETTINGS["scan_dir"] == ""
rows = {x["name"]: x for x in dr.state_view()["providers"]}
assert set(rows) == set(CHAIN)
for name in CHAIN:
    row = rows[name]
    assert row["name"] == name and row["status"] and "models_count" in row
    assert all(k in row for k in ("models_ok", "models_bad", "models_untested"))
assert (rows["okprov"]["models_ok"], rows["okprov"]["models_bad"], rows["okprov"]["models_untested"]) == (5, 3, 2)
assert (rows["badprov"]["models_ok"], rows["badprov"]["models_bad"], rows["badprov"]["models_untested"]) == (0, 2, 2)
assert (rows["untestedprov"]["models_ok"], rows["untestedprov"]["models_bad"], rows["untestedprov"]["models_untested"]) == (0, 0, 3)
assert rows["failedprov"]["status"] == "failed"
assert (rows["failedprov"]["models_ok"], rows["failedprov"]["models_bad"], rows["failedprov"]["models_untested"]) == (0, 6, 0)
assert (rows["unknownprov"]["models_ok"], rows["unknownprov"]["models_bad"], rows["unknownprov"]["models_untested"]) == (1, 1, None)
assert rows["unknownprov"]["models_count"] is None
assert rows["okprov"]["models_count"] == 10

SETTINGS["scan_dir"] = ""
rows = {x["name"]: x for x in dr.state_view()["providers"]}
assert (rows["okprov"]["models_ok"], rows["okprov"]["models_bad"], rows["okprov"]["models_untested"]) == (3, 2, 5)
print("ok router model counts")
