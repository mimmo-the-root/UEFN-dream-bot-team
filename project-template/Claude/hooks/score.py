#!/usr/bin/env python3
"""Score page data: how far the project is against its own plan, release by release.

Reads ONLY the project's own documents (Claude/docs/ROADMAP.md, BUGS.md, RELEASE-READINESS.md, STATUS.md), so the
page updates by itself when tasks or bugs are closed. Nothing here is typed by hand.

Per criterion and release: T = plan (what the roadmap expects), B = built, V = proven (0-5 scale).
  value = min(5, 5 * weighted task count / depth)
  T counts planned tasks of releases <= k; B counts Done + 0.5 * In progress; V counts Done minus open-bug penalties.
Criteria: Claude/reference/score-criteria.json (+ approved extras in Claude/docs/score-criteria-extra.json).
Task -> criterion: keywords, or an explicit entry in Claude/docs/score-map.json ({"T-012": ["audio"]}).
Small agent adjustments (bounded +-1, with a reason): Claude/docs/score-notes.json ({"audio": {"adj": -0.5, "why": "..."}}).
CLI: score.py [project] [--json] [--snapshot]
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SEV = (("block", 1.0), ("crit", 1.0), ("major", 0.6), ("high", 0.6), ("med", 0.3), ("minor", 0.1), ("low", 0.1))
VERDICT = (("not ready", 1.5), ("ready with", 3.5), ("ready", 5.0))


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _tables(text):
    import docs_lint
    return [rows for _l, _h, rows in docs_lint.tables(text)]


def criteria(project):
    ref = os.path.join(project, "Claude", "reference", "score-criteria.json")
    if not os.path.isfile(ref):
        ref = os.path.join(os.path.dirname(HERE), "reference", "score-criteria.json")
    base = list(_json(ref, {}).get("criteria", []))
    extra = _json(os.path.join(project, "Claude", "docs", "score-criteria-extra.json"), [])
    ix = {c["id"]: i for i, c in enumerate(base)}
    for c in extra if isinstance(extra, list) else []:
        if isinstance(c, dict) and c.get("id") and c.get("n"):
            c.setdefault("g", "additional"); c.setdefault("w", 4); c.setdefault("kind", "tasks"); c.setdefault("depth", 3)
            if c["id"] in ix:
                base[ix[c["id"]]] = c
            else:
                base.append(c)
    return base


def _rel_key(code):
    m = re.fullmatch(r"P(\d+)-R(\d+)", code)
    return (int(m.group(1)), int(m.group(2))) if m else (-1, 0)


def tasks(project):
    t = _read(os.path.join(project, "Claude", "docs", "ROADMAP.md"))
    out = []
    for rows in _tables(t):
        if not any(re.match(r"^T-\d+", r.get("id", "")) for r in rows):
            continue
        for r in rows:
            tid = r.get("id", "")
            if not re.match(r"^T-\d+", tid):
                continue
            st = r.get("status", "").lower()
            if st.startswith("out of scope") or st.startswith("fuori scope"):
                continue
            rel = r.get("release", "").strip()
            if rel.lower() == "later":
                continue
            done = bool(re.match(r"^(done|fatto|complet|chiuso|closed|risolto|resolved)", st))
            prog = st.startswith("in progress")
            out.append({"id": tid, "text": (r.get("feature", "") + " " + r.get("acceptance criteria", "")).lower(),
                        "title": r.get("feature", "")[:80], "rel": rel if re.fullmatch(r"P\d+-R\d+", rel) else "Earlier",
                        "done": done, "prog": prog})
        break
    return out


def bugs(project):
    t = _read(os.path.join(project, "Claude", "docs", "BUGS.md"))
    out = []
    for rows in _tables(t):
        for r in rows:
            title = r.get("title", "") or r.get("id", "")
            m = re.match(r"B-\d+", title)
            if not m:
                continue
            if not re.match(r"^(open|in progress)", r.get("status", "").lower()):
                continue
            sev = r.get("severity", "").lower()
            pen = next((p for k, p in SEV if sev.startswith(k)), 0.3)
            linked = re.findall(r"T-\d+", " ".join(r.values()))
            out.append({"id": m.group(0), "pen": pen, "tasks": linked, "title": title[:70]})
    return out


def verdict(project):
    t = _read(os.path.join(project, "Claude", "docs", "RELEASE-READINESS.md"))
    for m in re.finditer(r"^##\s.*?verdict:\s*([^\n]*)", t, re.I | re.M):
        v = m.group(1).lower()
        if "example" in m.group(0).lower() or "replace" in m.group(0).lower():
            continue
        for k, val in VERDICT:
            if v.strip("*( ").startswith(k):
                return val, m.group(1).strip()
    return None, ""


def _docs_value(project):
    try:
        import docs_lint
        n = len(docs_lint.lint(project))
    except Exception:
        n = 0
    v = max(0.0, 5.0 - 0.5 * n)
    st = os.path.join(project, "Claude", "docs", "STATUS.md")
    why = "%d format problem(s)" % n
    if not os.path.isfile(st):
        v = min(v, 2.0); why += ", no STATUS.md"
    elif time.time() - os.path.getmtime(st) > 14 * 86400:
        v = max(0.0, v - 1.5); why += ", STATUS.md older than 14 days"
    return v, why


def _val(w, depth):
    return max(0.0, min(5.0, 5.0 * w / float(depth or 3)))


def _hist(project):
    out = {}
    for line in _read(os.path.join(project, "Claude", "logs", "score-history.jsonl")).splitlines():
        try:
            d = json.loads(line)
            out[d["release"]] = d["rows"]
        except (ValueError, KeyError):
            continue
    return out


def compute(project):
    cs = criteria(project)
    ts = tasks(project)
    if not ts or not cs:
        return {"available": False, "reason": "Not started: the score needs a plan. Run /spec for the idea, then /piano for the tasks: every criterion starts at 0 and fills in as the work is done."}
    rels = sorted({t["rel"] for t in ts}, key=_rel_key)
    cur = next((i for i, r in enumerate(rels) if any(not t["done"] for t in ts if t["rel"] == r)), len(rels) - 1)
    ix = {r: i for i, r in enumerate(rels)}
    tmap = _json(os.path.join(project, "Claude", "docs", "score-map.json"), {})
    notes = _json(os.path.join(project, "Claude", "docs", "score-notes.json"), {})
    bs = bugs(project)
    hist = _hist(project)
    ver, ver_txt = verdict(project)
    dval, dwhy = _docs_value(project)
    # state: planned count the first time we measured (for scope)
    sp = os.path.join(project, "Claude", "logs", "score-state.json")
    st = _json(sp, {})
    if "planned" not in st:
        st = {"planned": len(ts), "first_seen": time.strftime("%Y-%m-%d")}
        try:
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            with open(sp, "w", encoding="utf-8") as f:
                json.dump(st, f)
        except OSError:
            pass
    # task -> criteria
    mapped, unmapped = {}, []
    tc = [c for c in cs if c.get("kind") in ("tasks", "ship")]
    for t in ts:
        if t["id"] in tmap:
            ids = [i for i in tmap[t["id"]] if any(c["id"] == i for c in cs)]
        else:
            ids = [c["id"] for c in tc if any(re.search(r"\b" + re.escape(k.strip()), t["text"]) for k in c.get("keywords", []))]
        mapped[t["id"]] = ids
        if not ids:
            unmapped.append({"id": t["id"], "title": t["title"]})
    n = len(rels)
    # nothing done and nothing in progress yet = not started: criteria that start with free points (feasibility, scope, docs) stay at 0
    started = any(t["done"] or t["prog"] for t in ts)
    out_c = []
    open_pen = sum(b["pen"] for b in bs)
    for c in cs:
        kind, d = c.get("kind", "tasks"), c.get("depth", 3)
        mine = [t for t in ts if c["id"] in mapped[t["id"]]]
        T, B, V, ev = [], [], [], []
        pen = sum(b["pen"] for b in bs if any(x in [t["id"] for t in mine] for x in b["tasks"]))
        adj = max(-1.0, min(1.0, float((notes.get(c["id"]) or {}).get("adj", 0))))
        for k in range(n):
            upto = [t for t in mine if ix[t["rel"]] <= k]
            T.append(round(_val(len(upto), d), 2))
            B.append(round(_val(sum(1 for t in upto if t["done"]) + 0.5 * sum(1 for t in upto if t["prog"] and not t["done"]), d), 2))
            v = _val(sum(1 for t in upto if t["done"]), d)
            if k == cur:
                v = v - pen + adj
            V.append(round(max(0.0, min(5.0, v)), 2))
        if kind == "feasibility":
            for k in range(n):
                T[k] = 4.0
            cv = max(0.0, 4.5 - open_pen)
            B = [round(min(4.5, 4.5 - 0.5 * open_pen), 2) if k == cur else 0.0 for k in range(n)]
            V = [round(cv, 2) if k == cur else 0.0 for k in range(n)]
            ev.append("%d open bug(s), penalty %.1f" % (len(bs), open_pen) if started else "not started: nothing built or checked yet")
            if not started:
                B = [0.0] * n; V = [0.0] * n
        elif kind == "scope":
            first, now = max(1, st.get("planned", len(ts))), len(ts)
            cv = 5.0 if now <= first else round(5.0 * first / now, 2)
            T, B, V = [5.0] * n, [cv] * n, [cv] * n
            ev.append("planned %d task(s) when first measured, %d now" % (first, now) if started else "not started: it is measured once work begins")
            if not started:
                B = [0.0] * n; V = [0.0] * n
        elif kind == "ship":
            tv = _val(sum(1 for t in mine if t["done"]), d)
            cv = ver if ver is not None else tv
            if ver is not None and mine:
                cv = (ver + tv) / 2.0
            T = [round(5.0 * (k + 1) / n, 2) for k in range(n)]
            B = [round(cv, 2) if k == cur else 0.0 for k in range(n)]
            V = list(B)
            ev.append("readiness verdict: %s" % (ver_txt or "none yet"))
        elif kind == "docs":
            T = [5.0] * n
            B = [round(dval, 2) if k == cur else 0.0 for k in range(n)]
            V = list(B)
            ev.append(dwhy if started else "not started: it is measured once work begins")
            if not started:
                B = [0.0] * n; V = [0.0] * n
        if kind != "tasks":
            ev.extend("%s %s" % (t["id"], "done" if t["done"] else "open") for t in mine[:4])
        else:
            ev.append("%d/%d mapped task(s) done" % (sum(1 for t in mine if t["done"]), len(mine)) if mine else "no task planned for this criterion")
            if pen:
                ev.append("open bugs linked: penalty %.1f" % pen)
        if adj:
            ev.append("agent note %+.1f: %s" % (adj, (notes.get(c["id"]) or {}).get("why", "")))
        # past releases: use the saved snapshot when there is one; unknown past values of live criteria copy the current one
        for k in range(cur):
            h = (hist.get(rels[k]) or {}).get(c["id"])
            if h:
                B[k], V[k] = h.get("B", B[k]), h.get("V", V[k])
            elif kind in ("scope", "ship", "docs", "feasibility"):
                B[k], V[k] = B[cur], V[cur]
        out_c.append({"id": c["id"], "n": c["n"], "g": c.get("g", "additional"), "w": c.get("w", 0), "T": T,
                      "B": B[:cur + 1], "V": V[:cur + 1], "tip": c.get("tip", ""), "ev": ev})
    return {"available": True, "releases": rels, "last": cur, "criteria": out_c, "unmapped": unmapped,
            "open_bugs": len(bs), "generated": time.strftime("%Y-%m-%d %H:%M")}


def snapshot(project):
    """Append one history row per CLOSED release (all its tasks Done) that has none yet. Called after ROADMAP/BUGS edits."""
    d = compute(project)
    if not d.get("available"):
        return 0
    ts = tasks(project)
    hp = os.path.join(project, "Claude", "logs", "score-history.jsonl")
    have = set(_hist(project))
    added = 0
    for k, r in enumerate(d["releases"]):
        if r in have or not all(t["done"] for t in ts if t["rel"] == r) or k > d["last"]:
            continue
        rows = {c["id"]: {"T": c["T"][k], "B": c["B"][k], "V": c["V"][k]} for c in d["criteria"] if k < len(c["V"])}
        os.makedirs(os.path.dirname(hp), exist_ok=True)
        with open(hp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "release": r, "rows": rows}) + "\n")
        added += 1
    return added


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    proj = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--snapshot" in sys.argv:
        print("snapshots added: %d" % snapshot(proj))
    else:
        print(json.dumps(compute(proj), indent=1 if "--json" not in sys.argv else None))
