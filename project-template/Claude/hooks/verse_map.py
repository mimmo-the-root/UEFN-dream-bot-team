#!/usr/bin/env python3
"""verse_map.py - script-generated map of a project's Verse code: index, symbol table, component cards, wiring.
Zero AI tokens. Reads the .verse files only; writes ONLY to --out (default <project>/Claude/docs/map).

  python verse_map.py build [--project DIR] [--out DIR]    (re)generate; unchanged files keep their card
  python verse_map.py check [--project DIR] [--out DIR]    which files changed since the map was built (hash)
  python verse_map.py symbol NAME [--out DIR]              where a symbol is defined (file:line), nothing else
  python verse_map.py role FILE "TEXT" [--out DIR]         set a file's one-line role (kept across rebuilds in roles.tsv)
  python verse_map.py learn [--batch N] [--full] [--out DIR]  next N unread cards (default 12, signal-only view; --full = whole cards), never truncated
  python verse_map.py learned [--all] [--out DIR]          mark the cards of the last batch as learned (--all: every card)
Facts only: role comes from the file's "# Summary:" header, everything else from the code. Anything the code cannot
tell (level-placed device config and wiring) is NOT guessed here; it stays [I]/unknown for the coder's MCP tools.
Output: INDEX.md (read first, small), WIRING.md, symbols.tsv, cards/<file>.md, meta.json.
"""
import hashlib, json, os, re, sys, time

VERSION = 3
SKIP = {"Claude", ".git", "node_modules", "__pycache__"}
TYPE_RE = re.compile(r"^(\w+)\s*(?:<[^>]*>)*\s*:=\s*(class|struct|enum|interface|module)\b(?:\(([^)]*)\))?")
EDIT_RE = re.compile(r"^\s*@editable\s+(\w+)\s*:\s*([^=#]+?)\s*(?:=|#|$)")
VAR_RE = re.compile(r"^\s*var\s+(?:<[^>]*>\s*)?(\w+)\s*:\s*([^=#]+?)\s*(?:=|#|$)")
EVENT_RE = re.compile(r"^\s*(\w+)\s*(?:<[^>]*>)*\s*:\s*(?:event|listenable|subscribable)\s*\(")
FUNC_RE = re.compile(r"^(\s*)(\w+)((?:<\w+>)*)\s*\(.*\)\s*((?:<\w+>)*)\s*(?::\s*[^=#]+?)?\s*=")
SUB_RE = re.compile(r"([\w\.\[\]\(\)]+?)\.Subscribe\(\s*([\w\.]+)")
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
                block, k = [], n - 2
                while k >= 0 and lines[k].lstrip().startswith("#"):
                    s = lines[k].lstrip("# ").strip()
                    s = s.strip("-= ")
                    if s and not re.fullmatch(r"[-=_*#\s]+", s) and not (s.upper() == s and len(s) < 60):
                        block.insert(0, s)
                    k -= 1
                prev = " ".join(block[:2])
                cur = {"name": m.group(1), "kind": m.group(2), "parents": (m.group(3) or "").strip(), "line": n,
                       "doc": prev[:140], "editables": [], "vars": [], "events": [], "funcs": []}
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
            src = s.group(1)
            ev = re.sub(r"\(\)$", "", src.split(".")[-1])
            info["subs"].append((cur["name"], src[: -len(src.split(".")[-1]) - 1] or "?", ev, s.group(2), n))
    if not info["summary"] and info["types"] and info["types"][0]["doc"]:
        info["summary"] = "(from comment) " + info["types"][0]["doc"]
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
    more = lambda l: (" (+%d more)" % (len(l) - 15)) if len(l) > 15 else ""
    out.append("uses (files): " + (", ".join("%s(%d)" % x for x in outs[:15]) + more(outs) or "none found"))
    out.append("used by (files): " + (", ".join("%s(%d)" % x for x in ins[:15]) + more(ins) or "no reference found in project .verse files"))
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


def load_roles(outdir):
    p = os.path.join(outdir, "roles.tsv")
    out = {}
    if os.path.isfile(p):
        for ln in open(p, encoding="utf-8"):
            if "\t" in ln:
                k, v = ln.rstrip("\n").split("\t", 1)
                out[k] = v
    return out


def cmd_role(outdir, rel, text):
    roles = load_roles(outdir)
    roles[rel] = text.strip()[:160]
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "roles.tsv"), "w", encoding="utf-8").write("".join("%s\t%s\n" % kv for kv in sorted(roles.items())))
    print("role saved for %s (rebuild to refresh its card and the index)" % rel)


