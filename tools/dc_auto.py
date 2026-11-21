#!/usr/bin/env python3
"""Director's Cut auto mode (T-028): one deterministic pass, no model.

Usage: python tools/dc_auto.py LAB [--timestamp STAMP] [--max-rows N]

LAB is the Claude folder of a lab (plan/, scratch/, docs/, hooks/); its parent is
accepted too. Reads plan/analysis-rows.json, scratch/T-028-proposal.md and
plan/intake/*, builds at most five rows with tools/dc_rows.py, drops duplicates
and owner-only items, requires tools/auditor.py approval, then copies the
roadmap to a .bak-DC-<timestamp>, appends the rows and records the undo in
plan/DC-LOG.md. The PM step uses pm_routine.py (cap 3) and writes plan/QUEUE.json
only through pm_queue.py.
"""
import argparse
import datetime
import fnmatch
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auditor  # noqa: E402
import dc_rows  # noqa: E402
import plan_json  # noqa: E402
import pm_queue  # noqa: E402
import pm_routine  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAX_NEW_ROWS = 5
MAX_OPEN_PER_RELEASE = 8
SOURCE = "Director's Cut T-028 auto"
OWNER_IDS = {"T-027", "T-044", "T-046", "T-070", "T-071", "T-117"}
OWNER_TEXT = (
    r"\[owner\b", r"owner[- ]?only",
    r"owner (?:confirms|decides|runs|approves|signs|pays|pushes|publishes)",
    r"\bpay(?:ing|ment|ments|s)?\b", r"\bbilling\b",
    r"\b(?:git )?push(?:ing|ed)?\b", r"\bpublish(?:ing|ed|es)?\b",
    r"version bump", r"bump (?:the )?version",
    r"\b(?:start|schedule) (?:the )?(?:scheduler|cron|scheduled task)\b",
)
OWNER_RE = re.compile("|".join(OWNER_TEXT), re.I)
DEPENDENCY_RE = re.compile(r"T-\d+", re.I)
HYBRID_RE = re.compile(r"suite green|tests? (?:pass|green)|no live llm|fake", re.I)
DONE_RE = re.compile(r"^(done|out of scope|closed|fixed|resolved|fatto|fuori scope|chiuso|complet\w*)\b", re.I)


def lab_paths(lab):
    lab = os.path.abspath(lab)
    kb = lab
    if not os.path.isdir(os.path.join(kb, "plan")) and os.path.isdir(os.path.join(lab, "Claude", "plan")):
        kb = os.path.join(lab, "Claude")
    project = os.path.dirname(kb) if os.path.basename(kb).lower() == "claude" else kb
    return {"lab": lab, "kb": kb, "project": project,
            "roadmap": os.path.join(kb, "docs", "ROADMAP.md"),
            "queue": os.path.join(kb, "plan", "QUEUE.json"),
            "log": os.path.join(kb, "plan", "DC-LOG.md")}


