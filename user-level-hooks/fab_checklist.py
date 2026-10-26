#!/usr/bin/env python3
"""Fab checklist (v1.110): every check the kit can do on a Fab product, grouped in six stations, for the console "Checklist" page.

Lives in ~/.claude/hooks, next to fab_pack.py and fab_assets.py. Writes only in the lab folder (~/.claude/fab-lab/<Product>/), never in the project.

  fab_checklist.py [project folder]        print the verdict and the items that are not green
  fab_checklist.py tags                    the tags the portal suggests, by category (choose the listing tags only among these)

Data: build(root, lab) -> {name, stations:[{id, n, d, items:[{id, t, s, w, ev, fix}]}], counts, pct, verdict, message, listing, validation}
Item state s: pass | fail | warn | todo | manual | na.  Who w: kit (done by the kit) | ed (needs a record from UEFN) | you | x (added after a rejection).
Items that only the owner can judge are "manual" until he ticks them (lab/confirm.json); the UEFN validation is "fail" until a clean log is recorded.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fab_pack  # noqa: E402

GENERIC_TAGS = {"game", "system", "tool", "tools", "asset", "assets", "pack", "fortnite", "uefn", "verse", "map", "kit"}


# ---- small helpers -------------------------------------------------------------

def _read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _jload(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _jsave(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def _item(i, t, s, w, ev="", fix=""):
    return {"id": i, "t": t, "s": s, "w": w, "ev": ev, "fix": fix}


def _by(strs, pat):
    r = re.compile(pat, re.I)
    return [x for x in strs if r.search(x)]


def _short(lst, n=2):
    return "; ".join(lst[:n]) + (" (+%d more)" % (len(lst) - n) if len(lst) > n else "")


def _verdict_item(i, t, w, blocks, warns, ok_ev, pat, fix=""):
    """pass/fail/warn from the strings the pack check gave for one rule."""
    b, wn = _by(blocks, pat), _by(warns, pat)
    if b:
        return _item(i, t, "fail", w, _short(b), fix)
    if wn:
        return _item(i, t, "warn", w, _short(wn), fix)
    return _item(i, t, "pass", w, ok_ev)


# ---- listing (FabListing/listing.md) -------------------------------------------

def listing_path(root):
    base = fab_pack.product_folder(root)
    for p in (os.path.join(base, "FabListing", "listing.md"), os.path.join(root, "FabListing", "listing.md")):
        if os.path.isfile(p):
            return p
    return ""


TECH_FIELDS = [("Modular / extensible", "yes or no"), ("Includes UI components", "yes or no"), ("Network integration ready", "yes or no"), ("AI features", "yes or no"),
               ("Code framework", "Blueprint, C++ or Other (Verse is Other)"), ("Projects", "a number"), ("C++ classes", "a number (0 for Verse)"),
               ("Input methods", "any of Gamepad, Keyboard, Mouse, Other")]


def tech_fields(root):
    """(missing_or_todo field names, suggestions) for the portal's Technical details of a UEFN Source product."""
    text = _read(listing_path(root))
    m = re.search(r"^##\s+Technical details\s*\n(.*?)(?=^##\s|\Z)", text, re.I | re.M | re.S)
    sec = m.group(1) if m else ""
    open_ = []
    for name, _allowed in TECH_FIELDS:
        mm = re.search(r"^\s*[-*]\s*%s\s*:\s*(.*)$" % re.escape(name), sec, re.I | re.M)
        v = mm.group(1).strip() if mm else ""
        if not v or v.upper().startswith("TODO"):
            open_.append(name)
    has_ui = False
    for base, dirs, files in os.walk(os.path.join(root, "Content")):
        dirs[:] = [d for d in dirs if d not in fab_pack.UEFN_INTERNAL]
        if any(f.startswith(("WBP_", "WB_")) and f.endswith(".uasset") for f in files):
            has_ui = True
            break
    sug = {"Code framework": "Other (the code is Verse)", "Projects": "1", "C++ classes": "0", "AI features": "No unless the product uses an AI service",
           "Includes UI components": "Yes" if has_ui else "No widget assets found: probably No"}
    return open_, sug


