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
"""
import argparse, hashlib, json, os, re, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--profile", default=os.path.join(os.path.expanduser("~"), ".claude", "skills"))
ap.add_argument("--apply", action="store_true")
ap.add_argument("--all", action="store_true")
a = ap.parse_args()
os.environ["UEFN_SKILLS_DIR"] = a.profile
sys.path.insert(0, os.path.join(REPO, "project-template", "Claude", "hooks"))
import skills_lib as L

BLOCK = re.compile(r"<!-- PATTERNS:BEGIN -->.*?<!-- PATTERNS:END -->", re.S)
SKIP_FILES = ("usage.json", "ledger.jsonl", "maps.json", "support.json", "overlay.json", "merged.json")


def read(p):
    with open(p, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def h(b):
    return hashlib.sha256(b).hexdigest() if b is not None else None


def candidates(slug):
    src = os.path.join(a.profile, "genre", slug)
    dst = os.path.join(REPO, "user-level-skills", "genre", slug)
    out = []  # (relative path, new bytes)
    sk = os.path.join(src, "SKILL.md")
    if os.path.isfile(sk):
        t = BLOCK.sub("<!-- PATTERNS:BEGIN -->\n<!-- PATTERNS:END -->", read(sk).decode("utf-8"))
        out.append(("SKILL.md", t.encode("utf-8")))
    for sub in ("official", "references"):
        d = os.path.join(src, sub)
        for base, _, files in os.walk(d) if os.path.isdir(d) else []:
            for n in sorted(files):
                if n in SKIP_FILES:
                    continue
                p = os.path.join(base, n)
                out.append((os.path.relpath(p, src).replace(os.sep, "/"), read(p)))
    tmp = tempfile.mkdtemp()
    r = L.export_pack(slug, tmp)
    if r.get("ok") and r.get("patterns"):
        o = json.load(open(r["path"], encoding="utf-8"))
        o.pop("exported_at", None)
        out.append(("community/%s.json" % slug, (json.dumps(o, indent=2, ensure_ascii=False) + "\n").encode("utf-8")))
    elif not r.get("ok"):
        print("  [%s] community pack NOT exported: %s" % (slug, r.get("error")))
    return src, dst, out


def leaks(slug, data):
    try:
        deny = L._deny_terms(slug)
    except Exception:
        deny = ()
    txt = data.decode("utf-8", "replace")
    found = list(L.text_findings(txt[:100000], deny))
    return found


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
        lk = leaks(slug, data) if not rel.startswith("official/") else bad_pack(data)
        todo.append((slug, rel, cur, data, "new" if old is None else "changed", lk))

if not todo:
    print("Repo is up to date with your profile genre/technique skills.")
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
