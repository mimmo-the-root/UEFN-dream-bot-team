#!/usr/bin/env python3
"""reputation.py - the score of a creator is computed from outcomes, not from how many lessons were sent.

compute(intake, revoked=None) -> {"handles": {handle: {"score", "confirmed", "lessons", "genres", "strict"}}}
  +3  a lesson of the handle is confirmed (by another handle, or by the owner)
  +1  for each additional independent handle that sent the same pattern_id (given to the handles that were there first, once confirmed)
  -5  a lesson of the handle is revoked / refuted
   0  archived
A handle with score 0 is `strict`: its contributions get the stricter screening and a daily limit. No levels in v1."""
import json, os, sys

W_CONFIRMED, W_EXTRA, W_REVOKED = 3, 1, -5


def compute(intake, revoked=None):
    revoked = revoked or {}
    rev_ids, rev_handles = set(revoked.get("ids", [])), {h.lower() for h in revoked.get("handles", [])}
    out = {}

    def row(h):
        return out.setdefault(h, {"score": 0, "confirmed": 0, "lessons": 0, "genres": set(), "revoked": 0})

    for pid, e in sorted((intake.get("lessons") or {}).items()):
        hs = list(e.get("handles", []))
        for h in hs + list(e.get("blocked_handles", [])):
            row(h)["lessons"] += 1
        for h in hs:
            row(h)["genres"].add(e.get("genre", ""))
        if pid in rev_ids:
            for h in hs:
                r = row(h); r["score"] += W_REVOKED; r["revoked"] += 1
            continue
        if e.get("state") == "confirmed":
            for i, h in enumerate(hs):
                r = row(h); r["score"] += W_CONFIRMED; r["confirmed"] += 1
                # the extra independent confirmations count for everyone who sent the lesson
                r["score"] += W_EXTRA * (len(hs) - 1)
    for h in rev_handles:
        r = row(h)
        r["score"] += W_REVOKED * max(1, r["lessons"])
        r["revoked"] += 1
    res = {}
    for h, r in sorted(out.items()):
        res[h] = {"score": r["score"], "confirmed": r["confirmed"], "lessons": r["lessons"], "genres": sorted(g for g in r["genres"] if g),
                  "strict": r["score"] <= 0}
    return {"handles": res}


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    def rd(p, d):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return d
    intake = rd(os.path.join(root, "contributions", "INTAKE.json"), {})
    revoked = rd(os.path.join(root, "project-template", "Claude", "community-revoked.json"), {})
    out = compute(intake, revoked)
    with open(os.path.join(root, "reputation.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True); f.write("\n")
    print("%d handles" % len(out["handles"]))


if __name__ == "__main__":
    main()
