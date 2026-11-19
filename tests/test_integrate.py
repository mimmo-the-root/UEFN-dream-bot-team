"""tools/integrate.py on temporary git repos with a fake test command."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "integrate.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t"] + list(a),
                       capture_output=True, text=True)
    assert p.returncode == 0, (a, p.stderr)
    return p.stdout.strip()


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
        f.write(t)


def commit_on(repo, branch, name, text, msg, base="main"):
    git(repo, "checkout", "-q", "-B", branch, base)
    write(os.path.join(repo, name), text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)
    git(repo, "checkout", "-q", base)


def run(repo, lab, *extra):
    cmd = [sys.executable, TOOL, "--repo", repo, "--target", "main", "--lab", lab,
           "--test-cmd", '"%s" -c "import os,sys;sys.exit(1 if os.path.exists(\'BAD\') else 0)"' % sys.executable] + list(extra)
    return subprocess.run(cmd, capture_output=True, text=True)


def snapshot(repo, lab):
    refs = git(repo, "for-each-ref")
    logs = {}
    for r, _, fs in os.walk(lab):
        for f in fs:
            logs[os.path.join(r, f)] = open(os.path.join(r, f), "rb").read()
    return refs, logs


base = tempfile.mkdtemp(prefix="test-integrate-")
try:
    repo = os.path.join(base, "repo")
    lab = os.path.join(base, "lab")
    os.makedirs(repo)
    subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
    write(os.path.join(repo, "a.txt"), "a\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    commit_on(repo, "r2/good", "good.txt", "g\n", "T-501: good package")
    commit_on(repo, "r1/pkg-bad", "BAD", "x\n", "T-502: bad package")
    commit_on(repo, "feature/other", "o.txt", "o\n", "not an integrator branch")
    write(os.path.join(lab, "docs", "ROADMAP.md"),
          "| T-501 | good | To do | acc | P1 |\r\n| T-502 | bad | To do | acc | P1 |\r\n")
    os.makedirs(os.path.join(lab, "plan"))

    before = snapshot(repo, lab)
    p = run(repo, lab, "--dry-run")
    ok(p.returncode == 0 and "would merge r2/good" in p.stdout and "feature/other" not in p.stdout, "dry-run lists only r1/r2 branches")
    ok(snapshot(repo, lab) == before, "dry-run changes nothing")

    p = run(repo, lab, "--json")
    data = json.loads(p.stdout)
    st = {r["branch"]: r["status"] for r in data["results"]}
    ok(p.returncode == 1 and st == {"r2/good": "merged", "r1/pkg-bad": "failed"}, "one merged, one failed, exit 1: %s" % st)
    ok(os.path.exists(os.path.join(repo, "good.txt")) and not os.path.exists(os.path.join(repo, "BAD")),
       "checked-out target fast-forwarded with the good branch only")
    ok(git(repo, "rev-list", "--merges", "--count", "main") == "1", "merge commit is --no-ff")
    ok(git(repo, "status", "--porcelain") == "", "user working tree clean")
    ok(git(repo, "rev-parse", "r1/pkg-bad") == git(repo, "rev-parse", "r1/pkg-bad"), "failed branch still present")
    ok(git(repo, "worktree", "list").count("\n") == 0, "no temp worktree left")
    fb = open(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md")).read()
    pr = open(os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md")).read()
    ok("PLANNER-AUTO: COMMITTED r2/good " + git(repo, "rev-parse", "--short=9", "main") in fb and "tests ok" in fb, "COMMITTED line written")
    ok("| integrate | r1/pkg-bad |" in pr and "tests failed" in pr, "problem line written")
    road = open(os.path.join(lab, "docs", "ROADMAP.md"), "rb").read()
    ok(b"| T-501 | good | Done - merged" in road and b"suite ok" in road and b"| T-502 | bad | In progress" in road, "roadmap rows updated")
    ok(road.count(b"\r\n") == 2 and road.replace(b"\r\n", b"").count(b"\n") == 0, "CRLF kept")

    after = snapshot(repo, lab)
    p = run(repo, lab)
    ok(p.returncode == 0 and snapshot(repo, lab) == after, "second run changes nothing and exits 0")

    # target not checked out anywhere: update-ref path
    git(repo, "checkout", "-q", "--detach")
    commit_on(repo, "r2/second", "second.txt", "s\n", "T-503: second", base="main")
    git(repo, "checkout", "-q", "--detach")
    p = run(repo, lab)
    ok(p.returncode == 0 and git(repo, "rev-list", "--merges", "--count", "main") == "2", "target advanced by update-ref when not checked out")

    # unfinished merge blocks the run
    git(repo, "checkout", "-q", "main")
    open(os.path.join(repo, ".git", "MERGE_HEAD"), "w").write(git(repo, "rev-parse", "HEAD") + "\n")
    commit_on_ok = subprocess.run(["git", "-C", repo, "branch", "r2/more", "HEAD~1"], capture_output=True)
    p = run(repo, lab)
    ok(p.returncode == 1 and "unfinished merge" in p.stdout, "unfinished merge is reported")
    os.remove(os.path.join(repo, ".git", "MERGE_HEAD"))

    p = subprocess.run([sys.executable, TOOL, "--bogus"], capture_output=True, text=True)
    ok(p.returncode == 2, "usage error exits 2")
finally:
    shutil.rmtree(base, ignore_errors=True)
print("ALL PASS")
