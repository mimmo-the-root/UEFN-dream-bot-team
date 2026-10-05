#!/usr/bin/env python3
"""Format check for Claude/docs/ROADMAP.md and BUGS.md (the formats the Agent Console reads).
Prints one line per problem and exits 1 when something is wrong, 0 otherwise. Read-only.
Usage: python Claude/hooks/docs_lint.py [project dir]   (default: CLAUDE_PROJECT_DIR or cwd)"""
import os, re, sys

TASK_COLS = ["id", "feature", "status", "acceptance criteria", "priority", "release"]
BUG_COLS = ["title", "severity", "status"]
PHASE_COLS = ["id", "phase", "goal", "exit criteria", "status"]
TASK_OK = re.compile(r"^(to do|todo|in progress|blocked|done|out of scope|da fare|in corso|bloccat\w*|fatto|fuori scope|wip|complet\w*|chiuso|closed|risolto|resolved)\b", re.I)
BUG_OK = re.compile(r"^(open|in progress|fixed|closed|done|resolved|wontfix|aperto|in corso|fatto|risolto|chiuso)\b", re.I)


def tables(text):
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        if re.match(r"^\|.*\|\s*$", lines[i]) and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip().lower() for c in lines[i].split("|")[1:-1]]
            rows, j = [], i + 2
            while j < len(lines) and re.match(r"^\|.*\|\s*$", lines[j]):
                cells = [c.strip() for c in lines[j].split("|")[1:-1]]
                rows.append(dict(zip(head, cells)))
                j += 1
            yield i + 1, head, rows
            i = j
        else:
            i += 1


def lint(project):
    out = []
    docs = os.path.join(project, "Claude", "docs")
    rp, bp = os.path.join(docs, "ROADMAP.md"), os.path.join(docs, "BUGS.md")
    if os.path.isfile(rp):
        t = open(rp, encoding="utf-8", errors="replace").read()
        found, seen = 0, set()
        for line, head, rows in tables(t):
            if not any(re.match(r"^T-\d+", r.get("id", "")) for r in rows):
                continue
            found += 1
            if found > 1:
                out.append("ROADMAP.md line %d: a second tasks table; keep ONE table under '## Tasks'" % line)
            if head != TASK_COLS:
                out.append("ROADMAP.md line %d: columns are %s; expected exactly: %s" % (line, " | ".join(head), " | ".join(TASK_COLS)))
            for r in rows:
                tid = r.get("id", "")
                if not re.fullmatch(r"T-\d{3}", tid):
                    out.append("ROADMAP.md: id '%s' is not T-<3 digits>" % tid)
                if tid in seen:
                    out.append("ROADMAP.md: duplicate id %s" % tid)
                seen.add(tid)
                if not TASK_OK.match(r.get("status", "")):
                    out.append("ROADMAP.md %s: status '%s' must start with To do / In progress / Blocked / Done / Out of scope" % (tid, r.get("status", "")))
                if not r.get("release", "").strip():
                    out.append("ROADMAP.md %s: empty Release cell (the console groups by it)" % tid)
        if not found:
            out.append("ROADMAP.md: no tasks table with T-xxx ids found under '## Tasks'")
        # Delivery standard (v1.88): only enforced once the project has a '## Phases' section, so older
        # projects keep working until planner-docs introduces it. Closed tasks keep their old Release names.
        if re.search(r"^##\s*Phases", t, re.M | re.I):
            ph = [(l, h, r) for (l, h, r) in tables(t) if any(re.match(r"^PH-\d+", x.get("id", "")) for x in r)]
            if not ph:
                out.append("ROADMAP.md: '## Phases' needs a table with PH-0, PH-1... ids (columns: ID | Phase | Goal | Exit criteria | Status)")
            else:
                line, head, rows = ph[0]
                if head != PHASE_COLS:
                    out.append("ROADMAP.md line %d: Phases columns are %s; expected exactly: %s" % (line, " | ".join(head), " | ".join(PHASE_COLS)))
                active = [r for r in rows if r.get("status", "").lower().startswith("active")]
                if len(active) != 1:
                    out.append("ROADMAP.md Phases: exactly one phase must be Active (found %d)" % len(active))
                for r in rows:
                    if not re.match(r"^(planned|active|done)\b", r.get("status", ""), re.I):
                        out.append("ROADMAP.md Phases %s: status must start with Planned / Active / Done" % r.get("id", "?"))
            for line, head, rows in tables(t):
                for r in rows:
                    if re.match(r"^T-\d+", r.get("id", "")) and not re.match(r"^(done|out of scope|fatto|fuori scope|complet\w*|chiuso|closed|risolto|resolved)\b", r.get("status", ""), re.I):
                        rel = r.get("release", "").strip()
                        if rel and not re.fullmatch(r"P\d-R\d+|Later", rel):
                            out.append("ROADMAP.md %s: Release '%s' must be P<phase>-R<n> (e.g. P0-R1) or Later (backlog)" % (r["id"], rel))
    if os.path.isfile(bp):
        t = open(bp, encoding="utf-8", errors="replace").read()
        seen = set()
        for line, head, rows in tables(t):
            if not any(re.match(r"^B-\d+", r.get("id", r.get("title", ""))) for r in rows):
                continue
            missing = [c for c in BUG_COLS if c not in head]
            if missing:
                out.append("BUGS.md line %d: table lacks column(s): %s" % (line, ", ".join(missing)))
            for r in rows:
                bid = r.get("id", "") or r.get("title", "")
                m = re.match(r"B-\d+", bid)
                if not m:
                    out.append("BUGS.md: row '%s' has no B-<3 digits> id at the start of its Title cell" % bid[:40])
                    continue
                if not re.fullmatch(r"B-\d{3}", m.group(0)):
                    out.append("BUGS.md: id '%s' is not B-<3 digits>" % m.group(0))
                if m.group(0) in seen:
                    out.append("BUGS.md: duplicate id %s" % m.group(0))
                seen.add(m.group(0))
                if not BUG_OK.match(r.get("status", "")):
                    out.append("BUGS.md %s: status '%s' must start with Open / In progress / Fixed / Closed" % (m.group(0), r.get("status", "")))
        prose = [l for l in t.split("\n") if re.match(r"^\s*[-*]\s*\**B-\d+", l)]
        if prose:
            out.append("BUGS.md: %d bug(s) written as prose list items; move them into the table" % len(prose))
    return out


def post_edit():
    """PostToolUse hook: only when ROADMAP.md / BUGS.md was just edited. Problems go to stderr with exit 2,
    which Claude sees immediately and must fix (it never blocks anything else)."""
    import json
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    f = str((data.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
    if not re.search(r"/Claude/docs/(ROADMAP|BUGS)\.md$", f):
        return 0
    problems = lint(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    if problems:
        sys.stderr.write("Docs format check failed after your edit. The Agent Console reads a FIXED format; fix the "
                         "file (do not change the format, do not add sections or tables):\n" + "\n".join(problems[:15]) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    if "--post-edit" in sys.argv:
        sys.exit(post_edit())
    proj = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    problems = lint(proj)
    for p in problems:
        print(p)
    print("docs format OK" if not problems else "%d format problem(s): fix them in the file, do not change the format" % len(problems))
    sys.exit(1 if problems else 0)
