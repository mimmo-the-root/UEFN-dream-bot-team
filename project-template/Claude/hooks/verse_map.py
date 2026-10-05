#!/usr/bin/env python3
"""verse_map.py - script-generated map of a project's Verse code: index, symbol table, component cards, wiring.
Zero AI tokens. Reads the .verse files only; writes ONLY to --out (default <project>/Claude/docs/map).

  python verse_map.py build [--project DIR] [--out DIR]    (re)generate; unchanged files keep their card
  python verse_map.py check [--project DIR] [--out DIR]    which files changed since the map was built (hash)
  python verse_map.py symbol NAME [--out DIR]              where a symbol is defined (file:line), nothing else
Facts only: role comes from the file's "# Summary:" header, everything else from the code. Anything the code cannot
tell (level-placed device config and wiring) is NOT guessed here; it stays [I]/unknown for the coder's MCP tools.
Output: INDEX.md (read first, small), WIRING.md, symbols.tsv, cards/<file>.md, meta.json.
"""
import hashlib, json, os, re, sys, time

VERSION = 1
SKIP = {"Claude", ".git", "node_modules", "__pycache__"}
TYPE_RE = re.compile(r"^(\w+)\s*(?:<[^>]*>)*\s*:=\s*(class|struct|enum|interface|module)\b(?:\(([^)]*)\))?")
EDIT_RE = re.compile(r"^\s*@editable\s+(\w+)\s*:\s*([^=#]+?)\s*(?:=|#|$)")
VAR_RE = re.compile(r"^\s*var\s+(?:<[^>]*>\s*)?(\w+)\s*:\s*([^=#]+?)\s*(?:=|#|$)")
EVENT_RE = re.compile(r"^\s*(\w+)\s*(?:<[^>]*>)*\s*:\s*(?:event|listenable|subscribable)\s*\(")
FUNC_RE = re.compile(r"^(\s*)(\w+)((?:<\w+>)*)\s*\(.*\)\s*((?:<\w+>)*)\s*(?::\s*[^=#]+?)?\s*=")
SUB_RE = re.compile(r"([\w\.\[\]\(\)]+?)\.(\w+)\.Subscribe\(\s*(\w+)\s*\)")
NOTE_RE = re.compile(r"#.*\b(NOTE|WARNING|ATTENZIONE|ATTENTION|TODO|FIXME|BUG|B-\d+|CRITICAL|IMPORTANT)\b", re.I)
KW = {"if", "for", "loop", "block", "case", "else", "set", "return", "break", "spawn", "branch", "race", "sync", "rush", "defer", "using", "option", "not", "and", "or", "array", "map"}


