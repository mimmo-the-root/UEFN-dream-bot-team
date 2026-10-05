#!/usr/bin/env python3
"""Automatic history trimming: fewer tokens read, nothing lost (v1.87).

Moves OLD HISTORY out of the files agents read, into Claude/docs/archive/ (kept, with a pointer left behind):
  STATUS.md      older log entries (keeps the newest 5) when the file is over 8 KB
  BUGS.md        detail sections of bugs already resolved (keeps heading + 2 lines) when the file is over 12 KB
  *.verse        long dated change-history comment paragraphs (FIX / NUOVO / STORIA / DIAGNOSTICA / REGRESSIONE ...)
                 in files over 20 KB: keeps the first 3 comment lines + a pointer, full text goes to the archive
Safety: Verse CODE is never touched (the non-comment lines are compared before and after; on any difference the
file is left as it was). Every changed file is backed up first in Claude/logs/kit-backup/<time>-trim/.
Opt out: create the file Claude/docs/.no-history-trim.

  python Claude/hooks/history_trim.py [project dir]            # report only
  python Claude/hooks/history_trim.py [project dir] --apply
"""
import hashlib, os, re, shutil, sys, time

KEEP_STATUS = 5
STATUS_MIN, BUGS_MIN, VERSE_MIN = 8000, 12000, 20000
HIST_START = re.compile(r"^\s*#\s*(FIX|NUOVO|NUOVA|STORIA|DIAGNOSTICA|DIAGNOSTICO|LOG DIAGNOSTICO|REGRESSIONE|SUPERATO|TARATURA|SEMPLIFICATO|ABBANDONATO)\b")
KEEP_LINES, MIN_PARA = 3, 7
SKIP_DIRS = {".git", "Claude", "__ExternalActors__", "__ExternalObjects__", "node_modules", "__pycache__"}


