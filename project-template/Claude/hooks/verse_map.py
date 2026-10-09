#!/usr/bin/env python3
"""verse_map.py - script-generated map of a project's Verse code: index, symbol table, component cards, wiring.
Zero AI tokens. Reads the .verse files only; writes ONLY to --out (default <project>/Claude/docs/map).

  python verse_map.py build [--project DIR] [--out DIR]    (re)generate; unchanged files keep their card
  python verse_map.py check [--project DIR] [--out DIR]    which files changed since the map was built (hash)
  python verse_map.py symbol NAME [--out DIR]              where a symbol is defined (file:line), nothing else
  python verse_map.py role FILE "TEXT" [--out DIR]         set a file's one-line role (kept across rebuilds in roles.tsv)
  python verse_map.py learn [--cap N] [--full] [--cards-only]  next batch: brief card + COMPLETE source of each unread file (default 60k chars); ends with a receipt token
  python verse_map.py learned TOKEN                        mark the batch as learned; refuses any token but the one printed at the END of the batch (--all: every file)
  python verse_map.py docs [--project DIR]                 next project documents not read yet (complete) + names they mention that the code map does not know
  python verse_map.py docpatch list | apply ID... | apply --all | revert STAMP   check/apply/undo the reverse-engineered corrections in map/doc-patches.json (exact text, backup)
  python verse_map.py status [--project DIR]               what is learned and what is missing (also written to map/PROGRESS.md)
  python verse_map.py docsdone TOKEN [--project DIR]       mark the documents of the last batch as read (needs the receipt token at the batch end)
Facts only: role comes from the file's "# Summary:" header, everything else from the code. Anything the code cannot
tell (level-placed device config and wiring) is NOT guessed here; it stays [I]/unknown for the coder's MCP tools.
Output: INDEX.md (read first, small), WIRING.md, symbols.tsv, cards/<file>.md, meta.json.
"""
import hashlib, json, os, re, shutil, sys, time

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


DEPTH = "source"  # what a learning pass reads: the full source of each file (+ its brief card). "cards" = cards only (cheap mode)
LEARN_CAP = 60000  # characters per batch (a single longer file is printed alone, complete)


def _read_state(path):
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def learn_pending(outdir, depth=DEPTH):
    """(first_pass, [files not learned yet at this depth], total) or None when there is no map."""
    mp = os.path.join(outdir, "meta.json")
    if not os.path.isfile(mp):
        return None
    cur = json.load(open(mp))["files"]
    st = _read_state(os.path.join(outdir, "learned.json"))
    # a pass that only saw the cards does not count as having read the sources
    seen = st.get("files", {}) if (st.get("depth", "cards") == "source" or depth == "cards") else {}
    return (not st, [f for f, v in cur.items() if seen.get(f) != v["sha"]], len(cur))


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


def _receipt(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:6]


def cmd_learn(project, outdir, cap=LEARN_CAP, full=False, cards_only=False):
    """Print the next batch (brief card + complete source of each file) and a receipt token that only the COMPLETE output contains.
    `learned TOKEN` is the only way to mark the batch: a truncated read cannot know the token."""
    depth = "cards" if cards_only else DEPTH
    r = learn_pending(outdir, depth)
    if r is None:
        print("no map yet: run build"); return
    first, todo, total = r
    print("learning (%s): %s, %d of %d files to read" % ("full source" if depth == "source" else "cards only", "FIRST PASS (whole project)" if first else "incremental", len(todo), total))
    out, part, used = [], [], 0
    for f in todo:
        cp = _card_path(outdir, f)
        card = open(cp, encoding="utf-8").read() if os.path.isfile(cp) else "# %s\n(no card)" % f
        body = "=== %s ===\n%s\n" % (f, card if full else _brief(card))
        if depth == "source":
            try:
                body += "--- source ---\n" + open(os.path.join(project, f), encoding="utf-8", errors="replace").read() + "\n--- end of %s ---\n" % f
            except OSError:
                body += "(source not readable)\n"
        if part and used + len(body) > cap:
            break
        part.append(f); out.append(body); used += len(body)
    text = "\n".join(out)
    tok = _receipt(text)
    print("this batch: %d file(s), %d characters\n" % (len(part), len(text)))
    print(text)
    json.dump({"files": part, "token": tok, "depth": depth}, open(os.path.join(outdir, "learn-batch.json"), "w"))
    print("[END OF BATCH. Receipt token: %s. After queueing the proposals run `learned %s`; it refuses any other token, so a cut-off read cannot be marked.]" % (tok, tok))
    if len(todo) > len(part):
        print("[%d more file(s) after this batch: `learned`, then `learn` again]" % (len(todo) - len(part)))


