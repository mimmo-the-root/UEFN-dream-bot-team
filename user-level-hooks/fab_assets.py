#!/usr/bin/env python3
"""Fab asset scan (v1.110): finds in the .uasset/.umap files the traces of ANOTHER project that make Epic's validation fail.

Why: Fab validates the whole project after importing it. An asset copied by hand from another project keeps (1) its old internal
package name (for example /pilars/Rank_UI/T_Bronze_I) and sometimes (2) a hard import of an asset that does not exist here
(for example a Sound Cue pointing to /pilars/HUD_WBP/UI/S_Point): Epic reports "Disallowed reference to ...". The editor's own
validation may not show it, because it often checks only the assets you touched. The editor rewrites the internal name only when it
saves the asset.

Reads only the header of each package (name table + import table). Never writes. Layout of UE 5.5+ packages (UEFN 42.x); a file it
cannot read is listed as "not understood", never as an error. Used by fab_pack.py check; can run alone:

  python fab_assets.py <UEFN project root>
"""
import os, re, struct, sys

class Bad(Exception):
    pass

# Mounts that belong to Epic (plugins every UEFN project can depend on). Anything else that is imported and does not exist in this
# project is reported as "check it": a mount of another of your projects is NOT allowed in a Fab package.
EPIC_EXACT = {"Script", "Engine", "Game", "FortniteGame", "FortUILibrary", "ContentHall", "Itemization", "FortWater", "VerseColors",
              "Verse", "VerseDevices", "VerseEngine", "VerseUIStarterKit", "CreativeCoreDevices", "Niagara", "Paper2D", "Fortnite", "FNE_UI"}
EPIC_PREFIX = ("CRD_", "Creative", "Fort", "Verse", "UEFN", "Athena", "BR", "Valkyrie")


def is_epic_mount(m):
    return m in EPIC_EXACT or m.startswith(EPIC_PREFIX)


def _fstr(b, p):
    n, = struct.unpack_from('<i', b, p)
    p += 4
    if n == 0:
        return "", p
    if n < 0:
        n = -n
        return b[p:p + 2 * (n - 1)].decode('utf-16-le', 'replace'), p + 2 * n
    return b[p:p + n - 1].decode('utf-8', 'replace'), p + n


def read_header(path):
    with open(path, 'rb') as f:
        head = f.read(64)
        if len(head) < 64 or struct.unpack_from('<I', head, 0)[0] != 0x9E2A83C1:
            raise Bad("not a package")
        f.seek(0)
        b = f.read(1 << 16)
        try:
            leg, = struct.unpack_from('<i', b, 4)
            p = 8 + (0 if leg == -4 else 4) + 4 + (4 if leg <= -8 else 0) + 4
            v5 = struct.unpack_from('<i', b, 12 if leg == -4 else 16)[0] if leg <= -8 else 0
            if v5 >= 1016:
                p += 20
            total, = struct.unpack_from('<i', b, p)
        except struct.error:
            raise Bad("summary")
        if not 64 < total < (256 << 20):
            raise Bad("header size")
        if total > len(b):
            f.seek(0)
            b = f.read(total)
    return b


def parse(path):
    """(package names found in the name table, [imported package names]). Raises Bad when the layout is not understood."""
    b = read_header(path)
    try:
        leg, = struct.unpack_from('<i', b, 4)
        p = 8
        if leg != -4:
            p += 4
        p += 4
        v5 = 0
        if leg <= -8:
            v5, = struct.unpack_from('<i', b, p)
            p += 4
        p += 4
        if v5 >= 1016:
            p += 20
        p += 4  # total header size
        if leg <= -2:
            n, = struct.unpack_from('<i', b, p)
            p += 4
            if not 0 <= n < 200:
                raise Bad("custom versions")
            p += n * 20
        _, p = _fstr(b, p)
        flags, = struct.unpack_from('<I', b, p)
        p += 4
        ncount, noff = struct.unpack_from('<ii', b, p)
        p += 8
        if v5 >= 1008:
            p += 8
        if not (flags & 0x80000000):
            _, p = _fstr(b, p)
        p += 8
        _ecount, eoff, icount, ioff = struct.unpack_from('<iiii', b, p)
        if not (0 < noff < len(b) and 0 <= ncount < 500000 and 0 <= icount < 200000 and 0 < ioff <= eoff <= len(b)):
            raise Bad("layout")
        names, q = [], noff
        for _ in range(ncount):
            s, q = _fstr(b, q)
            q += 4
            names.append(s)
        imports = []
        if icount:
            size = (eoff - ioff) // icount
            if size not in (28, 32, 36, 40):
                raise Bad("import size")
            for i in range(icount):
                _cp, _cpn, cn, _cnn, outer, on, _onn = struct.unpack_from('<iiiiiii', b, ioff + i * size)
                if outer == 0 and names[cn] == "Package":
                    imports.append(names[on])
        return names, imports
    except (struct.error, IndexError):
        raise Bad("layout")


