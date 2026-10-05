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
MANAGED = ("Claude/hooks/", "Claude/reference/", "Claude/SETUP-INSTRUCTIONS.md", "Claude/KIT-VERSION", ".claude/commands/kit-update.md", ".claude/commands/kit-doctor.md", ".claude/commands/restore-point.md", ".claude/commands/verse-map.md")
CREATE_ONLY = ("Claude/docs-template/",)
SKIP_PARTS = ("__pycache__",)
FAILED = []
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
        ok = False
        for attempt in range(4):  # Windows: a file can be locked for a moment (browser, antivirus, console)
            try:
                shutil.copyfile(src, dst)
                ok = True
                break
            except PermissionError:
                time.sleep(0.4 * (attempt + 1))
        if not ok:
            FAILED.append(rel)
            continue
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


REMINDER_NEW = 'echo "Reminder: only if tasks were closed this session and not yet recorded, make ONE batched planner-docs call - never one per reply."'
REMINDER_OLD_PREFIX = "echo Reminder:"


def repair_settings(project):
    """Replace the old / broken unquoted 'echo Reminder: ...' Stop hooks (parentheses broke bash) by the fixed
    one, and drop duplicates. Only touches commands that start with that exact echo."""
    pp = os.path.join(project, ".claude", "settings.json")
    if not os.path.isfile(pp):
        return []
    with open(pp, encoding="utf-8") as f:
        d = json.load(f)
    changed, seen = 0, False
    for ev in (d.get("hooks") or {}).values():
        for e in ev:
            keep = []
            for h in e.get("hooks", []):
                c = h.get("command", "")
                if re.match(r"^echo\s+[\"']?Reminder:", c):
                    if seen:
                        changed += 1
                        continue
                    seen = True
                    if c != REMINDER_NEW:
                        h["command"] = REMINDER_NEW
                        changed += 1
                keep.append(h)
            e["hooks"] = keep
    if changed:
        with open(pp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return ["settings.json: reminder hook repaired"]
    return []


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


def genre_from_epic(project, skills_lib):
    """No Claude/docs/.genre yet but the console already cached Epic's rankings for the island code: Epic
    reports the genre the island is ranked in. Use that slug (it is a fact from Epic, not a guess), check it
    against the official genre list when available, write .genre. Returns the slug or ""."""
    try:
        cache = os.path.join(project, "Claude", "logs", "fortnite-island-rankings-cache.json")
        if not os.path.isfile(cache):
            return ""
        with open(cache, encoding="utf-8-sig") as f:
            body = json.load(f)
        data = (body.get("payload") or body).get("data") or []
        slug = ""
        for row in reversed(data):
            g = (row.get("genres") or [])
            if g and g[0].get("genreSlug"):
                slug = str(g[0]["genreSlug"]).strip().lower()
                break
        if not slug or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", slug):
            return ""
        official = os.path.join(skills_lib.genre_root(), "fortnite-genres-official.json")
        if os.path.isfile(official):
            with open(official, encoding="utf-8") as f:
                known = {g.get("slug") for g in json.load(f).get("genres", [])}
            if known and slug not in known:
                return ""
        gfile = os.path.join(project, "Claude", "docs", ".genre")
        os.makedirs(os.path.dirname(gfile), exist_ok=True)
        with open(gfile, "w", encoding="utf-8", newline="\n") as f:
            f.write(slug + "\n")
        return slug
    except Exception:
        return ""


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
        if not slug:
            slug = genre_from_epic(project, skills_lib)
            if slug:
                notes.append("genre '%s' taken from Epic's ranking of this island and saved in Claude/docs/.genre (edit that file to change it)" % slug)
        if slug and slug != "epic-template":
            try:
                if not os.path.isfile(os.path.join(skills_lib.gdir(slug), "pack", "patterns.json")):
                    skills_lib.init_genre(slug)
                    notes.append("genre skill '%s' created" % slug)
            except ValueError:
                pass
        groot = skills_lib.genre_root()
        for g in (os.listdir(groot) if os.path.isdir(groot) else []):
            inc = os.path.join(groot, g, "local", "incoming")
            for n in (sorted(os.listdir(inc)) if os.path.isdir(inc) else []):
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
            # Official reference packs (shipped with the kit, e.g. distilled from Epic templates/docs) live in
            # <genre>/official/*.json. They are proposed (never applied silently) and the call is idempotent:
            # nothing new -> no proposal, a version you already skipped stays skipped.
            off = os.path.join(groot, g, "official")
            if os.path.isdir(off):
                for n in sorted(os.listdir(off)):
                    p = os.path.join(off, n)
                    if not (n.endswith(".json") and os.path.isfile(p)):
                        continue
                    try:
                        with open(p, encoding="utf-8") as f:
                            obj = json.load(f)
                        res = skills_lib.merge_pack(g, obj, os.path.splitext(n)[0], official=True)
                    except Exception as e:
                        res = {"ok": False, "error": str(e)}
                    if res.get("ok") and res.get("proposal"):
                        notes.append("official reference pack %s for '%s': queued for your approval (Skills page)" % (n, g))
    except Exception:
        pass
    return notes


def docs_align(project):
    """Keep ROADMAP.md / BUGS.md in the current format (adds missing columns, ids), with a backup. Idempotent."""
    try:
        sys.path.insert(0, os.path.join(project, "Claude", "hooks"))
        import docs_migrate
        bk = os.path.join(project, "Claude", "logs", "kit-backup", time.strftime("%Y%m%d-%H%M%S") + "-docs")
        return ["docs aligned: " + n for n in docs_migrate.run(project, bk)]
    except Exception:
        return []


def neutralize_backups(project):
    """Backups must never be compilable: rename any .verse left under Claude/logs/ to .verse.bak
    (v1.86.22: UEFN compiles every .verse below Content/, so a backup copy breaks the build)."""
    notes, n = [], 0
    root = os.path.join(project, "Claude", "logs")
    try:
        for base, dirs, files in os.walk(root):
            for f in files:
                if f.endswith(".verse"):
                    p = os.path.join(base, f)
                    try:
                        os.rename(p, p + ".bak")
                        n += 1
                    except OSError:
                        pass
    except Exception:
        pass
    if n:
        notes.append("backup copies of .verse files renamed to .verse.bak (%d) so UEFN does not compile them" % n)
    return notes


def history_align(project):
    """Move old history out of STATUS/BUGS and condense history comments in big .verse files
    (code is never touched; full text goes to Claude/docs/archive/, backup in kit-backup). Idempotent.
    Opt out: create Claude/docs/.no-history-trim."""
    try:
        sys.path.insert(0, os.path.join(project, "Claude", "hooks"))
        import history_trim
        return ["history trimmed: " + l for l in history_trim.run(project, apply=True)]
    except Exception:
        return []


def restart_console(project):
    """After the kit files changed, restart THIS project's console server so it serves the new files
    (v1.86.8). Only touches a listener on 8765 that answers /whoami with this project. Best effort."""
    import subprocess
    port = 8765
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:%d/whoami" % port, timeout=2) as r:
            who = json.loads(r.read().decode("utf-8"))
        norm = lambda x: os.path.normcase(os.path.abspath(str(x))).rstrip("\\/")
        if norm(who.get("project", "")) != norm(project):
            return ""
    except Exception:
        return ""
    server_ps1 = os.path.join(project, "Claude", "hooks", "agent-console-server.ps1")
    server_py = os.path.join(project, "Claude", "hooks", "agent-console-server.py")
    try:
        if os.name == "nt":
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=10).stdout
            pids = {l.split()[-1] for l in out.splitlines() if (":%d " % port) in l and "LISTENING" in l}
            for pid in pids:
                if pid.isdigit():
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=10)
            time.sleep(0.6)
            if os.path.isfile(server_ps1):
                flags = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
                subprocess.Popen(["powershell", "-ExecutionPolicy", "Bypass", "-File", server_ps1],
                                 creationflags=flags, close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run("lsof -ti tcp:%d | xargs -r kill" % port, shell=True, timeout=10)
            time.sleep(0.6)
            if os.path.isfile(server_py):
                subprocess.Popen([sys.executable, server_py], cwd=project, start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Agent Console restarted with the new files (reload the browser tab)."
    except Exception:
        return ""


LOCK_MAX_AGE = 90


def _acquire_lock(project):
    """Two kit-sync hooks can start together (the project's own and the global one in your profile).
    Only one may write; the other exits quietly. A lock older than 90 s is considered stale."""
    path = os.path.join(project, "Claude", "logs", ".kit-sync.lock")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and time.time() - os.path.getmtime(path) > LOCK_MAX_AGE:
            os.remove(path)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return path
    except FileExistsError:
        return None
    except OSError:
        return ""  # cannot lock (read-only?): carry on without


def run(project):
    out = {"updated": [], "added": [], "settings": [], "claude_md": [], "notes": [], "version": ""}
    lock = _acquire_lock(project)
    if lock is None:
        return out  # another kit-sync is working on this project right now
    try:
        return _run(project, out)
    finally:
        if lock:
            try:
                os.remove(lock)
            except OSError:
                pass


def _run(project, out):
    tpl = template_dir()
    if os.path.isdir(tpl):
        try:
            tv, pv = _read_version(tpl), _read_version(project)
            out["version"] = tv
            out["from"] = pv
            if tv and pv and _newer(pv, tv):
                pass  # project is newer than the profile template: never downgrade
            else:
                out["updated"], out["added"], _ = sync_files(project, tpl)
                out["settings"] = repair_settings(project) + merge_settings(project, tpl)
                out["claude_md"] = merge_claude_md(project, tpl)
        except Exception as e:
            out["notes"].append("kit update skipped: %s" % e)
    if FAILED:
        out["notes"].append("%d file(s) were busy and will be updated at the next session start: %s" % (len(FAILED), ", ".join(FAILED[:3])))
    out["notes"] += docs_align(project)
    out["notes"] += neutralize_backups(project)
    out["notes"] += history_align(project)
    out["notes"] += genre_and_inbox(project)
    try:  # Verse map at session start: refresh an old map (also after a kit update), or bootstrap a missing one
        import verse_map
        mdir = os.path.join(project, "Claude", "docs", "map")
        has_map = os.path.isfile(os.path.join(mdir, "meta.json"))
        if has_map:
            verse_map.cmd_build(project, mdir)
        elif sum(1 for _ in verse_map.verse_files(project)) > 5:
            verse_map.cmd_build(project, mdir)
            out["notes"].append("Verse map created in Claude/docs/map/ (script, no AI tokens). Read INDEX.md plus one card instead of the sources.")
        gp = os.path.join(project, "Claude", "docs", ".genre")
        genre = open(gp, encoding="utf-8").read().strip() if os.path.isfile(gp) else ""
        lr = verse_map.learn_pending(mdir) if genre and genre != "epic-template" else None
        pend = len(lr[1]) if lr else 0
        marker = os.path.join(project, "Claude", "logs", ".post-update")
        if out["updated"] or out["added"]:
            # The agents loaded in THIS session are still the old ones: leave a marker, announce learning after the restart.
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w") as f:
                f.write(out.get("version") or "")
        else:
            was_update = os.path.isfile(marker)
            if was_update:
                try:
                    os.remove(marker)
                except OSError:
                    pass
                out["notes"].append("Kit v%s is active (post-update check done): Verse map %s%s."
                                    % (out.get("version") or "?", "current" if os.path.isfile(os.path.join(mdir, "meta.json")) else "not needed (5 Verse files or fewer)",
                                       (", %d card(s) to learn" % pend) if pend else ", nothing to learn"))
            if pend:
                out["notes"].append("LEARN: %d Verse map card(s) not learned yet%s. Follow planner-docs step 4b: `python Claude/hooks/verse_map.py learn`, "
                                    "read only those cards, queue proposals for the owner's approval, then `verse_map.py learned`."
                                    % (pend, " (first pass: whole map)" if lr[0] else ""))
    except Exception:
        pass
    try:  # restore point at session start when the code changed and the newest point is older than 6 h (silent)
        import safety_net
        pts = safety_net.points(project)
        if not pts or time.time() - os.path.getmtime(os.path.join(project, safety_net.RP, pts[0], "manifest.json")) > 6 * 3600:
            safety_net.snapshot(project, "session start")
    except Exception:
        pass
    if out["updated"] or out["added"]:
        msg = restart_console(project)
        if msg:
            out["notes"].append(msg)
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
        parts = []
        nf = len(r["updated"]) + len(r["added"])
        if nf:
            parts.append("%d file%s (%d new)" % (nf, "" if nf == 1 else "s", len(r["added"])))
        if r["settings"]:
            parts.append("%d hook setting%s" % (len(r["settings"]), "" if len(r["settings"]) == 1 else "s"))
        if r["claude_md"]:
            parts.append("CLAUDE.md block%s: %s" % ("" if len(r["claude_md"]) == 1 else "s", ", ".join(r["claude_md"])))
        project = os.environ.get("CLAUDE_PROJECT_DIR") or (sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
        marker = os.path.join(project, "Claude", "logs", ".kit-sync-reported")
        recent = False
        try:
            recent = os.path.isfile(marker) and time.time() - os.path.getmtime(marker) < 180
            os.makedirs(os.path.dirname(marker), exist_ok=True)
            with open(marker, "w") as f:
                f.write(str(time.time()))
        except OSError:
            pass
        if recent:
            names = ", ".join((r["updated"] + r["added"])[:3]) or "settings"
            msgs.append("✅ KIT: one more step of the same update was applied (%s: %s). Nothing else to do; restart once." % ("; ".join(parts), names))
        else:
            frm = ("from v%s " % r.get("from")) if r.get("from") else "from an old kit "
            msgs.append("✅ KIT UPDATED %sto v%s: %s. Restart Claude Code (close and reopen) so the new files are read. "
                        "Old versions are saved in Claude/logs/kit-backup/." % (frm, r["version"] or "?", "; ".join(parts)))
    msgs += r["notes"]
    if msgs:
        text = " ".join(msgs)
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "SessionStart",
                                                 "additionalContext": "[kit] " + text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