# Tags the portal suggests, by category (read from the portal's tag picker, Oct 2026). The portal's search may know more; this is the suggested list.
TAG_CATALOG = {
    "Rendering style": ["Anime", "Cartoon", "Stylized", "Voxel", "Lowpoly", "Realistic", "Pixel"],
    "Period / theme": ["Steampunk", "Victorian", "Ancient", "Cyberpunk", "Fantasy", "Abstract", "Gothic", "Grunge", "Isometric", "Medieval", "Minimalist", "Modern", "Postapocalyptic", "Retro", "Scifi"],
    "Animation": ["Animated", "Rigged"],
    "Features": ["Seamless", "Destructible", "Level", "Modular", "Pbr", "Procedural", "Script"],
    "Engine": ["Blueprint", "Lumen", "Nanite", "Niagara", "Animationblueprint", "Controlrig", "Epicskeleton", "Editorutilities", "Pcg", "Metasounds", "Umg"],
    "Materials": ["Wood", "Cloth", "Stone", "Transparent", "Emissive", "Fabric", "Glass", "Leather", "Metal", "Metallic", "Organic", "Paper", "Plastic", "Reflective"],
}
TAG_ALL = {x.lower() for v in TAG_CATALOG.values() for x in v}


def read_listing(root):
    p = listing_path(root)
    text = _read(p)
    out = {"path": p, "title": "", "short": "", "desc": "", "tags": [], "tag_info": [], "tag_catalog": TAG_CATALOG, "tech_todo": 0, "has_file": bool(p)}
    if not text:
        return out

    def field(name):
        m = re.search(r"^\s*%s:\s*(.*)$" % name, text, re.I | re.M)
        v = m.group(1).strip() if m else ""
        return "" if (not v or v.upper().startswith("TODO")) else v

    def section(name):
        m = re.search(r"^##\s+%s\s*\n(.*?)(?=^##\s|\Z)" % name, text, re.I | re.M | re.S)
        v = m.group(1).strip() if m else ""
        return "" if (not v or v.upper().startswith("TODO")) else v

    out["title"], out["short"] = field("Title"), field("Short description")
    out["desc"] = section("Description")
    out["tags"] = [t.strip().lstrip("-* ").strip() for t in re.split(r"[,\n]", section("Tags")) if t.strip().lstrip("-* ").strip()]
    tech = re.search(r"^##\s+Technical details\s*\n(.*?)(?=^##\s|\Z)", text, re.I | re.M | re.S)
    out["tech_todo"] = len(re.findall(r"TODO", tech.group(1))) if tech else 0
    out["tag_info"] = [{"t": x, "known": x.lower() in TAG_ALL} for x in out["tags"]]
    out["tag_catalog"] = TAG_CATALOG
    return out


# ---- UEFN validation record ----------------------------------------------------

def parse_validation(text):
    """Counts errors and warnings in a pasted UEFN validation log. A summary line such as '3 errors' wins over counting lines."""
    errs = warns = None
    m = re.findall(r"(\d+)\s+error", text, re.I)
    if m:
        errs = sum(int(x) for x in m)
    m = re.findall(r"(\d+)\s+warning", text, re.I)
    if m:
        warns = sum(int(x) for x in m)
    lines = [l for l in text.splitlines() if l.strip()]
    if errs is None:
        errs = len([l for l in lines if re.search(r"\berror\b\s*[:\]]|:\s*error\b|\[error\]|\bError\b:", l, re.I) and not re.search(r"\b0\s+error", l, re.I)])
    if warns is None:
        warns = len([l for l in lines if re.search(r"\bwarning\b\s*[:\]]|:\s*warning\b|\[warning\]", l, re.I) and not re.search(r"\b0\s+warning", l, re.I)])
    sample = [l.strip()[:200] for l in lines if re.search(r"error|warning|disallowed|illegal|reference", l, re.I)][:8]
    return {"errors": errs, "warnings": warns, "lines": len(lines), "sample": sample}


def save_validation(lab, text, skipped_fixup):
    if not text.strip():
        raise ValueError("the log is empty")
    rec = parse_validation(text)
    rec["at"] = time.strftime("%Y-%m-%d %H:%M")
    rec["skip_fixup"] = bool(skipped_fixup)
    _jsave(os.path.join(lab, "validation.json"), rec)
    return rec


# ---- UEFN validation read from the editor log (automatic) ------------------------

STAMP_RE = re.compile(r"^\[(\d{4})\.(\d\d)\.(\d\d)-(\d\d)\.(\d\d)\.(\d\d)")
VAL_PATTERN = "UEFNValidation|LogContentValidation"


def _mcp_map():
    d = os.path.join(os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(os.path.expanduser("~"), ".claude", "kit-template"), "Claude", "hooks")
    if d not in sys.path:
        sys.path.insert(0, d)
    import mcp_map
    return mcp_map


