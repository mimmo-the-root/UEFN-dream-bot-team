#!/usr/bin/env python3
"""vault_check.py - read-only checks of the second brain vault. Zero AI tokens, never writes.

  python vault_check.py names  [--vault DIR]   canonical folder/index names -> what this vault really uses; duplicate-folder warnings
  python vault_check.py links  [--vault DIR]   broken [[wikilinks]] (path-style and name-style, Obsidian rules)
  python vault_check.py stats  [--vault DIR]   articles per folder, missing sections/fields, articles no index lists
The vault is --vault, else $SECOND_BRAIN, else the "Second brain path" in ~/.claude/CLAUDE.md. Names come from names.json
(English canonical + Italian synonyms), so a vault that mixes both languages is handled as it is.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
N = json.load(open(os.path.join(HERE, "..", "names.json"), encoding="utf-8"))
LINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
MAXLINES = int(os.environ.get("VAULT_CHECK_MAX", "40"))


def vault_path(argv):
    if "--vault" in argv:
        return argv[argv.index("--vault") + 1]
    if os.environ.get("SECOND_BRAIN"):
        return os.environ["SECOND_BRAIN"]
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    try:
        m = re.search(r"\*\*Second brain path\*\*:\s*`([^`]*)`", open(os.path.join(home, "CLAUDE.md"), encoding="utf-8").read())
    except OSError:
        m = None
    if m and m.group(1) != "<SECOND_BRAIN_PATH>":
        return m.group(1)
    sys.exit("No vault: pass --vault DIR (rule 11 in ~/.claude/CLAUDE.md still has the placeholder).")


def articles(vault):
    for base, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("Clippings", "lilbee", "raw")]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(base, f)


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def frontmatter_keys(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---", text, re.S)
    return set(re.findall(r"^([A-Za-z_][\w-]*):", m.group(1), re.M)) if m else set()


def cmd_names(vault):
    wiki = os.path.join(vault, "wiki")
    have = set(os.listdir(wiki)) if os.path.isdir(wiki) else set()
    for canon, alts in N["folders"].items():
        found = [a for a in alts if a in have]
        if len(found) > 1:
            print("WARN  duplicate folders for %s: %s (merge them; never write to both)" % (canon, ", ".join(found)))
        elif found:
            print("ok    %-20s -> wiki/%s%s" % (canon, found[0], "" if found[0] == canon else "   (Italian name; use as is)"))
        else:
            print("--    %-20s not present" % canon)
    idx = {}
    for d in sorted(have) + ["."]:
        p = os.path.join(wiki, d)
        if os.path.isdir(p):
            fs = [f for f in N["index_files"] if os.path.isfile(os.path.join(p, f))]
            if fs:
                idx[d] = fs
    for d, fs in idx.items():
        print("index wiki/%s: %s%s" % (d, ", ".join(fs), "   WARN more than one index" if len(fs) > 1 else ""))


def cmd_links(vault):
    files = [f for f in articles(vault) if os.path.relpath(f, vault).replace("\\", "/").split("/")[0] in ("wiki", "output")]
    keys = {}
    allf = list(articles(vault))
    for p in allf:
        rel = os.path.relpath(p, vault).replace("\\", "/")[:-3].lower()
        keys[rel] = p
    bad = []
    for p in files:
        for m in LINK.finditer(read(p)):
            t = m.group(1).strip().replace("\\", "/")
            if re.search(r"\.(png|jpe?g|gif|webp|pdf|svg)$", t, re.I):
                continue
            t = t[:-3] if t.lower().endswith(".md") else t
            if t.startswith(("./", "../")):
                cand = os.path.normpath(os.path.join(os.path.dirname(os.path.relpath(p, vault)), t)).replace("\\", "/").lower()
                ok = cand in keys
            else:
                tl = t.lower().lstrip("/")
                ok = tl in keys or any(k == tl or k.endswith("/" + tl) for k in keys)
            if not ok:
                bad.append((os.path.relpath(p, vault).replace("\\", "/"), t))
    print("links: %d article file(s), %d broken link(s)" % (len(files), len(bad)))
    for f, t in bad[:MAXLINES]:
        print("  %s -> [[%s]]" % (f, t))
    if len(bad) > MAXLINES:
        print("  ... %d more" % (len(bad) - MAXLINES))


def cmd_stats(vault):
    wiki = os.path.join(vault, "wiki")
    per, miss_src, miss_fm, impl, unlisted = {}, [], [], 0, []
    created_keys = set(N["frontmatter"]["created"]); src_keys = set(N["frontmatter"]["sources"])
    src_secs = N["sections"]["sources"]; impl_secs = N["sections"]["verse_implementation"]
    idx_text = {}
    for p in articles(wiki):
        if os.path.basename(p) in N["index_files"]:
            idx_text[os.path.dirname(p)] = idx_text.get(os.path.dirname(p), "") + read(p).lower()
    for p in articles(wiki):
        b = os.path.basename(p)
        if b in N["index_files"]:
            continue
        rel = os.path.relpath(p, wiki).replace("\\", "/")
        top = rel.split("/")[0] if "/" in rel else "."
        per[top] = per.get(top, 0) + 1
        t = read(p); fk = frontmatter_keys(t)
        if not (fk & created_keys) or not (fk & src_keys):
            miss_fm.append(rel)
        if not any(("## " + s) in t for s in src_secs):
            miss_src.append(rel)
        impl += any(("## " + s) in t for s in impl_secs)
        if b[:-3].lower() not in idx_text.get(os.path.dirname(p), "") and rel.count("/") >= 1:
            unlisted.append(rel)
    print("articles: %d  (%s)" % (sum(per.values()), ", ".join("%s %d" % kv for kv in sorted(per.items()))))
    print("with a Verse implementation section: %d" % impl)
    for label, lst in (("missing created/sources fields", miss_fm), ("without a Sources section", miss_src), ("not named in their folder index", unlisted)):
        print("%s: %d%s" % (label, len(lst), ("  e.g. " + ", ".join(lst[:3])) if lst else ""))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("names", "links", "stats"):
        print(__doc__); return 0
    v = vault_path(a)
    {"names": cmd_names, "links": cmd_links, "stats": cmd_stats}[a[0]](v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
