#!/usr/bin/env python3
"""collect_recipes.py - put the recipes you approved on the Skills page ("Share in the kit") into the kit's official recipes.

Run by publish.ps1 on the maintainer's computer (and by hand: `python tool/collect_recipes.py [--dry]`).
Reads ~/.claude/skills/genre/<skill>/local/recipes.json (or $UEFN_SKILLS_DIR), takes only the recipes with share = approved, and merges
them by name into user-level-skills/genre/<skill>/official/recipes-official.json. Nothing else leaves your profile: the map keys, the
decision and the dates are dropped. A recipe whose text has a token, a personal path or an e-mail address is NOT collected (it is reported).
Then update-my-profile.cmd gives the official recipes to everybody who updates the kit.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import privacy_scan as PS   # same patterns as the repo scan


def skills_dir():
    return os.environ.get("UEFN_SKILLS_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills")


def findings(text):
    out = []
    for name, rx in PS.TOKEN_RES:
        if rx.search(text):
            out.append(name)
    for rx in PS.PATH_RES:
        for m in rx.finditer(text):
            if m.group(1).lower() not in PS.PATH_OK:
                out.append("personal path")
    for m in PS.EMAIL_RE.finditer(text):
        if m.group(0).split("@")[1].lower() not in PS.EMAIL_OK_DOMAINS:
            out.append("e-mail address")
    return sorted(set(out))


def collect(dry=False, skills=None, repo=None):
    skills, repo = skills or skills_dir(), repo or REPO
    added, updated, refused = [], [], []
    gdir = os.path.join(skills, "genre")
    if not os.path.isdir(gdir):
        return {"added": added, "updated": updated, "refused": refused, "note": "no skills folder on this computer: nothing collected"}
    for slug in sorted(os.listdir(gdir)):
        lp = os.path.join(gdir, slug, "local", "recipes.json")
        if not os.path.isfile(lp):
            continue
        try:
            with open(lp, encoding="utf-8") as f:
                local = json.load(f).get("recipes", [])
        except (OSError, ValueError):
            continue
        todo = [r for r in local if r.get("share") == "approved" and r.get("steps")]
        if not todo:
            continue
        op = os.path.join(repo, "user-level-skills", "genre", slug, "official", "recipes-official.json")
        if not os.path.isdir(os.path.dirname(op)):
            refused.append((slug, "", "the kit has no official folder for this skill"))
            continue
        try:
            with open(op, encoding="utf-8") as f:
                off = json.load(f)
        except (OSError, ValueError):
            off = {"schema": 1, "recipes": []}
        for r in todo:
            clean = {k: v for k, v in r.items() if k not in ("maps", "share", "share_at", "added", "fab", "tier", "origin")}
            clean["origin"] = "official"
            bad = findings(json.dumps(clean, ensure_ascii=False))
            if bad:
                refused.append((slug, r.get("name", ""), ", ".join(bad)))
                continue
            names = [x.get("name") for x in off["recipes"]]
            if clean["name"] in names:
                i = names.index(clean["name"])
                if off["recipes"][i] != clean:
                    off["recipes"][i] = clean
                    updated.append((slug, clean["name"]))
            else:
                off["recipes"].append(clean)
                added.append((slug, clean["name"]))
        if (added or updated) and not dry:
            with open(op, "w", encoding="utf-8") as f:
                json.dump(off, f, indent=1, ensure_ascii=False)
                f.write("\n")
    return {"added": added, "updated": updated, "refused": refused}


def curate_community(dry=False, repo=None):
    """Recipes the community proposed and YOU merged (a merged pull request is your approval) are shipped with the kit as
    user-level-skills/genre/<skill>/community/recipes-community.json; every user finds them in the inbox of the Skills page and approves them there.
    Each file is checked again; a recipe already official, or that fails, is left out. Returns (written, refused)."""
    import contrib_recipe as CR
    repo = repo or REPO
    root = os.path.join(repo, "contributions", "recipes")
    written, refused = [], []
    if not os.path.isdir(root):
        return written, refused
    for skill in sorted(os.listdir(root)):
        sd = os.path.join(root, skill)
        if skill not in CR.SKILLS or not os.path.isdir(sd):
            continue
        by = {}
        for rid in sorted(os.listdir(sd)):
            for fn in sorted(os.listdir(os.path.join(sd, rid))) if os.path.isdir(os.path.join(sd, rid)) else []:
                fp = os.path.join(sd, rid, fn)
                if not fn.endswith(".json") or os.path.islink(fp):
                    continue
                rel = "contributions/recipes/%s/%s/%s" % (skill, rid, fn)
                try:
                    with open(fp, encoding="utf-8") as f:
                        doc = json.load(f)
                except (OSError, ValueError):
                    refused.append((rel, "not readable")); continue
                e = CR.validate(doc, fn[:-5], rel)
                if e:
                    refused.append((rel, "; ".join(e[:2]))); continue
                by.setdefault(rid, []).append(doc["recipe"])
        off = []
        try:
            with open(os.path.join(repo, "user-level-skills", "genre", skill, "official", "recipes-official.json"), encoding="utf-8") as f:
                off = [x.get("name") for x in json.load(f).get("recipes", [])]
        except (OSError, ValueError):
            pass
        out = []
        for rid, recs in sorted(by.items()):
            if recs[0]["name"] in off:
                continue
            out.append(dict(recs[0], contributors=len(recs)))
        cd = os.path.join(repo, "user-level-skills", "genre", skill, "community")
        if out and not dry and os.path.isdir(os.path.dirname(cd)):
            os.makedirs(cd, exist_ok=True)
            with open(os.path.join(cd, "recipes-community.json"), "w", encoding="utf-8") as f:
                json.dump({"schema": 1, "recipes": out}, f, indent=1, ensure_ascii=False)
                f.write("\n")
        written += [(skill, x["name"]) for x in out]
    return written, refused


def main(argv):
    w, rf = curate_community(dry="--dry" in argv)
    for skill, name in w:
        print("community recipe shipped: %s / %s" % (skill, name))
    for rel, why in rf:
        print("COMMUNITY RECIPE REFUSED %s: %s" % (rel, why))
    r = collect(dry="--dry" in argv)
    if r.get("note"):
        print(r["note"])
    for slug, name in r["added"]:
        print("added   %s / %s" % (slug, name))
    for slug, name in r["updated"]:
        print("updated %s / %s" % (slug, name))
    for slug, name, why in r["refused"]:
        print("REFUSED %s / %s: %s" % (slug, name, why))
    if not (r["added"] or r["updated"] or r["refused"]):
        print("no recipe approved for sharing: nothing to collect")
    return 1 if (r["refused"] or rf) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
