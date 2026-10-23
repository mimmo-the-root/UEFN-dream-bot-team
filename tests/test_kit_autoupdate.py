"""Automatic profile update: the global SessionStart hook starts a throttled background check; kit_fetch --auto installs a newer release."""
import importlib.util, io, os, shutil, sys, tempfile, zipfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import kit_fetch
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
try:
    home = os.path.join(d, "home", ".claude")
    os.environ["UEFN_HOME"] = home
    # a release zip made from this repo
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for part in ("project-template", "user-level-agents", "user-level-skills"):
            for b, ds, fs in os.walk(os.path.join(root, part)):
                ds[:] = [x for x in ds if x != "__pycache__"]
                for f in fs:
                    p = os.path.join(b, f); zf.write(p, "o-r-abc/" + os.path.relpath(p, root).replace(os.sep, "/"))
    new = open(os.path.join(root, "project-template", "Claude", "KIT-VERSION")).read().strip()
    kit_fetch.latest_tag = lambda repo=None: "v" + new
    kit_fetch._get = lambda url: buf.getvalue()
    os.makedirs(os.path.join(home, "kit-template", "Claude"))
    open(os.path.join(home, "kit-template", "Claude", "KIT-VERSION"), "w").write("1.0.0")
    ok(kit_fetch.auto() == 0 and open(os.path.join(home, "kit-template", "Claude", "KIT-VERSION")).read().strip() == new, "a newer release is installed into the profile")
    log = open(os.path.join(home, "kit-auto-update.log")).read()
    ok("1.0.0 ->" in log and not os.path.exists(os.path.join(home, "kit-auto-update.lock")), "one log line, no lock left")
    kit_fetch.auto()
    ok("up to date" in open(os.path.join(home, "kit-auto-update.log")).read(), "nothing is downloaded when the profile is current")
    # the version file is copied last
    src = tempfile.mkdtemp(); order = []
    os.makedirs(os.path.join(src, "project-template", "Claude")); open(os.path.join(src, "project-template", "Claude", "KIT-VERSION"), "w").write("9.9.9")
    open(os.path.join(src, "project-template", "Claude", "a.txt"), "w").write("a")
    real = shutil.copy2; shutil.copy2 = lambda s, dd, **k: (order.append(os.path.basename(s)), real(s, dd, **k))[1]
    kit_fetch.apply(src, os.path.join(d, "h2")); shutil.copy2 = real
    ok(order == ["a.txt", "KIT-VERSION"], "KIT-VERSION is written last, so an interrupted update is retried")
    # hook: throttle and opt-out
    spec = importlib.util.spec_from_file_location("ksg", os.path.join(root, "user-level-hooks", "kit-sync-global.py"))
    src_text = open(spec.origin, encoding="utf-8").read().split("try:\n    sys.exit(main())")[0]
    ns = {"__name__": "ksg"}; exec(compile(src_text, spec.origin, "exec"), ns)
    import subprocess
    calls = []
    class P:  # no real process in the test
        def __init__(self, *a, **k): calls.append(a)
    real_popen = subprocess.Popen; subprocess.Popen = P
    os.environ["HOME"] = os.path.join(d, "home"); os.environ["USERPROFILE"] = os.path.join(d, "home")
    tpl = os.path.join(home, "kit-template")
    ok(ns["maybe_auto_update"](tpl) is True and len(calls) == 1, "the hook starts the background check")
    ok(ns["maybe_auto_update"](tpl) is False and len(calls) == 1, "the second session within 6 hours does not")
    os.remove(os.path.join(home, "kit-update-check.stamp")); open(os.path.join(home, "kit-auto-update.off"), "w").close()
    ok(ns["maybe_auto_update"](tpl) is False, "kit-auto-update.off switches it off")
    subprocess.Popen = real_popen
    # the project hook (kit_sync) starts the same background check, so `/kit-update --fetch` once is enough to switch it on
    import kit_sync
    calls.clear(); subprocess.Popen = P
    for f in ("kit-update-check.stamp", "kit-auto-update.off"):
        try: os.remove(os.path.join(home, f))
        except OSError: pass
    ok(kit_sync.auto_update_check() is True and len(calls) == 1 and kit_sync.auto_update_check() is False, "kit_sync (project hook) starts the check once per 6 hours")
    subprocess.Popen = real_popen
    # release_zip: prefers the kit.zip asset (GitHub counts its downloads), falls back to the source zip
    import json
    seen = []
    def fake(url, accept="application/vnd.github+json"):
        seen.append((url, accept))
        if "/releases/tags/" in url:
            return json.dumps({"assets": [{"name": "kit.zip", "url": "https://api.github.com/repos/o/r/releases/assets/7"}]}).encode()
        return b"ZIP"
    kit_fetch._get = fake
    ok(kit_fetch.release_zip("v9.9.9") == b"ZIP" and seen[-1] == ("https://api.github.com/repos/o/r/releases/assets/7", "application/octet-stream"), "the update downloads the kit.zip asset when the release has one")
    kit_fetch._get = lambda url, accept="": json.dumps({"assets": []}).encode() if "/releases/tags/" in url else url.encode()
    ok(b"/zipball/v9.9.9" in kit_fetch.release_zip("v9.9.9"), "without the asset it falls back to the source zip")
    wf = open(os.path.join(root, ".github", "workflows", "release.yml")).read()
    ok("kit.zip" in wf and "gh release upload" in wf, "the release workflow builds and uploads kit.zip")
finally:
    shutil.rmtree(d, ignore_errors=True)
