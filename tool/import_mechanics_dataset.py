#!/usr/bin/env python3
"""import_mechanics_dataset.py - turns the edge cases, common bugs, balance notes and accessibility notes of an open game-mechanics dataset into
reference lessons for the genre skills (the kit's pack format, tier "reference").

  python tool/import_mechanics_dataset.py DATASET_DIR [--per-genre 10] [--write]

DATASET_DIR is the folder with data/<category>/<mechanic>.json (CC0 data: no credit is required). Without --write it only prints what it would write.
With --write it writes user-level-skills/genre/<genre>/official/official-reference-mechanics-<genre>.json for every genre of the kit that has a genre
skill folder. Selection is deterministic: engine-specific lines are dropped, only short lines that pass the kit's own pattern gate are kept, the mechanics
that are core to a genre come first, and no mechanic gives more than two lessons to one genre."""
import glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as S  # noqa: E402

GENRE_OF_DATASET = {"survival": ["survival"], "strategy": ["strategy"], "racing": ["sports-racing"], "simulation": ["simulation-tycoon"], "shooter": ["shooter"],
                    "rpg": ["adventure-rpg"], "adventure": ["adventure-rpg"], "roguelike": ["roguelike"], "platformer": ["deathrun-platformer"], "party": ["party-mini-games"],
                    "arcade": ["party-mini-games"], "sandbox": ["simulation-tycoon"], "open_world": ["adventure-rpg"], "escape_room": ["adventure-rpg"], "stealth": ["adventure-rpg"]}
GENRE_OF_CATEGORY = {"vehicles": ["sports-racing"], "economy": ["simulation-tycoon"], "crafting": ["simulation-tycoon", "survival"], "survival": ["survival"], "roguelike": ["roguelike"],
                     "platforming": ["deathrun-platformer"], "strategy": ["strategy"], "multiplayer": ["party-mini-games", "shooter"], "progression": ["adventure-rpg", "simulation-tycoon", "roguelike"],
                     "combat": ["shooter", "adventure-rpg"], "ai": ["shooter", "survival", "adventure-rpg"], "puzzle": ["adventure-rpg", "party-mini-games"], "movement": ["deathrun-platformer", "shooter"],
                     "traversal": ["deathrun-platformer", "adventure-rpg"], "narrative": ["adventure-rpg"], "ui_ux": ["*"], "accessibility": ["*"], "camera": ["*"]}
SECTION_OF_KIND = {"common_bugs": "pitfalls", "edge_cases": "pitfalls", "balancing_notes": "balance", "accessibility_notes": "launch-checklist"}
KIND_LABEL = {"common_bugs": "common bug", "edge_cases": "edge case", "balancing_notes": "balance note", "accessibility_notes": "accessibility note"}
KIND_ORDER = ["common_bugs", "edge_cases", "balancing_notes", "accessibility_notes"]
ENGINE = re.compile(r"\b(unity|godot|unreal|blueprint|montage|rigid ?body|shader|gpu|nanite|prefab|scriptable|monobehaviour|animator|animation event|navmesh|a\* ?cache|delta ?time|tick rate|frame ?rate|fixed (simulation )?step|fixed update|scene transition|scene load|lod|draw call|garbage|pooled|object pool|ecs|sprite|tilemap|canvas|framebuffer)\b", re.I)


def genres_of(m, ours):
    """{our genre: relevance}. 3 = the mechanic names this genre itself; 1 = only its category fits. Camera, interface and accessibility mechanics fit every genre
    a little (1) and a genre they name much more (3)."""
    g = {}
    for x in m.get("genres", []):
        for y in GENRE_OF_DATASET.get(x, []):
            g[y] = 3
    for x in GENRE_OF_CATEGORY.get(m.get("category"), []):
        for y in (ours if x == "*" else [x]):
            g.setdefault(y, 1)
    return {k: v for k, v in g.items() if k in ours}


def load(dataset):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(dataset, "data", "*", "*.json")))]


def candidates(m, rel):
    is_core = (m.get("scope_profile") or {}).get("mvp_role") == "core"
    core = (3 if is_core else 1) + rel
    out = []
    for kind in KIND_ORDER:
        for i, text in enumerate(m.get(kind) or []):
            t = " ".join(str(text).split()).rstrip()
            if len(t) < 50 or len(t) > 200 or ENGINE.search(t) or t.count(";") > 1 or re.search(r"\b[a-z]+_[a-z_]+\b", t):
                continue
            if rel < 3 and not (kind == "accessibility_notes" or is_core):
                continue   # a mechanic that does not name this genre is used only for accessibility, or when it is core to the game
            out.append({"mech": m["id"], "name": m["name"], "kind": kind, "text": t, "core": core, "i": i, "rel": rel})
    return out


def make_pattern(c):
    cond = "Adding or tuning %s" % c["name"].lower()
    if c["kind"] == "accessibility_notes":
        cond = "Making %s usable for every player" % c["name"].lower()
    p = {"variant": "*", "section": SECTION_OF_KIND[c["kind"]], "condition": cond[:140], "action": c["text"], "statement": ("%s: %s" % (c["name"], KIND_LABEL[c["kind"]]))[:200],
         "tier": "reference", "status": "active", "support": 0, "against": 0}
    p["id"] = S.pattern_id(p["variant"], p["condition"], p["action"])
    return p


def build(dataset, per_genre=10, ours=None):
    ours = ours or sorted(os.path.basename(os.path.dirname(f)) for f in glob.glob(os.path.join(ROOT, "user-level-skills", "genre", "*", "SKILL.md")))
    ours = [g for g in ours if g not in ("mechanics", "materials", "llm-npc-conversations")]
    mech = load(dataset)
    pool = {g: [] for g in ours}
    for m in mech:
        for g, rel in genres_of(m, ours).items():
            pool[g] += candidates(m, rel)
    out, used = {}, set()   # a lesson goes to one genre only: the genres with the fewest candidates choose first
    for g, cs in sorted(pool.items(), key=lambda kv: (len(kv[1]), kv[0])):
        per_mech, picked, seen = {}, [], set(used)
        quota = {"common_bugs": 4, "edge_cases": 3, "balancing_notes": 2, "accessibility_notes": 1}
        for kind in KIND_ORDER:
            for c in sorted([x for x in cs if x["kind"] == kind], key=lambda x: (-x["core"], x["mech"], x["i"])):
                if len([p for p in picked if p["kind"] == kind]) >= quota[kind] or per_mech.get(c["mech"], 0) >= 2:
                    continue
                p = make_pattern(c)
                if S.validate_pattern(p) or p["id"] in seen:
                    continue
                seen.add(p["id"]); per_mech[c["mech"]] = per_mech.get(c["mech"], 0) + 1
                picked.append(dict(p, kind=kind))
        picked = picked[:per_genre]
        used |= {p["id"] for p in picked}
        out[g] = [{k: v for k, v in p.items() if k != "kind"} for p in picked]
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        print(__doc__)
        return 2
    n = int(sys.argv[sys.argv.index("--per-genre") + 1]) if "--per-genre" in sys.argv else 10
    if "--per-genre" in sys.argv:
        a = [x for x in a if x != str(n)]
    res = build(a[0], n)
    for g, ps in res.items():
        print("%-20s %d lessons" % (g, len(ps)))
        if "--write" in sys.argv and ps:
            d = os.path.join(ROOT, "user-level-skills", "genre", g, "official")
            os.makedirs(d, exist_ok=True)
            json.dump({"schema": 1, "genre": g, "pack_version": 1, "patterns": ps}, open(os.path.join(d, "official-reference-mechanics-%s.json" % g), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
