"""Release summary for the What's new page."""
import json, os, sys, tempfile
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "tool"))
import community_summary as M
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
E = lambda state, hs, genre: {"state": state, "handles": hs, "genre": genre}
intake = {"lessons": {"p-000000000001": E("confirmed", ["ada", "bob"], "survival"), "p-000000000002": E("hypothesis", ["ada"], "tycoon"),
                      "p-000000000003": E("hypothesis", ["cy"], "tycoon"), "p-000000000004": E("archived", [], "survival")}}
rep = {"handles": {"ada": {"score": 7, "confirmed": 1, "lessons": 2, "genres": ["survival", "tycoon"]}, "bob": {"score": 4, "confirmed": 1, "lessons": 1, "genres": ["survival"]},
                   "cy": {"score": 0, "confirmed": 0, "lessons": 1, "genres": ["tycoon"]}}}
st = {"p-000000000001": "When a round starts: teleport everyone from one manager."}
s = M.build_summary("v1.99.0", intake, rep, None, {"title": "v1.99.0 - The pack", "items": ["a", "b"]}, st, today="2026-10-14")
ok(s["release"]["tag"] == "v1.99.0" and s["release"]["items"] == ["a", "b"], "release block from the changelog entry")
ok({x["genre"]: x["status"] for x in s["skills"]} == {"survival": "new", "tycoon": "new"}, "genres with no earlier pack are new")
ok(s["counts"] == {"new_skills": 2, "improved_skills": 0, "received": 4, "confirmed": 1, "hypotheses": 2, "archived": 1, "added": 3, "contributors": 3, "new_contributors": 3}, "counts: %s" % s["counts"])
ok([t["handle"] for t in s["top"]] == ["ada", "bob", "cy"] and s["top"][0]["delta"] == 7, "top sorted by score with the delta")
ok(s["helpful"] and s["helpful"][0]["confirmations"] == 2 and s["helpful"][0]["text"].startswith("When a round"), "the lesson confirmed by most creators is listed with its text")
ok(s["thanks"] == ["ada", "bob", "cy"], "thanks follow the score")
intake2 = json.loads(json.dumps(intake)); intake2["lessons"]["p-000000000005"] = E("hypothesis", ["dee"], "survival")
rep2 = json.loads(json.dumps(rep)); rep2["handles"]["ada"]["score"] = 10; rep2["handles"]["dee"] = {"score": 0, "confirmed": 0, "lessons": 1, "genres": ["survival"]}
s2 = M.build_summary("v1.99.1", intake2, rep2, s)
ok({x["genre"]: (x["status"], x["added"]) for x in s2["skills"]} == {"survival": ("improved", 1)}, "only genres with new lessons since the last release, marked improved")
ok(s2["top"][0]["delta"] == 3 and [t["handle"] for t in s2["top"] if t["new"]] == ["dee"], "delta from the previous release; new contributors flagged")
e = M.build_summary("v1.99.0", {}, {})
ok(e["counts"]["received"] == 0 and e["skills"] == [] and e["top"] == [] and e["thanks"] == [], "an empty intake gives a valid empty summary")
json.dumps(s)
