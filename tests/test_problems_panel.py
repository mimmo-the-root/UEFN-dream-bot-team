"""T-093: the nine console pages carry a Problemi panel (counts, ages, one-click Handled from GET /problems) and a Configurazione debug-bundle export (POST /debug-bundle), and every script parses."""
import glob, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
pages = sorted(glob.glob(os.path.join(HOOKS, "agent-console*.html")))
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

BASE_REV = {"agent-console-docs.html": 11, "agent-console-models.html": 9}
node = shutil.which("node")
ok(len(pages) == 9, "expected nine agent-console pages, found %d" % len(pages))
for p in pages:
    name = os.path.basename(p)
    t = open(p, encoding="utf-8").read()
    rev = re.search(r"<!-- kit-console-rev: (\d+) -->", t)
    want = BASE_REV.get(name, 8) + 1
    ok(rev is not None and int(rev.group(1)) >= want, "%s: kit-console-rev bumped to >= %d" % (name, want))
    m = re.search(r"<!-- problems-panel:begin -->(.*?)<!-- problems-panel:end -->", t, re.S)
    ok(m is not None, "%s: problems-panel block present" % name)
    b = m.group(1) if m else ""
    for marker in ('"/problems"', '"/problems/handled"', '"X-Router-Action"', "line_id",
                   "age_days", "Handled", "Problemi", "data-problems-tab", "d.open", "d.closed"):
        ok(marker in b, "%s: problems panel has %s" % (name, marker))
    cfg = re.search(r"<!-- config-tab:begin -->(.*?)<!-- config-tab:end -->", t, re.S)
    c = cfg.group(1) if cfg else ""
    for marker in ('"/debug-bundle"', '"X-Router-Action"', "Export debug bundle", "j.zip", "j.error"):
        ok(marker in c, "%s: debug bundle button has %s" % (name, marker))
    if node:
        for i, js in enumerate(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", t, re.S)):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
                fh.write(js)
            r = subprocess.run([node, "--check", fh.name], capture_output=True, text=True)
            os.unlink(fh.name)
            ok(r.returncode == 0, "%s: script %d: %s" % (name, i, (r.stderr.strip().splitlines() or ["node --check ok"])[-1]))
print("problems panel tests OK (%d pages%s)" % (len(pages), "" if node else ", node missing: syntax check skipped"))
