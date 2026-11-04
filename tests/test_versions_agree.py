"""The version is the same everywhere: KIT-VERSION, every console page, the top entry of CHANGELOG.md, README and whats-new.json."""
import glob, json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
rd = lambda *p: open(os.path.join(ROOT, *p), encoding="utf-8").read()
ver = rd("project-template", "Claude", "KIT-VERSION").strip()
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
check("KIT-VERSION is X.Y.Z", bool(re.match(r"^\d+\.\d+\.\d+$", ver)))
bad = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console*.html")) if ver not in open(p, encoding="utf-8").read()]
check("every console page carries %s (%s)" % (ver, ", ".join(bad) or "all"), not bad)
m = re.search(r"^## v([\d.]+)", rd("CHANGELOG.md"), re.M)
check("the top entry of CHANGELOG.md is %s" % ver, bool(m) and m.group(1) == ver)
check("README names the version in its What's new heading", ("v" + ver) in rd("README.md"))
check("whats-new.json has this version", ver in json.loads(rd("project-template", "Claude", "reference", "whats-new.json"))["versions"])
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
