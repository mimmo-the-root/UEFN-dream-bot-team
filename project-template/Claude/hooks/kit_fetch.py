#!/usr/bin/env python3
"""kit_fetch.py - bring the kit in your profile (~/.claude) to the newest GitHub release, then sync this project.

Usage (from the project folder):  python Claude/hooks/kit_fetch.py [--check] [--zip FILE] [--force]
  --check   only print the installed and the latest version, change nothing
  --zip     use a release zip you already downloaded (offline / tests); default: download the latest release
  --force   apply even if the release is not newer
Updates: ~/.claude/kit-template, ~/.claude/agents, ~/.claude/skills (never local/ or pack/ folders), each replaced file
is first copied to ~/.claude/kit-backup/<timestamp>/. Then runs the normal project sync. Does not touch ~/.claude/CLAUDE.md.
Safety: HTTPS to api.github.com only, zip paths checked (no ../), size cap 60 MB, only three folders are read from the zip.
Env: UEFN_KIT_REPO (default mimmo-the-root/UEFN-dream-bot-team), UEFN_HOME (profile dir), UEFN_KIT_TEMPLATE.
"""
import io, json, os, re, shutil, sys, time, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_sync  # noqa: E402

REPO = os.environ.get("UEFN_KIT_REPO", "mimmo-the-root/UEFN-dream-bot-team")
CAP = 60 * 1024 * 1024
PARTS = {"project-template": "kit-template", "user-level-agents": "agents", "user-level-skills": "skills"}
SKIP_DIRS = {"local", "pack", "__pycache__"}  # skills' private/learned data and caches are never replaced


def _get(url):
    if not url.startswith("https://api.github.com/"):
        raise ValueError("refusing non-GitHub URL")
    req = urllib.request.Request(url, headers={"User-Agent": "uefn-kit-fetch", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(CAP + 1)
    if len(data) > CAP:
        raise ValueError("download larger than %d MB" % (CAP // 1048576))
    return data


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
    """Extract only the three kit folders, refusing unsafe paths. Returns the version found in the zip."""
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
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                changed += 1
    return changed, backup


def main():
    argv = sys.argv[1:]
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
        zbytes = _get("https://api.github.com/repos/%s/zipball/%s" % (REPO, tag))
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