def latest_run(lines):
    """The lines of the most recent validation: those within 3 minutes of the last stamped line (the log keeps older runs of the session).
    The lines the MCP call itself writes in the log (it names the pattern) are not validation output."""
    import datetime
    keep = [l for l in lines if "LogModelContextProtocol" not in l and "Dispatching" not in l and "Running tool" not in l]
    stamped = []
    for l in keep:
        m = STAMP_RE.match(l.strip())
        stamped.append(datetime.datetime(*[int(x) for x in m.groups()]) if m else None)
    last = max((s for s in stamped if s), default=None)
    if not last:
        return keep
    return [l for l, s in zip(keep, stamped) if s is None or (last - s).total_seconds() <= 180]


def read_editor_validation(root, lab, client=None):
    """Ask the open editor (MCP, read only) for the validation lines of its log and keep the result. Never writes in the editor or the project.
    Returns the probe: {at, reachable, lines, errors, warnings}."""
    probe = {"at": time.strftime("%Y-%m-%d %H:%M"), "reachable": False, "lines": 0, "errors": 0, "warnings": 0}
    try:
        mm = _mcp_map()
        if client is None:
            url = mm.find_url(root)
            if not mm.port_open(url):
                raise RuntimeError("UEFN is not reachable")
            client = mm.Client(url)
            client.start()
        text = client.call("call_tool", {"toolset_name": "EditorToolset.LogsToolset", "tool_name": "GetLogEntries",
                                         "arguments": {"category": "", "maxEntries": 0, "pattern": VAL_PATTERN}})
        probe["reachable"] = True
        data = None
        try:
            data = _mcp_map().parse_text(text)
        except Exception:
            data = None
        if isinstance(data, dict):
            data = data.get("entries") or data.get("lines") or data.get("result")
        raw = [x if isinstance(x, str) else str(x.get("message", x)) if isinstance(x, dict) else str(x) for x in data] if isinstance(data, list) else text.splitlines()
        run = latest_run([l for l in raw if l.strip()])
        if run:
            joined = "\n".join(run)
            errs = [l for l in run if re.search(r":\s*Error\b|\bError:", l)]
            warns = [l for l in run if re.search(r":\s*Warning\b|\bWarning:", l)]
            probe.update(lines=len(run), errors=len(errs), warnings=len(warns))
            _jsave(os.path.join(lab, "validation.json"), {"at": probe["at"], "errors": len(errs), "warnings": len(warns), "lines": len(run),
                                                         "sample": [l.strip()[:200] for l in (errs + warns)][:8], "source": "editor log"})
    except Exception as e:  # not reachable, odd reply: the state stays "to do", never a guess
        probe["error"] = str(e)[:120]
    _jsave(os.path.join(lab, "validation-probe.json"), probe)
    return probe


def _verse_check():
    d = os.path.join(os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(os.path.expanduser("~"), ".claude", "kit-template"), "Claude", "hooks")
    if d not in sys.path:
        sys.path.insert(0, d)
    import verse_check
    return verse_check


def read_verse_build(lab, checker=None):
    """Ask the open editor to build the Verse code (same request as the editor's Build Verse Code) and keep the result. Three states, never a guess."""
    try:
        r = (checker or _verse_check().check)()
    except Exception as e:
        r = {"state": "not_analyzed", "reason": "%s" % e}
    rec = {"at": time.strftime("%Y-%m-%d %H:%M"), "state": r.get("state", "not_analyzed"), "errors": r.get("errors", 0), "warnings": r.get("warnings", 0),
           "reason": r.get("reason", ""), "message": " ".join(str(r.get("message", "")).split())[:300]}
    _jsave(os.path.join(lab, "verse-build.json"), rec)
    return rec


def ensure_third_party(root):
    """Recreate FabListing/third_party.md when the listing folder exists but the file is gone (never overwrites)."""
    d = os.path.join(fab_pack.product_folder(root), "FabListing")
    p = os.path.join(d, "third_party.md")
    if os.path.isdir(d) and not os.path.isfile(p):
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(fab_pack.third_party_md(root))
        return True
    return False


def refresh(root, lab):
    ensure_third_party(root)
    st = scan_state(root, lab)
    read_editor_validation(root, lab)
    read_verse_build(lab)
    return st


# ---- heavy part: what the kit finds in the files (cached) ----------------------