def cmd_learned(project, outdir, token="", all_cards=False):
    """Mark the files of the last printed batch as learned; needs the batch's receipt token (or --all)."""
    mp = os.path.join(outdir, "meta.json")
    if not os.path.isfile(mp):
        print("no map yet: run build"); return 1
    cur = json.load(open(mp))["files"]
    lp, bp = os.path.join(outdir, "learned.json"), os.path.join(outdir, "learn-batch.json")
    st = _read_state(lp)
    bt = _read_state(bp)
    if not all_cards and (not bt or token != bt.get("token")):
        print("REFUSED: pass the receipt token printed at the END of the batch (`learned <token>`). If you did not see it, the output was cut: run `learn` again and read it complete.")
        return 1
    depth = "source" if all_cards else bt.get("depth", DEPTH)
    seen = st.get("files", {}) if st.get("depth", "cards") == depth else {}
    batch = list(cur) if all_cards else bt.get("files", [])
    for f in batch:
        if f in cur:
            seen[f] = cur[f]["sha"]
    json.dump({"at": time.strftime("%Y-%m-%d %H:%M"), "depth": depth, "files": seen}, open(lp, "w"), indent=0)
    if os.path.isfile(bp):
        os.remove(bp)
    print("learned.json updated: %d file(s) marked, %d of %d learned in total (%s)" % (len(batch), len([f for f in cur if seen.get(f) == cur[f]["sha"]]), len(cur), depth))
    write_progress(project, outdir)
    return 0


DOC_SKIP = ("STATUS.md", "BUGS.md", "ROADMAP.md")  # task trackers: planner-docs owns them and they change every session
DOCS_VERSION = 2  # bump to make every document be read again (v2: design decisions for the starter sections)
STALE_RE = re.compile(r"\b(draft|bozza|proposed|proposal|planned|todo|to do|not implemented|non implementat\w*|nessun codice|no code|da fare|wip|in progress|in corso)\b", re.I)
DOC_CAP = 40000  # characters per batch (a single longer doc is printed alone, complete)


def project_docs(project):
    """Documentation worth learning from: Claude/docs/*.md (not the trackers) and Claude/logs/PLAYTEST-*.md."""
    out = []
    for sub, pat in (("Claude/docs", lambda n: n.endswith(".md") and n not in DOC_SKIP), ("Claude/logs", lambda n: n.startswith("PLAYTEST") and n.endswith(".md"))):
        base = os.path.join(project, *sub.split("/"))
        for n in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if pat(n) and os.path.isfile(os.path.join(base, n)):
                out.append(sub + "/" + n)
    return out


def _doc_sha(project, rel):
    return sha(open(os.path.join(project, rel), encoding="utf-8", errors="replace").read())


def docs_pending(project, outdir):
    lp = os.path.join(outdir, "docs-learned.json")
    st = _read_state(lp)
    seen = st.get("files", {}) if st.get("v", 1) == DOCS_VERSION else {}
    return (not st, [r for r in project_docs(project) if seen.get(r) != _doc_sha(project, r)])


def _known_names(outdir):
    names = set()
    sp = os.path.join(outdir, "symbols.tsv")
    if os.path.isfile(sp):
        for l in open(sp, encoding="utf-8"):
            parts = l.rstrip("\n").split("\t")
            names.update(re.findall(r"[A-Za-z_][\w]*", " ".join(parts[:3])))
    mp = os.path.join(outdir, "meta.json")
    if os.path.isfile(mp):
        for f in json.load(open(mp))["files"]:
            names.add(os.path.basename(f).lower())
    return names


