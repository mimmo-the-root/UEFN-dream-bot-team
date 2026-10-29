#!/usr/bin/env python3
"""build_kit_wiki.py - turn the kit manual into a ready-made wiki for the second brain: second-brain-template/wiki/kit/.

The manual (docs/manual/*.md) is the one place the kit's own knowledge is written. This script copies it into the vault format
(frontmatter, [[wikilinks]], Related articles, Sources, a wiki-index), so that the second brain Cod reads already knows how the kit
works: the four steps, the helpers, the commands, the console, the rules. No AI, deterministic: the same manual gives the same files.

  python tool/build_kit_wiki.py          write second-brain-template/wiki/kit/
  python tool/build_kit_wiki.py --check  exit 1 if the files on disk are not what the manual would produce (used by the tests)
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "docs", "manual")
OUT = os.path.join(ROOT, "second-brain-template", "wiki", "kit")
SKIP = {"mcp-tool-reference"}          # a generated list of tools: not knowledge to read, and large
VERSION = open(os.path.join(ROOT, "project-template", "Claude", "KIT-VERSION"), encoding="utf-8").read().strip()


def title_of(text, name):
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    return m.group(1) if m else name.replace("-", " ").capitalize()


def convert(text, names):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)\n?", "", text)                      # pictures stay in the manual
    text = re.sub(r"\[([^\]]+)\]\(ch:([a-z0-9-]+)(?:#[^)]*)?\)", lambda m: "[[%s|%s]]" % (m.group(2), m.group(1)) if m.group(2) in names else m.group(1), text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def related(text, names, me):
    seen = []
    for m in re.finditer(r"\[\[([a-z0-9-]+)\|", text):
        if m.group(1) != me and m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def build():
    files = {}
    names = sorted(f[:-3] for f in os.listdir(SRC) if f.endswith(".md") and f[:-3] not in SKIP)
    titles = {}
    pages = {}
    for n in names:
        raw = open(os.path.join(SRC, n + ".md"), encoding="utf-8").read().replace("\r\n", "\n")
        titles[n] = title_of(raw, n)
        pages[n] = convert(raw, set(names))
    for n in names:
        rel = related(pages[n], names, n)
        out = "---\ntags: [kit, manual]\ncreated: kit-%s\nupdated: kit-%s\nsources: [docs/manual/%s.md]\ntype: kit\nstatus: current\n---\n" % (VERSION, VERSION, n)
        out += pages[n]
        if rel:
            out += "\n## Related articles\n" + "".join("- [[%s|%s]]\n" % (r, titles[r]) for r in rel)
        out += "\n## Sources\n- The kit manual, chapter \"%s\" (docs/manual/%s.md), kit v%s. Rebuilt on every kit release: do not edit this page, edit the manual.\n" % (titles[n], n, VERSION)
        files[n + ".md"] = out
    idx = "# Kit knowledge\n\nHow the Dream Bot Team kit works, in the kit's own words. Rebuilt from the manual on every release (kit v%s). Read `how-the-kit-thinks` first.\n\n" % VERSION
    idx += "".join("- [[%s|%s]]\n" % (n, titles[n]) for n in names)
    files["wiki-index.md"] = idx
    return files


def main():
    files = build()
    if "--check" in sys.argv:
        bad = []
        for f, t in files.items():
            p = os.path.join(OUT, f)
            if not os.path.isfile(p) or open(p, encoding="utf-8", newline="").read() != t:
                bad.append(f)
        extra = [f for f in (os.listdir(OUT) if os.path.isdir(OUT) else []) if f not in files]
        for f in bad + extra:
            print("out of date:", f)
        return 1 if bad or extra else 0
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f not in files:
            os.remove(os.path.join(OUT, f))
    for f, t in files.items():
        open(os.path.join(OUT, f), "w", encoding="utf-8", newline="").write(t)
    print("kit wiki: %d pages in %s" % (len(files) - 1, os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