def scan_state(root, lab=None):
    blocks, warns, notes = fab_pack.check(root)
    st = {"at": time.strftime("%Y-%m-%d %H:%M"), "blocks": blocks, "warns": warns, "notes": notes}
    top = os.path.basename(root.rstrip("/\\"))
    st["has_uproject"] = any(f.endswith(".uefnproject") for f in os.listdir(root)) if os.path.isdir(root) else False
    st["has_plugin"] = any(f.endswith(".uplugin") for f in _walk_names(root))
    st["has_content"] = os.path.isdir(os.path.join(root, "Content"))
    st["verse"] = len(fab_pack.verse_files(root)) if st["has_content"] else 0
    st["assets"] = sum(1 for _ in _walk_assets(root))
    st["zips"] = [top + ".zip"] if os.path.isfile(os.path.join(os.path.dirname(root.rstrip("/\\")), top + ".zip")) else []
    if lab:
        _jsave(os.path.join(lab, "checklist-cache.json"), st)
    return st


def _walk_names(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in fab_pack.UEFN_INTERNAL and d not in fab_pack.FORBIDDEN_DIRS]
        for f in files:
            yield f


def _walk_assets(root):
    for f in _walk_names(os.path.join(root, "Content")):
        if f.endswith((".uasset", ".umap")):
            yield f


# ---- the stations --------------------------------------------------------------

def _tech_item(root, lst):
    open_, sug = tech_fields(root)
    if not open_:
        return _item("l-tech", "Technical information: all fields of the portal form are filled", "pass", "kit", "All %d fields have a value." % len(TECH_FIELDS))
    allowed = dict(TECH_FIELDS)
    hint = " | ".join("%s: %s%s" % (n, allowed[n], (" - suggested: " + sug[n]) if n in sug else "") for n in open_)
    return _item("l-tech", "Technical information: all fields of the portal form are filled", "warn", "kit", "%d field(s) to fill: %s." % (len(open_), ", ".join(open_)), hint)


def tech_table(root):
    """The portal's Technical details for the listing card: [{name, allowed, value, suggested}] (value from listing.md, empty when TODO)."""
    text = _read(listing_path(root))
    m = re.search(r"^##\s+Technical details\s*\n(.*?)(?=^##\s|\Z)", text, re.I | re.M | re.S)
    sec = m.group(1) if m else ""
    _open, sug = tech_fields(root)
    rows = []
    for name, allowed in TECH_FIELDS + [("Additional information", "free text")]:
        mm = re.search(r"^\s*[-*]\s*%s\s*:\s*(.*)$" % re.escape(name), sec, re.I | re.M)
        v = mm.group(1).strip() if mm else ""
        rows.append({"name": name, "allowed": allowed, "value": "" if (not v or v.upper().startswith("TODO")) else v, "suggested": sug.get(name, "")})
    return rows


def product_files(root):
    """The documents `fab_pack.py docs` creates inside Content/<Product>/ : key, label, path, exists, size, what it is for."""
    base = fab_pack.product_folder(root)
    rows = [("readme", "README.md", "Documentation/README.md", "Setup and usage for the customer: what is inside, requirements, setup steps, usage, known limits"),
            ("author", "AUTHOR.md", "Documentation/AUTHOR.md", "Your signature (ASCII art and links), the same one as in the Verse headers"),
            ("settings", "SETTINGS.md", "Documentation/SETTINGS.md", "Every setting of the devices (generated from the Verse code)"),
            ("listing", "listing.md", "FabListing/listing.md", "Texts for the portal: title, short description, description, tags, technical details"),
            ("third_party", "third_party.md", "FabListing/third_party.md", "Third-party content with author and licence")]
    if not fab_pack.verse_files(root):  # no Verse code: no settings to document, so no SETTINGS.md
        rows = [r for r in rows if r[0] != "settings"]
    out = []
    for key, label, rel, what in rows:
        p = os.path.join(base, *rel.split("/"))
        out.append({"key": key, "label": label, "rel": rel, "what": what, "exists": os.path.isfile(p), "size": os.path.getsize(p) if os.path.isfile(p) else 0, "path": p})
    return out


def read_product_file(root, key):
    for f in product_files(root):
        if f["key"] == key:
            if not f["exists"]:
                raise ValueError("%s does not exist yet: ask the agent to run fab_pack.py docs --apply" % f["label"])
            return f["label"], _read(f["path"])
    raise ValueError("unknown file")


