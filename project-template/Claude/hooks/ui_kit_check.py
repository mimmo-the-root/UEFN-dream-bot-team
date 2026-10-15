#!/usr/bin/env python3
"""Check that Epic's Verse UI Kit is installed in this project and that its AGENTS.md is a known version.

Read-only unless --accept is given. Prints one ASCII JSON line.

States (exit code):
  ok               0  kit and AGENTS.md are present and the AGENTS.md is a version this kit was written against
  package_missing  1  no VerseUIKit folder (optional: UI can be built without it; the free kit is on Fab)
  agents_missing   2  kit is there but its AGENTS.md is not (it is a separate download on the Fab page)
  agents_changed   3  AGENTS.md differs from every version reviewed so far: Epic changed it

Epic's AGENTS.md is never copied into the kit (Fab EULA). It lives once on your computer, for all
projects: ~/.claude/skills/verse-ui-kit/references/epic/AGENTS.md (a copy inside a project's
VerseUIKit folder is used first when present). Only its SHA-256 is compared, against
Claude/reference/ui-kit-reviewed-hashes.json (shipped) and epic/reviewed.json next to it (yours).

Usage: ui_kit_check.py [DIR | --project DIR] [--check]
       ui_kit_check.py --diff      what changed since the last version you accepted
       ui_kit_check.py --accept    remember the current AGENTS.md as reviewed (only after the owner agreed)
       ui_kit_check.py --store FILE  put Epic's AGENTS.md (your Fab download) in the one shared place
"""
import argparse, difflib, hashlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def norm_sha(path):
    b = open(path, "rb").read().lstrip(b"\xef\xbb\xbf").replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest(), b.decode("utf-8", "replace")


def find_kit(project):
    cands = [os.path.join(project, "VerseUIKit")]
    for d, dirs, files in os.walk(project):
        if os.path.basename(d) == "VerseUIKit":
            cands.append(d)
            dirs[:] = []
            continue
        if os.path.relpath(d, project).count(os.sep) >= 3:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if x not in ("Claude", ".claude", "__ExternalActors__", "__ExternalObjects__")]
    for c in cands:
        if os.path.isfile(os.path.join(c, "ui_modules.verse")) and os.path.isdir(os.path.join(c, "Widgets")):
            return c
    return None


def epic_dir():
    return os.environ.get("UEFN_KIT_EPIC_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills", "verse-ui-kit", "references", "epic")


def find_agents(project, kit):
    for p in (os.path.join(kit, "AGENTS.md"), os.path.join(project, "AGENTS.md"), os.path.join(epic_dir(), "AGENTS.md")):
        if os.path.isfile(p):
            return p
    return None


def load(path, key):
    try:
        return [x["sha256"] for x in json.load(open(path, encoding="utf-8-sig")).get(key, []) if "sha256" in x]
    except (OSError, ValueError, TypeError, AttributeError):
        return []


def local_paths():
    d = epic_dir()
    return d, os.path.join(d, "reviewed.json"), os.path.join(d, "accepted")


def result(state, code, message, **kw):
    out = dict(state=state, message=message, **kw)
    print(json.dumps(out, ensure_ascii=True))
    return code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="project folder (same as --project)")
    ap.add_argument("--project", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--diff", action="store_true")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--store", metavar="FILE")
    a = ap.parse_args()
    project = os.path.abspath(a.project or a.path or os.path.join(HERE, "..", ".."))
    if a.store:
        try:
            os.makedirs(epic_dir(), exist_ok=True)
            data = open(a.store, "rb").read()
            open(os.path.join(epic_dir(), "AGENTS.md"), "wb").write(data)
        except OSError as e:
            return result("not_saved", 4, "Could not store the file: %s" % e.__class__.__name__)
        return result("stored", 0, "Epic's AGENTS.md is now in the shared place for all projects.", agents_path=os.path.join(epic_dir(), "AGENTS.md"))
    kit = find_kit(project)
    if not kit:
        return result("package_missing", 1, "The Verse UI Kit is not in this project. It is optional: build the UI without it (verse-ui-kit skill, references/without-kit.md) and mention that the free kit on Fab (fn.gg/verse-ui-kit) can save time. Never block the task on it.")
    agents = find_agents(project, kit)
    if not agents:
        return result("agents_missing", 2, "The kit is installed but Epic's AGENTS.md is missing on this computer. It is a separate download on the kit's Fab page. Put it once in %s (or run this script with --store <file>); it then serves every project. Then run this check again." % epic_dir(), kit_root=kit)
    sha, text = norm_sha(agents)
    shipped = load(os.path.join(project, "Claude", "reference", "ui-kit-reviewed-hashes.json"), "reviewed")
    _, store, copies = local_paths()
    mine = load(store, "reviewed")
    known = sha in shipped or sha in mine
    base = dict(kit_root=kit, agents_path=agents, sha256=sha)
    if a.accept:
        try:
            os.makedirs(copies, exist_ok=True)
            data = {"reviewed": []}
            if os.path.isfile(store):
                data = json.load(open(store, encoding="utf-8-sig"))
            if sha not in mine:
                data["reviewed"].append({"sha256": sha, "date": time.strftime("%Y-%m-%d")})
                tmp = store + ".tmp"
                json.dump(data, open(tmp, "w", encoding="utf-8"), indent=1)
                os.replace(tmp, store)
            open(os.path.join(copies, "AGENTS-%s.md" % sha[:8]), "w", encoding="utf-8", newline="\n").write(text)
        except OSError as e:
            return result("not_saved", 4, "Could not record the version: %s" % e.__class__.__name__, **base)
        return result("ok", 0, "Remembered this AGENTS.md as reviewed (private copy kept next to the shared AGENTS.md, never published).", **base)
    if a.diff:
        old = sorted(os.path.join(copies, f) for f in os.listdir(copies)) if os.path.isdir(copies) else []
        old = [p for p in old if not os.path.basename(p).startswith("AGENTS-" + sha[:8])]
        if not old:
            return result("no_previous", 0, "No earlier accepted copy to compare with. The shipped list only holds fingerprints; compare with the original download by hand.", **base)
        prev = max(old, key=os.path.getmtime)
        before = open(prev, encoding="utf-8").read().splitlines()
        d = list(difflib.unified_diff(before, text.splitlines(), "accepted", "current", lineterm="", n=1))
        print("\n".join(d[:200]))
        return result("diff", 0, "%d changed lines against %s" % (len([x for x in d if x[:1] in "+-" and x[:3] not in ("+++", "---")]), os.path.basename(prev)), **base)
    if not known:
        return result("agents_changed", 3, "Epic's AGENTS.md is different from every version reviewed so far. Tell the owner and offer to analyze what changed (run with --diff if an earlier copy was accepted); do not change the verse-ui-kit skill without the owner's yes. After the review run --accept.", **base)
    return result("ok", 0, "Verse UI Kit and its AGENTS.md are present and match a reviewed version.", **base)


if __name__ == "__main__":
    sys.exit(main())