USER_RE = re.compile(rb"Users[/\\]+([A-Za-z0-9][A-Za-z0-9 ._@+-]{1,40}?)[/\\]")
SKIP_USERS = {b"Public", b"Default", b"All Users", b"Shared"}
MAX_READ = 16 << 20


def user_names(path):
    """User names found in the import records of a texture or sound ('C:/Users/<name>/Downloads/x.png'): the editor keeps the full source path."""
    try:
        if os.path.getsize(path) > MAX_READ:
            return set()
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return set()
    return {m.group(1).decode("utf-8", "replace") for m in USER_RE.finditer(data) if m.group(1) not in SKIP_USERS and not re.fullmatch(rb"[xX]+", m.group(1))}  # a name replaced by xxxx is already cleaned


def mount_of(path):
    return path.split("/")[1] if path.startswith("/") and path.count("/") >= 2 else ""


def own_mount(root):
    """The mount of this project = the name of its .uplugin file (a GUID)."""
    try:
        for n in os.listdir(root):
            if n.endswith(".uplugin"):
                return n[:-len(".uplugin")]
    except OSError:
        pass
    return ""


def own_name(names, stem):
    """The package name the file carries for itself: a name table entry like /<mount>/.../<stem> (no dot)."""
    for s in names:
        if s.startswith("/") and "." not in s and s.rsplit("/", 1)[-1] == stem and s.count("/") >= 2:
            return s
    return ""


def scan(root):
    """(blocks, warnings, notes) as lists of text for fab_pack.check."""
    content = os.path.join(root, "Content")
    mine = own_mount(root)
    if not mine or not os.path.isdir(content):
        return [], [], []
    stale_files, imports_by_file, unread, users = {}, {}, [], {}
    existing = set()
    for base, dirs, files in os.walk(content):
        dirs[:] = [d for d in dirs if d not in ("__ExternalActors__", "__ExternalObjects__", "Collections", "Developers", "Claude")]
        for f in files:
            if f.endswith((".uasset", ".umap")):
                rel = os.path.relpath(os.path.join(base, f), content).replace(os.sep, "/")
                existing.add("/" + mine + "/" + os.path.splitext(rel)[0])
    for base, dirs, files in os.walk(content):
        dirs[:] = [d for d in dirs if d not in ("__ExternalActors__", "__ExternalObjects__", "Collections", "Developers", "Claude")]
        for f in files:
            if not f.endswith((".uasset", ".umap")):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, content).replace(os.sep, "/")
            try:
                names, imps = parse(p)
            except (Bad, OSError):
                unread.append(rel)
                continue
            for u in user_names(p):
                users.setdefault(u, []).append(rel)
            on = own_name(names, os.path.splitext(f)[0])
            if on and mount_of(on) and mount_of(on) != mine:
                stale_files[rel] = mount_of(on)
            imports_by_file[rel] = imps
    stale_mounts = set(stale_files.values())
    blocks, warns, notes = [], [], []
    unknown = {}
    for rel, imps in sorted(imports_by_file.items()):
        for i in imps:
            m = mount_of(i)
            if not m or m == mine or is_epic_mount(m):
                continue
            if m in stale_mounts:
                blocks.append("%s: imports %s, an asset of another project (%s) that does not exist here: Epic reports 'Disallowed reference'. "
                              "In the editor point it to the asset of this project, then save it" % (rel, i, m))
            else:
                unknown.setdefault(i, []).append(rel)
    for i, files in sorted(unknown.items()):
        warns.append("%s is imported by %s but is not part of this project: if it is not an Epic library, Epic's validation will reject it "
                     "(check it in the Reference Viewer)" % (i, ", ".join(files[:3]) + (" +%d" % (len(files) - 3) if len(files) > 3 else "")))
    if stale_files:
        by = {}
        for rel, m in stale_files.items():
            by.setdefault(m, []).append(rel)
        for m, files in sorted(by.items()):
            warns.append("%d asset(s) still carry the internal name of another project (/%s/...), for example %s: they were copied by hand. "
                         "Open and save them in the editor to rewrite the name (the editor only does it when it saves)" % (len(files), m, files[0]))
    for u, files in sorted(users.items()):
        warns.append("%d asset(s) keep the source path of the Windows user '%s' (the editor records where a file was imported from), for example %s: "
                     "it exposes a real user name in the package, and it shows where the file came from (declare third-party content)"
                     % (len(files), u, files[0]))
    if unread:
        notes.append("%d asset file(s) not understood by the scan (other layout): %s" % (len(unread), ", ".join(unread[:3])))
    return blocks, warns, notes


