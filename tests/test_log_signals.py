"""Log signals: parse, summarize, judge against rules, record."""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-level-hooks"))
import log_signals as s
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
log = """LogVerse: [SIGNAL] round_end winner=3 seconds=120
LogVerse: [SIGNAL] round_end winner=4 seconds=300
LogVerse: Error: something broke
LogVerse: Warning: slow
LogVerse: [SIGNAL] reward who=bob amount=10
"""
r = s.parse(log)
ok(r["signals"]["round_end"]["count"] == 2 and r["signals"]["round_end"]["fields"]["seconds"]["avg"] == 210.0, "counts and numeric fields")
ok(r["signals"]["reward"]["fields"]["who"]["values"] == ["bob"], "text fields are listed")
ok(r["errors"] == 1 and r["warnings"] == 1, "error and warning lines counted, signal lines are not")
rules = {"expect": {"round_end": {"min": 3}, "match_start": {"min": 1}}, "never": ["reward"], "range": {"round_end.seconds": [30, 250]}}
f = s.judge(r, rules)
ok(len(f) == 4, "four findings: too few, missing, forbidden, out of range")
ok(any("match_start" in x and "saw 0" in x for x in f), "a signal never printed is a finding, not fine")
ok(s.judge(r, {"expect": {"round_end": {"min": 1}}}) == [], "satisfied rule gives no finding")
d = tempfile.mkdtemp()
try:
    lp = os.path.join(d, "a.log"); open(lp, "w").write(log)
    ok(s.main(["summary", lp, "--record", d]) == 0, "summary with --record runs")
    ok(len(open(os.path.join(d, "Claude", "logs", "signals.jsonl")).read().splitlines()) == 1, "one history row recorded")
    os.makedirs(os.path.join(d, "Claude", "docs"))
    json.dump({"never": ["reward"]}, open(os.path.join(d, "Claude", "docs", "signals.json"), "w"))
    ok(s.main(["summary", lp, "--record", d]) == 1, "rules file in the project is picked up")
finally:
    shutil.rmtree(d, ignore_errors=True)