def _drift(text, known):
    """Possible drift: .verse files and `identifiers` the document mentions that the code map does not know (heuristic, facts to confirm)."""
    miss = []
    for f in re.findall(r"([\w\-]+\.verse)", text):
        if f.lower() not in known and f not in miss:
            miss.append(f)
    for ident in re.findall(r"`([A-Za-z_][\w]{3,})`", text):
        if (("_" in ident or (ident != ident.lower() and ident != ident.upper())) and ident not in known and ident not in miss):
            miss.append(ident)
    return miss


def cmd_docs(project, outdir, cap=DOC_CAP):
    """Next batch of project documents not read yet (complete, never truncated) + names they mention that the code map does not know."""
    first, todo = docs_pending(project, outdir)
    print("docs: %s, %d to read" % ("FIRST PASS (all documentation)" if first else "incremental", len(todo)))
    known, used, part, out = _known_names(outdir), 0, [], []
    for rel in todo:
        text = open(os.path.join(project, rel), encoding="utf-8", errors="replace").read()
        if part and used + len(text) > cap:
            break
        part.append(rel); used += len(text)
        miss = _drift(text, known)
        stale = sorted(set(m.group(0).lower() for m in STALE_RE.finditer(text)))
        out.append("=== %s ===\n%s\n[possible drift vs code map: %s]\n[status words to verify against the code: %s]\n" % (rel, text, (", ".join(miss[:15]) + (" (+%d more)" % (len(miss) - 15) if len(miss) > 15 else "")) if miss else "none found", ", ".join(stale[:12]) if stale else "none"))
    body = "\n".join(out)
    tok = _receipt(body)
    print(body)
    os.makedirs(outdir, exist_ok=True)
    json.dump({"files": part, "token": tok}, open(os.path.join(outdir, "docs-batch.json"), "w"))
    if part:
        print("[END OF BATCH. Receipt token: %s. After processing run `docsdone %s`; it refuses any other token.]" % (tok, tok))
    if len(todo) > len(part):
        print("[%d more document(s): `docsdone`, then `docs` again]" % (len(todo) - len(part)))


def cmd_docsdone(project, outdir, token="", all_docs=False):
    lp, bp = os.path.join(outdir, "docs-learned.json"), os.path.join(outdir, "docs-batch.json")
    bt = _read_state(bp)
    if not all_docs and (not bt or token != bt.get("token")):
        print("REFUSED: pass the receipt token printed at the END of the batch (`docsdone <token>`). If you did not see it, the output was cut: run `docs` again and read it complete.")
        return 1
    st0 = _read_state(lp)
    seen = st0.get("files", {}) if st0.get("v", 1) == DOCS_VERSION else {}
    batch = project_docs(project) if all_docs else bt.get("files", [])
    if not all_docs:
        ps, rv = _patches(outdir), _read_state(os.path.join(outdir, PATCH_FILE)).get("reviewed", [])
        reviewed = {str(r.get("file", "")).replace("\\", "/") for r in rv if str(r.get("note", "")).strip()}
        undecided = [r for r in batch if not any(str(p.get("file", "")).replace("\\", "/") == r and p.get("status") == "applied" for p in ps) and r not in reviewed]
        unapplied = [p.get("id", "?") for p in ps if str(p.get("file", "")).replace("\\", "/") in batch and p.get("status") != "applied"]
        if unapplied:
            print("REFUSED: correction(s) not applied yet: %s. Run `docpatch list`, fix invalid ones, then `docpatch apply --all`." % ", ".join(unapplied)); return 1
        if undecided:
            print("REFUSED: no decision recorded for: %s. For each document either write the corrections (doc-patches.json `patches`, then `docpatch apply --all`) or, when you compared it with the code and it is accurate, add `{\"file\": \"<path>\", \"note\": \"what you verified\"}` to `reviewed` in doc-patches.json. Documents are never left stale by skipping." % ", ".join(undecided)); return 1
        if os.path.isfile(os.path.join(outdir, PATCH_FILE)):  # reviews are valid for this version of the document only
            d = _read_state(os.path.join(outdir, PATCH_FILE)); d["reviewed"] = [r for r in rv if str(r.get("file", "")).replace("\\", "/") not in batch]
            json.dump(d, open(os.path.join(outdir, PATCH_FILE), "w"), indent=1)
    for rel in batch:
        if os.path.isfile(os.path.join(project, rel)):
            seen[rel] = _doc_sha(project, rel)
    os.makedirs(outdir, exist_ok=True)
    json.dump({"at": time.strftime("%Y-%m-%d %H:%M"), "v": DOCS_VERSION, "files": seen}, open(lp, "w"), indent=0)
    if os.path.isfile(bp):
        os.remove(bp)
    print("docs-learned.json updated: %d document(s) marked, %d of %d read in total" % (len(batch), sum(1 for r in project_docs(project) if r in seen), len(project_docs(project))))
    write_progress(project, outdir)
    return 0


