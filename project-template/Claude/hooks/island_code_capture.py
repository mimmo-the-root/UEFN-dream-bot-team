#!/usr/bin/env python3
"""UserPromptSubmit hook: when the owner's message contains an island code (1234-5678-9012), save it to
Claude/docs/.island-code (only if that file is empty/missing) and tell Claude where it went. If a DIFFERENT
code is already saved, nothing is overwritten (it may be a competitor's island): Claude is told to ask.
Never prints the file content anywhere else; never fails a prompt."""
import json, os, re, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = str(data.get("prompt") or "")
    codes = list(dict.fromkeys(re.findall(r"(?<![\d-])\d{4}-\d{4}-\d{4}(?![\d-])", prompt)))
    if not codes:
        return 0
    project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    docs = os.path.join(project, "Claude", "docs")
    if not os.path.isdir(docs):
        return 0
    f = os.path.join(docs, ".island-code")
    cur = ""
    if os.path.isfile(f):
        with open(f, encoding="utf-8", errors="replace") as fh:
            cur = fh.read().strip()
    if not cur:
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(codes[0] + "\n")
        msg = ("[kit] Island code %s saved to Claude/docs/.island-code by the kit. Do NOT copy it into memory, skills "
               "or lessons; it stays only in that file." % codes[0])
    elif codes[0] != cur:
        msg = ("[kit] The message has an island code (%s) different from the one in Claude/docs/.island-code. Ask the owner "
               "whether it REPLACES that file or is another island (for example a competitor). Do not store it in memory."
               % codes[0])
    else:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    return 0

try:
    sys.exit(main())
except Exception:
    sys.exit(0)
