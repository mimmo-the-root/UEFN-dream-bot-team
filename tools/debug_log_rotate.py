#!/usr/bin/env python3
"""debug_log_rotate.py - keep each debug file to the last N lines (setting debug.max_lines in kit-settings.json).

Older lines are moved to Claude/logs/archive/<file>-<YYYY-MM-DD>.txt (appended, with a summary header), so logs never
grow without limit and nothing is lost. A leading header block of a plan file (lines up to the first blank line) is kept.
API: rotate(project=None, max_lines=None, today=None) -> list of result strings. Stdlib only.
CLI: python tools/debug_log_rotate.py [--project DIR] [--max-lines N]
"""
import datetime, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_config  # noqa: E402

FILES = [
    os.path.join("Claude", "plan", "FEEDBACK-FROM-COD.md"),
    os.path.join("Claude", "plan", "PROBLEMS-FROM-COD.md"),
    os.path.join("Claude", "plan", "PENDING-TESTS.md"),
    os.path.join("Claude", "logs", "task-status.log"),
]


def rotate_file(fp, archive_dir, max_lines, today):
    if not os.path.isfile(fp):
        return None
    with open(fp, encoding="utf-8", errors="replace", newline="") as f:
        lines = f.read().split("\n")
    trailing = lines and lines[-1] == ""
    if trailing:
        lines = lines[:-1]
    head = []
    if fp.endswith(".md"):
        for i, ln in enumerate(lines):
            if not ln.strip():
                head = lines[:i + 1]
                break
    body = lines[len(head):]
    if len(body) <= max_lines:
        return None
    cut = len(body) - max_lines
    old, keep = body[:cut], body[cut:]
    os.makedirs(archive_dir, exist_ok=True)
    name = os.path.basename(fp)
    ap = os.path.join(archive_dir, "%s-%s.txt" % (name, today))
    with open(ap, "a", encoding="utf-8", newline="\n") as f:
        f.write("# %s: %d older lines rolled on %s (first: %s | last: %s)\n"
                % (name, len(old), today, old[0][:60], old[-1][:60]))
        f.write("\n".join(old) + "\n")
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(head + keep) + "\n")
    os.replace(tmp, fp)
    return "%s: kept %d, rolled %d to %s" % (name, len(keep), len(old), ap)


def rotate(project=None, max_lines=None, today=None):
    proj = kit_config.project_dir(project)
    if max_lines is None:
        max_lines = kit_config.get("debug.max_lines", proj, 2000)
    if isinstance(max_lines, bool) or not isinstance(max_lines, int) or max_lines < 1:
        max_lines = 2000
    today = today or datetime.date.today().isoformat()
    ad = os.path.join(proj, "Claude", "logs", "archive")
    out = []
    for rel in FILES:
        r = rotate_file(os.path.join(proj, rel), ad, max_lines, today)
        if r:
            out.append(r)
    return out


def main(argv):
    project = None
    ml = None
    if "--project" in argv:
        project = argv[argv.index("--project") + 1]
    if "--max-lines" in argv:
        ml = int(argv[argv.index("--max-lines") + 1])
    res = rotate(project, ml)
    print("\n".join(res) if res else "nothing to rotate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
