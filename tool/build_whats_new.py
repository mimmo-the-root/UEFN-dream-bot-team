#!/usr/bin/env python3
"""build_whats_new.py - builds project-template/Claude/reference/whats-new.json from CHANGELOG.md.

After an update the kit says, on the first start, what changed: "Updated to v1.116.0. Got 3 features, 2 fixes and 4 other changes."
This file is where those numbers come from (kit_sync.py reads it). One line per bullet of each `## vX.Y.Z` entry.

A bullet is a feature, a fix or an other change. Write the kind at the start of the bullet to be exact: `[feature]`, `[fix]` or `[other]`.
Without a tag the first 220 characters decide: words like fixed, works again, no longer, broken, refuses -> fix; adds, new, now, starting, support
-> feature; anything else -> other. The tag is removed from the text shown.

  python tool/build_whats_new.py            writes the file
  python tool/build_whats_new.py --check    exits 1 when the file is out of date (the test uses this)
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "project-template", "Claude", "reference", "whats-new.json")
FIX = re.compile(r"\b(fix|fixed|fixes|works again|work again|no longer|broken|bug|bugs|stopped|refuses?|wrong|corrected|failed|crash|crashed|never fired|did not|does not)\b", re.I)
FEATURE = re.compile(r"\b(adds?|added|new|now|starting|support|introduc\w+|first|can now|lets you|comes with)\b", re.I)


def kind(text):
    m = re.match(r"\s*\[(feature|fix|other)\]\s*", text, re.I)
    if m:
        return m.group(1).lower(), text[m.end():]
    head = text[:220]
    if FIX.search(head):
        return "fix", text
    if FEATURE.search(head):
        return "feature", text
    return "other", text


def lead(text):
    m = re.match(r"\*\*(.+?)\*\*", text.strip())
    s = m.group(1) if m else re.split(r"(?<=[.!?])\s", text.strip(), 1)[0]
    return re.sub(r"\s+", " ", s).strip(" .")[:110]


def build(log):
    out = {}
    for m in re.finditer(r"^## v([\d.]+)\s+[—-]\s+(.*?)\n(.*?)(?=^## v|\Z)", log, re.M | re.S):
        ver, title, body = m.group(1), m.group(2).strip(), m.group(3)
        n = {"feature": 0, "fix": 0, "other": 0}
        heads = []
        for l in body.split("\n"):
            if l.startswith("- "):
                k, t = kind(l[2:])
                n[k] += 1
                if len(heads) < 4:
                    heads.append(lead(t))
        out[ver] = {"title": title, "features": n["feature"], "fixes": n["fix"], "other": n["other"], "headlines": heads}
    return {"note": "Built by tool/build_whats_new.py from CHANGELOG.md; do not edit by hand.", "versions": out}


def main():
    data = build(open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read())
    text = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=False) + "\n"
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if cur != text:
            print("whats-new.json is out of date: run python tool/build_whats_new.py")
            return 1
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("whats-new.json: %d versions" % len(data["versions"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