def stations(root, st, lab):
    B, W, N = st["blocks"], st["warns"], st["notes"]
    lst = read_listing(root)
    val = _jload(os.path.join(lab, "validation.json"), None)
    out = []

    # 1 Project
    complete = st["has_uproject"] and st["has_content"] and st["has_plugin"]
    s1 = [
        _item("p-complete", "One project, complete (project file, plugin file, all content)", "pass" if complete else "fail", "kit",
              "Project file, plugin file and Content folder found." if complete else "Missing: " + ", ".join(n for n, ok in (("project file", st["has_uproject"]), ("plugin file", st["has_plugin"]), ("Content folder", st["has_content"])) if not ok) + ".",
              "" if complete else "Zip the whole project folder, the one that holds the .uefnproject file."),
        _verdict_item("p-forbidden", "No kit files, scripts or editor folders in the package", "kit", B, W, "No Claude folder, no Python scripts, no Saved or Intermediate.",
                      r"must not contain|Python scripts", "Remove them from the project (the zip leaves them out, but the Fab review looks at the project)."),
        _item("p-vcs", "No version-control or workspace files in the archive", "pass", "kit",
              ".lore, .loreignore, .urcignore and *.code-workspace are left out when the kit makes the zip." + (" They are present in the project folder." if _by(N, r"\.lore") else "")),
        _verdict_item("p-names", "Names use letters, digits and underscore only", "kit", B, W, "%d asset(s) checked." % st["assets"], r"letters, digits and underscore",
                      "Rename them in the editor (it keeps the references)."),
        _verdict_item("p-paths", "File paths are 140 characters or shorter", "kit", B, W, "Every path fits.", r"path is \d+",
                      "Shorten the folder or file names, or the project folder name."),
        _verdict_item("p-empty", "No empty or vaguely named folders", "kit", B, W, "No empty folder, no vague name.", r"empty folder|vague folder|is long",
                      "Delete or fill them in the editor."),
        _item("p-one", "One pack folder named like the product", "warn" if _by(N, r"more than one asset folder") else "pass", "kit",
              _short(_by(N, r"more than one asset folder")) or "Content holds one product folder.", "Move the assets into one folder, or accept the risk."),
        _item("p-types", "Each asset type in its own folder (materials, textures, sounds...)", "manual", "you", "The kit cannot judge how you grouped them.", "Open the Content Browser and look once."),
        _item("p-redirectors", "No redirectors left in the folders", "manual", "you", "A redirector is a leftover from moving an asset. Only the editor can remove it: the agents cannot.", "In the Content Browser right-click the product folder and choose Fix Up Redirectors, then tick this."),
    ]
    out.append({"id": "project", "n": "1 Project", "d": "Is it one clean, complete project?", "items": s1})

    # 2 Content
    foreign = _verdict_item("c-foreign", "No reference to assets of another project", "x", B, W, "%d assets read, no foreign import." % st["assets"], r"another project|not part of this project",
                            "Clean the references in the editor, then run the check again.")
    s2 = [
        foreign,
        _verdict_item("c-names", "No name of another project saved inside the assets", "x", B, W, "All internal names use this project's plugin.", r"internal name of another project",
                      "Rebuild or re-save those assets inside this project."),
        _verdict_item("c-users", "No Windows user name left in the import paths", "x", B, W, "No user name found in the source paths.", r"Windows user",
                      "Clean the import path in the editor; declare the source of each file in station 4."),
        _item("c-tex", "Textures: width and height are powers of 2, 2k at most", "manual", "ed", "The kit cannot read texture sizes yet.", "In the Content Browser sort the textures by size and look once."),
        _item("c-audio", "Audio: .wav source, no distortion or hitching", "manual", "you", "", "Listen to every sound once."),
        _item("c-work", "Assets complete, work as intended, no visual defects", "manual", "you", "", "Play the map and look at every screen."),
    ]
    out.append({"id": "content", "n": "2 Content", "d": "Do the assets belong to this project and look right?", "items": s2})

    # 3 Build
    probe = _jload(os.path.join(lab, "validation-probe.json"), None)
    if val is None:
        if not probe:
            ev, fx = "Not read yet.", "Press Run all checks: the kit reads the validation from the open editor by itself."
        elif not probe.get("reachable"):
            ev, fx = "%s: the editor was not reachable." % probe["at"], "Open UEFN with this project and press Run all checks."
        else:
            ev, fx = "%s: the editor log has no validation yet." % probe["at"], "The editor validates when you start a play session or publish: do one of them, then press Run all checks."
        vi = _item("b-valid", "UEFN validation: no errors or consequential warnings", "todo", "ed", ev, fx)
    elif val.get("errors", 0) > 0:
        vi = _item("b-valid", "UEFN validation: no errors or consequential warnings", "fail", "ed",
                   "%s: %d errors, %d warnings. %s" % (val.get("at", ""), val["errors"], val.get("warnings", 0), _short(val.get("sample", []), 2)),
                   "Fix the errors in the editor, validate again and press Run all checks.")
    elif val.get("warnings", 0) > 0:
        vi = _item("b-valid", "UEFN validation: no errors or consequential warnings", "warn", "ed",
                   "%s: 0 errors, %d warnings. %s" % (val.get("at", ""), val["warnings"], _short(val.get("sample", []), 2)), "Read the warnings: clean the ones that mention a reference.")
    else:
        vi = _item("b-valid", "UEFN validation: no errors or consequential warnings", "pass", "ed", "%s: 0 errors, 0 warnings." % val.get("at", ""))
    vbd = _jload(os.path.join(lab, "verse-build.json"), None)
    vt = "Verse compiles with no errors or warnings"
    if not vbd:
        verse_item = _item("b-verse", vt, "todo", "ed", "Not built yet.", "Press Run all checks: the kit asks the open editor to build the Verse code.")
    elif vbd["state"] == "clean" and not vbd["warnings"]:
        verse_item = _item("b-verse", vt, "pass", "ed", "%s: build finished with 0 errors, 0 warnings (%d Verse file(s))." % (vbd["at"], st["verse"]))
    elif vbd["state"] == "clean":
        verse_item = _item("b-verse", vt, "warn", "ed", "%s: 0 errors, %d warnings. %s" % (vbd["at"], vbd["warnings"], vbd["message"][:160]), "Open the Verse log in the editor and clean the warnings.")
    elif vbd["state"] == "errors":
        verse_item = _item("b-verse", vt, "fail", "ed", "%s: %d errors. %s" % (vbd["at"], vbd["errors"], vbd["message"][:200]), "Fix them in the code, then press Run all checks.")
    else:
        verse_item = _item("b-verse", vt, "todo", "ed", "%s: %s" % (vbd["at"], vbd.get("reason") or "the editor did not answer."), "Open UEFN with this project and press Run all checks.")
    s3 = [
        verse_item,
        vi,
        _item("b-dev", "Devices are clean: clear names, no loose nodes, no errors", "manual", "you", "", "Open the widget graphs and the level once."),
        _item("b-play", "Map loads with no errors or warnings in a play session", "manual", "you", "", "Start a play session and read the log."),
    ]
    out.append({"id": "build", "n": "3 Build", "d": "Does it compile and validate with no errors?", "items": s3})

    # 4 Listing
    if not lst["has_file"]:
        s4 = [_item("l-file", "Listing texts exist (FabListing/listing.md)", "fail", "kit", "No listing.md found.", "Ask the kit to create the documents: fab_pack.py docs --apply.")]
    else:
        ttl = len(lst["title"])
        generic = [t for t in lst["tags"] if t.lower() in GENERIC_TAGS]
        s4 = [
            _item("l-title", "Title", "pass" if 0 < ttl <= 30 else ("warn" if ttl else "todo"), "kit",
                  "%d characters." % ttl if ttl else "Not written yet.", "" if 0 < ttl <= 30 else ("Shorten it to about 30 characters." if ttl else "Write the title in listing.md.")),
            _item("l-short", "Short description", "pass" if lst["short"] else "todo", "kit", "%d characters." % len(lst["short"]) if lst["short"] else "Not written yet.", "" if lst["short"] else "Write it in listing.md."),
            _item("l-desc", "Description", "pass" if len(lst["desc"]) > 200 else ("warn" if lst["desc"] else "todo"), "kit",
                  "%d characters." % len(lst["desc"]) if lst["desc"] else "Not written yet.", "" if len(lst["desc"]) > 200 else "Say what it does, what is included and how it is used."),
            _item("l-tags", "Tags", "todo" if not lst["tags"] else "pass", "kit",
                  ("%d tags%s." % (len(lst["tags"]), ("; not in the portal's suggested list: " + ", ".join(x["t"] for x in lst["tag_info"] if not x["known"]) + " (its search may still have them)") if any(not x["known"] for x in lst["tag_info"]) else "")) if lst["tags"] else "No tags yet.",
                  "" if lst["tags"] else "Add tags in listing.md."),
        ]
    docs_ok = os.path.isfile(os.path.join(fab_pack.product_folder(root), "Documentation", "README.md"))
    tp = _read(os.path.join(fab_pack.product_folder(root), "FabListing", "third_party.md"))
    tp_open = tp.count("TODO")
    s4 += [
        _item("l-doc", "Setup documentation is included", "pass" if docs_ok else "fail", "kit", "Documentation/README.md found." if docs_ok else "No Documentation/README.md.", "" if docs_ok else "Run fab_pack.py docs --apply."),
        _item("l-third", "Third-party content is declared with author and licence", "warn" if (tp_open or _by(W, r"third-party")) else ("pass" if tp else "todo"), "kit",
              "%d row(s) still TODO in third_party.md." % tp_open if tp_open else ("Declared." if tp else "third_party.md was missing."), "Write author, source and licence of every file that is not yours." if tp else "Press Run all checks: the kit recreates the file, then fill it in."),
        _item("l-images", "Images show the real product (thumbnail and gallery)", "manual", "you", "", "Prepare the thumbnail and gallery by hand."),
        _item("l-honest", "Texts are accurate; nothing offensive; no content you may not resell", "manual", "you", "", "Read the listing once more before sending."),
    ]
    out.append({"id": "listing", "n": "4 Listing", "d": "Are texts, images and licences ready?", "items": s4})

    # 5 Extra round (before the zip): memory and a private release, each one an extra validation
    out.append({"id": "extra", "n": "5 Extra", "d": "One more round of validation before the zip", "ordered": True, "items": [
        _item("x-mem", "Memory calculation of the project", "manual", "you", "A project over its memory budget can fail to load or be refused.",
              "Run the memory calculation in UEFN, look at the result and tick this when it is inside the limits."),
        _item("x-priv", "Private release of the project", "manual", "you", "A private release goes through a further round of validation without being public.",
              "Publish the project as a private release, wait for its validation to finish, fix what it reports, then tick this.")]})

    # 5 Zip
    zr = _jload(os.path.join(lab, "zipcheck.json"), None)
    zips = st.get("zips") or []
    s5 = [
        _item("z-make", "Make the zip with the kit (whole project, one folder)", "pass" if zips else "todo", "kit",
              ("Found: %s." % zips[-1]) if zips else "Not made yet.", "" if zips else "Use the Make the zip button when stations 1 to 4 have no block."),
        _item("z-reread", "Then re-read the finished zip: names, paths, forbidden files, asset scan", "pass" if zr and zr.get("ok") else ("fail" if zr else "todo"), "kit",
              ("%s: clean." % zr["at"]) if zr and zr.get("ok") else (_short(zr.get("problems", [])) if zr else ("Make the zip first. The kit then unzips it in a temporary folder and runs the same checks on the copy." if not zips else "The kit unzips it in a temporary folder and runs the same checks on the copy.")),
              "" if zr and zr.get("ok") else ("Make the zip first." if not zips else "Use the Re-read the zip button.")),
    ]
    out.append({"id": "zip", "n": "6 Zip", "d": "The archive the portal wants: first make it, then re-read it", "items": s5, "ordered": True})

    # 6 Submit
    out.append({"id": "submit", "n": "7 Submit", "d": "On the portal", "items": [
        _item("s-send", "Upload and send for review", "manual", "you", "", "Do it on the Fab portal, then tick it here.")]})

    return out, lst, val


