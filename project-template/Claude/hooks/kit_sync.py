#!/usr/bin/env python3
"""Kit self-update + session-start housekeeping (v1.84).

Runs at every fresh Claude session (SessionStart hook, via kit-sync.ps1/.sh). Does four things,
all silent and safe when there is nothing to do:

1. KIT UPDATE  - compares this project's kit files with the reference copy kept in your user
   profile (~/.claude/kit-template, copied there once at install). Files that are missing or
   older are replaced automatically; the previous version of a replaced file is saved under
   Claude/logs/kit-backup/<timestamp>/. settings.json is only ever ADDED to (new hooks), never
   rewritten, and CLAUDE.md only changes inside <!-- KIT:BEGIN x --> ... <!-- KIT:END x --> blocks.
2. GENRE INIT  - creates the genre skill folders for the genre in Claude/docs/.genre (no manual init).
3. COMMUNITY INBOX - packs dropped into ~/.claude/skills/genre/<slug>/local/incoming/*.json are
   validated and turned into ONE proposal each (approve on the Skills page); files are then moved
   to incoming/done/. Nothing changes in your skill until you approve.
4. Prints the hook JSON, including the "kit updated - restart the session" message when files changed.

Never touches: Claude/docs, Claude/logs (except backups), your settings.json permissions, your CLAUDE.md
outside KIT blocks. Best effort: any failure is swallowed so a session can always start.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANAGED = ("Claude/hooks/", "Claude/reference/", "Claude/SETUP-INSTRUCTIONS.md", "Claude/KIT-VERSION")
CREATE_ONLY = ("Claude/docs-template/",)
SKIP_PARTS = ("__pycache__",)
BLOCK_RE = re.compile(r"<!-- KIT:BEGIN ([\w-]+) -->.*?<!-- KIT:END \1 -->", re.S)


def template_dir():
    return os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(os.path.expanduser("~"), ".claude", "kit-template")


def _norm_hash(path):
    with open(path, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _read_version(root):
    try:
        with open(os.path.join(root, "Claude", "KIT-VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
        for n in files:
            full = os.path.join(base, n)
            yield os.path.relpath(full, root).replace(os.sep, "/"), full


def _newer(a, b):
    def t(v):
        return tuple(int(x) for x in re.findall(r"\d+", v)[:4]) or (0,)
    return t(a) > t(b)


def sync_files(project, tpl):
    changed, added, backup = [], [], None
    for rel, src in _walk(tpl):
        managed = rel.startswith(MANAGED)
        create_only = rel.startswith(CREATE_ONLY)
        if not (managed or create_only):
            continue
        dst = os.path.join(project, *rel.split("/"))
        exists = os.path.isfile(dst)
        if exists and (create_only or _norm_hash(src) == _norm_hash(dst)):
            continue
        if exists:
            if backup is None:
                backup = os.path.join(project, "Claude", "logs", "kit-backup", time.strftime("%Y%m%d-%H%M%S"))
            bdst = os.path.join(backup, *rel.split("/"))
            os.makedirs(os.path.dirname(bdst), exist_ok=True)
            shutil.copy2(dst, bdst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        (changed if exists else added).append(rel)
    return changed, added, backup


def _cmd_key(cmd):
    m = re.search(r"([\w.-]+\.(?:ps1|sh|py))", cmd or "")
    return m.group(1) if m else (cmd or "")


def merge_settings(project, tpl):
    """Additive merge: add hook entries whose script the project does not reference yet."""
    tp = os.path.join(tpl, ".claude", "settings.json")
    pp = os.path.join(project, ".claude", "settings.json")
    if not os.path.isfile(tp):
        return []
    with open(tp, encoding="utf-8") as f:
        tset = json.load(f)
    if os.path.isfile(pp):
        with open(pp, encoding="utf-8") as f:
            pset = json.load(f)
    else:
        pset = {"hooks": {}}
    added = []
    phooks = pset.setdefault("hooks", {})
    for event, entries in (tset.get("hooks") or {}).items():
        have = {_cmd_key(h.get("command")) for e in phooks.get(event, []) for h in e.get("hooks", [])}
        for e in entries:
            keys = {_cmd_key(h.get("command")) for h in e.get("hooks", [])}
            if keys and keys <= have:
                continue
            missing = [h for h in e.get("hooks", []) if _cmd_key(h.get("command")) not in have]
            if not missing:
                continue
            ne = dict(e)
            ne["hooks"] = missing
            phooks.setdefault(event, []).append(ne)
            added.append("%s:%s" % (event, ",".join(sorted(keys))))
            have |= keys
    if added:
        os.makedirs(os.path.dirname(pp), exist_ok=True)
        with open(pp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(pset, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return added


def merge_claude_md(project, tpl):
    tp = os.path.join(tpl, "CLAUDE.md")
    pp = os.path.join(project, "CLAUDE.md")
    if not (os.path.isfile(tp) and os.path.isfile(pp)):
        return []
    with open(tp, encoding="utf-8") as f:
        tt = f.read()
    with open(pp, encoding="utf-8", newline="") as f:
        pt = f.read()
    nl = "\r\n" if "\r\n" in pt else "\n"
    pt = pt.replace("\r\n", "\n")
    done = []
    for m in BLOCK_RE.finditer(tt):
        name, block = m.group(1), m.group(0)
        cur = re.search(r"<!-- KIT:BEGIN %s -->.*?<!-- KIT:END %s -->" % (name, name), pt, re.S)
        if cur:
            if cur.group(0) == block:
                continue
            pt = pt[:cur.start()] + block + pt[cur.end():]
        else:
            # first time: replace the old unmarked copy of this rule (added by an earlier kit version), else append
            old = re.search(r"^- \*\*Skill Harness — the genre skill learns.*?(?=^- \*\*|\Z)", pt, re.S | re.M) if name == "skill-harness" else None
            if old:
                pt = pt[:old.start()] + block + "\n" + pt[old.end():]
            else:
                pt = pt.rstrip("\n") + "\n" + block + "\n"
        done.append(name)
    if done:
        with open(pp, "w", encoding="utf-8", newline="") as f:
            f.write(pt.replace("\n", nl))
    return done


def genre_and_inbox(project):
    notes = []
    try:
        sys.path.insert(0, os.path.join(project, "Claude", "hooks"))
        import skills_lib
    except Exception:
        return notes
    try:
        gfile = os.path.join(project, "Claude", "docs", ".genre")
        slug = ""
        if os.path.isfile(gfile):
            with open(gfile, encoding="utf-8") as f:
                slug = f.read().strip().lower()
        if slug:
            try:
                if not os.path.isfile(os.path.join(skills_lib.gdir(slug), "pack", "patterns.json")):
                    skills_lib.init_genre(slug)
                    notes.append("genre skill '%s' created" % slug)
            except ValueError:
                pass
        groot = skills_lib.genre_root()
        for g in (os.listdir(groot) if os.path.isdir(groot) else []):
            inc = os.path.join(groot, g, "local", "incoming")
            if not os.path.isdir(inc):
                continue
            for n in sorted(os.listdir(inc)):
                p = os.path.join(inc, n)
                if not (n.endswith(".json") and os.path.isfile(p)):
                    continue
                try:
                    with open(p, encoding="utf-8") as f:
                        obj = json.load(f)
                    res = skills_lib.merge_pack(g, obj, os.path.splitext(n)[0])
                except Exception as e:
                    res = {"ok": False, "error": str(e)}
                done = os.path.join(inc, "done" if res.get("ok") else "rejected")
                os.makedirs(done, exist_ok=True)
                shutil.move(p, os.path.join(done, n))
                notes.append("community pack %s for '%s': %s" % (n, g, "queued for your approval" if res.get("ok") else "rejected (" + str(res.get("error")) + ")"))
    except Exception:
        pass
    return notes


def run(project):
    out = {"updated": [], "added": [], "settings": [], "claude_md": [], "notes": [], "version": ""}
    tpl = template_dir()
    if os.path.isdir(tpl):
        try:
            tv, pv = _read_version(tpl), _read_version(project)
            out["version"] = tv
            if tv and pv and _newer(pv, tv):
                pass  # project is newer than the profile template: never downgrade
            else:
                out["updated"], out["added"], _ = sync_files(project, tpl)
                out["settings"] = merge_settings(project, tpl)
                out["claude_md"] = merge_claude_md(project, tpl)
        except Exception as e:
            out["notes"].append("kit update skipped: %s" % e)
    out["notes"] += genre_and_inbox(project)
    return out


def main():
    project = os.environ.get("CLAUDE_PROJECT_DIR") or (sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    try:
        r = run(project)
    except Exception:
        r = {"updated": [], "added": [], "settings": [], "claude_md": [], "notes": [], "version": ""}
    changed = r["updated"] or r["added"] or r["settings"] or r["claude_md"]
    msgs = []
    if changed:
        n = len(r["updated"]) + len(r["added"]) + len(r["settings"]) + len(r["claude_md"])
        msgs.append("Kit updated to v%s (%d change%s). Restart the session (close Claude and start it again) so the new files are read. "
                    "Previous versions are saved in Claude/logs/kit-backup/." % (r["version"] or "?", n, "" if n == 1 else "s"))
    msgs += r["notes"]
    if msgs:
        text = " ".join(msgs)
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": "[kit] " + text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
