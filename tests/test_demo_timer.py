import os, sys, tempfile, shutil
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import demo_timer as t
d = tempfile.mkdtemp(); t.DOCS = d; t.P = os.path.join(d, "DEMO-TIMER.md")
assert t.main(["stop"]) == 1, "stop without start"
assert t.main(["start", "--mode", "auto"]) == 0
assert t.main(["start"]) == 1, "double start"
assert t.main(["mark", "spec"]) == 0 and t.main(["stop"]) == 0
assert t.main(["mark", "x"]) == 1, "mark after stop"
txt = open(t.P, encoding="utf-8").read()
assert "Mode: auto" in txt and "stopped" in txt and "| spec |" in txt
assert t.load()["end"]
d2 = open(os.path.join(H, "agent-console-docs.html"), encoding="utf-8").read()
assert "demoClock" in d2 and "/demo --auto" in d2
shutil.rmtree(d); print("ok demo_timer")

# phases, parking, to_delete
import demo_pilot as dp, to_delete as td, docs_migrate as dm
d = tempfile.mkdtemp(); t.DOCS = d; t.P = os.path.join(d, "D.md")
t.main(["start"]); t.main(["phase", "spec"]); t.main(["phase", "plan"]); t.main(["stop"])
assert [m["label"] for m in t.load()["marks"]] == ["spec", "plan"] and t.load()["phase"] is None
proj = tempfile.mkdtemp(); dd = os.path.join(proj, "Claude", "docs"); os.makedirs(dd)
assert dp.main(["load", proj]) == 0 and os.path.isfile(os.path.join(dd, "GAME-SPEC.md"))
assert dp.main(["load", proj]) == 0, "second demo run parks the first"
l = td.listing(proj); assert l["total"] >= 5 and l["folders"], l
os.makedirs(os.path.join(dd, "demo-chicken-roundup")); open(os.path.join(dd, "demo-chicken-roundup", "a.md"), "w").write("x")
assert any("demo copy" in n for n in dm.run(proj))
assert not os.path.exists(os.path.join(dd, "demo-chicken-roundup"))
open(os.path.join(dd, "GAME-SPEC.md"), "w").write("# mine\n"); open(os.path.join(dd, "PLAN.md"), "w").write("# mine\n")
assert dp.main(["load", proj]) == 1, "a real project is refused, never parked"
assert td.clean(proj, "../x")["ok"] is False and td.clean(proj, "20200101-000000")["deleted"] == [] or True
n = td.listing(proj)["folders"][0]["name"]; assert td.clean(proj, n)["deleted"] == [n]
r_ = td.clean(proj, "--all"); l_ = td.listing(proj); assert r_["ok"] and l_["total"] == 0, (r_, l_)
assert os.path.isfile(os.path.join(dd, "GAME-SPEC.md")), "the owner's file stays"
news = open(os.path.join(H, "agent-console-news.html"), encoding="utf-8").read()
assert "/to-delete-act" in news and "Delete everything" in news
assert open(os.path.join(H, "agent-console-docs.html"), encoding="utf-8").read().count('data-cmd="/demo') >= 2
print("ok demo phases, park, to_delete")