PATCH_FILE = "doc-patches.json"


def _patches(outdir):
    return _read_state(os.path.join(outdir, PATCH_FILE)).get("patches", [])


def _patch_state(project, p):
    """pending | applied | invalid (find text missing or not unique, or file outside the documentation)."""
    if p.get("status") == "applied":
        return "applied"
    rel = str(p.get("file", "")).replace("\\", "/")
    if rel not in project_docs(project):
        return "invalid: not a project document"
    text = open(os.path.join(project, rel), encoding="utf-8", errors="replace").read()
    n = text.count(p.get("find", "")) if p.get("find") else 0
    return "pending" if n == 1 else "invalid: find text occurs %d times (needs exactly 1)" % n


def cmd_docpatch(project, outdir, args):
    """Reverse-engineered corrections to the documents: the coder writes them to doc-patches.json ({id, file, find, replace, reason, source});
    this checks and applies them with exact text matching and a backup. Zero tokens, nothing is applied without the owner's go."""
    sub = args[0] if args else "list"
    pp = os.path.join(outdir, PATCH_FILE)
    st = _read_state(pp)
    ps = st.get("patches", [])
    if sub == "list":
        pend = 0
        for p in ps:
            state = _patch_state(project, p)
            pend += state == "pending"
            print("[%s] %s  %s  (%s)\n    reason: %s\n    source: %s" % (state, p.get("id"), p.get("file"), (p.get("find", "")[:60] + "...").replace("\n", " "), p.get("reason", ""), p.get("source", "")))
        print("%d patch(es), %d ready to apply" % (len(ps), pend)); return 0
    if sub == "apply":
        want = [a for a in args[1:] if not a.startswith("--")]
        done = 0
        stamp = time.strftime("%Y%m%d-%H%M%S")
        for p in ps:
            if "--all" not in args and p.get("id") not in want:
                continue
            state = _patch_state(project, p)
            if state != "pending":
                print("skipped %s: %s" % (p.get("id"), state)); continue
            rel = p["file"].replace("\\", "/")
            full = os.path.join(project, rel)
            text = open(full, encoding="utf-8", errors="replace").read()
            bdst = os.path.join(project, "Claude", "logs", "doc-backup", stamp, *rel.split("/"))
            os.makedirs(os.path.dirname(bdst), exist_ok=True)
            shutil.copy2(full, bdst)
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(text.replace(p["find"], p.get("replace", ""), 1))
            p["status"] = "applied"; p["applied"] = stamp; done += 1
            print("applied %s -> %s (backup in Claude/logs/doc-backup/%s)" % (p["id"], rel, stamp))
        st["patches"] = ps
        json.dump(st, open(pp, "w"), indent=1)
        print("%d patch(es) applied" % done)
        write_progress(project, outdir)
        return 0
    if sub == "revert":
        r = cmd_docrevert(project, outdir, args[1] if len(args) > 1 else "")
        write_progress(project, outdir)
        return r
    print("usage: docpatch list | apply ID... | apply --all | revert STAMP"); return 1