def counts(items):
    c = {"pass": 0, "fail": 0, "warn": 0, "todo": 0, "manual": 0, "na": 0}
    for i in items:
        c[i["s"]] += 1
    return c


def pct(c):
    tot = c["pass"] + c["fail"] + c["warn"] + c["todo"] + c["manual"]
    return int(round(100.0 * c["pass"] / tot)) if tot else 100


def build(root, lab, state=None):
    """The whole page data. `state` is a cached scan_state (the heavy part); the manual ticks and the validation record are applied here."""
    st = state or _jload(os.path.join(lab, "checklist-cache.json"), None) or scan_state(root, lab)
    sts, lst, val = stations(root, st, lab)
    ticks = _jload(os.path.join(lab, "confirm.json"), {})
    for s in sts:
        for it in s["items"]:
            if it["id"] in ticks and it["s"] in ("manual", "todo") and it["w"] in ("you", "ed", "x"):
                it["s"] = "pass"
                it["ev"] = "You confirmed it on %s." % ticks[it["id"]]
                it["tick"] = True
            it["tickable"] = it["w"] in ("you", "ed", "x") and (it["s"] == "manual" or it.get("tick", False))
        s["counts"] = counts(s["items"])
    allit = [i for s in sts if s["id"] != "submit" for i in s["items"]]   # sending it on the portal is the last act, not a check on the product
    c = counts(allit)
    total = c["pass"] + c["fail"] + c["warn"] + c["todo"] + c["manual"]
    first = next((s for s in sts if s["counts"]["fail"]), None)
    if c["fail"]:
        bad = [i for i in allit if i["s"] == "fail"]
        verdict = "NOT READY"
        msg = "%d check%s block the upload: %s. Open station %s to see what to do. After that, %d warning%s and %d item%s to confirm are left; they do not stop the upload." % (
            c["fail"], "" if c["fail"] == 1 else "s", "; ".join(i["t"] for i in bad[:3]), first["n"].split()[0], c["warn"], "" if c["warn"] == 1 else "s", c["manual"] + c["todo"], "" if c["manual"] + c["todo"] == 1 else "s")
    elif c["warn"] or c["todo"] or c["manual"]:
        verdict = "NOT YET"
        msg = "Nothing blocks the upload. %d warning%s to clean up and %d item%s that only you can confirm or finish." % (c["warn"], "" if c["warn"] == 1 else "s", c["manual"] + c["todo"], "" if c["manual"] + c["todo"] == 1 else "s")
    else:
        verdict = "READY"
        msg = "Ready to publish: every check is green. Upload the zip on the portal, then tick station 7."
    blocked_before_zip = any(s["counts"]["fail"] for s in sts if s["id"] in ("project", "content", "build", "listing"))
    lst["tech"] = tech_table(root)
    lst["files"] = [{k: v for k, v in f.items() if k != "path"} for f in product_files(root)]
    return {"name": os.path.basename(root.rstrip("/\\")), "root": root, "scanned_at": st.get("at", ""), "stations": sts, "counts": c, "total": total,
            "pct": pct(c), "verdict": verdict, "message": msg, "listing": lst, "validation": val, "can_zip": not blocked_before_zip}


