#!/usr/bin/env python3
"""kit_fetch.py - bring the kit in your profile (~/.claude) to the newest GitHub release, then sync this project.

Usage (from the project folder):  python Claude/hooks/kit_fetch.py [--check] [--zip FILE] [--force]
  --check   only print the installed and the latest version, change nothing
  --zip     use a release zip you already downloaded (offline / tests); default: download the latest release
  --force   apply even if the release is not newer
Updates: ~/.claude/kit-template, ~/.claude/agents, ~/.claude/skills, ~/.claude/hooks (never local/ or pack/ folders), each replaced file
is first copied to ~/.claude/kit-backup/<timestamp>/. Then runs the normal project sync. Does not touch ~/.claude/CLAUDE.md.
Safety: HTTPS to api.github.com only, zip paths checked (no ../), size cap 60 MB, only these four folders are read from the zip.
Env: UEFN_KIT_REPO (default mimmo-the-root/UEFN-dream-bot-team), UEFN_HOME (profile dir), UEFN_KIT_TEMPLATE.
"""
import io, json, os, re, shutil, sys, time, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_sync  # noqa: E402

REPO = os.environ.get("UEFN_KIT_REPO", "mimmo-the-root/UEFN-dream-bot-team")
CAP = 60 * 1024 * 1024
TIMEOUT = 30
PARTS = {"project-template": "kit-template", "user-level-agents": "agents", "user-level-skills": "skills", "user-level-hooks": "hooks"}  # hooks: the global SessionStart hook updates itself too
SKIP_DIRS = {"local", "pack", "__pycache__"}  # skills' private/learned data and caches are never replaced