def _read(p):
    with open(p, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def _write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def _append_archive(path, header, body):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cur = _read(path) if os.path.isfile(path) else "# Archive (history moved out of the working files; read only when you need the why)\n"
    key = hashlib.sha1(body.encode("utf-8")).hexdigest()[:8]
    if key in cur:
        return key
    with open(path, "a" if os.path.isfile(path) else "w", encoding="utf-8", newline="") as f:
        f.write("\n\n## %s [%s]\n\n%s\n" % (header, key, body.rstrip("\n")))
    return key


# ------------------------------------------------------------------ STATUS.md
def trim_status(text, arch):
    nl = "\r\n" if "\r\n" in text else "\n"
    t = text.replace("\r\n", "\n")
    if len(t.encode("utf-8")) < STATUS_MIN:
        return text, 0
    m = re.search(r"^## Log\s*$", t, re.M)
    if not m:
        return text, 0
    head, rest = t[:m.end()], t[m.end():]
    parts = re.split(r"(?m)^(?=## )", rest)
    pre, entries = parts[0], [p for p in parts[1:] if p.strip()]
    if len(entries) <= KEEP_STATUS:
        return text, 0
    old = entries[KEEP_STATUS:]
    _append_archive(arch, "STATUS log entries moved on %s" % time.strftime("%Y-%m-%d"), "".join(old))
    new = head + pre + "".join(entries[:KEEP_STATUS]).rstrip("\n") + "\n\n(Older log entries: Claude/docs/archive/STATUS-ARCHIVE.md - read only if needed.)\n"
    return new.replace("\n", nl), len(old)


# ------------------------------------------------------------------ BUGS.md
def trim_bugs(text, arch):
    nl = "\r\n" if "\r\n" in text else "\n"
    t = text.replace("\r\n", "\n")
    if len(t.encode("utf-8")) < BUGS_MIN:
        return text, 0
    parts = re.split(r"(?m)^(?=### )", t)
    out, moved = [parts[0]], 0
    for p in parts[1:]:
        lines = p.split("\n")
        h = lines[0]
        tag = re.search(r"\[([^\]]*)\]", h)
        # body = until the next "## " heading (a "### " part may run into the next "## " section)
        cut = next((i for i, l in enumerate(lines) if i and l.startswith("## ")), len(lines))
        body, tail = lines[1:cut], lines[cut:]
        done = tag and re.search(r"resolved|fixed|closed|risolto|chiuso", tag.group(1), re.I) and not re.search(r"still open|\bnew\b|not resolved|to confirm|open\b", tag.group(1), re.I)
        if done and len(body) > 6 and "archive/BUGS-ARCHIVE.md" not in p:
            _append_archive(arch, h.strip("# ").strip()[:90], "\n".join([h] + body))
            keep = [b for b in body if b.strip()][:2]
            p = "\n".join([h] + keep + ["(Full detail archived: Claude/docs/archive/BUGS-ARCHIVE.md)", ""] + tail)
            moved += 1
        out.append(p)
    return "".join(out).replace("\n", nl), moved


# ------------------------------------------------------------------ Verse
def _is_comment(l):
    return l.lstrip().startswith("#") and not l.lstrip().startswith("#!")


def trim_verse(text, arch, rel):
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    if len(text.encode("utf-8")) < VERSE_MIN:
        return text, 0
    out, i, moved, n = [], 0, 0, len(lines)
    while i < n:
        if not _is_comment(lines[i]):
            out.append(lines[i]); i += 1; continue
        j = i
        while j < n and _is_comment(lines[j]):
            j += 1
        run = lines[i:j]
        k = 0
        res = []
        while k < len(run):  # split the run in paragraphs at bare "#" lines
            e = k
            while e < len(run) and run[e].strip() not in ("#", ""):
                e += 1
            para = run[k:e]
            if len(para) >= MIN_PARA and HIST_START.match(para[0]) and not any("history:" in x for x in para[:KEEP_LINES + 1]):
                key = _append_archive(arch, "%s (history comment)" % rel, "\n".join(para))
                ind = re.match(r"\s*", para[0]).group(0)
                res += para[:KEEP_LINES] + ["%s# (history, %d more lines: Claude/docs/archive/verse/%s [%s])" % (ind, len(para) - KEEP_LINES, os.path.basename(arch), key)]
                moved += 1
            else:
                res += para
            if e < len(run):
                res.append(run[e])
            k = e + 1
        out += res
        i = j
    new = "\n".join(out)
    # safety: code (non-comment lines) must be identical
    code = lambda ls: [l for l in ls if not _is_comment(l)]
    if code(new.split("\n")) != code(lines):
        return text, 0
    return new.replace("\n", nl), moved


def run(project, apply=False):
    """Returns a list of report lines. With apply=True it writes (after a backup)."""
    docs = os.path.join(project, "Claude", "docs")
    if os.path.isfile(os.path.join(docs, ".no-history-trim")):
        return []
    arch_dir = os.path.join(docs, "archive")
    bk = os.path.join(project, "Claude", "logs", "kit-backup", time.strftime("%Y%m%d-%H%M%S") + "-trim")
    report = []

    def commit(path, old, new, what):
        if new == old:
            return
        saved = len(old.encode("utf-8")) - len(new.encode("utf-8"))
        report.append("%s: %s (-%d KB)" % (os.path.relpath(path, project).replace(os.sep, "/"), what, max(saved, 0) // 1024))
        if apply:
            dst = os.path.join(bk, os.path.relpath(path, project))
            if dst.endswith(".verse"):
                dst += ".bak"  # a backup must NEVER keep the .verse extension: UEFN compiles every .verse under Content/
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(path, dst)
            _write(path, new)

    for name, fn, arch in (("STATUS.md", trim_status, "STATUS-ARCHIVE.md"), ("BUGS.md", trim_bugs, "BUGS-ARCHIVE.md")):
        p = os.path.join(docs, name)
        if os.path.isfile(p):
            old = _read(p)
            a = os.path.join(arch_dir, arch)
            if not apply:  # dry-run must not write the archive
                a = os.path.join(bk, "dry", arch)
            new, k = fn(old, a)
            if k:
                commit(p, old, new, "%d section(s) moved to archive" % k)
    for base, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".verse"):
                continue
            p = os.path.join(base, f)
            old = _read(p)
            if len(old.encode("utf-8")) < VERSE_MIN:
                continue
            rel = os.path.relpath(p, project).replace(os.sep, "__")
            a = os.path.join(arch_dir, "verse", rel + ".md")
            if not apply:
                a = os.path.join(bk, "dry", rel + ".md")
            new, k = trim_verse(old, a, os.path.relpath(p, project).replace(os.sep, "/"))
            if k:
                commit(p, old, new, "%d history comment block(s) condensed, code untouched" % k)
    if not apply and os.path.isdir(os.path.join(bk, "dry")):
        shutil.rmtree(bk, ignore_errors=True)
    return report


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    proj = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    r = run(proj, apply="--apply" in sys.argv)
    for l in r:
        print(l)
    if not r:
        print("nothing to trim")
