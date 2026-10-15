"""text_scan: reports emoji, decorative and invisible characters; leaves normal typography alone."""
import os, sys, json, tempfile, importlib.util, subprocess
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
path = os.path.join(root, "project-template", "Claude", "hooks", "text_scan.py")
spec = importlib.util.spec_from_file_location("text_scan", path)
ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
kinds = lambda t: [x["kind"] for x in ts.scan_text(t)]

ok(kinds("Corri veloce \U0001F680 vinci!") == ["emoji"], "rocket emoji found")
ok(kinds("❤️ love") == ["symbol", "invisible"], "heart + variation selector found")
ok(kinds("\U0001D5E1\U0001D5E2\U0001D5E3") == ["fancy-letters"] * 3, "fake bold letters found")
ok(kinds("a​b c") == ["invisible", "invisible"], "zero-width and non-breaking space found")
ok(kinds("══ TITLE ══") == ["decoration"] * 4, "box-drawing decoration found")
ok(kinds("é̂̃̄") == ["zalgo"], "stacked combining marks found")
ok(kinds("Città “prova” — vai… café è qui") == [], "accents, curly quotes, dash, ellipsis are fine")
f = ts.scan_text("ok\nline \U0001F525 here")[0]
ok(f["line"] == 2 and f["col"] == 6 and f["code"] == "U+1F525", "line, column and code are reported")

d = tempfile.mkdtemp()
open(os.path.join(d, "title.md"), "w", encoding="utf-8").write("Clean title\n")
r = subprocess.run([sys.executable, path, d], capture_output=True, text=True)
ok(r.returncode == 0 and json.loads(r.stdout)["state"] == "clean", "clean folder -> exit 0")
open(os.path.join(d, "post.md"), "w", encoding="utf-8").write("Play now \U0001F3AE\n")
r = subprocess.run([sys.executable, path, d], capture_output=True, text=True)
j = json.loads(r.stdout)
ok(r.returncode == 1 and j["state"] == "found" and j["findings"][0]["file"].endswith("post.md"), "emoji in a file -> exit 1 with file name")
r = subprocess.run([sys.executable, path, os.path.join(d, "missing")], capture_output=True, text=True)
ok(r.returncode == 2 and json.loads(r.stdout)["state"] == "nothing_to_scan", "nothing to scan is its own state, not 'clean'")
ok("\U0001F3AE" not in r.stdout and all(ord(c) < 128 for c in r.stdout), "output is plain ASCII (safe on any console)")
