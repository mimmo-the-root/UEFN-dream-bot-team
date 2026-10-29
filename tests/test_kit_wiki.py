"""The kit wiki for the second brain (second-brain-template/wiki/kit) is exactly what the manual produces, and passes the vault's own free checks."""
import os, shutil, subprocess, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
B = os.path.join(root, "tool", "build_kit_wiki.py")
V = os.path.join(root, "user-level-skills", "second-brain-query", "scripts", "vault_check.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
r = subprocess.run([sys.executable, B, "--check"], capture_output=True, text=True)
ok(r.returncode == 0, "the kit wiki is up to date with the manual (run tool/build_kit_wiki.py if not): " + r.stdout.strip()[:200])
d = tempfile.mkdtemp()
try:
    shutil.copytree(os.path.join(root, "second-brain-template", "wiki", "kit"), os.path.join(d, "wiki", "kit"))
    open(os.path.join(d, "wiki", "index.md"), "w").write("# Wiki index\n- [[kit/wiki-index|Kit]]\n")
    os.makedirs(os.path.join(d, "raw"))
    out = subprocess.run([sys.executable, V, "links", "--vault", d], capture_output=True, text=True).stdout
    ok("0 broken link" in out, "no broken link in the kit wiki: " + out.strip()[:200])
    out = subprocess.run([sys.executable, V, "stats", "--vault", d], capture_output=True, text=True).stdout
    ok("missing created/sources fields: 0" in out and "without a Sources section: 0" in out, "every kit page has its fields and a Sources section")
    ok("how-the-kit-thinks.md" in os.listdir(os.path.join(d, "wiki", "kit")), "the page that explains the kit is there")
finally:
    shutil.rmtree(d, ignore_errors=True)
print("kit wiki tests OK")
