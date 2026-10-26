#!/usr/bin/env python3
"""Promote updated genre/technique skills from YOUR profile to the kit repo (personal tool, not shipped).

Dry-run by default. Never copies local/ (map names, task ids, notes), usage or ledger files.
What can be promoted, always after a privacy scan:
  - official/*.json   official reference packs (Epic-derived, in our own words)
  - references/*      reference notes
  - SKILL.md          with the generated PATTERNS block emptied (it is regenerated on each machine)
  - community pack    your approved patterns, via skills_lib export (runs its privacy check), written to
                      genre/<slug>/community/<slug>.json (optional file users can drop into local/incoming)
Nothing is committed: you review `git status` and commit yourself.

  py -3 tool\\promote-genre-skills.py            # report only
  py -3 tool\\promote-genre-skills.py --apply    # ask per file
  py -3 tool\\promote-genre-skills.py --apply --all
  py -3 tool\\promote-genre-skills.py --apply --all --community-only   # only your approved lessons (publish.ps1 runs this by itself)
"""
import argparse, hashlib, json, os, re, sys, tempfile

REPO = os.environ.get("UEFN_KIT_REPO") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--profile", default=os.path.join(os.path.expanduser("~"), ".claude", "skills"))
ap.add_argument("--apply", action="store_true")
ap.add_argument("--all", action="store_true")
ap.add_argument("--auto", action="store_true", help="what publish.ps1 runs: a skill already in the kit gets only its lessons pack; a NEW skill with something to ship goes in whole")
ap.add_argument("--community-only", action="store_true", help="only the lessons pack (what publish.ps1 runs by itself)")
a = ap.parse_args()
os.environ["UEFN_SKILLS_DIR"] = a.profile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "project-template", "Claude", "hooks"))   # the code is always this checkout; UEFN_KIT_REPO only moves where the packs are written
import skills_lib as L

HOLD = L.load_hold()
try:   # this tool only exists on the maintainer's computer: mark the profile so the Skills page shows the release boxes
    if not L.is_maintainer():
        open(os.path.join(a.profile, "maintainer.json"), "w").write('{"maintainer": true}\n')
except OSError:
    pass
BLOCK = re.compile(r"<!-- PATTERNS:BEGIN -->.*?<!-- PATTERNS:END -->", re.S)
SKIP_FILES = ("usage.json", "ledger.jsonl", "maps.json", "support.json", "overlay.json", "merged.json")


