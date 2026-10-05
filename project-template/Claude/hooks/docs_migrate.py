#!/usr/bin/env python3
"""Align an existing project's ROADMAP.md / BUGS.md to the current format contract, keeping every row.
Run by kit_sync after a kit update (with a backup), or by hand: python Claude/hooks/docs_migrate.py [project dir]

What it does, and only this:
  ROADMAP.md  - tasks table: adds missing contract columns (Release -> "Unassigned"), puts the contract columns
                in contract order; unknown extra columns stay after them (nothing is deleted).
  BUGS.md     - bug tables: a Title without a B-<3 digits> id gets the next free id as a prefix; a separate ID
                column is folded into the Title ("B-007: title").
Prints what changed, or nothing. Exit 0 always. Idempotent."""
import os, re, shutil, sys, time

TASK_COLS = ["ID", "Feature", "Status", "Acceptance criteria", "Priority", "Release"]
DEFAULTS = {"Release": "Unassigned"}


def split(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def join(cells):
    return "| " + " | ".join(cells) + " |"


def table_spans(lines):
    i = 0
    while i < len(lines):
        if re.match(r"^\|.*\|\s*$", lines[i]) and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|\s*$", lines[i + 1]):
            j = i + 2
            while j < len(lines) and re.match(r"^\|.*\|\s*$", lines[j]):
                j += 1
            yield i, j
            i = j
        else:
            i += 1


def migrate_roadmap(text):
    lines = text.split("\n")
    notes = []
    for a, b in list(table_spans(lines)):
        head = split(lines[a])
        low = [h.lower() for h in head]
        rows = [split(l) for l in lines[a + 2:b]]
        if not any(re.match(r"^T-\d+", (r[0] if r else "")) for r in rows) or "id" not in low:
            continue
        want = [c for c in TASK_COLS]
        extra = [h for h in head if h.lower() not in [w.lower() for w in want]]
        new_head = want + extra
        if head == new_head:
            continue
        out = []
        for r in rows:
            d = {low[k]: (r[k] if k < len(r) else "") for k in range(len(low))}
            cells = [d.get(w.lower(), DEFAULTS.get(w, "")) or DEFAULTS.get(w, "") if w.lower() not in d else d[w.lower()] for w in want]
            cells = [c if c != "" or w not in DEFAULTS else DEFAULTS[w] for c, w in zip(cells, want)]
            cells += [d.get(e.lower(), "") for e in extra]
            out.append(join(cells))
        block = [join(new_head), "|" + "---|" * len(new_head)] + out
        lines[a:b] = block
        notes.append("ROADMAP.md: tasks table aligned to the contract columns (%d rows kept)" % len(out))
        break
    return "\n".join(lines), notes


def migrate_bugs(text):
    lines = text.split("\n")
    notes = []
    used = {int(m) for m in re.findall(r"\bB-(\d+)\b", text)}
    nxt = (max(used) if used else 0)
    changed = 0
    for a, b in list(table_spans(lines)):
        head = split(lines[a])
        low = [h.lower() for h in head]
        if "title" not in low and "id" not in low:
            continue
        rows = lines[a + 2:b]
        if not any(re.match(r"^\|\s*B-\d+", l) for l in rows) and "severity" not in low:
            continue
        if "id" in low:  # fold ID column into Title
            k, t = low.index("id"), low.index("title") if "title" in low else None
            if t is not None:
                nr = []
                for l in rows:
                    c = split(l)
                    if len(c) > max(k, t):
                        if re.fullmatch(r"B-\d+", c[k]) and not re.match(r"^B-\d+", c[t]):
                            c[t] = "%s: %s" % (c[k], c[t])
                        del c[k]
                    nr.append(join(c))
                tt = [h for n, h in enumerate(head) if n != k]
                lines[a:b] = [join(tt), "|" + "---|" * len(tt)] + nr
                b = a + 2 + len(nr)
                head, low = tt, [h.lower() for h in tt]
                changed += len(nr)
        if "title" in low:
            tcol = low.index("title")
            for n in range(a + 2, b):
                c = split(lines[n])
                if len(c) > tcol and c[tcol] and not re.match(r"^B-\d+", c[tcol]) and c[tcol] not in ("(empty)",):
                    nxt += 1
                    c[tcol] = "B-%03d: %s" % (nxt, c[tcol])
                    lines[n] = join(c)
                    changed += 1
    if changed:
        notes.append("BUGS.md: %d bug row(s) aligned (Title starts with its B-id)" % changed)
    return "\n".join(lines), notes


def run(project, backup_root=None):
    docs = os.path.join(project, "Claude", "docs")
    done = []
    for name, fn in (("ROADMAP.md", migrate_roadmap), ("BUGS.md", migrate_bugs)):
        p = os.path.join(docs, name)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8", newline="") as f:
            raw = f.read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        new, notes = fn(raw.replace("\r\n", "\n"))
        if notes and new != raw.replace("\r\n", "\n"):
            if backup_root:
                os.makedirs(os.path.join(backup_root, "docs"), exist_ok=True)
                shutil.copy2(p, os.path.join(backup_root, "docs", name))
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(new.replace("\n", nl))
            done += notes
    return done


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    bk = os.path.join(proj, "Claude", "logs", "kit-backup", time.strftime("%Y%m%d-%H%M%S"))
    for n in run(proj, bk):
        print(n)
