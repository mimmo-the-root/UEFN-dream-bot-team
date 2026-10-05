#!/usr/bin/env python3
"""vault_check.py - read-only checks of the second brain vault. Zero AI tokens, never writes.

  python vault_check.py names  [--vault DIR]   canonical folder/index names -> what this vault really uses; duplicate-folder warnings
  python vault_check.py links  [--vault DIR]   broken [[wikilinks]] (path-style and name-style, Obsidian rules)
  python vault_check.py stats  [--vault DIR]   articles per folder, missing sections/fields, articles no index lists
  python vault_check.py dups   [--vault DIR]   possible duplicate articles (shared alias, or near-identical titles)
  python vault_check.py sections [--vault DIR]          headings of the vault CLAUDE.md with line ranges and ~tokens
  python vault_check.py section "TEXT" [--vault DIR]    print only the section(s) whose heading contains TEXT
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
    per, miss_src, miss_fm, impl, unlisted, stubs = {}, [], [], 0, [], []
    hist = cev = 0
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
        if re.search(r"^tags:.*\b(rinominato|renamed)\b", t, re.M):
            stubs.append(rel); per[top] -= 1
            continue
        if not (fk & created_keys) or not (fk & src_keys):
            miss_fm.append(rel)
        if not any(("## " + s) in t for s in src_secs):
            miss_src.append(rel)
        impl += any(("## " + s) in t for s in impl_secs)
        hist += any(("## " + s) in t for s in N["sections"]["history"])
        cev += any(("## " + s) in t for s in N["sections"]["counter_evidence"])
        if b[:-3].lower() not in idx_text.get(os.path.dirname(p), "") and rel.count("/") >= 1:
            unlisted.append(rel)
    print("articles: %d  (%s)" % (sum(per.values()), ", ".join("%s %d" % kv for kv in sorted(per.items()))))
    print("with a Verse implementation section: %d" % impl)
    print("kit format (new/updated articles only): with History %d, with Counter-evidence %d, log.md %s" % (hist, cev, "yes" if os.path.isfile(os.path.join(wiki, "log.md")) else "no"))
    print("rename stubs (redirect pages, safe to delete by hand): %d" % len(stubs))
    for label, lst in (("missing created/sources fields", miss_fm), ("without a Sources section", miss_src), ("not named in their folder index", unlisted)):
        print("%s: %d%s" % (label, len(lst), ("  e.g. " + ", ".join(lst[:3])) if lst else ""))


def _headings(lines):
    out, fence = [], False
    for i, l in enumerate(lines):
        if l.lstrip().startswith("```"):
            fence = not fence
        m = re.match(r"^(#{1,3})\s+(.*\S)", l)
        if m and not fence:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def _spans(lines):
    hs = _headings(lines)
    res = []
    for k, (i, lvl, title) in enumerate(hs):
        end = len(lines)
        for j, l2, _ in hs[k + 1:]:
            if l2 <= lvl:
                end = j; break
        res.append((i, end, lvl, title))
    return res


def cmd_sections(vault):
    lines = read(os.path.join(vault, "CLAUDE.md")).splitlines()
    for i, end, lvl, title in _spans(lines):
        if lvl <= 2:
            print("%4d-%-4d ~%4d tok  %s%s" % (i + 1, end, sum(len(x) for x in lines[i:end]) // 4, "  " * (lvl - 1), title))


def cmd_section(vault, query):
    lines = read(os.path.join(vault, "CLAUDE.md")).splitlines()
    shown = 0
    for i, end, lvl, title in _spans(lines):
        if query.lower() in title.lower() and lvl <= 3:
            print("\n".join(lines[i:end])); print(); shown += 1
            if lvl <= 2:
                break
    if not shown:
        print("No section with %r in its heading. Run `sections`." % query)


def _tokens(s):
    return {w for w in re.split(r"[^a-z]+", s.lower()) if len(w) > 3}


def cmd_dups(vault):
    arts = {}
    for p in articles(os.path.join(vault, "wiki")):
        if os.path.basename(p) in N["index_files"]:
            continue
        t = read(p)
        if re.search(r"^tags:.*\b(rinominato|renamed)\b", t, re.M):
            continue  # redirect stub left by a rename; not a duplicate
        rel = os.path.relpath(p, vault).replace("\\", "/")
        m = re.search(r"^aliases:\s*(.*?)(?=^\S|\Z)", t, re.S | re.M)
        al = [x.strip(" -\"'[]") for x in re.split(r"[\n,]", m.group(1))] if m else []
        al = [a for a in al if a]
        title = re.search(r"^#\s+(.*\S)", t, re.M)
        arts[rel] = (title.group(1) if title else os.path.basename(p)[:-3], al)
    owners = {}
    for rel, (title, al) in arts.items():
        for a in set(x.lower() for x in al + [title]):
            owners.setdefault(a, []).append(rel)
    found = []
    for a, rs in owners.items():
        if len(rs) == 2:  # 3+ files sharing a word is a generic tag/status, not a duplicate
            found.append((rs[0], rs[1], "same alias/title: " + a))
    rels = list(arts)
    for i, a in enumerate(rels):
        ta = _tokens(os.path.basename(a)[:-3])
        for b in rels[i + 1:]:
            tb = _tokens(os.path.basename(b)[:-3])
            da, db = re.findall(r"\d+", os.path.basename(a)), re.findall(r"\d+", os.path.basename(b))
            ta2, tb2 = ta - {"release", "versione", "note", "rilascio"}, tb - {"release", "versione", "note", "rilascio"}
            same_words = ta2 and ta2 == tb2 and da == db
            if (same_words or (len(ta & tb) >= 2 and len(ta & tb) / len(ta | tb) >= 0.7 and da == db)) and os.path.dirname(a) == os.path.dirname(b):
                found.append((a, b, "near-identical names"))
    print("dups: %d possible duplicate pair(s)" % len(found))
    for a, b, why in found[:15]:
        print("  %s  <->  %s   (%s)" % (a, b, why))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("names", "links", "stats", "dups", "sections", "section"):
        print(__doc__); return 0
    v = vault_path(a)
    if a[0] == "section":
        cmd_section(v, a[1] if len(a) > 1 and not a[1].startswith("--") else "")
    else:
        {"names": cmd_names, "links": cmd_links, "stats": cmd_stats, "dups": cmd_dups, "sections": cmd_sections}[a[0]](v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