def sha(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8", "replace")).hexdigest()[:10]


def verse_files(project):
    for base, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for f in sorted(files):
            if f.endswith(".verse"):
                yield os.path.relpath(os.path.join(base, f), project).replace("\\", "/")


def parse(rel, text):
    lines = text.splitlines()
    summary, i = [], 0
    for ln in lines[:40]:
        m = re.match(r"#\s*Summary:\s*(.*)", ln)
        if m:
            summary = [m.group(1).strip()]
        elif summary and re.match(r"#\s{2,}\S", ln):
            summary.append(ln.lstrip("# ").strip())
        elif summary:
            break
    info = {"file": rel, "lines": len(lines), "sha": sha(text), "summary": " ".join(summary), "types": [], "notes": [], "subs": [],
            "uses": {}, "persist": []}
    cur = None
    for n, ln in enumerate(lines, 1):
        if ln.strip() == "" or ln.lstrip().startswith("#"):
            if NOTE_RE.search(ln) and len(info["notes"]) < 6 and n > 20:
                info["notes"].append((n, ln.strip("# ").strip()[:110]))
            continue
        if not ln.startswith((" ", "\t")):
            m = TYPE_RE.match(ln)
            if m:
                prev = lines[n - 2].strip() if n >= 2 and lines[n - 2].lstrip().startswith("#") else ""
                cur = {"name": m.group(1), "kind": m.group(2), "parents": (m.group(3) or "").strip(), "line": n,
                       "doc": prev.lstrip("# ").strip()[:100], "editables": [], "vars": [], "events": [], "funcs": []}
                info["types"].append(cur)
            else:
                cur = None
            continue
        if cur is None:
            continue
        m = EDIT_RE.match(ln)
        if m:
            cur["editables"].append((m.group(1), m.group(2).strip(), n)); continue
        m = EVENT_RE.match(ln)
        if m:
            cur["events"].append((m.group(1), n)); continue
        m = VAR_RE.match(ln)
        if m:
            cur["vars"].append((m.group(1), m.group(2).strip(), n))
            if re.search(r"weak_map\s*\(\s*player", m.group(2)) or "persist" in m.group(2).lower():
                info["persist"].append((cur["name"], m.group(1), n))
            continue
        m = FUNC_RE.match(ln)
        if m and m.group(2) not in KW and len(m.group(1)) <= 4:
            cur["funcs"].append((m.group(2), (m.group(3) + m.group(4)).replace("><", ",").strip("<>"), n))
        for s in SUB_RE.finditer(ln):
            info["subs"].append((cur["name"], s.group(1), s.group(2), s.group(3), n))
    names = {e[0] for t in info["types"] for e in t["editables"]}
    for ln in lines:
        for m in re.finditer(r"\b(\w+)\.(\w+)\(", ln):
            if m.group(1) in names:
                info["uses"].setdefault(m.group(1), set()).add(m.group(2))
    return info


def build_graph(infos, texts):
    defined = {t["name"]: f for f, i in infos.items() for t in i["types"]}
    edges = {}
    for f, text in texts.items():
        body = re.sub(r"#.*", "", text)
        for name, owner in defined.items():
            if owner != f:
                c = len(re.findall(r"\b%s\b" % re.escape(name), body))
                if c:
                    edges[(f, owner)] = edges.get((f, owner), 0) + c
    return defined, edges


def card(info, edges):
    f = info["file"]
    out = ["# %s" % f, "", "lines %d · hash %s · built %s" % (info["lines"], info["sha"], time.strftime("%Y-%m-%d"))]
    out.append("role: %s" % (info["summary"] or "(no '# Summary:' header; unknown)"))
    outs = sorted(((b, c) for (a, b), c in edges.items() if a == f), key=lambda x: -x[1])
    ins = sorted(((a, c) for (a, b), c in edges.items() if b == f), key=lambda x: -x[1])
    out.append("uses (files): " + (", ".join("%s(%d)" % x for x in outs[:8]) or "none found"))
    out.append("used by (files): " + (", ".join("%s(%d)" % x for x in ins[:8]) or "no reference found in project .verse files"))
    for t in info["types"]:
        out += ["", "## %s `%s`%s  (line %d)" % (t["kind"], t["name"], (" : " + t["parents"]) if t["parents"] else "", t["line"])]
        if t["doc"]:
            out.append("note: " + t["doc"])
        if t["editables"]:
            out.append("@editable (%d): " % len(t["editables"]) + "; ".join("%s:%s" % (a, b) for a, b, _ in t["editables"][:40]))
        if t["events"]:
            out.append("events declared: " + ", ".join("%s@%d" % e for e in t["events"]))
        if t["vars"]:
            out.append("state vars (%d): " % len(t["vars"]) + ", ".join("%s" % v[0] for v in t["vars"][:30]) + (" ..." if len(t["vars"]) > 30 else ""))
        if t["funcs"]:
            out.append("functions (%d): " % len(t["funcs"]) + ", ".join("%s@%d%s" % (a, c, ("[" + b + "]") if b and b != "public" else "") for a, b, c in t["funcs"][:60]))
    subs = info["subs"]
    if subs:
        out += ["", "## Subscriptions (event -> handler)"] + ["- %s: %s.%s -> %s (line %d)" % s[:1] + "" if False else "- %s: %s.%s -> %s (line %d)" % s for s in subs[:50]]
    if info["uses"]:
        out += ["", "## Calls on bound devices (@editable.method)"] + ["- %s: %s" % (k, ", ".join(sorted(v)[:12])) for k, v in sorted(info["uses"].items())[:40]]
    if info["persist"]:
        out += ["", "## Per-player / persistent state"] + ["- %s.%s (line %d)" % p for p in info["persist"][:20]]
    if info["notes"]:
        out += ["", "## Pitfall comments in code"] + ["- line %d: %s" % n for n in info["notes"]]
    return "\n".join(out) + "\n"


def cmd_build(project, outdir):
    files = list(verse_files(project))
    texts = {f: open(os.path.join(project, f), encoding="utf-8", errors="replace").read() for f in files}
    meta_p = os.path.join(outdir, "meta.json")
    old = json.load(open(meta_p))["files"] if os.path.isfile(meta_p) else {}
    infos = {f: parse(f, texts[f]) for f in files}
    defined, edges = build_graph(infos, texts)
    os.makedirs(os.path.join(outdir, "cards"), exist_ok=True)
    changed = 0
    for f, i in infos.items():
        cp = os.path.join(outdir, "cards", f.replace("/", "__")[:-6] + ".md")
        if old.get(f, {}).get("sha") != i["sha"] or not os.path.isfile(cp):
            open(cp, "w", encoding="utf-8").write(card(i, edges)); changed += 1
    # symbols
    sym = []
    for f, i in infos.items():
        for t in i["types"]:
            sym.append("%s\t%s\t%s:%d\t%s" % (t["kind"], t["name"], f, t["line"], t["parents"]))
            sym += ["editable\t%s.%s\t%s:%d\t%s" % (t["name"], a, f, c, b) for a, b, c in t["editables"]]
            sym += ["event\t%s.%s\t%s:%d\t" % (t["name"], a, f, c) for a, c in t["events"]]
            sym += ["func\t%s.%s\t%s:%d\t%s" % (t["name"], a, f, c, b) for a, b, c in t["funcs"]]
            sym += ["var\t%s.%s\t%s:%d\t%s" % (t["name"], a, f, c, b) for a, b, c in t["vars"]]
    open(os.path.join(outdir, "symbols.tsv"), "w", encoding="utf-8").write("\n".join(sym) + "\n")
    # index
    tot = sum(i["lines"] for i in infos.values())
    idx = ["# Verse map - %s" % os.path.basename(os.path.abspath(project)), "",
           "built %s · %d files · %d lines · tool v%d. Read this first; open ONE card (`cards/<file>.md`) for the file you will touch; "
           "`python Claude/hooks/verse_map.py symbol NAME` finds a symbol. Stale if `check` lists the file." % (time.strftime("%Y-%m-%d"), len(infos), tot, VERSION), "",
           "| file | lines | hash | types | role |", "|---|---|---|---|---|"]
    for f, i in sorted(infos.items()):
        idx.append("| %s | %d | %s | %s | %s |" % (f, i["lines"], i["sha"], ", ".join(t["name"] for t in i["types"][:4]) + ("..." if len(i["types"]) > 4 else ""), (i["summary"] or "-")[:90]))
    indeg = {}
    for (a, b), c in edges.items():
        indeg[b] = indeg.get(b, 0) + c
    idx += ["", "Most depended-on files: " + ", ".join("%s(%d)" % x for x in sorted(indeg.items(), key=lambda x: -x[1])[:8])]
    open(os.path.join(outdir, "INDEX.md"), "w", encoding="utf-8").write("\n".join(idx) + "\n")
    # wiring
    w = ["# Wiring map (from code; level-placed wiring is not visible here)", "", "## File coupling (caller -> callee, mentions of the callee's types)", ""]
    w += ["- %s -> %s (%d)" % (a, b, c) for (a, b), c in sorted(edges.items(), key=lambda x: -x[1])[:60]]
    w += ["", "## Event subscriptions (subscriber type: source.event -> handler)", ""]
    for f, i in sorted(infos.items()):
        w += ["- %s `%s`: %s.%s -> %s (line %d)" % (f, s[0], s[1], s[2], s[3], s[4]) for s in i["subs"]]
    open(os.path.join(outdir, "WIRING.md"), "w", encoding="utf-8").write("\n".join(w) + "\n")
    json.dump({"tool": VERSION, "built": time.strftime("%Y-%m-%d %H:%M"), "files": {f: {"sha": i["sha"], "lines": i["lines"]} for f, i in infos.items()}},
              open(meta_p, "w", encoding="utf-8"), indent=1)
    print("map built: %d files, %d lines, %d symbols; %d card(s) regenerated; index ~%d tokens" % (
        len(infos), tot, len(sym), changed, os.path.getsize(os.path.join(outdir, "INDEX.md")) // 4))


def cmd_check(project, outdir):
    mp = os.path.join(outdir, "meta.json")
    if not os.path.isfile(mp):
        print("no map yet: run build"); return
    old = json.load(open(mp))["files"]
    cur = {f: sha(open(os.path.join(project, f), encoding="utf-8", errors="replace").read()) for f in verse_files(project)}
    stale = [f for f, h in cur.items() if f in old and old[f]["sha"] != h]
    new = [f for f in cur if f not in old]
    gone = [f for f in old if f not in cur]
    print("map is %s: %d changed, %d new, %d removed" % ("current" if not (stale or new or gone) else "STALE", len(stale), len(new), len(gone)))
    for tag, lst in (("changed", stale), ("new", new), ("removed", gone)):
        for f in lst[:15]:
            print("  %s %s" % (tag, f))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("build", "check", "symbol"):
        print(__doc__); return 0
    opt = lambda k, d: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    project = os.path.abspath(opt("--project", os.getcwd()))
    outdir = os.path.abspath(opt("--out", os.path.join(project, "Claude", "docs", "map")))
    if a[0] == "build":
        cmd_build(project, outdir)
    elif a[0] == "check":
        cmd_check(project, outdir)
    else:
        q = a[1].lower() if len(a) > 1 else ""
        sp = os.path.join(outdir, "symbols.tsv")
        hits = [l for l in open(sp, encoding="utf-8") if q and q in l.split("\t")[1].lower()] if os.path.isfile(sp) else []
        print("".join(hits[:25]) or "no symbol matching %r (run build?)" % q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
