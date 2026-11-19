#!/usr/bin/env python3
"""Auto-integrator: merge r1/* and r2/* branches into a target branch when the suite passes.

Usage: python tools/integrate.py --repo REPO --target release/ibrido-0 [--lab LABDIR]
       [--timeout 600] [--test-cmd "python tests/run_all.py"] [--dry-run] [--json]

For each local branch r1/* or r2/* with commits not in the target: temp detached worktree,
merge --no-ff, run the test command, and only on a pass move the target to the merge commit.
Never pushes, never deletes branches or tags, never forces. Exit: 0 ok/nothing to do, 1 a branch
failed or integration was blocked, 2 usage error.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time

PREFIXES = ("r1/", "r2/")
_CHILD = [None]  # test process currently running, killed if this run is terminated
TID = re.compile(r"\bT-\d{1,4}\b")


def now():
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime())


def git(repo, *args, check=False):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
    return p


def out(repo, *args):
    p = git(repo, *args)
    return p.stdout.strip() if p.returncode == 0 else ""


def append_line(path, line):
    """Append one line, matching the file's existing line ending (default LF)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = b""
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    if data and not data.endswith(b"\n"):
        data += nl
    with open(path, "wb") as f:
        f.write(data + line.encode("utf-8") + nl)


def worktrees(repo):
    """List of (path, branch-or-None) from git worktree list --porcelain."""
    res, cur = [], {}
    for ln in out(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not ln:
            if cur:
                res.append((cur.get("worktree"), cur.get("branch", "").replace("refs/heads/", "") or None))
            cur = {}
        elif " " in ln:
            k, v = ln.split(" ", 1)
            cur[k] = v
    return res


def unfinished_merge(repo):
    for wt, _ in worktrees(repo):
        p = git(wt, "rev-parse", "--git-path", "MERGE_HEAD")
        if p.returncode == 0:
            mh = p.stdout.strip()
            if not os.path.isabs(mh):
                mh = os.path.join(wt, mh)
            if os.path.exists(mh):
                return wt
    return None


def discover(repo, target):
    names = out(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines()
    found = []
    for b in sorted(names):
        if b == target or not b.startswith(PREFIXES):
            continue
        n = out(repo, "rev-list", "--count", "%s..%s" % (target, b))
        if n.isdigit() and int(n) > 0:
            found.append(b)
    return found


def kill_group(proc):
    """Kill the whole process group of a child started with start_new_session."""
    try:
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except OSError:
        pass


def pid_alive(pid):
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def acquire_lock(repo):
    """Create <git-common-dir>/integrate.lock holding our pid. Returns lock path, or None when
    another live run holds it. A lock whose pid is dead is taken over."""
    gd = out(repo, "rev-parse", "--git-common-dir")
    gd = gd if os.path.isabs(gd) else os.path.join(repo, gd)
    path = os.path.join(gd, "integrate.lock")
    for _ in range(3):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    pid = int(f.read().strip() or 0)
            except (OSError, ValueError):
                pid = 0
            if pid and pid_alive(pid):
                return None
            try:
                os.unlink(path)
            except OSError:
                pass
            continue
        with os.fdopen(fd, "w") as f:
            f.write("%d\n" % os.getpid())
        return path
    return None


def prune_stale(repo, log):
    """Remove leftover temp worktrees (<tmp>/integrate-*/wt) of killed runs, then git worktree prune."""
    tmp = os.path.realpath(tempfile.gettempdir())
    for path, _ in worktrees(repo):
        if not path:
            continue
        rp = os.path.realpath(path)
        base = os.path.dirname(rp)
        if (os.path.basename(rp) == "wt" and os.path.basename(base).startswith("integrate-")
                and os.path.dirname(base) == tmp):
            git(repo, "worktree", "unlock", path)
            git(repo, "worktree", "remove", "--force", "--force", path)
            shutil.rmtree(base, ignore_errors=True)
            log("removed stale worktree %s" % path)
    git(repo, "worktree", "prune")


def _terminate(signum, frame):
    raise SystemExit(128 + signum)


def run_tests(cmd, cwd, timeout):
    argv = shlex.split(cmd)
    if argv and argv[0] in ("python", "python3") and not shutil.which(argv[0]):
        argv[0] = sys.executable
    try:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace",
                                start_new_session=(os.name != "nt"))
    except OSError as e:
        return False, "test command could not start: %s" % e
    _CHILD[0] = proc
    try:
        text, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_group(proc)
        proc.communicate()
        return False, "tests timed out after %ss" % timeout
    except BaseException:
        kill_group(proc)
        raise
    finally:
        _CHILD[0] = None
    if proc.returncode == 0:
        return True, ""
    tail = " / ".join([l.strip() for l in (text or "").splitlines() if l.strip()][-2:])
    return False, ("tests failed (exit %d) %s" % (proc.returncode, tail)).strip()[:300]


def task_ids(repo, target, branch):
    msgs = out(repo, "log", "--format=%B", "%s..%s" % (target, branch))
    seen = []
    for t in TID.findall(msgs):
        if t not in seen:
            seen.append(t)
    return seen


def set_status(lab, ids, status, note, pct, gate, log):
    """Write roadmap status: batch mode of task_status.py if it has one, else one direct row edit."""
    if not lab or not ids:
        return
    ts = os.path.join(lab, "hooks", "task_status.py")
    if os.path.exists(ts):
        try:
            has_batch = "--batch" in open(ts, encoding="utf-8", errors="replace").read()
        except OSError:
            has_batch = False
        if has_batch:
            fd, tmp = tempfile.mkstemp(suffix=".txt", text=True)
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                for i in ids:
                    f.write("%s|%s|%s|%s|%s\n" % (i, status, note, pct, gate))
            try:
                p = subprocess.run([sys.executable, ts, "--batch", tmp], cwd=lab, capture_output=True, text=True)
                if p.returncode != 0:
                    log("status batch failed: %s" % (p.stderr or p.stdout).strip()[:200])
            finally:
                os.unlink(tmp)
            return
    road = os.path.join(lab, "docs", "ROADMAP.md")
    if not os.path.exists(road):
        return
    with open(road, "rb") as f:
        raw = f.read()
    lines = raw.splitlines(keepends=True)
    changed = False
    for n, ln in enumerate(lines):
        for i in ids:
            if ln.startswith(("| %s |" % i).encode()):
                body = ln.rstrip(b"\r\n")
                tail = ln[len(body):]
                cells = body.decode("utf-8").split(" | ")
                if len(cells) > 3:
                    cells[2] = "%s - %s" % (status, note)
                    lines[n] = " | ".join(cells).encode("utf-8") + tail
                    changed = True
    if changed:
        with open(road, "wb") as f:
            f.write(b"".join(lines))


def lint(lab, log):
    lp = os.path.join(lab, "hooks", "docs_lint.py") if lab else ""
    if lp and os.path.exists(lp):
        p = subprocess.run([sys.executable, lp], cwd=lab, capture_output=True, text=True)
        if p.returncode != 0:
            log("docs_lint reported problems: %s" % (p.stdout or p.stderr).strip()[:300])


def already_failed(lab, branch, tip):
    path = os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md") if lab else ""
    if not path or not os.path.exists(path):
        return False
    key = "| integrate | %s |" % branch
    with open(path, encoding="utf-8", errors="replace") as f:
        return any(key in l and "tip %s" % tip in l for l in f)


def integrate_one(repo, target, branch, tip, args, lab, log):
    """Returns dict result. Leaves the repo untouched on failure."""
    res = {"branch": branch, "tip": tip, "status": "failed", "sha": "", "reason": ""}
    base = tempfile.mkdtemp(prefix="integrate-")
    wt = os.path.join(base, "wt")
    added = False

    def fail(reason):
        res["status"], res["reason"] = "failed", reason
        if lab:
            append_line(os.path.join(lab, "plan", "PROBLEMS-FROM-COD.md"),
                        "%s | integrate | %s | %s (tip %s)" % (now(), branch, reason, tip))
        return res
    try:
        old = out(repo, "rev-parse", target)
        p = git(repo, "worktree", "add", "--detach", wt, target)
        if p.returncode != 0:
            return fail("worktree add failed: %s" % p.stderr.strip()[:200])
        added = True
        ident = []
        if not out(wt, "config", "user.name"):
            ident += ["-c", "user.name=integrator"]
        if not out(wt, "config", "user.email"):
            ident += ["-c", "user.email=integrator@localhost"]
        m = git(wt, *(ident + ["merge", "--no-ff", "-m", "Merge %s (auto-integrate)" % branch, branch]))
        if m.returncode != 0:
            git(wt, "merge", "--abort")
            return fail("merge failed: %s" % " ".join((m.stdout + m.stderr).split())[:200])
        sha = out(wt, "rev-parse", "HEAD")
        short = sha[:9]
        ids = task_ids(repo, target, branch)
        set_status(lab, ids, "In progress", "merged %s; suite running" % short, 80, "", log)
        ok, why = run_tests(args.test_cmd, wt, args.timeout)
        if not ok:
            set_status(lab, ids, "In progress", "integration of %s failed: %s" % (short, why[:80]), 80, "", log)
            lint(lab, log)
            return fail(why)
        # advance the target
        holder = next((p for p, b in worktrees(repo) if b == target), None)
        if holder:
            if out(holder, "status", "--porcelain"):
                set_status(lab, ids, "In progress", "merged %s; blocked: target worktree dirty" % short, 80, "", log)
                return fail("target %s is checked out in %s with local changes; not touched" % (target, holder))
            f = git(holder, "merge", "--ff-only", sha)
            if f.returncode != 0:
                return fail("fast-forward of checked-out target failed: %s" % f.stderr.strip()[:200])
        else:
            u = git(repo, "update-ref", "-m", "integrate %s" % branch, "refs/heads/" + target, sha, old)
            if u.returncode != 0:
                return fail("update-ref failed: %s" % u.stderr.strip()[:200])
        set_status(lab, ids, "Done", "merged %s, suite ok" % short, 100, "pass", log)
        lint(lab, log)
        if lab:
            append_line(os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md"),
                        "%s | PLANNER-AUTO: COMMITTED %s %s tests ok" % (now(), branch, short))
        res.update(status="merged", sha=sha)
        return res
    finally:
        if added:
            git(repo, "worktree", "remove", "--force", wt)
        shutil.rmtree(base, ignore_errors=True)
        git(repo, "worktree", "prune")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="integrate.py", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--lab")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--test-cmd", default="python tests/run_all.py")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    repo = os.path.abspath(args.repo)
    lab = os.path.abspath(args.lab) if args.lab else None
    msgs = []

    def log(m):
        msgs.append(m)
        if not args.json:
            print(m)

    def finish(results, code):
        if args.json:
            print(json.dumps({"repo": repo, "target": args.target, "dry_run": args.dry_run,
                              "results": results, "messages": msgs}, indent=2))
        return code

    if args.timeout <= 0 or not os.path.isdir(repo) or git(repo, "rev-parse", "--git-dir").returncode != 0:
        print("integrate: --repo must be a git repository and --timeout positive", file=sys.stderr)
        return 2
    if git(repo, "rev-parse", "--verify", "--quiet", "refs/heads/" + args.target).returncode != 0:
        print("integrate: target branch %s not found" % args.target, file=sys.stderr)
        return 2
    blocked = unfinished_merge(repo)
    if blocked:
        log("unfinished merge in %s: resolve or abort it first; nothing done" % blocked)
        return finish([], 1)
    lock = None
    if not args.dry_run:
        lock = acquire_lock(repo)
        if lock is None:
            print("integrate: another run is active")
            return 0
    old_handlers = {}
    try:
        for sg in (signal.SIGTERM, signal.SIGINT):
            old_handlers[sg] = signal.signal(sg, _terminate)
        if not args.dry_run:
            prune_stale(repo, log)
        return run_all(repo, args, lab, log, finish)
    finally:
        if _CHILD[0] is not None:
            kill_group(_CHILD[0])
        for sg, h in old_handlers.items():
            signal.signal(sg, h)
        if lock:
            try:
                os.unlink(lock)
            except OSError:
                pass


def run_all(repo, args, lab, log, finish):
    results, code = [], 0
    for br in discover(repo, args.target):
        tip = out(repo, "rev-parse", "--short=9", br)
        if args.dry_run:
            results.append({"branch": br, "tip": tip, "status": "would-merge", "sha": "", "reason": ""})
            log("would merge %s (%s)" % (br, tip))
            continue
        if already_failed(lab, br, tip):
            results.append({"branch": br, "tip": tip, "status": "skipped", "sha": "",
                            "reason": "already failed at this tip"})
            log("skip %s: already failed at tip %s" % (br, tip))
            continue
        r = integrate_one(repo, args.target, br, tip, args, lab, log)
        results.append(r)
        if r["status"] == "merged":
            log("merged %s -> %s %s" % (br, args.target, r["sha"][:9]))
        else:
            code = 1
            log("FAILED %s: %s" % (br, r["reason"]))
    if not results:
        log("nothing to integrate")
    return finish(results, code)


if __name__ == "__main__":
    sys.exit(main())
