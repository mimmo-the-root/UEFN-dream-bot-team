"""Score page data: built from ROADMAP / BUGS / RELEASE-READINESS, no hand-typed numbers."""
import json, os, shutil, sys, tempfile
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import score
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

d = tempfile.mkdtemp()
try:
    docs = os.path.join(d, "Claude", "docs"); os.makedirs(docs)
    ok(score.compute(d)["available"] is False, "no ROADMAP: empty state with a reason")
    hdr = "| ID | Feature | Status | Acceptance criteria | Priority | Release |\n|---|---|---|---|---|---|\n"
    rows = [("T-001", "Core gameplay loop with rounds", "Done", "rounds end", "P1", "P0-R1"),
            ("T-002", "Level layout and landmarks", "Done", "route", "P1", "P0-R1"),
            ("T-003", "Music loop and sfx", "To do", "audio", "P2", "P0-R2"),
            ("T-004", "Daily reward and leaderboard", "In progress", "return", "P2", "P0-R2"),
            ("T-005", "Misc cleanup", "To do", "x", "P3", "P0-R2"),
            ("T-006", "Later idea", "To do", "x", "P3", "Later")]
    open(os.path.join(docs, "ROADMAP.md"), "w").write("# Roadmap\n\n## Tasks\n\n" + hdr + "\n".join("| %s | %s | %s | %s | %s | %s |" % r for r in rows) + "\n")
    open(os.path.join(docs, "BUGS.md"), "w").write("# Bugs\n\n| Title | Where | Severity | Probable cause | Status |\n|---|---|---|---|---|\n| B-001 gameplay crash on T-001 | A.verse | major | x | Open |\n| B-002 old | B.verse | minor | x | Fixed |\n")
    s = score.compute(d)
    ok(s["available"] and s["releases"] == ["P0-R1", "P0-R2"] and s["last"] == 1, "releases are ordered, current = first release with open tasks")
    c = {x["id"]: x for x in s["criteria"]}
    ok(c["gameplay"]["T"][0] > 0 and c["audio"]["T"][0] == 0 and c["audio"]["T"][1] > 0, "plan target grows when a release plans audio tasks")
    ok(c["gameplay"]["V"][0] > c["gameplay"]["V"][1], "an open bug linked to a task lowers the proven value of its criterion")
    ok(c["ret"]["B"][1] > c["ret"]["V"][1] == 0.0, "in progress counts as built, not as proven")
    ok(s["unmapped"] == [{"id": "T-005", "title": "Misc cleanup"}], "unmapped tasks are reported, Later is excluded")
    ok(c["feas"]["V"][1] < 4.5, "open bugs lower feasibility")
    # explicit map beats keywords
    open(os.path.join(docs, "score-map.json"), "w").write(json.dumps({"T-005": ["visuals"]}))
    ok(score.compute(d)["unmapped"] == [] and {x["id"]: x for x in score.compute(d)["criteria"]}["visuals"]["T"][1] > 0, "score-map.json classifies a task")
    # agent note is bounded
    open(os.path.join(docs, "score-notes.json"), "w").write(json.dumps({"fun": {"adj": -5, "why": "playtest was boring"}}))
    ok(any("playtest was boring" in e for e in {x["id"]: x for x in score.compute(d)["criteria"]}["fun"]["ev"]), "agent note shown as evidence")
    # extra criterion approved through the skill
    open(os.path.join(docs, "score-criteria-extra.json"), "w").write(json.dumps([{"id": "walk", "n": "Walkie", "keywords": ["walkie"], "w": 3}]))
    ok("walk" in {x["id"] for x in score.compute(d)["criteria"]}, "approved extra criteria are added")
    # T0: a plan with nothing started scores 0 everywhere, no free points
    d0 = tempfile.mkdtemp()
    try:
        d0docs = os.path.join(d0, "Claude", "docs"); os.makedirs(d0docs)
        open(os.path.join(d0docs, "ROADMAP.md"), "w").write("# Roadmap\n\n## Tasks\n\n" + hdr + "| T-001 | Core gameplay loop | To do | x | P1 | P0-R1 |\n| T-002 | Music loop | To do | x | P2 | P0-R1 |\n")
        z = score.compute(d0)
        ok(all(max(x["B"]) == 0 and max(x["V"]) == 0 for x in z["criteria"]), "T0: nothing started = every criterion at 0, no free points for feasibility, scope or docs")
    finally:
        shutil.rmtree(d0, ignore_errors=True)
    # snapshot: R1 is closed, R2 is not
    ok(score.snapshot(d) == 1 and score.snapshot(d) == 0, "one history row per closed release, never twice")
    ok(len(open(os.path.join(d, "Claude", "logs", "score-history.jsonl")).read().splitlines()) == 1, "history file has one row")
finally:
    shutil.rmtree(d, ignore_errors=True)

rd = lambda n: open(os.path.join(H, n), encoding="utf-8-sig").read()
for page in ("agent-console.html", "agent-console-stats.html", "agent-console-docs.html", "agent-console-flow.html", "agent-console-skills.html", "agent-console-news.html", "agent-console-score.html"):
    ok('href="agent-console-score.html"' in rd(page), "%s links to the Score page" % page)
sp = rd("agent-console-score.html")
ok('"/score-data"' in sp and "made-up" not in sp.lower() and "document.write" not in sp, "the Score page reads live data, nothing hard-coded")
ok("/score-data" in rd("agent-console-server.py") and "SCORE_HTML_PATH" in rd("agent-console-server.py"), "the Python server serves the page and the data")
ok("/score-data" in rd("agent-console-server.ps1") and "ScoreHtmlPath" in rd("agent-console-server.ps1"), "the PowerShell server serves the page and the data")
ok(os.path.isfile(os.path.join(H, "..", "..", "..", "user-level-skills", "project-scoring", "SKILL.md")), "the project-scoring skill ships")