def _get(url, accept="application/vnd.github+json"):
    if not url.startswith("https://api.github.com/"):
        raise ValueError("refusing non-GitHub URL")
    req = urllib.request.Request(url, headers={"User-Agent": "uefn-kit-fetch", "Accept": accept})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(CAP + 1)
    if len(data) > CAP:
        raise ValueError("download larger than %d MB" % (CAP // 1048576))
    return data


def release_zip(tag, repo=REPO):
    """The release file kit.zip when the release has one (GitHub counts its downloads: that is how we know roughly how many
    machines took each version; nothing is sent from your computer), else GitHub's automatic source zip."""
    try:
        rel = json.loads(_get("https://api.github.com/repos/%s/releases/tags/%s" % (repo, tag)))
        for a in rel.get("assets", []):
            if a.get("name") == "kit.zip" and a.get("url", "").startswith("https://api.github.com/"):
                return _get(a["url"], "application/octet-stream")
    except Exception:  # noqa: BLE001
        pass
    return _get("https://api.github.com/repos/%s/zipball/%s" % (repo, tag))


def latest_tag(repo=REPO):
    try:
        return json.loads(_get("https://api.github.com/repos/%s/releases/latest" % repo))["tag_name"]
    except Exception:  # no release object: fall back to the highest vX.Y.Z tag
        tags = [t["name"] for t in json.loads(_get("https://api.github.com/repos/%s/tags?per_page=100" % repo))]
        tags = [t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
        if not tags:
            raise
        return max(tags, key=lambda t: tuple(int(x) for x in t[1:].split(".")))


def extract(zbytes, dest):
    """Extract only the kit folders, refusing unsafe paths. Returns the version found in the zip."""
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    version = ""
    for info in z.infolist():
        if info.is_dir():
            continue
        parts = info.filename.split("/")
        if len(parts) < 3 or parts[1] not in PARTS:
            continue
        rel = "/".join(parts[1:])
        if ".." in parts or rel.startswith("/") or ":" in parts[0] or "\\" in info.filename:
            raise ValueError("unsafe path in zip: " + info.filename)
        if SKIP_DIRS & set(parts[2:-1]):
            continue
        target = os.path.join(dest, *parts[1:])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with z.open(info) as src, open(target, "wb") as out:
            out.write(src.read())
        if rel == "project-template/Claude/KIT-VERSION":
            version = open(target, encoding="utf-8").read().strip()
    if not version:
        raise ValueError("zip is not a kit release (no project-template/Claude/KIT-VERSION)")
    return version


def apply(extracted, home):
    """Copy the extracted folders into the profile, backing up every file that changes."""
    backup = os.path.join(home, "kit-backup", time.strftime("%Y%m%d-%H%M%S"))
    changed = 0
    last = []  # the version file goes last: an interrupted update is retried at the next check instead of looking finished
    for src_name, dst_name in PARTS.items():
        src = os.path.join(extracted, src_name)
        for base, dirs, files in os.walk(src):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                s = os.path.join(base, f)
                rel = os.path.relpath(s, src)
                d = os.path.join(home, dst_name, rel)
                if os.path.isfile(d) and kit_sync._norm_hash(d) == kit_sync._norm_hash(s):
                    continue
                if os.path.isfile(d):
                    b = os.path.join(backup, dst_name, rel)
                    os.makedirs(os.path.dirname(b), exist_ok=True)
                    shutil.copy2(d, b)
                if dst_name == "kit-template" and rel.replace("\\", "/") == "Claude/KIT-VERSION":
                    last.append((s, d))
                    continue
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                changed += 1
    for s, d in last:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        changed += 1
    return changed, backup


def auto():
    """Background mode (started by the global SessionStart hook, never blocks a session): if a newer release exists,
    download it into the profile. Projects pick it up at their next session start (kit_sync). Quiet; one log line."""
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    log = os.path.join(home, "kit-auto-update.log")
    lock = os.path.join(home, "kit-auto-update.lock")

    def say(msg):
        try:
            with open(log, "a", encoding="utf-8") as f:
                f.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        except OSError:
            pass
    try:
        if os.path.exists(lock) and time.time() - os.path.getmtime(lock) < 600:
            return 0  # another run is working
        os.makedirs(home, exist_ok=True)
        open(lock, "w").write(str(os.getpid()))
    except OSError:
        return 0
    try:
        cur = ""
        try:
            cur = open(os.path.join(home, "kit-template", "Claude", "KIT-VERSION"), encoding="utf-8").read().strip()
        except OSError:
            pass
        tag = latest_tag()
        if cur and not kit_sync._newer(tag.lstrip("v"), cur):
            say("up to date (%s)" % cur)
            return 0
        import tempfile
        tmp = tempfile.mkdtemp(prefix="kitfetch-")
        try:
            new = extract(release_zip(tag), tmp)
            n, _backup = apply(tmp, home)
            say("profile %s -> %s (%s): %d file(s)" % (cur or "none", new, tag, n))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        say("failed: %s" % e)
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass
    return 0


def main():
    argv = sys.argv[1:]
    if "--auto" in argv:
        global TIMEOUT
        TIMEOUT = 20
        return auto()
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    project = os.getcwd()
    cur = ""
    try:
        cur = open(os.path.join(home, "kit-template", "Claude", "KIT-VERSION"), encoding="utf-8").read().strip()
    except OSError:
        pass
    if "--zip" in argv:
        zbytes = open(argv[argv.index("--zip") + 1], "rb").read()
        tag = "(zip)"
    else:
        tag = latest_tag()
        if "--check" in argv:
            print("installed %s, latest release %s" % (cur or "none", tag))
            return 0
        zbytes = release_zip(tag)
    import tempfile
    tmp = tempfile.mkdtemp(prefix="kitfetch-")
    try:
        new = extract(zbytes, tmp)
        if "--check" in argv:
            print("installed %s, zip has %s" % (cur or "none", new))
            return 0
        if cur and not kit_sync._newer(new, cur) and "--force" not in argv:
            print("Kit in your profile (%s) is already up to date with %s." % (cur, tag))
        else:
            n, backup = apply(tmp, home)
            print("Kit %s -> %s from %s: %d profile file(s) updated%s." % (cur or "none", new, tag, n, ("; old copies in " + backup) if n else ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    r = kit_sync.run(project)
    print("Project sync: %d updated, %d added." % (len(r.get("updated", [])), len(r.get("added", []))))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("kit-fetch failed: %s" % e)
        sys.exit(1)
