#!/usr/bin/env python3
"""Backend for the console Problems panel (T-093): summarise plan/PROBLEMS-FROM-COD.md and
plan/PENDING-TESTS.md as JSON, and mark one line as handled (append-only, never deletes a line).

Line format: "<YYYY-MM-DD HH:MM> | <id> | ... " ; '#' lines and blank lines are not entries.
A handled line ends with " [HANDLED <YYYY-MM-DD HH:MM>]". line_id is the first 8 hex chars of
the sha1 of the entry text without the marker, so it survives appends and reordering.

Usage: python tools/problems_summary.py [plan_dir]   (default: ./plan or $UEFN_PLAN_DIR)
"""
import datetime, hashlib, json, os, re, sys

FILES = ("PROBLEMS-FROM-COD.md", "PENDING-TESTS.md")
MARK = re.compile(r"\s*\[HANDLED (\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?)\]\s*$")
DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2}))?")


def line_id(text):
    return hashlib.sha1(MARK.sub("", text).strip().encode("utf-8")).hexdigest()[:8]


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _entries(path):
    """Yield (index, raw_line, text) for entry lines of a file."""
    for i, raw in enumerate(_read(path).split("\n")):
        t = raw.rstrip("\r")
        if t.strip() and not t.lstrip().startswith("#"):
            yield i, raw, t


def _age_days(text, now):
    m = DATE.match(text.strip())
    if not m:
        return None
    try:
        d = datetime.datetime(int(m.group(1)[:4]), int(m.group(1)[5:7]), int(m.group(1)[8:10]),
                              int(m.group(2) or 0), int(m.group(3) or 0))
    except ValueError:
        return None
    return round(max((now - d).total_seconds(), 0) / 86400.0, 2)


def summarize(plan_dir, now=None):
    now = now or datetime.datetime.now()
    out = {"files": {}, "open": 0, "closed": 0}
    for name in FILES:
        path = os.path.join(plan_dir, name)
        items, o, c = [], 0, 0
        if os.path.isfile(path):
            for i, _raw, t in _entries(path):
                handled = MARK.search(t) is not None
                parts = [p.strip() for p in MARK.sub("", t).split("|")]
                o, c = (o, c + 1) if handled else (o + 1, c)
                items.append({"line_id": line_id(t), "line_no": i + 1, "status": "closed" if handled else "open",
                              "age_days": _age_days(t, now), "date": parts[0], "ref": parts[1] if len(parts) > 1 else "",
                              "text": MARK.sub("", t).strip()})
        out["files"][name] = {"open": o, "closed": c, "items": items}
        out["open"] += o
        out["closed"] += c
    return out


def mark_handled(path, line_id_, now=None):
    """Append ' [HANDLED <date time>]' to the entry with this line_id. Returns True if marked,
    False if not found or already handled. No line is ever removed."""
    now = now or datetime.datetime.now()
    text = _read(path)
    lines = text.split("\n")
    for i, raw, t in _entries(path):
        if line_id(t) == line_id_:
            if MARK.search(t):
                return False
            cr = "\r" if raw.endswith("\r") else ""
            lines[i] = t + " [HANDLED %s]" % now.strftime("%Y-%m-%d %H:%M") + cr
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(lines))
            os.replace(tmp, path)
            return True
    return False


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("UEFN_PLAN_DIR", "plan")
    print(json.dumps(summarize(d), indent=2, ensure_ascii=False))
