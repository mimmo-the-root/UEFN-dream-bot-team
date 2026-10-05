import os, subprocess, sys, tempfile, shutil
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
def run(script, *a):
    return subprocess.run([sys.executable, os.path.join(root, "tool", script), *a], capture_output=True, text=True)
d = tempfile.mkdtemp()
try:
    open(os.path.join(d, "a.md"), "w").write("see C:\\Users\\bob\\x and ghp_" + "a" * 36 + "\n")  # privacy-scan: allow
    open(os.path.join(d, ".mcp.json"), "w").write("{}")
    r = run("privacy_scan.py", d)
    assert r.returncode == 1 and "personal path" in r.stdout and "GitHub token" in r.stdout and ".mcp.json" in r.stdout, r.stdout
    os.remove(os.path.join(d, "a.md")); os.remove(os.path.join(d, ".mcp.json"))
    open(os.path.join(d, "ok.md"), "w").write("path C:\\Users\\<you>\\.claude and C:\\path\\to\\vault\n")
    assert run("privacy_scan.py", d).returncode == 0
    sk = os.path.join(d, "skills", "my-skill"); os.makedirs(sk)
    open(os.path.join(sk, "SKILL.md"), "w").write("---\nname: wrong\ndescription: short\n---\nsee references/nope.md\n")
    r = run("validate_skills.py", os.path.join(d, "skills"))
    assert r.returncode == 1 and "name must equal" in r.stdout and "missing file" in r.stdout and "description" in r.stdout, r.stdout
    open(os.path.join(sk, "SKILL.md"), "w").write("---\nname: my-skill\ndescription: A valid description that is long enough.\nlast_reviewed: 2026-10-05\nsources: [original]\n---\nbody\n")
    r = run("validate_skills.py", "--strict", os.path.join(d, "skills"))
    assert r.returncode == 0, r.stdout
    print("repo checks tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