def read_context(kb):
    analysis = []
    ap = os.path.join(kb, "plan", "analysis-rows.json")
    if os.path.isfile(ap):
        with open(ap, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            analysis = data
    with open(os.path.join(kb, "scratch", "T-028-proposal.md"), encoding="utf-8") as f:
        proposal = f.read()
    intake = {}
    d = os.path.join(kb, "plan", "intake")
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.isfile(p) and name.lower().endswith(".md"):
                with open(p, encoding="utf-8", errors="replace") as f:
                    intake[name] = f.read()
    return {"analysis": analysis, "proposal": proposal, "intake": intake}


def intake_coverage(proposal, names):
    cov = {}
    for i, line in enumerate(proposal.splitlines()):
        if not line.lstrip().startswith("|"):
            continue
        head = [c.lower() for c in dc_rows.split_row(line)]
        if "source file" not in head or "id" not in head:
            continue
        si, ii = head.index("source file"), head.index("id")
        for row in proposal.splitlines()[i + 1:]:
            if not row.lstrip().startswith("|"):
                break
            cells = dc_rows.split_row(row)
            if len(cells) <= max(si, ii):
                continue
            pats = [os.path.basename(p.strip()) for p in re.split(r"[;,]", cells[si]) if p.strip()]
            cov[cells[ii]] = sum(1 for n in names if any(fnmatch.fnmatchcase(n, p) for p in pats))
        break
    return cov


def task_rows(text):
    rows = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8 and re.fullmatch(r"T-\d+", cells[0]):
            rows.append(cells)
    return rows


def open_releases(text):
    counts = {}
    for cells in task_rows(text):
        if DONE_RE.match(cells[2]) or not cells[5]:
            continue
        counts[cells[5]] = counts.get(cells[5], 0) + 1
    return counts


def owner_reason(tid, text):
    if tid in OWNER_IDS:
        return "owner-only id " + tid
    m = OWNER_RE.search(text)
    return "owner-only text " + m.group(0) if m else ""


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def build_candidates(ctx, roadmap_text, limit):
    items = dc_rows.parse(ctx["proposal"])
    rows = dc_rows.format_rows(items, SOURCE)
    current = task_rows(roadmap_text)
    used_ids = {c[0] for c in current}
    used_features = {normalize(c[1]) for c in current}
    candidates, dropped = [], []
    for item, row in zip(items, rows):
        tid = item["id"]
        if tid in used_ids:
            dropped.append((tid, "duplicate id"))
            continue
        feat = normalize(item["feature"])
        if feat in used_features:
            dropped.append((tid, "duplicate feature"))
            continue
        text = " ".join((item["feature"], item["acceptance criteria"]))
        reason = owner_reason(tid, text)
        if reason:
            dropped.append((tid, reason))
            continue
        used_ids.add(tid)
        used_features.add(feat)
        if len(candidates) < limit:
            candidates.append({"id": tid, "feature": item["feature"],
                               "acceptance": item["acceptance criteria"],
                               "priority": item["priority"], "release": item["release"],
                               "row": row, "index": len(candidates)})
        else:
            dropped.append((tid, "cap %d" % MAX_NEW_ROWS))
    return candidates, dropped


def audit_batch(candidates):
    plan = {"source": "dc_auto", "count": len(candidates),
            "items": [{"id": c["id"], "title": c["feature"], "status": "To do - Later",
                       "command": c["acceptance"], "priority": c["priority"],
                       "release": c["release"]} for c in candidates]}
    queue = pm_queue.build_queue(plan)
    return auditor.audit(plan, queue)


def release_key(name):
    m = re.search(r"R(\d+)", str(name))
    return (int(m.group(1)) if m else 10 ** 6, str(name))


def replace_release(row, release):
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    cells[5] = release
    return "| " + " | ".join(cells) + " |"


def rebalance(candidates, roadmap_text):
    counts = open_releases(roadmap_text)
    known = sorted(set(list(counts) + [c["release"] for c in candidates]), key=release_key)
    order = sorted(candidates, key=lambda c: (
        0 if DEPENDENCY_RE.search(c["feature"] + " " + c["acceptance"]) else 1 if HYBRID_RE.search(c["acceptance"]) else 2,
        c["index"]))
    notes = []
    for c in order:
        if counts.get(c["release"], 0) >= MAX_OPEN_PER_RELEASE:
            text = c["feature"] + " " + c["acceptance"]
            deps = [d.upper() for d in DEPENDENCY_RE.findall(text) if d.upper() != c["id"]]
            dep_rels = [next((o["release"] for o in candidates if o["id"] == d), "")
                        for d in deps]
            pool = [r for r in dep_rels if r and counts.get(r, 0) < MAX_OPEN_PER_RELEASE]
            if not pool:
                pool = [r for r in known if counts.get(r, 0) < MAX_OPEN_PER_RELEASE]
            target = pool[0] if pool else "Later"
            if target != c["release"]:
                notes.append("%s: Release %s -> %s (max %d open per release)" % (
                    c["id"], c["release"], target, MAX_OPEN_PER_RELEASE))
                c["release"] = target
                c["row"] = replace_release(c["row"], target)
        counts[c["release"]] = counts.get(c["release"], 0) + 1
    return notes


def append_rows(path, rows):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    eol = "\r\n" if "\r\n" in text else "\n"
    parts = text.split(eol)
    at = None
    for i, line in enumerate(parts):
        if re.match(r"^\|\s*ID\s*\|", line, re.I):
            at = i
            while at < len(parts) and parts[at].lstrip().startswith("|"):
                at += 1
            break
    if at is None:
        at = len(parts)
        while at > 0 and not parts[at - 1].strip():
            at -= 1
    parts[at:at] = list(rows)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(parts))
    return eol


def backup_roadmap(path, stamp):
    dst = path + ".bak-DC-" + stamp
    n = 2
    while os.path.exists(dst):
        dst = path + ".bak-DC-" + stamp + "-" + str(n)
        n += 1
    shutil.copyfile(path, dst)
    return dst