def set_tick(lab, item_id, on):
    p = os.path.join(lab, "confirm.json")
    d = _jload(p, {})
    if on:
        d[item_id] = time.strftime("%Y-%m-%d %H:%M")
    else:
        d.pop(item_id, None)
    _jsave(p, d)
    return d


def reread_zip(root, lab):
    """Unzip the newest zip next to the project in a temp folder and run the same checks on the copy."""
    import tempfile
    import zipfile
    top = os.path.basename(root.rstrip("/\\"))
    par = os.path.dirname(root.rstrip("/\\"))
    zp = os.path.join(par, top + ".zip")
    if not os.path.isfile(zp):
        raise ValueError("no %s.zip next to the project: make the zip first" % top)
    zips = [zp]
    probs = []
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zips[-1]) as z:
            tops = {n.split("/")[0] for n in z.namelist() if n.strip("/")}
            if tops != {top}:
                probs.append("the archive must hold exactly one top folder named %s (found: %s)" % (top, ", ".join(sorted(tops))))
            z.extractall(tmp)
        copy = os.path.join(tmp, top)
        if os.path.isdir(copy):
            b, w, _n = fab_pack.check(copy)
            probs += b
    rec = {"at": time.strftime("%Y-%m-%d %H:%M"), "zip": os.path.basename(zips[-1]), "ok": not probs, "problems": probs[:20]}
    _jsave(os.path.join(lab, "zipcheck.json"), rec)
    return rec


def main(argv):
    if argv and argv[0] == "tags":  # the portal's suggested tags, by category: the only ones a listing should use
        for k, v in TAG_CATALOG.items():
            print("%s: %s" % (k, ", ".join(v)))
        return 0
    import fab_lab
    base = argv[0] if argv else os.getcwd()
    root = fab_pack.find_root(base)
    if not root:
        print("not a UEFN project folder"); return 1
    lab = fab_lab.ensure_lab(root)
    d = build(root, lab, refresh(root, lab))
    print("%s: %s  %d%%  (%d of %d passed)" % (d["name"], d["verdict"], d["pct"], d["counts"]["pass"], d["total"]))
    print(d["message"])
    for s in d["stations"]:
        for i in s["items"]:
            if i["s"] not in ("pass", "na"):
                print("  [%s] %s - %s%s" % (i["s"], s["n"], i["t"], (": " + i["ev"]) if i["ev"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
