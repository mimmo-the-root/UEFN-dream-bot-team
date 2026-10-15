"""ui_kit_check: package missing / AGENTS.md missing / changed / ok, accept and diff. Epic's file is never copied into the kit."""
import os, sys, json, tempfile, subprocess, shutil
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
script = os.path.join(root, "project-template", "Claude", "hooks", "ui_kit_check.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def run(proj, *args):
    env = dict(os.environ, UEFN_KIT_EPIC_DIR=os.path.join(proj, "_epic"))
    r = subprocess.run([sys.executable, script, "--project", proj] + list(args), capture_output=True, text=True, env=env)
    lines = r.stdout.strip().splitlines()
    return r.returncode, json.loads(lines[-1]), r.stdout

def project(with_kit=True, agents=None, claude_md=None):
    p = tempfile.mkdtemp()
    os.makedirs(os.path.join(p, "Claude", "reference"))
    shutil.copy(os.path.join(root, "project-template", "Claude", "reference", "ui-kit-reviewed-hashes.json"), os.path.join(p, "Claude", "reference"))
    if with_kit:
        k = os.path.join(p, "VerseUIKit")
        os.makedirs(os.path.join(k, "Widgets"))
        open(os.path.join(k, "ui_modules.verse"), "w").write("# test\n")
        if agents is not None:
            open(os.path.join(k, "AGENTS.md"), "wb").write(agents)
    if claude_md:
        open(os.path.join(p, "CLAUDE.md"), "w").write(claude_md)
    return p

c, r, _ = run(project(with_kit=False))
ok(c == 1 and r["state"] == "package_missing" and "optional" in r["message"] and "Never block" in r["message"], "no VerseUIKit folder -> package_missing, but optional and never blocking")
c, r, _ = run(project())
ok(c == 2 and r["state"] == "agents_missing" and "separate download" in r["message"], "kit without AGENTS.md -> agents_missing")
p = project(agents=b"Some guide v1\n")
c, r, _ = run(p)
ok(c == 3 and r["state"] == "agents_changed", "unknown AGENTS.md -> agents_changed")
c, r, _ = run(p, "--diff")
ok(r["state"] == "no_previous", "diff without an accepted copy says so")
c, r, _ = run(p, "--accept")
ok(c == 0 and os.path.isfile(os.path.join(p, "_epic", "reviewed.json")), "accept remembers the version")
c, r, _ = run(p)
ok(c == 0 and r["state"] == "ok", "accepted version -> ok")
open(os.path.join(p, "VerseUIKit", "AGENTS.md"), "wb").write(b"Some guide v2\nnew line\n")
c, r, _ = run(p)
ok(c == 3, "a later change is noticed")
c, r, out = run(p, "--diff")
ok(c == 0 and "+new line" in out and "-" in out, "diff shows what changed against the accepted copy")
# line endings and BOM do not count as a change
q = project(agents=b"Some guide v1\n")
run(q, "--accept")
open(os.path.join(q, "VerseUIKit", "AGENTS.md"), "wb").write(b"\xef\xbb\xbfSome guide v1\r\n")
ok(run(q)[0] == 0, "BOM and CRLF are not a change")
# one shared copy for all projects: no AGENTS.md inside the project needed
g = project()
src = os.path.join(g, "download.md"); open(src, "wb").write(b"Epic guide\n")
ok(run(g)[1]["state"] == "agents_missing" and "_epic" in run(g)[1]["message"], "missing guide message names the shared place")
c, r, _ = run(g, "--store", src)
ok(c == 0 and r["state"] == "stored" and os.path.isfile(os.path.join(g, "_epic", "AGENTS.md")), "--store puts the download in the shared place")
c, r, _ = run(g)
ok(c == 3 and r["agents_path"].endswith(os.path.join("_epic", "AGENTS.md")), "shared copy is found without any file in the project")
run(g, "--accept")
ok(run(g)[0] == 0, "accepted once, ok after")
# kit found one level down (project root above Content)
t = tempfile.mkdtemp(); os.makedirs(os.path.join(t, "Plugins", "x", "Content", "VerseUIKit", "Widgets"))
open(os.path.join(t, "Plugins", "x", "Content", "VerseUIKit", "ui_modules.verse"), "w").write("#\n")
ok(run(t)[1]["state"] == "agents_missing", "kit found in a nested Content folder")
# shipped fingerprint is a real sha256 and no copy of Epic's text is shipped
hs = json.load(open(os.path.join(root, "project-template", "Claude", "reference", "ui-kit-reviewed-hashes.json")))["reviewed"]
ok(all(len(h["sha256"]) == 64 for h in hs), "shipped list holds only SHA-256 fingerprints")
found = [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs if f == "AGENTS.md" and "_spike" not in d and "_private" not in d and ".git" not in d.split(os.sep)]
ok(not found, "no AGENTS.md copy anywhere in the kit repo: %s" % found)
env = dict(os.environ, UEFN_KIT_EPIC_DIR=os.path.join(tempfile.mkdtemp(), "_epic"))
r = subprocess.run([sys.executable, script, project(with_kit=False)], capture_output=True, text=True, env=env)
ok(r.returncode == 1 and json.loads(r.stdout)["state"] == "package_missing", "project folder can be given as a plain argument")
