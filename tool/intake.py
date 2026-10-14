#!/usr/bin/env python3
"""intake.py - the intake of community lessons. Nothing is ever deleted: a lesson only changes state.

States: new (just arrived, not yet looked at; never written here) -> screened (passed, waits for a human / the cap)
        -> hypothesis (published as "to verify", one source is enough) -> confirmed (2+ distinct handles, or the owner)
        ; archived (rejected, kept with the reason, never shown).

update_intake(contrib_root, intake_path, owner_decisions=None, revoked=None, now=None) -> intake dict (also written to intake_path)
`contrib_root` is the folder holding <genre>/<pattern_id>/<handle>.json (the repo's contributions/)."""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import contrib_schema as C  # noqa: E402
import screen_contribution as S  # noqa: E402

HYPOTHESIS_CAP_PER_GENRE = 40
CONFIRM_AT = 2


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, RecursionError):   # RecursionError: a deeply nested JSON must not stop the whole run
        return default


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _files(contrib_root):
    out = []
    for g in sorted(os.listdir(contrib_root)) if os.path.isdir(contrib_root) else []:
        gd = os.path.join(contrib_root, g)
        for pid in sorted(os.listdir(gd)) if os.path.isdir(gd) else []:
            pd = os.path.join(gd, pid)
            for fn in sorted(os.listdir(pd)) if os.path.isdir(pd) else []:
                if fn.endswith(".json") and os.path.isfile(os.path.join(pd, fn)) and not os.path.islink(os.path.join(pd, fn)):
                    out.append((g, pid, fn[:-5], os.path.join(pd, fn)))
    return out


def update_intake(contrib_root, intake_path, owner_decisions=None, revoked=None, now=None):
    now = now or _now()
    owner = owner_decisions or {}
    revoked = revoked or {}
    rev_ids, rev_handles = set(revoked.get("ids", [])), {h.lower() for h in revoked.get("handles", [])}
    prev = _read(intake_path, {}).get("lessons", {})
    lessons, rejected_files = {}, {}
    for genre, pid, handle, path in _files(contrib_root):
        rel = "contributions/%s/%s/%s.json" % (genre, pid, handle)
        doc = _read(path, None)
        errs = C.validate(doc, handle, rel)
        if errs:
            rejected_files[rel] = errs
            continue
        h = handle.lower()
        L = lessons.setdefault(doc["pattern_id"], {"genre": doc["genre"], "variant": doc["variant"], "sections": [],
                                                   "docs": {}, "blocked": {}})
        L["sections"].append(doc["section"])
        verdict = S.screen(doc)
        if h in rev_handles:
            L["blocked"][h] = ["handle is revoked"]
        elif verdict["verdict"] == "block":
            L["blocked"][h] = verdict["reasons"]
        else:
            L["docs"][h] = (doc, verdict)
    out = {}
    for pid in sorted(lessons):
        L = lessons[pid]
        handles = sorted(L["docs"])
        flagged = [r for h in handles for r in L["docs"][h][1]["reasons"]]
        verdict = "flag" if flagged else "pass"
        secs = sorted(L["sections"])
        section = max(sorted(set(secs)), key=lambda x: (secs.count(x), x)) if secs else ""   # the most common section wins, never the first sender's
        entry = {"genre": L["genre"], "variant": L["variant"], "section": section, "handles": handles,
                 "blocked_handles": sorted(L["blocked"]), "verdict": verdict, "reasons": sorted(set(flagged)),
                 "since": prev.get(pid, {}).get("since", now)}
        dec = owner.get(pid)
        if pid in rev_ids:
            entry.update(state="archived", reasons=["revoked"])
        elif dec == "archived":
            entry.update(state="archived", reasons=["archived by the owner"])
        elif not handles:
            entry.update(state="archived", reasons=sorted({r for rs in L["blocked"].values() for r in rs}) or ["no valid contribution"])
        elif dec == "confirmed" or (len(handles) >= CONFIRM_AT and verdict == "pass"):
            entry["state"] = "confirmed"   # two handles confirm only a clean lesson; a flagged one waits for the owner
        elif verdict == "pass":
            entry["state"] = "hypothesis"
        else:
            entry["state"] = "screened"
        out[pid] = entry
    # cap: the oldest hypotheses of a genre stay hypotheses, the rest wait as screened (kept, never deleted)
    for g in {e["genre"] for e in out.values()}:
        hyp = sorted((e["since"], pid) for pid, e in out.items() if e["genre"] == g and e["state"] == "hypothesis")
        for _, pid in hyp[HYPOTHESIS_CAP_PER_GENRE:]:
            out[pid]["state"] = "screened"
            out[pid]["reasons"] = sorted(set(out[pid]["reasons"]) | {"hypothesis cap reached"})
    result = {"schema": 1, "lessons": out, "rejected_files": dict(sorted(rejected_files.items()))}
    os.makedirs(os.path.dirname(os.path.abspath(intake_path)), exist_ok=True)
    with open(intake_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=1, sort_keys=True)
        f.write("\n")
    return result


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(HERE, ".."))
    contrib = os.path.join(root, "contributions")
    revoked = _read(os.path.join(root, "project-template", "Claude", "community-revoked.json"), {})
    decisions = _read(os.path.join(contrib, "decisions.json"), {})
    r = update_intake(contrib, os.path.join(contrib, "INTAKE.json"), decisions, revoked)
    from collections import Counter
    print(dict(Counter(e["state"] for e in r["lessons"].values())), "rejected files:", len(r["rejected_files"]))