def progress_lines(project, outdir):
    """What is done and what is missing, from the state files only (zero tokens)."""
    out = []
    lr = learn_pending(outdir)
    if lr is None:
        return ["code: no map yet (it is built at session start when the project has more than 5 Verse files)"]
    first, todo, total = lr
    out.append("code: %d of %d Verse files learned from their complete source%s" % (total - len(todo), total, "" if not todo else " (%d left, about %d batch(es))" % (len(todo), max(1, len(todo) * 18000 // LEARN_CAP + 1))))
    dfirst, dtodo = docs_pending(project, outdir)
    nd = len(project_docs(project))
    out.append("documents: %d of %d read%s" % (nd - len(dtodo), nd, "" if not dtodo else " (%d left)" % len(dtodo)))
    ps = _patches(outdir)
    states = [_patch_state(project, p) for p in ps]
    out.append("document corrections: %d applied, %d ready to apply, %d invalid" % (states.count("applied"), states.count("pending"), sum(1 for x in states if x.startswith("invalid"))))
    dev = os.path.join(outdir, "DEVICES.md")
    if os.path.isfile(dev):
        t = open(dev, encoding="utf-8", errors="replace").read()
        out.append("devices: DEVICES.md of %s; wiring read: %s; settings read: %s" % (time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(dev))),
                   "yes" if re.search(r"WIRING-READ:\s*yes", t, re.I) else "NO", "yes" if re.search(r"SETTINGS-READ:\s*yes", t, re.I) else "NO"))
    else:
        out.append("devices: never read from the level (DEVICES.md missing)")
    return out


def write_progress(project, outdir):
    try:
        lines = progress_lines(project, outdir)
        open(os.path.join(outdir, "PROGRESS.md"), "w", encoding="utf-8").write(
            "# Learning progress (generated, zero tokens; %s)\n\nWhat is done and what is missing. The next session start continues automatically.\n\n%s\n" % (
                time.strftime("%Y-%m-%d %H:%M"), "\n".join("- " + l for l in lines)))
    except Exception:
        pass


def cmd_docrevert(project, outdir, stamp):
    bk = os.path.join(project, "Claude", "logs", "doc-backup", stamp)
    if not os.path.isdir(bk):
        print("no backup %s (see Claude/logs/doc-backup/)" % stamp); return 1
    n = 0
    for base, _, files in os.walk(bk):
        for f in files:
            src = os.path.join(base, f)
            rel = os.path.relpath(src, bk).replace(os.sep, "/")
            if rel in project_docs(project):
                shutil.copyfile(src, os.path.join(project, *rel.split("/"))); n += 1
    pp = os.path.join(outdir, PATCH_FILE)
    st = _read_state(pp)
    for p in st.get("patches", []):
        if p.get("applied") == stamp:
            p["status"] = "reverted"
    json.dump(st, open(pp, "w"), indent=1)
    print("%d document(s) restored from backup %s" % (n, stamp)); return 0


def _utf8_out():
    """Windows pipes default to cp1252: a document with an arrow or a typographic dash would crash `docs`/`learn`. Always print UTF-8."""
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    _utf8_out()
    a = sys.argv[1:]
    if not a or a[0] not in ("build", "check", "symbol", "role", "learn", "learned", "docs", "docsdone", "docpatch", "status"):
        print(__doc__); return 0
    tok = a[1] if len(a) > 1 and not a[1].startswith("--") else ""
    opt = lambda k, d: a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else d
    project = os.path.abspath(opt("--project", os.getcwd()))
    outdir = os.path.abspath(opt("--out", os.path.join(project, "Claude", "docs", "map")))
    if a[0] == "build":
        cmd_build(project, outdir)
    elif a[0] == "check":
        cmd_check(project, outdir)
    elif a[0] == "learn":
        n = opt("--cap", str(LEARN_CAP))
        cmd_learn(project, outdir, int(n) if n.isdigit() else LEARN_CAP, "--full" in a, "--cards-only" in a)
    elif a[0] == "status":
        write_progress(project, outdir)
        print("\n".join(progress_lines(project, outdir)))
    elif a[0] == "docpatch":
        return cmd_docpatch(project, outdir, a[1:])
    elif a[0] == "docs":
        cmd_docs(project, outdir)
    elif a[0] == "docsdone":
        return cmd_docsdone(project, outdir, tok, "--all" in a)
    elif a[0] == "learned":
        return cmd_learned(project, outdir, tok, "--all" in a)
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
