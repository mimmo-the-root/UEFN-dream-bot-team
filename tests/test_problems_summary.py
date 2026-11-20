"""tools/problems_summary.py: counts, ages and append-only mark_handled, on temp copies only."""
import datetime, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import problems_summary as ps
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
try:
    P = os.path.join(d, "PROBLEMS-FROM-COD.md"); T = os.path.join(d, "PENDING-TESTS.md")
    open(P, "w", encoding="utf-8", newline="").write(
        "# PROBLEMS\n# format: x\n2026-11-19 04:20 | T-023 | conflict | tried | NONE\n\n2026-11-17 04:20 | pkg-1 | other | t | NONE [HANDLED 2026-11-18 10:00]\n2026-11-19 03:50 | session | a | b | c\n")
    open(T, "w", encoding="utf-8", newline="").write("# PENDING\n# format\n")
    now = datetime.datetime(2026, 11, 20, 4, 20)
    s = ps.summarize(d, now)
    ok(s["open"] == 2 and s["closed"] == 1, "counts: %r" % ((s["open"], s["closed"]),))
    f = s["files"]["PROBLEMS-FROM-COD.md"]
    ok(f["items"][0]["age_days"] == 1.0 and f["items"][0]["ref"] == "T-023", "age and ref parsed")
    ok(s["files"]["PENDING-TESTS.md"]["items"] == [], "header-only file has no items")
    json.dumps(s)
    before = open(P, encoding="utf-8", newline="").read()
    lid = f["items"][0]["line_id"]
    ok(ps.mark_handled(P, lid, now) is True, "mark_handled marks")
    after = open(P, encoding="utf-8", newline="").read()
    ok(len(after.split("\n")) == len(before.split("\n")) and after.startswith(before.split("T-023")[0]), "no line deleted")
    ok(after.replace(" [HANDLED 2026-11-20 04:20]", "") == before, "only a marker was appended")
    s2 = ps.summarize(d, now)
    ok(s2["open"] == 1 and s2["closed"] == 2, "counts after marking")
    ok(ps.mark_handled(P, lid, now) is False, "already handled returns False")
    ok(ps.mark_handled(P, "deadbeef", now) is False, "unknown id returns False")
    ok(ps.summarize(os.path.join(d, "none"), now)["open"] == 0, "missing files are empty")
finally:
    shutil.rmtree(d, ignore_errors=True)
print("problems summary tests OK")
