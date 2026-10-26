#!/usr/bin/env python3
"""Mechanic recipes prepared by the kit itself (no AI, no agent), for a Fab product and for a map.

Reads the Verse code (and the README of the product when there is one) and writes a recipe for the skill "mechanics":
the devices it needs, the settings with their defaults, the Verse files with their code, the assets, the setup steps and what to
check. Only what the code and the README really say. Used by fab_lab.py (a product) and by kit_sync.py (a map, one recipe per
folder that holds a device).
"""
import hashlib, json, os, re, time

SKIP = ("Intermediate", "Saved", "node_modules", "Claude", ".git")


def verse_files(root, limit=12):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP]
        for f in sorted(files):
            if f.endswith(".verse") and len(out) < limit:
                try:
                    with open(os.path.join(base, f), encoding="utf-8", errors="replace") as fh:
                        out.append({"name": f, "code": fh.read()[:40000]})
                except OSError:
                    pass
    return out


def _readme(doc_root):
    if not doc_root:
        return ""
    for base, dirs, files in os.walk(doc_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP]
        if "README.md" in files and os.path.basename(base) == "Documentation":
            try:
                with open(os.path.join(base, "README.md"), encoding="utf-8", errors="replace") as fh:
                    return fh.read()
            except OSError:
                return ""
    return ""


def _section(txt, title):
    m = re.search(r"^##\s+%s\s*$(.*?)(?=^##\s|\Z)" % re.escape(title), txt, re.M | re.S)
    if not m:
        return []
    return [re.sub(r"^\s*(\d+\.|[-*])\s+", "", ln).strip() for ln in m.group(1).splitlines() if re.match(r"^\s*(\d+\.|[-*])\s+", ln)]


def _intro(txt):
    for ln in txt.splitlines()[1:]:
        if ln.strip() and not ln.startswith("#"):
            return " ".join(ln.split())
    return ""


def device_classes(files):
    code = "\n".join(f["code"] for f in files)
    return [c for c, base in re.findall(r"^(\w+)(?:<[^>]*>)?\s*:=\s*class(?:<[^>]*>)*\((\w+)\)", code, re.M) if base in ("creative_device", "creative_device_base")]


def build(files, product, doc_root=None, assets_root=None):
    """The recipe dict for these Verse files, or None when no file defines a device."""
    devices_cls = device_classes(files)
    if not files or not devices_cls:
        return None
    lines = "\n".join(f["code"] for f in files).splitlines()
    needs, settings, mats, pending_doc, i = [], [], 0, [], 0
    while i < len(lines):
        ln = lines[i].strip()
        if ln.startswith("#") and not ln.startswith("#("):
            pending_doc.append(ln.lstrip("# ").strip()); i += 1; continue
        m = re.match(r"@editable\s*(.*)$", ln)
        if m:
            decl, j = m.group(1).strip(), i
            while not decl and j + 1 < len(lines):
                j += 1; decl = lines[j].strip()
            f = re.match(r"(\w+)\s*:\s*([^=]+?)\s*(?:=\s*(.+))?$", decl)
            if f:
                name, typ, dflt = f.group(1), f.group(2).strip(), (f.group(3) or "").strip()
                doc = " ".join(pending_doc[-1:])
                if "_device" in typ:
                    needs.append("%s: a %s%s" % (name, typ.strip("?[]"), (" (%s)" % doc) if doc else ""))
                elif typ.startswith("?material") or typ.startswith("material"):
                    mats += 1
                else:
                    settings.append("%s (%s) = %s%s" % (name, typ, dflt or "-", (": " + doc) if doc else ""))
            i, pending_doc = j + 1, []
            continue
        if ln and not ln.startswith("@"):
            pending_doc = []
        i += 1
    assets = []
    if assets_root:
        for base, dirs, fs in os.walk(assets_root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP]
            n = sum(1 for x in fs if x.endswith(".uasset"))
            if n:
                rel = os.path.relpath(base, assets_root).replace("\\", "/")
                assets.append("%s: %d asset(s)" % ("Content" if rel == "." else rel, n))
    txt = _readme(doc_root)
    setup, usage, reqs = _section(txt, "Setup"), _section(txt, "Usage"), _section(txt, "Requirements")
    kind = "device" if len(devices_cls) == 1 else ("template" if len(devices_cls) > 3 else "mechanic")
    if mats:
        settings.append("%d material slots (Mat_*) default to the materials included: leave them unless you want other looks" % mats)
    name = re.sub(r"^root[ _-]+", "", re.sub(r"[^A-Za-z0-9 _-]+", " ", product).replace("_", " ").strip().lower()) or "mechanic"
    return {"name": name, "kind": kind, "use": (_intro(txt) or "Built from the Verse code of %s." % product)[:300],
            "steps": setup or ["Copy the folder into the project, keep its folder structure", "Place %s in the level" % ", ".join(devices_cls),
                               "Assign the devices it needs and set the options in the Details panel", "Launch a session and check it"],
            "devices": ["%s: the device to place in the level" % c for c in devices_cls] + needs, "settings": settings[:120],
            "wiring": [x for x in needs if "required" in x.lower()], "files": files,
            "assets": assets[:30] + ["Requirements: " + r for r in reqs],
            "verify": "; ".join(usage[:3]) or "Place the device, launch a session and check the behavior of the Verse code"}


def signature(files):
    return hashlib.sha1("".join(f["name"] + f["code"] for f in files).encode("utf-8", "replace")).hexdigest()


def groups_for_map(project):
    """One group per folder that holds Verse files with a device (a map has many mechanics)."""
    g = {}
    for base, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP]
        vs = verse_files(base, 12) if any(f.endswith(".verse") for f in files) else []
        # only the files of this very folder
        vs = [v for v in vs if os.path.isfile(os.path.join(base, v["name"]))]
        if vs and device_classes(vs):
            g[base] = vs
    return g


def ensure_map(project, map_name, add, limit=15):
    """Recipes of a map, prepared by the kit: one per folder with a device, redone only when its Verse changed. `add` = skills_lib.recipe_add.
    Returns the names saved now."""
    mark = os.path.join(project, "Claude", "docs", "auto-recipes.json")
    try:
        with open(mark, encoding="utf-8") as f:
            seen = json.load(f)
    except (OSError, ValueError):
        seen = {}
    saved = []
    for base, vs in list(groups_for_map(project).items())[:limit]:
        key = os.path.relpath(base, project).replace("\\", "/")
        sig = signature(vs)
        if seen.get(key) == sig:
            continue
        parent = os.path.dirname(base)
        rec = build(vs, os.path.basename(parent) if os.path.basename(base).lower() == "verse" else os.path.basename(base),
                    doc_root=parent, assets_root=parent if os.path.basename(base).lower() == "verse" else None)
        if not rec:
            continue
        r = add("mechanics", rec, map_name)
        if r.get("ok"):
            seen[key] = sig
            saved.append(rec["name"])
    if saved:
        os.makedirs(os.path.dirname(mark), exist_ok=True)
        with open(mark, "w", encoding="utf-8") as f:
            json.dump(seen, f, indent=1)
    return saved