def read(p):
    with open(p, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def h(b):
    return hashlib.sha256(b).hexdigest() if b is not None else None


def candidates(slug):
    if slug in HOLD["skills"]:
        return os.path.join(a.profile, "genre", slug), os.path.join(REPO, "user-level-skills", "genre", slug), []   # kept out by the owner (Skills page, 'Release' box)
    src = os.path.join(a.profile, "genre", slug)
    dst = os.path.join(REPO, "user-level-skills", "genre", slug)
    out = []  # (relative path, new bytes)
    new_skill = a.auto and not os.path.isfile(os.path.join(dst, "SKILL.md"))
    only_pack = a.community_only or (a.auto and not new_skill)
    sk = os.path.join(src, "SKILL.md")
    if os.path.isfile(sk) and not only_pack:
        t = BLOCK.sub("<!-- PATTERNS:BEGIN -->\n<!-- PATTERNS:END -->", read(sk).decode("utf-8"))
        out.append(("SKILL.md", t.encode("utf-8")))
    for sub in (() if only_pack else ("official", "references")):
        d = os.path.join(src, sub)
        for base, _, files in os.walk(d) if os.path.isdir(d) else []:
            for n in sorted(files):
                if n in SKIP_FILES:
                    continue
                p = os.path.join(base, n)
                out.append((os.path.relpath(p, src).replace(os.sep, "/"), read(p)))
    tmp = tempfile.mkdtemp()
    r = L.export_pack(slug, tmp, skip=HOLD["lessons"])
    if r.get("ok") and r.get("patterns"):
        o = json.load(open(r["path"], encoding="utf-8"))
        o.pop("exported_at", None)
        out.append(("community/%s.json" % slug, (json.dumps(o, indent=2, ensure_ascii=False) + "\n").encode("utf-8")))
    elif not r.get("ok"):
        print("  [%s] community pack NOT exported: %s" % (slug, r.get("error")))
    if new_skill and not any(rel.startswith(("community/", "official/")) for rel, _ in out):
        out = []   # a new skill with no lessons of yours and no official pack has nothing to ship yet (the starter note every skill gets is not enough)
    return src, dst, out


def leaks(slug, data, document=False):
    try:
        deny = L._deny_terms(slug)
    except Exception:
        deny = ()
    txt = data.decode("utf-8", "replace")
    if document:   # SKILL.md and reference notes are markdown by nature: only secrets, personal paths and your private terms count (a lesson pack also refuses code and markup)
        found = [n for n, rx in L._SECRET_RULES if rx.search(txt[:100000])]
        low = txt.lower()
        if any(len((x or "").strip()) >= 3 and (x or "").strip().lower() in low for x in deny):
            found.append("private_term")
        return found
    return list(L.text_findings(txt[:100000], deny))


def bad_pack(data):
    try:
        o = json.loads(data.decode("utf-8"))
        return [("%s" % pt.get("id"), f) for pt in o.get("patterns", []) for f in L.validate_pattern(pt)]
    except Exception as e:
        return ["not valid JSON: %s" % e]


groot = os.path.join(a.profile, "genre")
slugs = sorted(d for d in (os.listdir(groot) if os.path.isdir(groot) else []) if os.path.isdir(os.path.join(groot, d)))
todo = []
for slug in slugs:
    src, dst, items = candidates(slug)
    for rel, data in items:
        cur = os.path.join(dst, *rel.split("/"))
        old = read(cur) if os.path.isfile(cur) else None
        if h(old) == h(data):
            continue
        lk = bad_pack(data) if rel.startswith("official/") else leaks(slug, data, document=not rel.startswith("community/"))
        todo.append((slug, rel, cur, data, "new" if old is None else "changed", lk))

def write_kit_skills():
    """Claude/community/kit-skills.json: the skills that ship with the kit, so the Skills page can tell which of yours are new."""
    g = os.path.join(REPO, "user-level-skills", "genre")
    names = sorted(d for d in (os.listdir(g) if os.path.isdir(g) else []) if os.path.isfile(os.path.join(g, d, "SKILL.md")))
    path = os.path.join(REPO, "project-template", "Claude", "community", "kit-skills.json")
    text = json.dumps({"skills": names}, indent=2) + "\n"
    if not os.path.isfile(path) or open(path, encoding="utf-8").read() != text:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("kit-skills.json: %d skill(s) ship with the kit" % len(names))


if not todo:
    print("Repo is up to date with your profile genre/technique skills.")
    if a.apply:
        write_kit_skills()
    sys.exit(0)
print("%d file(s) differ from the repo:" % len(todo))
for slug, rel, cur, data, kind, lk in todo:
    print("  %-8s %s/%s%s" % (kind, slug, rel, "   BLOCKED: " + ", ".join(map(str, lk[:3])) if lk else ""))
if not a.apply:
    print("\nReport only. Run again with --apply to promote (asks per file; --all to skip the questions).")
    sys.exit(0)
n = 0
for slug, rel, cur, data, kind, lk in todo:
    if lk:
        print("skip (privacy findings): %s/%s" % (slug, rel))
        continue
    if not a.all and input("Promote %s/%s [%s]? (y/N) " % (slug, rel, kind)).strip().lower() != "y":
        continue
    os.makedirs(os.path.dirname(cur), exist_ok=True)
    with open(cur, "wb") as f:
        f.write(data)
    n += 1
print("Promoted %d file(s). Review with git status / git diff, then commit." % n)
write_kit_skills()
