"""The reference genre packs, the new mechanics recipes and the discipline skills: valid, consistent, and in the kit's own words."""
import glob, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as L

bad = []
G = os.path.join(ROOT, "user-level-skills", "genre")
official = {g["slug"] for g in json.load(open(os.path.join(G, "fortnite-genres-official.json"), encoding="utf-8"))["genres"]}
ids = {}
n_pat = 0
for f in sorted(glob.glob(os.path.join(G, "*", "official", "official-reference-*.json"))):
    slug = os.path.basename(os.path.dirname(os.path.dirname(f)))
    d = json.load(open(f, encoding="utf-8"))
    if d.get("genre") != slug or d.get("schema") != 1:
        bad.append("%s: genre or schema does not match its folder" % slug)
    if slug not in official:
        bad.append("%s: a reference pack needs a genre of the official Fortnite list" % slug)
    for p in d["patterns"]:
        n_pat += 1
        for fnd in L.validate_pattern(p):
            bad.append("%s %s: %s" % (slug, p.get("id"), fnd))
        if p.get("tier") != "reference":
            bad.append("%s %s: tier must be reference" % (slug, p.get("id")))
        if p["id"] in ids:
            bad.append("duplicate pattern id %s (%s and %s)" % (p["id"], ids[p["id"]], slug))
        ids[p["id"]] = slug
if n_pat < 75:
    bad.append("expected at least 75 reference patterns, found %d" % n_pat)
for slug in ("strategy", "shooter", "deathrun-platformer", "adventure-rpg", "simulation-tycoon"):
    if not os.path.isfile(os.path.join(G, slug, "SKILL.md")):
        bad.append("genre skill %s is missing" % slug)

rec = json.load(open(os.path.join(G, "mechanics", "official", "recipes-official.json"), encoding="utf-8"))["recipes"]
names = {r["name"] for r in rec}
for need in ("weighted loot box", "wave director", "currency and shop", "persistent levels", "hunger and needs", "ordered objectives", "course checkpoints"):
    if need not in names:
        bad.append("recipe %s is missing" % need)
for r in rec:
    for k in ("name", "use", "steps", "verify"):
        if not r.get(k):
            bad.append("recipe %s has no %s" % (r.get("name"), k))
    for fl in r.get("files", []):
        if fl["name"].endswith(".verse") and "Last modified" not in fl["code"] and r.get("origin") == "official" and r["name"] in ("weighted loot box", "wave director"):
            bad.append("recipe %s: Verse file without header" % r["name"])

S = os.path.join(ROOT, "user-level-skills")
for name in ("game-feel-uefn", "level-design-uefn", "camera-audio-uefn", "game-ai-uefn", "uefn-disciplines"):
    t = open(os.path.join(S, name, "SKILL.md"), encoding="utf-8").read()
    if "kind: discipline" not in t or "Use when" not in t or "When not to use" not in t:
        bad.append("%s: not a complete discipline skill" % name)

print(("PASS " if not bad else "FAIL ") + "reference packs (%d patterns), recipes and discipline skills" % n_pat + ("" if not bad else ": " + "; ".join(bad[:6])))
sys.exit(1 if bad else 0)
