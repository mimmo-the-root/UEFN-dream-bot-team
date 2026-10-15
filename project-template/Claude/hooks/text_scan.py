#!/usr/bin/env python3
"""Offline scan of publication texts for emoji, decorative Unicode and invisible characters.

Island titles, descriptions, tags, update notes and social posts read as machine-made (and can be
mangled by the platforms) when they carry emoji, fancy "bold" letters, box or arrow symbols, or
invisible characters. This script only reports; it never edits a file and sends nothing anywhere.

Plain accents (e, a, o with accents), curly quotes, dashes and the ellipsis are fine and not reported.

Usage: text_scan.py [file-or-folder ...]    (default: Claude/docs/publish/)
Prints one JSON line. Exit 0 = clean, 1 = findings, 2 = nothing to scan.
"""
import json, os, sys, unicodedata

TEXT_EXT = {".md", ".txt", ".json", ".html"}

# (first, last, category, advice)
RANGES = [
    (0x1F000, 0x1FAFF, "emoji", "remove it or say it in words"),
    (0x2600, 0x27BF, "symbol", "dingbat or pictograph: remove or write it in words"),
    (0x2B00, 0x2BFF, "symbol", "arrow or star symbol: remove it"),
    (0x2190, 0x21FF, "symbol", "arrow: write -> or use words"),
    (0x2500, 0x259F, "decoration", "box-drawing or block character: remove it"),
    (0x25A0, 0x25FF, "decoration", "geometric shape: remove it"),
    (0x2460, 0x24FF, "decoration", "circled or enclosed character: write a normal letter or number"),
    (0x1D400, 0x1D7FF, "fancy-letters", "styled letters (fake bold/italic): use normal letters"),
    (0xFF01, 0xFF5E, "fullwidth", "fullwidth form: use the normal character"),
    (0x02B0, 0x02FF, "fancy-letters", "modifier letter: use the normal letter"),
    (0x1D00, 0x1DBF, "fancy-letters", "small-cap or phonetic letter: use the normal letter"),
    (0xE000, 0xF8FF, "private-use", "private-use character: remove it"),
]
INVISIBLE = {
    0x200B: "zero-width space", 0x200C: "zero-width non-joiner", 0x200D: "zero-width joiner (glues emoji)",
    0x2060: "word joiner", 0xFEFF: "byte-order mark inside the text", 0x00AD: "soft hyphen",
    0x00A0: "non-breaking space", 0x202F: "narrow no-break space", 0x2007: "figure space",
    0x200E: "direction mark", 0x200F: "direction mark", 0x202A: "direction control", 0x202B: "direction control",
    0x202C: "direction control", 0x202D: "direction control", 0x202E: "direction control",
    0x2066: "direction control", 0x2067: "direction control", 0x2068: "direction control", 0x2069: "direction control",
    0xFE0F: "emoji variation selector", 0xFE0E: "text variation selector",
}

def classify(ch):
    cp = ord(ch)
    if cp in INVISIBLE:
        return "invisible", INVISIBLE[cp] + ": remove it"
    for a, b, cat, adv in RANGES:
        if a <= cp <= b:
            return cat, adv
    return None

def scan_text(text):
    out = []
    for ln, line in enumerate(text.splitlines(), 1):
        stacked = 0
        for col, ch in enumerate(line, 1):
            c = classify(ch)
            if c:
                stacked = 0
                out.append({"line": ln, "col": col, "char": ch if c[0] != "invisible" else "", "code": "U+%04X" % ord(ch), "kind": c[0], "advice": c[1]})
            elif unicodedata.category(ch) == "Mn":
                stacked += 1
                if stacked == 3:
                    out.append({"line": ln, "col": col, "char": "", "code": "U+%04X" % ord(ch), "kind": "zalgo", "advice": "stacked combining marks: use plain text"})
            else:
                stacked = 0
    return out

def files_under(targets):
    seen = []
    for t in targets:
        if os.path.isfile(t):
            seen.append(t)
        elif os.path.isdir(t):
            for d, _, fs in os.walk(t):
                seen += [os.path.join(d, f) for f in sorted(fs) if os.path.splitext(f)[1].lower() in TEXT_EXT]
    return seen

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    targets = args or [os.path.join(base, "Claude", "docs", "publish")]
    files = files_under(targets)
    if not files:
        print(json.dumps({"state": "nothing_to_scan", "reason": "no text files in: " + ", ".join(targets)}))
        return 2
    findings = []
    for f in files:
        try:
            text = open(f, encoding="utf-8-sig").read()
        except (OSError, UnicodeDecodeError):
            continue
        for x in scan_text(text):
            x["file"] = os.path.relpath(f, base) if f.startswith(base) else f
            findings.append(x)
    res = {"state": "found" if findings else "clean", "files": len(files), "count": len(findings), "findings": findings[:200]}
    sys.stdout.write(json.dumps(res, ensure_ascii=True) + "\n")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
