#!/usr/bin/env python3
"""Verse change log + header check (v1.108).

The header of a Verse file keeps ONLY: file name, an up-to-date English Summary, and the real
"Last modified: <date> - v<N>". The history of changes does NOT live in the file: it goes to
Claude/logs/verse-changes.jsonl (one line per change), next to verse-errors.jsonl. The learning
system reads both logs.

  python Claude/hooks/verse_changes.py add <file.verse> --summary "what changed" [--reason "why"] [--result ok|errors|reverted]
  python Claude/hooks/verse_changes.py list [--file name] [--last N]
  python Claude/hooks/verse_changes.py recurring                     # files whose changes failed or were reverted 2+ times (lesson candidates)
  python Claude/hooks/verse_changes.py check <file.verse> [more files]   # header rule; exit 1 on a problem
Logging never raises into the caller: a log problem must not break a build.
"""
import json, os, re, sys, time

# History markers. The Italian words (storia, modifiche, NUOVO...) are kept on purpose: they match
# old headers that existing user projects already contain; everything the code prints is English.
HIST = re.compile(r"^\s*#\s*(v\d+(\s*-\s*v?\d+)?\b|\d{4}-\d{2}-\d{2}\b|(history|changelog|change log|storia|modifiche)\b|(FIX|NEW|REGRESSION|NUOVO|NUOVA|STORIA|DIAGNOSTICA|REGRESSIONE|SUPERATO|TARATURA)\b)", re.I)
LASTMOD = re.compile(r"^\s*#\s*Last modified:\s*(\d{4}-\d{2}-\d{2})\s*[-—–]+\s*v(\d+)", re.I)
SUMMARY = re.compile(r"^\s*#\s*Summary:\s*\S", re.I)


def project_root(start):
    """The folder that holds Claude/hooks (the project's Content folder). A sub-agent may run from a deeper folder (for example
    Content/Claude), where the plain working directory would create Claude/Claude/logs: walk up a few levels instead."""
    d = os.path.abspath(start)
    for _ in range(5):
        if os.path.isfile(os.path.join(d, "Claude", "hooks", "kit_sync.py")):
            return d
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return os.path.abspath(start)


def log_path(project=None):
    base = project or os.environ.get("CLAUDE_PROJECT_DIR") or project_root(os.getcwd())
    return os.path.join(base, "Claude", "logs", "verse-changes.jsonl")


def record(file, summary, reason="", result="ok", path=None, ts=None):
    """Append one change row. Returns True on success, never raises."""
    try:
        path = path or log_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        row = {"ts": ts or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "file": os.path.basename(str(file)),
               "summary": str(summary)[:300], "reason": str(reason)[:300], "result": result}
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def read(path=None):
    path = path or log_path()
    rows = []
    if os.path.isfile(path):
        for l in open(path, encoding="utf-8", errors="replace"):
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass
    return rows


def recurring(rows, minimum=2):
    """Files whose changes ended in errors or were reverted at least `minimum` times: [(file, count, last summary)]."""
    seen = {}
    for r in rows:
        if r.get("result") in ("errors", "reverted") and r.get("file"):
            n, _ = seen.get(r["file"], (0, ""))
            seen[r["file"]] = (n + 1, r.get("summary", ""))
    return sorted(((f, n, s) for f, (n, s) in seen.items() if n >= minimum), key=lambda x: -x[1])


def header_block(text):
    """The leading comment block (before the first non-comment, non-blank line)."""
    out = []
    for l in text.replace("\r\n", "\n").split("\n"):
        s = l.strip()
        if s.startswith("#") and not s.startswith("#!"):
            out.append(l)
        elif s == "" and not out:
            continue
        else:
            break
    return out


def check_header(text):
    """Problems with the header (list of strings; empty = ok)."""
    h = header_block(text)
    p = []
    if not any(SUMMARY.match(l) for l in h):
        p.append("no '# Summary:' line")
    if not any(LASTMOD.match(l) for l in h):
        p.append("no '# Last modified: <YYYY-MM-DD> - v<N>' line")
    hist = [l for l in h if HIST.match(l) and not LASTMOD.match(l)]
    if hist:
        p.append("%d change-history line(s) in the header (move them to verse-changes.jsonl)" % len(hist))
    return p


def _main(argv):
    if not argv or argv[0] not in ("add", "list", "check", "recurring"):
        print(__doc__); return 2
    cmd, rest = argv[0], argv[1:]
    opt = {}
    pos = []
    i = 0
    while i < len(rest):
        if rest[i].startswith("--") and i + 1 < len(rest):
            opt[rest[i][2:]] = rest[i + 1]; i += 2
        else:
            pos.append(rest[i]); i += 1
    if cmd == "add":
        if not pos or not opt.get("summary"):
            print("usage: add <file.verse> --summary ... [--reason ...] [--result ok|errors|reverted]"); return 2
        print("logged" if record(pos[0], opt["summary"], opt.get("reason", ""), opt.get("result", "ok")) else "could not write the log")
        return 0
    if cmd == "recurring":
        rr = recurring(read())
        for f, n, s in rr:
            print("%s: %d failed or reverted changes, last: %s" % (f, n, s))
        if not rr:
            print("nothing recurring")
        return 0
    if cmd == "list":
        rows = [r for r in read() if not opt.get("file") or r.get("file") == opt["file"]]
        for r in rows[-int(opt.get("last", 20)):]:
            print("%s  %s  %s  [%s]  %s" % (r.get("ts", ""), r.get("file", ""), r.get("summary", ""), r.get("result", ""), r.get("reason", "")))
        return 0
    bad = 0
    for f in pos:
        pr = check_header(open(f, encoding="utf-8", errors="replace").read())
        for x in pr:
            print("%s: %s" % (f, x)); bad = 1
    if not bad:
        print("headers ok")
    return bad


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
