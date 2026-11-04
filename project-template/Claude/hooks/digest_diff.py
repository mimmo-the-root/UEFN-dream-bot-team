#!/usr/bin/env python3
"""digest_diff.py - what changed in the Verse API between two UEFN versions, from their digest files. Zero AI tokens, never touches the editor.

  python Claude/hooks/digest_diff.py OLD_DIR NEW_DIR [--out FILE] [--limit N]

OLD_DIR and NEW_DIR hold the digests copied before and after the update (Fortnite.digest.verse, UnrealEngine.digest.verse, Verse.digest.verse); a single
file works too. Prints (and writes, with --out) a markdown report: classes, interfaces and enums added or removed; members added, removed or whose
signature changed; and every added or changed line near the word experimental, deprecated or not publishable.
A member is read as "the line inside its class", so a moved argument or a new effect specifier shows as removed plus added of the same name = changed."""
import os, re, sys

DEF = re.compile(r"^\s*([A-Za-z_][\w]*)\s*(?:<[^>]*>)*\s*(?::=|:)\s*(?:<[^>]*>)*\s*(class|interface|struct|enum|module)\b")
FLAG = re.compile(r"experimental|deprecated|not[_ ]publishable|internal|preview", re.I)


def files(path):
    if os.path.isfile(path):
        return [path]
    out = []
    for d, _, fs in os.walk(path):
        out += [os.path.join(d, f) for f in fs if f.endswith(".verse")]
    return sorted(out)


def parse(path):
    """{(file, context path, member name): (signature, flagged)} for every member; definitions are members of their parent too."""
    out = {}
    for f in files(path):
        stack, prev_comment = [], ""
        for raw in open(f, encoding="utf-8", errors="replace"):
            line = raw.rstrip("\n").replace("\t", "    ")
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                prev_comment += " " + s
                continue
            ind = len(line) - len(line.lstrip(" "))
            while stack and stack[-1][0] >= ind:
                stack.pop()
            if s.startswith("using"):
                prev_comment = ""
                continue
            sig = re.sub(r"\s*=\s*external\s*\{\s*\}\s*$", "", s)
            name = re.match(r"([A-Za-z_][\w]*)", sig)
            m = DEF.match(line)
            ctx = " > ".join(x[1] for x in stack)
            key = (os.path.basename(f), ctx, (m.group(1) if m else (name.group(1) if name else sig))) if True else None
            flagged = bool(FLAG.search(prev_comment) or FLAG.search(sig))
            # overloads: keep each signature
            base = key
            n = 0
            while key in out:
                n += 1
                key = base + ("#%d" % n,)
            out[key] = (sig, flagged, bool(m))
            if m:
                stack.append((ind, m.group(1)))
            prev_comment = ""
    return out


def diff(old, new):
    ko, kn = {}, {}
    for k, v in old.items():
        ko.setdefault(k[:3], []).append(v)
    for k, v in new.items():
        kn.setdefault(k[:3], []).append(v)
    added = sorted(k for k in kn if k not in ko)
    removed = sorted(k for k in ko if k not in kn)
    changed = sorted(k for k in kn if k in ko and sorted(x[0] for x in kn[k]) != sorted(x[0] for x in ko[k]))
    return ko, kn, added, removed, changed


def report(old_path, new_path, limit=400):
    old, new = parse(old_path), parse(new_path)
    ko, kn, added, removed, changed = diff(old, new)
    isdef = lambda store, k: any(x[2] for x in store[k])
    flag = lambda store, k: any(x[1] for x in store[k])
    show = lambda k: ((k[1] + " > " if k[1] else "") + k[2])
    L = ["# Verse API diff", "", "%d members before, %d after: %d added, %d removed, %d changed." % (len(ko), len(kn), len(added), len(removed), len(changed)), ""]
    def sect(title, keys, store):
        L.append("## %s (%d)" % (title, len(keys)))
        L.append("")
        if not keys:
            L.append("- none")
        for k in keys[:limit]:
            sig = "; ".join(x[0] for x in store[k])[:150]
            L.append("- `%s`%s %s" % (show(k), " [experimental or deprecated]" if flag(store, k) else "", ("`" + sig + "`") if sig else ""))
        if len(keys) > limit:
            L.append("- ... and %d more" % (len(keys) - limit))
        L.append("")
    sect("Classes, interfaces, enums and modules added", [k for k in added if isdef(kn, k)], kn)
    sect("Classes, interfaces, enums and modules removed", [k for k in removed if isdef(ko, k)], ko)
    sect("Members added", [k for k in added if not isdef(kn, k)], kn)
    sect("Members removed", [k for k in removed if not isdef(ko, k)], ko)
    L += ["## Members whose signature changed (%d)" % len(changed), ""]
    for k in changed[:limit]:
        L.append("- `%s`: `%s` -> `%s`" % (show(k), "; ".join(x[0] for x in ko[k])[:110], "; ".join(x[0] for x in kn[k])[:110]))
    if not changed:
        L.append("- none")
    L += ["", "## Near experimental, deprecated or not publishable (added or changed)", ""]
    fl = [k for k in added + changed if flag(kn, k)]
    L += ["- `%s`" % show(k) for k in fl[:limit]] or ["- none"]
    return "\n".join(L) + "\n", {"added": len(added), "removed": len(removed), "changed": len(changed), "flagged": len(fl)}


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2:
        print(__doc__)
        return 2
    out = None
    lim = 400
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        a = [x for x in a if x != out]
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
        a = [x for x in a if x != str(lim)]
    text, n = report(a[0], a[1], lim)
    if out:
        open(out, "w", encoding="utf-8", newline="\n").write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
