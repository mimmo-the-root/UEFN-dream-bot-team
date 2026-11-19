#!/usr/bin/env python3
"""Deterministic orchestrator (no model). One run: pick the active release, move finished
packages to relay/done, refill relay/inbox + relay/running from relay/later, call integrate.py,
check the release, write the ORCHESTRATOR section in plan/STATUS.md and one line in logs/orchestrator.log.
Usage: python tools/orchestrate.py --lab LAB [--repo REPO] [--target release/ibrido-0] [--integrate-cmd CMD] [--dry-run]
Exit 0 normally, 1 if the roadmap is locked or does not parse. Never pushes, tags or bumps a version."""
import argparse, datetime, os, re, shlex, shutil, subprocess, sys

KEEP = 3
NAME_RE = re.compile(r"^(\d+)-t-(\d+)-.*\.md$", re.I)
SKIP_RE = re.compile(r"(?<![a-z])(frozen|later|owner-stop)(?![a-z])", re.I)
SECTION = "## ORCHESTRATOR"
LOCKS = ("ROADMAP.md.lock", "ROADMAP.lock", ".ROADMAP.md.lock", ".ROADMAP.lock")


def read(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return f.read().replace("\r\n", "\n")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def parse_roadmap(path):
    """Return list of rows (dicts) in file order; raise ValueError when a task row is malformed."""
    rows = []
    for line in read(path).split("\n"):
        m = re.match(r"^\|\s*T-(\d+)\s*\|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            raise ValueError("row T-%s has %d cells" % (m.group(1), len(cells)))
        rows.append({"id": int(m.group(1)), "status": cells[-6], "release": cells[-3],
                     "text": line, "idx": len(rows)})
    if not rows:
        raise ValueError("no task rows")
    return rows


def rel_key(name):
    m = re.search(r"R(\d+)", name)
    return (int(m.group(1)) if m else 10 ** 6, name)


def pkg_files(d):
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".md") and os.path.isfile(os.path.join(d, f)))


def tid(name):
    m = NAME_RE.match(name)
    return int(m.group(2)) if m else None


def header(path, key):
    m = re.search(r"^%s:[ \t]*(.*)$" % key, read(path), re.M | re.I)
    return m.group(1).strip() if m else ""


def plan_run(lab):
    rows = parse_roadmap(os.path.join(lab, "docs", "ROADMAP.md"))
    by_id = {r["id"]: r for r in rows}
    releases = sorted({r["release"] for r in rows if r["release"]}, key=rel_key)
    active = next((r["release"] for r in rows if r["status"].lower() == "in progress"), None)
    if not active:
        active = next((rel for rel in releases if any(r["release"] == rel and r["status"].lower() == "to do" for r in rows)), None)
    relay = os.path.join(lab, "relay")
    moves, problems = [], []
    done_names = set(pkg_files(os.path.join(relay, "done")))
    for sub in ("running", "inbox"):
        for f in pkg_files(os.path.join(relay, sub)):
            t = tid(f)
            if t in by_id and by_id[t]["status"].lower() == "done":
                if f in done_names:
                    problems.append("%s already in done, left in %s" % (f, sub))
                else:
                    moves.append((sub, "done", f))
                    done_names.add(f)
    moved_out = {(s, f) for s, _, f in moves}
    active_now = [f for sub in ("inbox", "running") for f in pkg_files(os.path.join(relay, sub)) if (sub, f) not in moved_out]
    done_ids = {f.split("-")[0] for f in done_names}
    cands = []
    for f in pkg_files(os.path.join(relay, "later")):
        t = tid(f)
        if t not in by_id or SKIP_RE.search(f):
            continue
        r = by_id[t]
        p = os.path.join(relay, "later", f)
        if r["release"] != active or r["status"].lower() != "to do":
            continue
        if "[owner]" in r["text"].lower() or header(p, "needs_owner").lower() == "yes":
            continue
        deps = [d for d in re.findall(r"\d+", header(p, "after"))]
        if any(d not in done_ids for d in deps):
            continue
        cands.append((r["idx"], f))
    for _, f in sorted(cands):
        if len(active_now) >= KEEP:
            break
        moves.append(("later", "inbox", f))
        active_now.append(f)
    counts = {"To do": 0, "In progress": 0, "Done": 0}
    for r in rows:
        for k in counts:
            if r["status"].lower() == k.lower():
                counts[k] += 1
    ready = None
    if active:
        prev = [rel for rel in releases if rel_key(rel) < rel_key(active)]
        cand = prev[-1] if prev else None
    else:
        cand = releases[-1] if releases else None
    if cand and all(r["status"].lower() == "done" for r in rows if r["release"] == cand):
        ready = cand
    return {"active": active, "counts": counts, "moves": moves, "problems": problems,
            "ready": ready, "queue": [f for f in active_now]}


