"""Every script in the console pages must parse: one wrong quote stops the whole page (the Models page went blank in 1.124.52).
Uses node --check when node is installed; skips otherwise."""
import glob, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
node = shutil.which("node")
if not node:
    print("ok console_js (skipped: node not installed)")
    sys.exit(0)
bad = []
for page in sorted(glob.glob(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console*.html"))):
    html = open(page, encoding="utf-8").read()
    for i, js in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        os.unlink(f.name)
        if r.returncode:
            bad.append("%s script %d: %s" % (os.path.basename(page), i, (r.stderr.strip().splitlines() or ["?"])[-1]))
assert not bad, "\n".join(bad)
print("ok console_js")
