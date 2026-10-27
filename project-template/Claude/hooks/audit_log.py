#!/usr/bin/env python3
"""Audit ledger (v1.114): findings of /audit, with the self-healing limits enforced. Writes Claude/docs/AUDIT.md.

  python Claude/hooks/audit_log.py add "text" --class minor|medium|major [--where file]
  python Claude/hooks/audit_log.py fix N [--ok|--failed]      # record an attempt on finding N
  python Claude/hooks/audit_log.py status                      # counts; exit 1 while a major or a medium is open

Rules (the Self-healing block of CONSTITUTION.md): a MINOR finding may be fixed by the kit by itself, at most 3 attempts per finding and 10
automatic fixes in the audit; after that it becomes MEDIUM. MEDIUM (breaks an acceptance criterion) and MAJOR (an error in the requirement,
any change to GAME-SPEC.md) are never fixed alone: they are listed for the owner. `fix` refuses when the limits are used up."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_TRY, MAX_FIX = 3, 10


def path(base=None):
    base = base or os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(os.path.join(HERE, "..", ".."))
    d = os.path.join(base, "Claude", "docs") if os.path.isdir(os.path.join(base, "Claude")) else os.path.join(base, "docs")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "AUDIT.md")


def load(p):
    try:
        t = open(p, encoding="utf-8").read()
    except OSError:
        return []
    m = re.search(r"<!-- data:(.*?) -->", t, re.S)
    return json.loads(m.group(1)) if m else []


def save(p, items):
    out = ["# Audit", "", "<!-- data:%s -->" % json.dumps(items), "", "| # | Class | Where | Finding | Tries | State |", "|---|---|---|---|---|---|"]
    for i, f in enumerate(items, 1):
        out.append("| %d | %s | %s | %s | %d | %s |" % (i, f["cls"], f.get("where", ""), f["text"].replace("|", "/"), f["tries"], f["state"]))
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")


def add(items, text, cls, where=""):
    if cls not in ("minor", "medium", "major"):
        raise ValueError("class must be minor, medium or major")
    items.append({"text": text, "cls": cls, "where": where, "tries": 0, "state": "open" if cls == "minor" else "for the owner"})
    return items


def fix(items, n, ok):
    f = items[n - 1]
    if f["cls"] != "minor":
        raise ValueError("only a minor finding is fixed by the kit alone: this one goes to the owner")
    if sum(1 for x in items if x["state"] == "fixed") >= MAX_FIX and ok:
        raise ValueError("the limit of %d automatic fixes is used up: the rest goes to the owner" % MAX_FIX)
    if f["tries"] >= MAX_TRY:
        raise ValueError("3 attempts already made: it becomes medium")
    f["tries"] += 1
    if ok:
        f["state"] = "fixed"
    elif f["tries"] >= MAX_TRY:
        f["cls"], f["state"] = "medium", "for the owner"
    return items


def status(items):
    c = {"minor": 0, "medium": 0, "major": 0}
    fixed = sum(1 for x in items if x["state"] == "fixed")
    for x in items:
        if x["state"] != "fixed":
            c[x["cls"]] += 1
    return c, fixed


def main(argv):
    p = path()
    items = load(p)
    cmd = argv[0] if argv else "status"
    try:
        if cmd == "add":
            cls = argv[argv.index("--class") + 1]
            where = argv[argv.index("--where") + 1] if "--where" in argv else ""
            save(p, add(items, argv[1], cls, where))
            print("added #%d (%s)" % (len(items), cls))
            return 0
        if cmd == "fix":
            save(p, fix(items, int(argv[1]), "--failed" not in argv))
            print("#%s: %s" % (argv[1], items[int(argv[1]) - 1]["state"]))
            return 0
    except (ValueError, IndexError) as e:
        print("Refused: %s" % e)
        return 1
    c, fixed = status(items)
    print("Audit: %d fixed by the kit; open: %d minor, %d medium and %d major for the owner" % (fixed, c["minor"], c["medium"], c["major"]))
    return 1 if (c["medium"] or c["major"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