# ---- automatic clean (v1.110) -----------------------------------------------------------------------------------------------
# The editor records where a file was imported from ('C:/Users/<name>/Downloads/x.png', '.../<other project>/...'). Fab's review sees
# it. The kit replaces those names with x of the SAME length (the file size and every offset stay the same: nothing else moves), after
# a backup kept OUTSIDE the project. Only names inside a path are touched, never a package name or an import.
SKIP_DIRS = ("__ExternalActors__", "__ExternalObjects__", "Collections", "Developers", "Claude")


def other_project_names(root):
    """Names of the owner's OTHER projects (registry + lab folders), at least 4 characters, longest first."""
    me = os.path.basename(os.path.abspath(root)).lower()
    names = set()
    home = os.path.join(os.path.expanduser("~"), ".claude")
    try:
        import kit_install
        for v in kit_install.load_registry().values():
            names.add(str(v.get("name", "")))
    except Exception:
        pass
    try:
        lab = os.environ.get("UEFN_FAB_LAB_DIR") or os.path.join(home, "fab-lab")
        names.update(os.listdir(lab))
    except OSError:
        pass
    return sorted({n for n in names if len(n) >= 4 and re.fullmatch(r"[A-Za-z0-9_.-]+", n) and n.lower() != me}, key=len, reverse=True)


def _x(n, wide):
    return ("x" * n).encode("utf-16-le" if wide else "ascii")


def _clean_bytes(data, others):
    """(new bytes, {label: count}). Same length, always."""
    out, counts = data, {}
    def sub(pat, group_label):
        nonlocal out
        def rep(m):
            counts[group_label(m)] = counts.get(group_label(m), 0) + 1
            a, b_ = m.span(1)
            return m.group(0)[:a - m.start()] + b"x" * (b_ - a) + m.group(0)[b_ - m.start():]
        out = pat.sub(rep, out)
    sub(USER_RE, lambda m: "user:" + m.group(1).decode("utf-8", "replace"))
    for n in others:
        sub(re.compile(rb"(?<=[/\\])(" + re.escape(n.encode("ascii")) + rb")(?![A-Za-z0-9_])"), lambda m, n=n: "project:" + n)
    # the same names written as UTF-16 (long source paths are stored that way)
    for label in list(counts):
        kind, name = label.split(":", 1)
        w = name.encode("utf-16-le")
        if w and w in out:
            counts[label] += out.count(w)
            out = out.replace(w, _x(len(name), True))
    return out, counts


def clean(root, apply=True, backup_dir=None):
    """Replace user names and other projects' names found in source paths. Returns (changed, problems):
    changed = [(relative file, {what: count})]. With apply=False nothing is written."""
    content = os.path.join(root, "Content")
    others = other_project_names(root)
    changed, problems = [], []
    for base, dirs, files in os.walk(content):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith((".uasset", ".umap")):
                continue
            p = os.path.join(base, f)
            try:
                if os.path.getsize(p) > MAX_READ:
                    continue
                with open(p, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            new, counts = _clean_bytes(data, others)
            counts = {k: v for k, v in counts.items() if v and not re.fullmatch(r"(user|project):[xX]+", k)}
            if not counts or new == data:
                continue
            assert len(new) == len(data)
            rel = os.path.relpath(p, content).replace(os.sep, "/")
            changed.append((rel, counts))
            if not apply:
                continue
            try:
                if backup_dir:
                    dst = os.path.join(backup_dir, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if not os.path.exists(dst):
                        with open(dst, "wb") as bf:
                            bf.write(data)
                with open(p, "r+b") as fh:
                    fh.write(new)
            except OSError:
                problems.append("%s could not be cleaned (is the editor holding it open? close UEFN and run it again)" % rel)
    return changed, problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    b, w, n = scan(argv[0])
    for x in b:
        print("BLOCK: " + x)
    for x in w:
        print("warning: " + x)
    for x in n:
        print("note: " + x)
    if not (b or w or n):
        print("asset scan: nothing found")
    return 1 if b else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
