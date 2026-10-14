#!/usr/bin/env python3
"""curator.py - turns the intake into ONE promotion proposal for the owner (the owner validates; this never merges anything).

build_promotion(intake, contrib_root, existing=None, classify_fn=None, today=None)
  -> {"packs": {genre: pack}, "revoked": {...}, "report_md": str}
- the lesson text is REGENERATED from the verified fields in a fixed template ("When <condition>: <action>."): the contributor's own
  `statement` is never copied into a skill; the original stays in the intake only;
- a lesson classified "orders" is held back (listed in the report); "unchecked" is included and marked so the owner knows;
- every generated statement goes through the same screening as a contribution;
- packs use the format of skills_lib.merge_pack (schema 1, genre, pack_version, patterns), so a creator receives them as ONE proposal."""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import contrib_schema as C  # noqa: E402
import screen_contribution as S  # noqa: E402
import classify as K  # noqa: E402
L = C.L


def canonical_statement(condition, action):
    c, a = condition.strip().rstrip(".:;"), action.strip().rstrip(".")
    s = "When %s: %s." % (c[0].lower() + c[1:] if c else c, a[0].lower() + a[1:] if a else a)
    return s if len(s) <= L.MAX_STATEMENT else s[:L.MAX_STATEMENT - 1].rstrip() + "."


def _doc(contrib_root, genre, pid, handle):
    try:
        if os.path.islink(os.path.join(contrib_root, genre, pid, handle + ".json")):
            return None
        with open(os.path.join(contrib_root, genre, pid, handle + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, RecursionError):
        return None


def _md(t):
    """Contributor text in the PR body: inside a code span, so @mentions and #123 links never ping or link anything."""
    return "`" + str(t).replace("`", "'").replace("\n", " ") + "`"


def build_promotion(intake, contrib_root, existing=None, classify_fn=None, today=None):
    today = today or datetime.date.today().isoformat()
    classify_fn = classify_fn or K.classify
    existing = existing or {}
    packs, lines, held, dup = {}, [], [], 0
    for pid, e in sorted((intake.get("lessons") or {}).items()):
        if e.get("state") not in ("hypothesis", "confirmed") or not e.get("handles"):
            continue
        genre = e["genre"]
        if pid in existing.get(genre, set()):
            dup += 1
            continue
        doc = _doc(contrib_root, genre, pid, e["handles"][0])
        if not doc or C.validate(doc, e["handles"][0], "contributions/%s/%s/%s.json" % (genre, pid, e["handles"][0])):
            held.append((pid, "file missing or invalid"))
            continue
        verdict = classify_fn(" | ".join([doc["condition"], doc["action"], doc["statement"]]))
        if verdict == "orders":
            held.append((pid, "classifier: gives orders"))
            continue
        item = {"id": pid, "variant": doc["variant"], "condition": doc["condition"].strip(), "action": doc["action"].strip(),
                "statement": canonical_statement(doc["condition"], doc["action"]),
                "tier": "hypothesis", "status": "active", "support": len(e["handles"]), "section": e.get("section") or doc["section"]}
        again = S.screen({"statement": item["statement"], "condition": item["condition"], "action": item["action"]})
        if again["verdict"] == "block":
            held.append((pid, "generated text blocked: " + "; ".join(again["reasons"])))
            continue
        pack = packs.setdefault(genre, {"schema": 1, "genre": genre, "pack_version": int(today.replace("-", "")), "patterns": []})
        pack["patterns"].append(item)
        lines.append("- `%s` (%s / %s, %s, by %s) - screening: %s%s, classifier: %s\n  > %s" % (
            pid, genre, doc["variant"], e["state"], ", ".join(_md("@" + h) for h in e["handles"]), e["verdict"],
            " (" + _md("; ".join(e["reasons"])) + ")" if e["reasons"] else "", verdict, _md(item["statement"])))
    rep = ["# Promotion proposal %s" % today, "",
           "%d lessons in %d genre pack(s); %d already in the packs; %d held back. Nothing is merged without your approval." % (
               sum(len(p["patterns"]) for p in packs.values()), len(packs), dup, len(held)), ""]
    rep += lines or ["_No lesson to promote._"]
    if held:
        rep += ["", "## Held back"] + ["- `%s`: %s" % h for h in held]
    revoked = {"ids": sorted(p for p, e in (intake.get("lessons") or {}).items() if e.get("state") == "archived" and ("revoked" in e.get("reasons", []) or "handle is revoked" in e.get("reasons", []))), "handles": []}
    return {"packs": packs, "revoked": revoked, "report_md": "\n".join(rep) + "\n"}


def main():
    root = os.path.abspath(os.path.join(HERE, ".."))
    with open(os.path.join(root, "contributions", "INTAKE.json"), encoding="utf-8") as f:
        intake = json.load(f)
    existing = {}
    gbase = os.path.join(root, "user-level-skills", "genre")
    for g in os.listdir(gbase) if os.path.isdir(gbase) else []:
        p = os.path.join(gbase, g, "community", "community.json")
        try:
            with open(p, encoding="utf-8") as f:
                existing[g] = {x["id"] for x in json.load(f).get("patterns", [])}
        except (OSError, ValueError, KeyError):
            pass
    revpath = os.path.join(root, "project-template", "Claude", "community-revoked.json")
    try:
        with open(revpath, encoding="utf-8") as f:
            rev_file = json.load(f)
    except (OSError, ValueError):
        rev_file = {}
    res = build_promotion(intake, os.path.join(root, "contributions"), existing)
    rev_ids = sorted(set(rev_file.get("ids", [])) | set(res["revoked"]["ids"]))
    with open(revpath, "w", encoding="utf-8", newline="\n") as f:   # clients remove these ids; banned handles are expanded into ids by the intake
        json.dump({"ids": rev_ids, "handles": sorted(set(rev_file.get("handles", [])))}, f, indent=1); f.write("\n")
    for g, pack in res["packs"].items():
        d = os.path.join(gbase, g, "community"); os.makedirs(d, exist_ok=True)
        old = []
        try:
            with open(os.path.join(d, "community.json"), encoding="utf-8") as f:
                old = json.load(f).get("patterns", [])
        except (OSError, ValueError):
            pass
        pack["patterns"] = [x for x in old + pack["patterns"] if x.get("id") not in rev_ids]   # a revoked lesson never ships again
        with open(os.path.join(d, "community.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(pack, f, indent=1, sort_keys=True); f.write("\n")
    for g in gbase and os.listdir(gbase) or []:   # packs of genres with no new lesson are pruned too
        pth = os.path.join(gbase, g, "community", "community.json")
        if os.path.isfile(pth) and g not in res["packs"]:
            with open(pth, encoding="utf-8") as f:
                pk = json.load(f)
            keep = [x for x in pk.get("patterns", []) if x.get("id") not in rev_ids]
            if len(keep) != len(pk.get("patterns", [])):
                pk["patterns"] = keep
                with open(pth, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(pk, f, indent=1, sort_keys=True); f.write("\n")
    with open(os.path.join(root, "promotion-report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(res["report_md"])
    print(res["report_md"])


if __name__ == "__main__":
    main()
