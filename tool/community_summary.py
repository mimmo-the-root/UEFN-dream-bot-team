#!/usr/bin/env python3
"""community_summary.py - the data of the What's new console page, built at release time and shipped with the kit
(project-template/Claude/community/community-summary.json), so the page works offline.

build_summary(tag, intake, reputation, previous=None, release=None, statements=None, today=None) -> dict
  release    = {"title": str, "items": [str]} from the CHANGELOG entry of the tag
  statements = {pattern_id: canonical statement} (from the community packs)
  previous   = the summary of the last release (its "state" gives what was already there, for 'new', 'added' and deltas)"""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = 10


def build_summary(tag, intake, reputation, previous=None, release=None, statements=None, today=None):
    today = today or datetime.date.today().isoformat()
    prev = (previous or {}).get("state", {})
    prev_genres, prev_ids, prev_scores = set(prev.get("genres", [])), set(prev.get("lesson_ids", [])), prev.get("scores", {})
    statements = statements or {}
    lessons = (intake or {}).get("lessons", {})
    live = {pid: e for pid, e in lessons.items() if e.get("state") in ("hypothesis", "confirmed")}
    handles = (reputation or {}).get("handles", {})
    by_genre = {}
    for pid, e in sorted(live.items()):
        g = by_genre.setdefault(e["genre"], {"genre": e["genre"], "lessons": 0, "confirmed": 0, "hypotheses": 0, "added": 0, "handles": set(), "best": None})
        g["lessons"] += 1
        g["confirmed" if e["state"] == "confirmed" else "hypotheses"] += 1
        if pid not in prev_ids:
            g["added"] += 1
        g["handles"] |= set(e.get("handles", []))
        if g["best"] is None or len(e.get("handles", [])) > g["best"][0]:
            g["best"] = (len(e.get("handles", [])), pid)
    skills = []
    for g in sorted(by_genre.values(), key=lambda x: (-x["added"], x["genre"])):
        if g["added"] == 0:
            continue
        hl = statements.get(g["best"][1], "") if g["best"] else ""
        skills.append({"genre": g["genre"], "status": "improved" if g["genre"] in prev_genres else "new", "added": g["added"],
                       "confirmed": g["confirmed"], "hypotheses": g["hypotheses"], "handles": sorted(g["handles"]), "highlight": hl})
    top = sorted(handles.items(), key=lambda kv: (-kv[1]["score"], kv[0]))[:TOP]
    top = [{"handle": h, "score": r["score"], "confirmed": r["confirmed"], "genres": r["genres"], "delta": r["score"] - prev_scores.get(h, 0),
            "new": h not in prev_scores} for h, r in top]
    helpful = sorted(((len(e.get("handles", [])), pid) for pid, e in live.items() if len(e.get("handles", [])) >= 2), key=lambda x: (-x[0], x[1]))[:5]
    helpful = [{"id": pid, "text": statements.get(pid, ""), "genre": live[pid]["genre"], "handles": live[pid]["handles"], "confirmations": n} for n, pid in helpful]
    contributors = sorted(h for h, r in handles.items() if r.get("lessons", 0) > 0)
    return {
        "schema": 1,
        "release": {"tag": tag, "date": today, "title": (release or {}).get("title", tag), "items": (release or {}).get("items", [])},
        "counts": {"new_skills": sum(1 for s in skills if s["status"] == "new"), "improved_skills": sum(1 for s in skills if s["status"] == "improved"),
                   "received": len(lessons), "confirmed": sum(1 for e in lessons.values() if e.get("state") == "confirmed"),
                   "hypotheses": sum(1 for e in lessons.values() if e.get("state") in ("hypothesis", "screened")),
                   "archived": sum(1 for e in lessons.values() if e.get("state") == "archived"),
                   "added": sum(s["added"] for s in skills), "contributors": len(contributors),
                   "new_contributors": sum(1 for h in contributors if h not in prev_scores)},
        "skills": skills, "top": top, "helpful": helpful, "thanks": sorted(contributors, key=lambda h: (-handles[h]["score"], h)),
        "state": {"genres": sorted(by_genre), "lesson_ids": sorted(live), "scores": {h: r["score"] for h, r in handles.items()}},
    }


def _release_from_changelog(root, tag):
    try:
        with open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8") as f:
            log = f.read()
    except OSError:
        return {"title": tag, "items": []}
    m = re.search(r"(?ms)^## (" + re.escape(tag) + r"\b[^\r\n]*)\r?\n(.*?)(?=^## |\Z)", log)
    if not m:
        return {"title": tag, "items": []}
    items = [re.sub(r"^[-*]\s+", "", ln).strip() for ln in m.group(2).splitlines() if re.match(r"^[-*]\s+", ln)]
    return {"title": m.group(1).strip(), "items": [i.replace("**", "") for i in items][:8]}


def main():
    root = os.path.abspath(os.path.join(HERE, ".."))
    def rd(p, d):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return d
    out_path = os.path.join(root, "project-template", "Claude", "community", "community-summary.json")
    with open(os.path.join(root, "project-template", "Claude", "KIT-VERSION"), encoding="utf-8") as f:
        tag = "v" + f.read().strip()
    prev = rd(out_path, None)
    if prev and prev.get("release", {}).get("tag") == tag:
        prev = prev.get("previous_for_rebuild", prev)  # same tag rebuilt: keep the comparison with the PREVIOUS release
    statements = {}
    gbase = os.path.join(root, "user-level-skills", "genre")
    for g in os.listdir(gbase) if os.path.isdir(gbase) else []:
        for x in rd(os.path.join(gbase, g, "community", "community.json"), {}).get("patterns", []):
            statements[x.get("id")] = x.get("statement", "")
    res = build_summary(tag, rd(os.path.join(root, "contributions", "INTAKE.json"), {}), rd(os.path.join(root, "reputation.json"), {}),
                        prev, _release_from_changelog(root, tag), statements)
    if prev:
        res["previous_for_rebuild"] = {"state": prev.get("state", {}), "release": {"tag": prev.get("release", {}).get("tag")}}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1, sort_keys=True); f.write("\n")
    print("community summary for %s: %d skills, %d contributors" % (tag, len(res["skills"]), res["counts"]["contributors"]))


if __name__ == "__main__":
    main()
