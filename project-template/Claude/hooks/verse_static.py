#!/usr/bin/env python3
"""Static check of Verse files, without the editor and without building (v1.110).

Catches the mistakes that are certain from the text alone, so a build is not wasted on them:

  error    unbalanced { } ( ) [ ]               mixed tabs and spaces in the indentation of one file
  error    @editable on a `var` declaration     the same top-level class or struct name defined in two files
  error    OnBegin / OnEnd declared without <override> in a creative_device class
  warning  Print( used outside a device class but /UnrealEngine.com/Temporary/Diagnostics is not imported
  warning  creative_device used but /Fortnite.com/Devices is not imported
  warning  Sleep( or spawn used but /Verse.org/Simulation is not imported

It does NOT prove the code compiles: a clean result here only means none of these mistakes is present. The real answer is
verse_check.py (needs the open editor). Read-only, no AI tokens.

  python Claude/hooks/verse_static.py [project folder | file.verse] [--json]     exit 1 when there is an error
"""
import json
import os
import re
import sys

SKIP_DIRS = {"Claude", ".claude", "__ExternalActors__", "__ExternalObjects__", "Saved", "Intermediate", ".git", "VerseUIKit"}


def strip(text):
    """The code with comments and string contents blanked (same length, same line breaks)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("<#", i):
            j = text.find("#>", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        elif c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append('"' + " " * max(0, j - i - 1) + ('"' if j < n and text[j] == '"' else ""))
            i = min(n, j + 1)
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_text(text, name="file"):
    """[(severity, line, message)] for one file."""
    res = []
    code = strip(text.replace("\r\n", "\n"))
    lines = code.split("\n")
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ln, l in enumerate(lines, 1):
        for ch in l:
            if ch in "([{":
                stack.append((ch, ln))
            elif ch in pairs:
                if not stack or stack[-1][0] != pairs[ch]:
                    res.append(("error", ln, "'%s' closes nothing that is open" % ch))
                    stack = []
                    break
                stack.pop()
    for ch, ln in stack[:1]:
        res.append(("error", ln, "'%s' is never closed" % ch))
    tabs = sum(1 for l in lines if re.match(r"^\t", l))
    spaces = sum(1 for l in lines if re.match(r"^ +\S", l))
    if tabs and spaces:
        res.append(("error", next(i for i, l in enumerate(lines, 1) if l.startswith("\t")), "tabs and spaces both used for indentation in this file"))
    for ln, l in enumerate(lines, 1):
        if re.match(r"^\s*@editable\b", l) and re.search(r"\bvar\b\s+\w+\s*:", l):
            res.append(("error", ln, "@editable cannot be put on a var"))
        if re.match(r"^\s*@editable\s*$", l) and ln < len(lines) and re.match(r"^\s*var\s+\w+\s*:", lines[ln]):
            res.append(("error", ln, "@editable cannot be put on a var"))
    cls = None
    for ln, l in enumerate(lines, 1):
        m = re.match(r"^(\w+)(?:<[^>]*>)*\s*:=\s*class\s*(?:<[^>]*>)?\s*\(([^)]*)\)", l)
        if m:
            cls = "creative_device" if "creative_device" in m.group(2) else None
        elif l and not l[0].isspace():
            cls = None
        if cls and re.match(r"^\s+(OnBegin|OnEnd)\s*(<[^>]*>)*\s*\(", l) and "<override>" not in l:
            res.append(("error", ln, "%s in a creative_device class needs <override>" % re.match(r"^\s+(\w+)", l).group(1)))
    if re.search(r"\bPrint\s*\(", code) and "/UnrealEngine.com/Temporary/Diagnostics" not in text and not re.search(r"\bcreative_device\b", code):  # inside a device class Print is inherited
        res.append(("warning", 1, "Print( is used but /UnrealEngine.com/Temporary/Diagnostics is not imported here"))
    if re.search(r"\bcreative_device\b", code) and "/Fortnite.com/Devices" not in text:
        res.append(("warning", 1, "creative_device is used but /Fortnite.com/Devices is not imported here"))
    if re.search(r"\b(Sleep\s*\(|spawn\s*[:{])", code) and "/Verse.org/Simulation" not in text:
        res.append(("warning", 1, "Sleep/spawn is used but /Verse.org/Simulation is not imported here"))
    return res


def top_names(text):
    code = strip(text.replace("\r\n", "\n"))
    return re.findall(r"^(\w+)(?:<[^>]*>)*\s*:=\s*(?:class|struct)\b", code, re.M)


def verse_files(target):
    if os.path.isfile(target):
        return [target]
    base = os.path.join(target, "Content") if os.path.isdir(os.path.join(target, "Content")) else target
    out = []
    for b, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        out += [os.path.join(b, f) for f in files if f.endswith(".verse")]
    return sorted(out)


def run(target):
    problems, seen = [], {}
    root = target if os.path.isdir(target) else os.path.dirname(target)
    for p in verse_files(target):
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        text = open(p, encoding="utf-8", errors="replace").read()
        for sev, ln, msg in check_text(text, rel):
            problems.append({"severity": sev, "file": rel, "line": ln, "message": msg})
        for n in top_names(text):
            if n in seen and seen[n] != rel:
                problems.append({"severity": "error", "file": rel, "line": 1, "message": "'%s' is also defined in %s" % (n, seen[n])})
            seen.setdefault(n, rel)
    return problems


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    target = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    probs = run(target)
    errs = sum(1 for p in probs if p["severity"] == "error")
    if "--json" in argv:
        print(json.dumps({"errors": errs, "warnings": len(probs) - errs, "problems": probs}, ensure_ascii=False))
    else:
        for p in probs:
            print("%s %s:%d %s" % (p["severity"].upper(), p["file"], p["line"], p["message"]))
        print("static check: %d error(s), %d warning(s) in %d file(s). Not a build: run verse_check.py for the real answer." % (errs, len(probs) - errs, len(verse_files(target))))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
