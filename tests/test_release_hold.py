"""The owner ticks which new skills and lessons go out at the release; unticked ones stay private."""
import json, os, sys, tempfile, subprocess
d = tempfile.mkdtemp(); os.environ["HOME"] = d; os.environ["USERPROFILE"] = d
os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as L
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
os.makedirs(os.path.join(d, "skills", "genre", "gun-game"))
ok(L.load_hold() == {"skills": [], "lessons": [], "mcp": []}, "nothing is held by default: everything goes out")
ok(L.hold_set("skill", "gun-game", True)["ok"] and L.load_hold()["skills"] == ["gun-game"], "a skill can be kept out")
ok(L.hold_set("skill", "gun-game", False)["ok"] and L.load_hold()["skills"] == [], "and put back")
ok(not L.hold_set("lesson", "nope", True)["ok"], "an unknown lesson is refused")
try:
    L.hold_set("skill", "../etc", True); bad = True
except Exception:
    bad = False
ok(not bad, "a name that is not a skill on this computer is refused")
src = open(os.path.join(ROOT, "tool", "promote-genre-skills.py"), encoding="utf-8").read()
ok('HOLD["skills"]' in src and 'skip=HOLD["lessons"]' in src, "the release tool leaves out what is held")
h = open(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-skills.html"), encoding="utf-8").read()
ok("/release-hold" in h and "Keep private" in h and "Make shareable" in h, "the Skills page has the Keep private / Make shareable buttons")
ok(not L.is_maintainer(), "a normal user is not the maintainer: no release boxes, GitHub sending as before")
open(os.path.join(d, "skills", "maintainer.json"), "w").write('{"maintainer": true}')
ok(L.is_maintainer() and L.summary()["maintainer"] is True, "the maintainer's profile is marked")
ok("SD.maintainer" in h and "mt=!!(SD&&SD.maintainer)" in h and "ready: next release" in h, "for the maintainer To share says it goes out at the release (no GitHub)")
cmd = open(os.path.join(ROOT, "update-my-profile.cmd"), encoding="utf-8").read()
ok("maintainer.json" in cmd and 'if exist "%SRC%publish.ps1"' in cmd, "update-my-profile.cmd marks the maintainer's profile")
ok(L.set_maintainer_mode("contributor")["ok"] and not L.is_maintainer() and L.summary()["maintainer_available"] is True, "the maintainer can switch to the contributor view to test what users see")
ok(L.set_maintainer_mode("maintainer")["ok"] and L.is_maintainer(), "and back")
ok(not L.set_maintainer_mode("x")["ok"], "an unknown view is refused")
ok(L.set_handle("@Ada-1")["ok"] and L.community_state()["handle"] == "Ada-1", "the GitHub name is saved once")
ok(not L.set_handle("a b/c")["ok"], "something that is not a GitHub name is refused")
url, pre, name = L._gh_url("contributions/x/<your-github-handle>.json", "{}", "Community lesson: p-1 (x)")
import urllib.parse as U
ok(name.endswith("/ada-1.json") and "message=" in url and "description=" in url and pre, "the GitHub page opens with name, title and description filled in")
url2, pre2, _ = L._gh_url("a/<your-github-handle>.json", "x" * 5000, "t")
ok(not pre2 and "value=" not in url2 and "message=" in url2, "too long: the title stays, the JSON is pasted")
ok("function stMaps()" in h and "Collected" in h and "Make shareable" in h and "(SF===x.st)" in h, "To share: one life (collected, ready, shared, private) and a Keep private / Make shareable button on every item")
ok("(SF===x.st)" in h, "the filters are the states")
ok(L.guess_section({"statement": "Elimination subscriptions must be re-created on every respawn"}) == "death-strategies" and L.guess_section({"statement": "x"}) == "architecture", "the section of a lesson is chosen by the kit")
ok(L.hold_set("mcp", "T.Set/DoIt", True)["ok"] and L.load_hold()["mcp"] == ["T.Set/DoIt"] and not L.hold_set("mcp", "bad name", True)["ok"], "a UEFN MCP recipe can be kept private")
ok(L.hold_set_many("mcp", ["T.Set/A", "T.Set/B", "nope"], True)["changed"] == 2 and L.hold_set_many("mcp", ["T.Set/A", "T.Set/B"], False)["changed"] == 2, "Promote all / Keep all private change a list at once")
ok("bulkBtns()" in h and h.count("bindKp(") >= 6 and "data-bulk" in h, "every section has the same buttons (Keep private, Make shareable, Promote all, Keep all private)")
ok("stChip(" in h and "<th>State</th>" in h and "data-hold=\"lesson\"" not in h, "every section has a State column; no more check boxes")
print("OK")