def cmd_build(project, outdir):
    files = list(verse_files(project))
    texts = {f: open(os.path.join(project, f), encoding="utf-8", errors="replace").read() for f in files}
    meta_p = os.path.join(outdir, "meta.json")
    meta_old = json.load(open(meta_p)) if os.path.isfile(meta_p) else {}
    old = meta_old.get("files", {}) if meta_old.get("tool") == VERSION else {}
    infos = {f: parse(f, texts[f]) for f in files}
    roles = load_roles(outdir)
    for f, i in infos.items():
        if f in roles:
            i["summary"] = roles[f]
    defined, edges = build_graph(infos, texts)
    os.makedirs(os.path.join(outdir, "cards"), exist_ok=True)
    changed = 0
    for f, i in infos.items():
        cp = os.path.join(outdir, "cards", f.replace("/", "__")[:-6] + ".md")
        if old.get(f, {}).get("sha") != i["sha"] or old.get(f, {}).get("role") != roles.get(f) or not os.path.isfile(cp):
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
    json.dump({"tool": VERSION, "built": time.strftime("%Y-%m-%d %H:%M"), "files": {f: {"sha": i["sha"], "lines": i["lines"], "role": roles.get(f)} for f, i in infos.items()}},
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


def learn_pending(outdir):
    """(first_pass, [files not learned yet]) or None when there is no map."""
    mp = os.path.join(outdir, "meta.json")
    if not os.path.isfile(mp):
        return None
    cur = json.load(open(mp))["files"]
    lp = os.path.join(outdir, "learned.json")
    seen = json.load(open(lp)).get("files", {}) if os.path.isfile(lp) else {}
    return (not os.path.isfile(lp), [f for f, v in cur.items() if seen.get(f) != v["sha"]], len(cur))


def _card_path(outdir, f):
    return os.path.join(outdir, "cards", f.replace("/", "__")[:-6] + ".md")


def _brief(text):
    """Signal-only view of a card: header, role, links, type headings, subscriptions, persistent state, pitfall comments."""
    keep, mode = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            mode = "full" if any(k in line for k in ("Pitfall", "Per-player", "Subscriptions")) else None
            keep.append(line) if (mode or line[3:].split(" ")[0] in ("class", "struct", "enum", "interface", "module")) else None
            continue
        if mode == "full" and line.strip():
            keep.append(line)
        elif line.startswith(("# ", "role:", "uses (files)", "used by", "note:", "events declared")):
            keep.append(line)
    return "\n".join(keep)


def cmd_learn(outdir, batch=12, full=False):
    """Print the next batch of cards the learning step has not read (complete, never truncated); remember the batch."""
    r = learn_pending(outdir)
    if r is None:
        print("no map yet: run build"); return
    first, todo, total = r
    print("learning: %s, %d of %d cards to read; this batch: %d" % ("FIRST PASS (whole map)" if first else "incremental", len(todo), total, min(batch, len(todo))))
    part = todo[:batch]
    json.dump({"files": part}, open(os.path.join(outdir, "learn-batch.json"), "w"))
    for f in part:
        cp = _card_path(outdir, f)
        text = open(cp, encoding="utf-8").read() if os.path.isfile(cp) else "# %s\n(no card)" % f
        print("\n=== %s ===\n%s" % (f, text if full else _brief(text)))
    if len(todo) > len(part):
        print("\n[%d more after this batch: queue proposals, run `learned`, then `learn` again]" % (len(todo) - len(part)))
    elif part:
        print("\n[last batch: queue proposals, then run `learned`]")


def cmd_learned(outdir, all_cards=False):
    """Mark as learned the cards of the last printed batch (or every card with --all)."""
    mp = os.path.join(outdir, "meta.json")
    if not os.path.isfile(mp):
        print("no map yet: run build"); return
    cur = json.load(open(mp))["files"]
    lp = os.path.join(outdir, "learned.json")
    seen = json.load(open(lp)).get("files", {}) if os.path.isfile(lp) else {}
    bp = os.path.join(outdir, "learn-batch.json")
    batch = list(cur) if all_cards else (json.load(open(bp)).get("files", []) if os.path.isfile(bp) else [])
    for f in batch:
        if f in cur:
            seen[f] = cur[f]["sha"]
    json.dump({"at": time.strftime("%Y-%m-%d %H:%M"), "files": seen}, open(lp, "w"), indent=0)
    if os.path.isfile(bp):
        os.remove(bp)
    print("learned.json updated: %d card(s) marked, %d of %d learned in total" % (len(batch), len([f for f in cur if seen.get(f) == cur[f]["sha"]]), len(cur)))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("build", "check", "symbol", "role", "learn", "learned"):
        print(__doc__); return 0
    opt = lambda k, d: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    project = os.path.abspath(opt("--project", os.getcwd()))
    outdir = os.path.abspath(opt("--out", os.path.join(project, "Claude", "docs", "map")))
    if a[0] == "build":
        cmd_build(project, outdir)
    elif a[0] == "check":
        cmd_check(project, outdir)
    elif a[0] == "learn":
        n = opt("--batch", "12")
        cmd_learn(outdir, int(n) if n.isdigit() else 12, "--full" in a)
    elif a[0] == "learned":
        cmd_learned(outdir, "--all" in a)
    elif a[0] == "role":
        cmd_role(outdir, a[1], a[2]) if len(a) > 2 else print('usage: role FILE "TEXT"')
    else:
        q = a[1].lower() if len(a) > 1 else ""
        sp = os.path.join(outdir, "symbols.tsv")
        hits = [l for l in open(sp, encoding="utf-8") if q and q in l.split("\t")[1].lower()] if os.path.isfile(sp) else []
        print("".join(hits[:25]) or "no symbol matching %r (run build?)" % q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