def run_integrate(args, lab):
    kit = os.path.dirname(os.path.abspath(__file__))
    if args.integrate_cmd:
        cmd = shlex.split(args.integrate_cmd)
    else:
        script = os.path.join(kit, "integrate.py")
        if not os.path.isfile(script):
            return "integrate: not installed"
        repo = args.repo or os.path.dirname(kit)
        cmd = [sys.executable, script, "--repo", repo, "--target", args.target, "--lab", lab, "--json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=args.integrate_timeout, encoding="utf-8", errors="replace")
    except Exception as e:  # noqa
        return "integrate: failed (%s)" % type(e).__name__
    return "integrate: ok" if r.returncode == 0 else "integrate: failed rc=%d" % r.returncode


def section_body(p, now, integ):
    mv = ["%s -> %s: %s" % m for m in p["moves"]]
    lines = ["- time: %s" % now,
             "- active release: %s" % (p["active"] or "none"),
             "- To do %d / In progress %d / Done %d" % (p["counts"]["To do"], p["counts"]["In progress"], p["counts"]["Done"]),
             "- queue (inbox+running): %s" % (", ".join(p["queue"]) or "empty"),
             "- moved: %s" % ("; ".join(mv) or "nothing"),
             "- %s" % integ,
             "- problems: %s" % ("; ".join(p["problems"]) or "none")]
    if p["ready"]:
        lines.append("RELEASE %s READY" % p["ready"])
    return "\n".join(lines) + "\n"


def strip_time(body):
    skip = ("- time:",) + (("- moved:",) if "- moved: nothing" in body else ())
    return "\n".join(l for l in body.split("\n") if not l.startswith(skip))


def update_status(path, body):
    text = read(path) if os.path.isfile(path) else ""
    m = re.search(r"^%s[ \t]*\n(.*?)(?=^## |\Z)" % re.escape(SECTION), text, re.M | re.S)
    new = SECTION + "\n" + body + "\n"
    if m:
        old = "\n".join(l for l in m.group(1).split("\n") if not l.startswith("- moved:"))
        if "- moved: nothing" in body and strip_time(old).strip() == strip_time(body).strip():
            return False
        text = text[:m.start()] + new + text[m.end():]
    else:
        text = text + ("" if not text or text.endswith("\n") else "\n") + ("\n" if text else "") + new
    write(path, text)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lab", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--target", default="release/ibrido-0")
    ap.add_argument("--integrate-cmd")
    ap.add_argument("--integrate-timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    lab = os.path.abspath(args.lab)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = os.path.join(lab, "logs", "orchestrator.log")

    def logline(msg):
        if not args.dry_run:
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, "a", encoding="utf-8", newline="\n") as f:
                f.write("%s %s\n" % (now, msg))

    docs = os.path.join(lab, "docs")
    for lk in LOCKS:
        if os.path.exists(os.path.join(docs, lk)):
            logline("roadmap locked (%s): nothing done" % lk)
            print("roadmap locked: nothing done")
            return 1
    try:
        p = plan_run(lab)
    except (ValueError, OSError) as e:
        logline("roadmap unreadable (%s): nothing done" % e)
        print("roadmap unreadable: %s" % e)
        return 1
    relay = os.path.join(lab, "relay")
    if args.dry_run:
        for s, d, f in p["moves"]:
            print("would move %s: %s -> %s" % (f, s, d))
        print("would run integrate" if (args.integrate_cmd or os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "integrate.py"))) else "integrate: not installed")
        print(section_body(p, now, "integrate: (dry run)"))
        return 0
    for s, d, f in p["moves"]:
        os.makedirs(os.path.join(relay, d), exist_ok=True)
        shutil.move(os.path.join(relay, s, f), os.path.join(relay, d, f))
    integ = run_integrate(args, lab)
    body = section_body(p, now, integ)
    update_status(os.path.join(lab, "plan", "STATUS.md"), body)
    if p["ready"]:
        fb = os.path.join(lab, "plan", "FEEDBACK-FROM-COD.md")
        line = "RELEASE %s READY" % p["ready"]
        old = read(fb) if os.path.isfile(fb) else ""
        if line not in old.split("\n"):
            write(fb, old + ("" if not old or old.endswith("\n") else "\n") + line + "\n")
    logline("release=%s todo=%d inprog=%d done=%d queue=%s moved=%s %s problems=%s" % (
        p["active"] or "none", p["counts"]["To do"], p["counts"]["In progress"], p["counts"]["Done"],
        ",".join(p["queue"]) or "empty", ";".join("%s>%s:%s" % m for m in p["moves"]) or "nothing", integ,
        ";".join(p["problems"]) or "none"))
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