def load_docs_lint(kb):
    paths = (os.path.join(kb, "hooks", "docs_lint.py"),
             os.path.join(ROOT, "project-template", "Claude", "hooks", "docs_lint.py"))
    path = next((p for p in paths if os.path.isfile(p)), "")
    if not path:
        raise ValueError("docs_lint.py not found")
    spec = importlib.util.spec_from_file_location("dc_docs_lint", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def docs_check(kb, project, roadmap_path):
    mod = load_docs_lint(kb)
    check_dir, shim = project, ""
    if not os.path.isfile(os.path.join(check_dir, "Claude", "docs", "ROADMAP.md")):
        shim = tempfile.mkdtemp()
        os.makedirs(os.path.join(shim, "Claude", "docs"))
        shutil.copyfile(roadmap_path, os.path.join(shim, "Claude", "docs", "ROADMAP.md"))
        check_dir = shim
    try:
        return mod.lint(check_dir)
    finally:
        if shim:
            shutil.rmtree(shim, ignore_errors=True)


def pm_step(kb, roadmap_path, queue_path):
    with open(roadmap_path, encoding="utf-8", newline="") as f:
        plan = plan_json.build_plan(f.read())
    with tempfile.TemporaryDirectory() as d:
        plan_path = os.path.join(d, "plan.json")
        with open(plan_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
            f.write("\n")
        pm_queue.main(["--plan", plan_path, "--out", queue_path])
    return pm_routine.routine(kb, queue_path, max_parallel=pm_queue.MAX_PARALLEL)


def write_log(path, stamp, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8", newline="") as f:
            old = f.read()
    eol = "\r\n" if "\r\n" in old else "\n"
    block = ["# Director's Cut auto - " + stamp] + ["- " + line for line in lines] + [""]
    gap = eol if old and not old.endswith(("\n", "\r")) else ""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(old + gap + eol.join(block))


def run(lab, timestamp=None, max_rows=MAX_NEW_ROWS):
    p = lab_paths(lab)
    kb, roadmap, queue = p["kb"], p["roadmap"], p["queue"]
    stamp = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ctx = read_context(kb)
    with open(roadmap, encoding="utf-8", newline="") as f:
        original = f.read()
    limit = max(0, min(MAX_NEW_ROWS, int(max_rows)))
    candidates, dropped = build_candidates(ctx, original, limit)
    verdict = audit_batch(candidates)
    report = {"timestamp": stamp, "approved": bool(verdict["approved"]),
              "reasons": verdict["reasons"], "candidates": [c["id"] for c in candidates],
              "dropped": dropped, "appended": [], "backup": "", "status": "pending"}
    if not verdict["approved"]:
        reason = "; ".join(verdict["reasons"])
        write_log(p["log"], stamp, ["Auditor REJECTED batch: " + reason,
                                    "No files changed: ROADMAP.md not copied or appended, QUEUE.json untouched, no backup created."])
        report["status"] = "rejected"
        return report
    notes = rebalance(candidates, original)
    coverage = intake_coverage(ctx["proposal"], ctx["intake"])
    bak = backup_roadmap(roadmap, stamp)
    append_rows(roadmap, [c["row"] for c in candidates])
    report["appended"] = [c["id"] for c in candidates]
    report["backup"] = os.path.basename(bak)
    problems = docs_check(kb, p["project"], roadmap)
    if problems:
        shutil.copyfile(bak, roadmap)
        write_log(p["log"], stamp, ["Auditor APPROVED batch: " + "; ".join(verdict["reasons"]),
                                    "docs_lint FAILED: " + "; ".join(problems),
                                    "Rolled back ROADMAP.md from " + report["backup"],
                                    "Undo: copy docs/" + report["backup"] + " back over docs/ROADMAP.md."])
        report["status"] = "rollback"
        report["reasons"] = problems
        return report
    pm = pm_step(kb, roadmap, queue)
    lines = ["Auditor APPROVED batch: " + "; ".join(verdict["reasons"]),
             "Read %d analysis rows and %d intake files" % (len(ctx["analysis"]), len(ctx["intake"])),
             "Intake coverage: " + ", ".join("%s=%d" % (c["id"], coverage.get(c["id"], 0)) for c in candidates),
             "Dropped: " + ("; ".join("%s (%s)" % d for d in dropped) or "none"),
             "Appended %d rows to docs/ROADMAP.md: %s" % (len(candidates), ", ".join(report["appended"])),
             "Rebalance: " + ("; ".join(notes) or "none needed"),
             "PM: pm_routine.py cap %d, free slots %d" % (pm["max_parallel"], pm["free_slots"]),
             "QUEUE.json written by pm_queue.py (%d queued)" % pm_routine.read_json(queue, {}).get("count", 0),
             "Backup: docs/" + report["backup"],
             "Undo: copy docs/" + report["backup"] + " back over docs/ROADMAP.md to restore the previous file; "
             "then regenerate plan/QUEUE.json through pm_queue.py only."]
    write_log(p["log"], stamp, lines)
    report["status"] = "approved"
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lab")
    ap.add_argument("--timestamp", default="")
    ap.add_argument("--max-rows", type=int, default=MAX_NEW_ROWS)
    a = ap.parse_args(argv)
    try:
        rep = run(a.lab, a.timestamp or None, a.max_rows)
    except (OSError, ValueError, KeyError) as e:
        print("dc_auto: " + str(e), file=sys.stderr)
        return 2
    if rep["status"] == "rejected":
        print("REJECTED: " + "; ".join(rep["reasons"]))
        return 1
    if rep["status"] == "rollback":
        print("ROLLBACK: docs_lint " + "; ".join(rep["reasons"]))
        return 2
    print("APPROVED: %d rows appended; backup %s; undo in plan/DC-LOG.md" % (
        len(rep["appended"]), rep["backup"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
