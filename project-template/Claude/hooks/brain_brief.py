#!/usr/bin/env python3
"""brain_brief.py - the second brain, wired into Claude Code. No AI tokens. Silent and harmless when the second brain is off.

  python brain_brief.py start        SessionStart hook: prints wiki/hot.md and how many raw sources wait to be ingested.
  python brain_brief.py after-edit   PostToolUse hook (Edit|Write): when a page under <vault>/wiki was just written, runs the free checks
                                     (broken links, quotes that are not in their raw file). Exit code 2 sends the problems back to Claude
                                     in the same turn, so the page is fixed before the work moves on.

The vault is $SECOND_BRAIN, else the "Second brain path" in ~/.claude/CLAUDE.md (rule 11). While that is still the placeholder, nothing happens.
Everything is best effort: a failure here never blocks a session.
"""
import json, os, re, subprocess, sys

HOME = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
CHECK = os.path.join(HOME, "skills", "second-brain-query", "scripts", "vault_check.py")


def vault():
    p = os.environ.get("SECOND_BRAIN", "")
    if not p:
        try:
            m = re.search(r"\*\*Second brain path\*\*:\s*`([^`]*)`", open(os.path.join(HOME, "CLAUDE.md"), encoding="utf-8").read())
            p = m.group(1) if m else ""
        except OSError:
            return ""
    if not p or p == "<SECOND_BRAIN_PATH>" or not os.path.isdir(p):
        return ""
    return os.path.abspath(p)


def run(*args):
    r = subprocess.run([sys.executable, CHECK, *args, "--vault", V], capture_output=True, text=True, timeout=25, errors="replace")
    return r.returncode, (r.stdout or "").strip()


def start():
    hot = run("hot")[1]
    status = run("status")[1].splitlines()
    out = ["Second brain is on: %s" % V,
           "Read order: wiki/hot.md (below) -> wiki/index.md -> the thematic wiki-index -> only then the page. Never read the vault for general coding questions."]
    if hot:
        out += ["--- wiki/hot.md ---", hot]
    else:
        out.append("(no wiki/hot.md yet: second-brain-librarian writes it, a dozen lines, after the next compile or handoff)")
    if status:
        out.append("Ingest: " + status[-1])
    print("\n".join(out))
    return 0


def after_edit():
    try:
        path = (json.load(sys.stdin).get("tool_input") or {}).get("file_path") or ""
    except ValueError:
        return 0
    if not path:
        return 0
    f, w = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.join(V, "wiki") + os.sep)
    if not f.startswith(w) or not f.endswith(".md"):
        return 0
    problems = []
    rc, o = run("quotes")
    if rc == 2:
        problems += [l for l in o.splitlines() if not l.startswith("quotes:")]
    rc, o = run("links")
    problems += [l for l in o.splitlines() if "->" in l]
    if problems:
        sys.stderr.write("Second brain checks failed after writing %s:\n%s\nFix the page now (the checks cost no tokens).\n" % (os.path.relpath(path, V), "\n".join(problems[:15])))
        return 2
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        V = vault()
        if not V or not os.path.isfile(CHECK) or mode not in ("start", "after-edit"):
            sys.exit(0)
        sys.exit(start() if mode == "start" else after_edit())
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
