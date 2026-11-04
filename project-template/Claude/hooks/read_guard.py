#!/usr/bin/env python3
"""read_guard.py - PreToolUse hook on Read: a whole-file read of a big document is refused and answered with its outline instead.
No AI, no network. A rule in a skill is a request; this is a key.

What it refuses: a Read with no offset and no limit of a .md .txt .json .jsonl .log .csv file bigger than 40 KB
(UEFN_KIT_READ_KB changes the size). What it answers: the headings of a markdown file with their line numbers, the keys of a
json file, or the first lines of anything else, and how to read one part (offset and limit).
Never refused: CLAUDE.md, SKILL.md, code files, small files, and any Read that already has an offset or a limit.
Switch off with UEFN_KIT_READ_GUARD=0. Never fails loudly: any error allows the read."""
import json, os, re, sys

DOC_EXT = (".md", ".txt", ".json", ".jsonl", ".log", ".csv")
ALWAYS = ("claude.md", "skill.md", "kit-version")


def outline(path, text):
    lines = text.split("\n")
    name = path.lower()
    if name.endswith(".md"):
        heads = ["%d: %s" % (i + 1, l.strip()[:90]) for i, l in enumerate(lines) if re.match(r"^#{1,3}\s", l)]
        if heads:
            return "Headings (line: text):\n" + "\n".join(heads[:60]) + ("\n... %d more" % (len(heads) - 60) if len(heads) > 60 else "")
    if name.endswith(".json"):
        try:
            d = json.loads(text)
            if isinstance(d, dict):
                return "Top-level keys: " + ", ".join("%s (%s)" % (k, type(v).__name__) for k, v in list(d.items())[:40])
            if isinstance(d, list):
                return "A list of %d items; read a slice." % len(d)
        except ValueError:
            pass
    return "First lines:\n" + "\n".join(l[:120] for l in lines[:8])


def verdict(ti):
    """Returns '' to allow, or the reason to refuse."""
    path = str(ti.get("file_path") or "")
    if not path or ti.get("offset") not in (None, "", 0) or ti.get("limit") not in (None, ""):
        return ""
    low = path.lower().replace("\\", "/")
    if not low.endswith(DOC_EXT) or os.path.basename(low) in ALWAYS or "/.claude/projects/" in low:
        return ""
    try:
        limit = int(float(os.environ.get("UEFN_KIT_READ_KB", "40")) * 1024)
        size = os.path.getsize(path)
        if size <= limit:
            return ""
        text = open(path, encoding="utf-8", errors="replace").read()
    except (OSError, ValueError):
        return ""
    n = text.count("\n") + 1
    return ("Refused by the kit: %s is %d KB (%d lines); reading all of it spends tokens you do not need. %s\n"
            "Find the part with Grep (the heading or a word), then Read with offset and limit (for example offset the heading line, limit 80). "
            "Read it whole only if the task needs all of it, and then ask the owner. Do not work around this refusal."
            % (os.path.basename(path), size // 1024, n, outline(path, text)))


def main():
    try:
        if os.environ.get("UEFN_KIT_READ_GUARD") == "0":
            return 0
        p = json.loads(sys.stdin.read() or "{}")
        why = verdict(p.get("tool_input") or {})
        if why:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
