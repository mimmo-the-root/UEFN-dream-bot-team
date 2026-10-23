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

Files that cannot be deleted are parked in _to_delete/. Never touches: Claude/docs, Claude/logs (except backups), your settings.json permissions, your CLAUDE.md
outside KIT blocks. Best effort: any failure is swallowed so a session can always start.
"""
import hashlib, contextlib, io
import json
import os
import re
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANAGED = ("Claude/hooks/", "Claude/reference/", "Claude/SETUP-INSTRUCTIONS.md", "Claude/KIT-VERSION", "Claude/community/", "Claude/community-revoked.json", ".claude/commands/kit-update.md", ".claude/commands/kit-doctor.md", ".claude/commands/restore-point.md", ".claude/commands/verse-map.md", ".claude/commands/learn-map.md", ".claude/commands/verse-check.md", ".claude/commands/text-scan.md", ".claude/commands/handoff.md", ".claude/commands/ui-kit-check.md", ".claude/commands/mcp-snapshot.md", ".claude/commands/devlog.md", ".claude/commands/jam-check.md", ".claude/commands/concept-card.md")
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


def uplugin_flag(project):
    """Old maps: the .uplugin of the project lacks "EnableVerseAssetReflection": true, so UEFN never generates the assets digest and the Verse build fails
    ("Expected /Asset dir with matching Verse path"). Add the flag (text insertion, BOM/CRLF/indent kept, backup next to the file). Idempotent."""
    notes = []
    cur = os.path.abspath(project)
    for _ in range(4):  # the plugin file sits next to the Content folder: <Plugin>/<Name>.uplugin, project = <Plugin>/Content
        try:
            for n in os.listdir(cur):
                if not n.endswith(".uplugin"):
                    continue
                p = os.path.join(cur, n)
                raw = open(p, "rb").read()
                text = raw.decode("utf-8-sig", errors="replace")
                if '"CanContainVerse"' not in text:
                    continue
                m = re.search(r'"EnableVerseAssetReflection"\s*:\s*(true|false)', text)
                if m:
                    if m.group(1) == "false":
                        notes.append("%s has EnableVerseAssetReflection=false: left as you set it (set it to true if the Verse build asks for the assets digest)." % n)
                    return notes
                lm = re.search(r'^([ \t]*)"CanContainContent"', text, re.M) or re.search(r'^([ \t]*)"[A-Za-z]+"\s*:', text, re.M)
                nl = "\r\n" if "\r\n" in text else "\n"
                ind = lm.group(1) if lm else "\t"
                new = text[:lm.start()] + ind + '"EnableVerseAssetReflection": true,' + nl + text[lm.start():] if lm else text
                if new == text:
                    return notes
                bak = p + ".bak-" + time.strftime("%Y%m%d")
                if not os.path.exists(bak):
                    shutil.copy2(p, bak)
                with open(p, "wb") as f:
                    f.write((b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + new.encode("utf-8"))
                notes.append("%s: added \"EnableVerseAssetReflection\": true (old map; without it UEFN never generates the assets digest). Backup: %s. Restart UEFN so it reloads the plugin." % (n, os.path.basename(bak)))
                return notes
        except OSError:
            pass
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return notes


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
        if slug and slug != "epic-template" and not skills_lib.genre_gate(project):
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
            try:  # update-my-profile overwrites the generated parts of SKILL.md/starter.md with the kit's empty ones: rebuild them from the learned pack (zero tokens)
                if os.path.isfile(os.path.join(groot, g, "pack", "patterns.json")):
                    skills_lib.render_skill(g)
            except Exception:
                pass
            try:  # a map type written two ways (pillar / pillars) becomes one type, with its lessons and evidence
                skills_lib.merge_variants(g, project)
            except Exception:
                pass
        _revoked_ids = []
        try:  # lessons the maintainer revoked leave your skills at the next update; the shipped community packs are offered as ONE proposal per genre
            with open(os.path.join(project, "Claude", "community-revoked.json"), encoding="utf-8") as _f:
                _rv = json.load(_f)
            _revoked_ids = list(_rv.get("ids", []))
            _r = skills_lib.apply_revoked(_revoked_ids)
            if _r.get("removed"):
                notes.append("community: %d revoked lesson(s) removed from your skills" % _r["removed"])
        except Exception:
            pass
        try:
            _c = skills_lib.import_community_dir(revoked_ids=_revoked_ids)
            if _c.get("queued"):
                notes.append("community: %d genre pack(s) of shared lessons waiting for your approval on the Skills page" % _c["queued"])
        except Exception:
            pass
        try:  # is the map of this project published? Only lessons of published maps can be shared with the community (checked at most once a day)
            skills_lib.sync_published(project)
        except Exception:
            pass
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
    try:
        out["notes"] += uplugin_flag(project)
    except Exception:
        pass
    try:
        sys.path.insert(0, os.path.join(project, "Claude", "hooks"))
        import skills_lib as _sl
        m = _sl.sync_profile_from_project(project)
        if m:
            out["notes"].append(m)
    except Exception:
        pass
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
        # a map made only of devices has no Verse code: it still learns from its documents and from the devices in the level
        no_code = bool(genre) and genre != "epic-template" and lr is None
        dp = verse_map.docs_pending(project, mdir) if (lr or no_code) else (True, [])
        pend_docs = len(dp[1])
        dev_todo = no_code and verse_map.devices_pending(mdir)
        prof_todo = bool(genre) and genre != "epic-template" and (has_map or no_code) and verse_map.profile_pending(mdir, project)
        if os.path.isfile(os.path.join(mdir, "meta.json")) or no_code:
            os.makedirs(mdir, exist_ok=True)
            verse_map.write_progress(project, mdir)
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
                                       (", %d file(s) and %d document(s) to learn" % (pend, pend_docs)) if (pend or pend_docs) else ", nothing to learn"))
            spec = os.path.join(project, "Claude", "docs", "SPEC.md")
            has_content = has_map or any(True for _ in verse_map.verse_files(project)) or (os.path.isfile(spec) and os.path.getsize(spec) > 1500)
            if not genre and has_content:
                out["notes"].append("GENRE (MANDATORY, do it now before answering the owner's first message, never ask): Claude/docs/.genre is empty (Epic's data may be missing: no island code, unpublished map or API error 403). Work the genre out YOURSELF from the project: its Verse files, SPEC.md and other documents, the devices in the level. Pick the closest slug in ~/.claude/skills/genre/fortnite-genres-official.json; "
                                    "The genre is ALWAYS one slug of that list (it is Epic's own Discover category, never a new one, never a mechanic): choose by the STRUCTURE of the game, using each genre's `hint` in that file: players per match, round length, lobby, how a match ends, not by single words in the documents ('last one standing' or 'elimination' do not make a Battle Royale: Battle Royale is a large map with 50-100 players and a long match; short rounds in an arena with a lobby are Party & Mini Games). When the island configuration is readable (max players, rounds, time limit), use it. A new mechanic such as pillars is learned INSIDE its genre: the core loop and mechanics become patterns of that genre. If the owner corrects the genre or the type on the console, that is final; if he tells you in chat that it is wrong, run `python Claude/hooks/skills_lib.py confirm-genre <right> --variant <type> --project .` (moves the lessons still waiting for approval). Do NOT write .genre or create the genre skill yourself: run `python Claude/hooks/skills_lib.py propose-genre <slug> --variant <map-type> --why \"<the facts that decided it: players, rounds, lobby, key mechanic>\" --project .` (the map type is a short free name for what this map is, e.g. pillars, red-vs-blue, checkpoint-race; reuse a type already known in that genre when it fits). It writes only a PROPOSAL: the owner confirms genre and type on the console (Skills page), and until then nothing is written to the genre skills (`skills_lib.py` tells you GENRE NOT CONFIRMED: lessons are held and the blueprint stays in Claude/docs/map/profile.json; both are saved by themselves when the owner confirms on the console, nothing for you to retry). IP RULE: if the documents (INDEX/SPEC/README/design notes) say the map is a version of the same base game dressed for an IP or franchise, the map TYPE is that IP as a short kebab-case name (the same base game with a different IP = the same genre, a different type); a map with no IP, or the shared base itself, is type `base`. Take it from the documents, never ask the owner in chat; he confirms it on the console. The blueprint of an IP variant records only what DIFFERS from the base (custom devices, rules, numbers) and points to the base blueprint for the rest. Then learn the core loop and the basic mechanics of this map (learn-map.md: the Verse files, the documents including planned design, the devices) so the next session starts from it.")
            if genre and genre != "epic-template" and (has_map or no_code or any(True for _ in verse_map.verse_files(project))):
                try:
                    import skills_lib as _sl2
                    _gs = _sl2.genre_state(project)
                    if _gs["status"] == "confirmed" and not _gs["variant"]:
                        out["notes"].append("TYPE (MANDATORY, before answering the owner's first message, never ask in chat): the genre '%s' is set but this map has no TYPE yet (pillars, red-vs-blue, checkpoint-race...). Decide it from the code, documents and devices (a short free name; reuse a type known in the genre when it fits: `python Claude/hooks/skills_lib.py patterns %s` shows the variants used) and run `python Claude/hooks/skills_lib.py propose-genre %s --variant <type> --why \"<facts>\" --project .` : the owner confirms it on the console (Skills page) before anything is written to the skills. IP RULE: if the documents (INDEX/SPEC/README/design notes) say the map is a version of the same base game dressed for an IP or franchise, the map TYPE is that IP as a short kebab-case name (the same base game with a different IP = the same genre, a different type); a map with no IP, or the shared base itself, is type `base`. Take it from the documents, never ask the owner in chat; he confirms it on the console. The blueprint of an IP variant records only what DIFFERS from the base (custom devices, rules, numbers) and points to the base blueprint for the rest." % (genre, genre, genre))
                except Exception:
                    pass
            if genre and genre != "epic-template" and (has_map or no_code) and not prof_todo:
                gaps, lessons_due = verse_map.profile_gaps(mdir), verse_map.profile_lessons_due(mdir)
                st0 = verse_map._read_state(os.path.join(mdir, "profile-learned.json"))
                if gaps:
                    verse_map.marker_update(mdir, gap_tries=st0.get("gap_tries", 0) + 1)
                    out["notes"].append("BLUEPRINT GAPS (MANDATORY, before answering the owner's first message, never ask): the map blueprint (Claude/docs/map/profile.json) lists `unknown` items. Read exactly those through the UEFN MCP (GetDeviceProperties / ListEventBindings / find_actors, the island configuration) when UEFN is connected, write what you read into the matching fields, remove it from `unknown`, and save again with `python Claude/hooks/skills_lib.py profile %s --map \"<name>\" --file Claude/docs/map/profile.json --project .`. What you cannot read stays in `unknown` (never invent a number); if UEFN is not connected do nothing now. This is try %d of 2." % (genre, st0.get("gap_tries", 0) + 1))
                if lessons_due:
                    verse_map.marker_update(mdir, lessons_asked=1)
                    out["notes"].append("LESSONS FROM THIS MAP (MANDATORY once, before answering the owner's first message, never ask): the blueprint of this map is written but no lesson was proposed from it. Queue 3 to 5 GENERAL lessons the blueprint teaches (how this kind of map is built: which devices drive the loop, how they are wired, which numbers worked), no map names or codes, one pattern each: `python Claude/hooks/skills_lib.py patterns %s` shows the wording already used (reuse it to add support), then `python Claude/hooks/skills_lib.py propose %s --variant <map type> --section <section> --condition \"...\" --action \"...\" --statement \"...\" --map \"<name>\"`. The owner approves them on the console. If nothing generalizes, propose none." % (genre, genre, genre))
            nverse = sum(1 for _ in verse_map.verse_files(project)) if no_code else 0
            code_txt = "no Verse files" if not nverse else "only %d Verse file(s), too few for a map: READ THEM COMPLETELY yourself (Read tool) before the documents" % nverse
            if no_code and (pend_docs or dev_todo or prof_todo):
                out["notes"].append("LEARN (MANDATORY, before answering the owner's first message whatever it is; never ask, never offer it as optional, never skip it because the message was about something else): this map has no Verse code map (%s). Learn from %d project document(s) not read yet%s and from the devices in the level. "
                                    "Follow `.claude/commands/learn-map.md` steps 1, 2, 6 and 7 (skip 3-5): documents first (`verse_map.py docs`, compared with the level and the device map; apply corrections with `docpatch`, record a decision for every document), "
                                    "then read the wiring and settings of the devices through the MCP and write `Claude/docs/map/DEVICES.md` with the `WIRING-READ:`/`SETTINGS-READ:`/`ISLAND-CONFIG-READ:` lines (the island configuration too: max players, teams, rounds, time limit, spawn mode). Then write the MAP BLUEPRINT (learn-map step 8): what this map is made of, its game loop, devices, rules and build order, so the genre skill knows how to build such a map. Queue generalized patterns with `skills_lib.py propose --section` (devices, architecture, run-loop, ...), "
                                    "never ask. If the session stops early, unmarked work restarts at the next session start (`Claude/docs/map/PROGRESS.md`)." % (code_txt, pend_docs, " (first pass)" if dp[0] else ""))
            if (pend or pend_docs or prof_todo) and not no_code:
                out["notes"].append("LEARN (MANDATORY, before answering the owner's first message whatever it is; never ask, never offer it as optional, never skip it because the message was about something else): %d Verse file(s) (complete source) and %d project document(s) not learned yet%s. Follow `.claude/commands/learn-map.md` (planner-docs step 4b): "
                                    "If the session stops early, nothing is needed: unmarked work is read again at the next start (`Claude/docs/map/PROGRESS.md` lists what is missing). "
                                    "code first (`verse_map.py learn`, complete sources), then documents (`verse_map.py docs`) compared with the code, then the devices in the level read through the MCP, then the MAP BLUEPRINT (learn-map step 8: what the map is made of, game loop, devices, rules, build order); queue proposals for the owner's approval, report discrepancies, never edit documents."
                                    % (pend, pend_docs, " (first pass: whole map and all documentation)" if lr[0] else ""))
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


def _log_run(project, r, emitted, announce):
    """One line per session start in Claude/logs/kit-sync.log (last 60 kept): lets us see what the hook did when no message shows."""
    try:
        lp = os.path.join(project, "Claude", "logs", "kit-sync.log")
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        line = "%s from=%s to=%s updated=%d added=%d settings=%d notes=%d emitted=%s announce=%s" % (
            time.strftime("%Y-%m-%d %H:%M:%S"), r.get("from") or "?", r.get("version") or "?", len(r["updated"]), len(r["added"]),
            len(r["settings"]), len(r["notes"]), emitted, announce)
        old = open(lp, encoding="utf-8").read().splitlines()[-59:] if os.path.isfile(lp) else []
        with open(lp, "w", encoding="utf-8") as f:
            f.write("\n".join(old + [line]) + "\n")
    except Exception:
        pass


def auto_update_check():
    """v1.108.3: at most once every 6 hours, start a detached background check of the newest GitHub release
    (kit_fetch.py --auto). Never delays or fails a session; the new kit reaches this project at the NEXT session start.
    Off: UEFN_KIT_AUTOUPDATE=0 or an empty ~/.claude/kit-auto-update.off. The global hook does the same (shared stamp)."""
    import subprocess
    home = os.environ.get("UEFN_HOME") or os.path.join(os.path.expanduser("~"), ".claude")
    fetch = os.path.join(HERE, "kit_fetch.py")
    stamp = os.path.join(home, "kit-update-check.stamp")
    if os.environ.get("UEFN_KIT_AUTOUPDATE") == "0" or os.path.exists(os.path.join(home, "kit-auto-update.off")) or not os.path.isfile(fetch):
        return False
    try:
        if os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 6 * 3600:
            return False
        os.makedirs(home, exist_ok=True)
        with open(stamp, "w") as f:
            f.write(str(time.time()))
    except OSError:
        return False
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, fetch, "--auto"], **kw)
    return True


def main():
    project = os.environ.get("CLAUDE_PROJECT_DIR") or (sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    try:
        # Hooks must print ONE JSON object and nothing else: anything a helper prints (e.g. "map built: ...")
        # would make Claude Code ignore the whole message, so all helper output is captured here.
        with contextlib.redirect_stdout(io.StringIO()):
            r = run(project)
    except Exception:
        r = {"updated": [], "added": [], "settings": [], "claude_md": [], "notes": [], "version": ""}
    try:  # the MCP map keeps itself current: a cheap check, the mapping runs in the background
        import mcp_map
        news = mcp_map.session_check(project)
        if news:
            r["notes"].append(news)
    except Exception:  # noqa: BLE001
        pass
    try:
        auto_update_check()
    except Exception:  # noqa: BLE001
        pass
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
    announce = bool(changed) or any("post-update check done" in n for n in r["notes"])
    _log_run(project, r, bool(msgs), announce)
    if msgs:
        text = " ".join(msgs)
        ctx = "[kit] " + text
        if announce:
            # The UI may not show a hook's systemMessage: also ask the model to say it in its first reply.
            ctx += (" ACTION (kit): in your FIRST reply tell the owner, in one short line, what the kit just did above"
                    " (version, and that Claude Code must be closed and reopened once if it says so). Say it once only."
                    " If a LEARN line is present, do not ask permission: after that line, run the learning at once"
                    " (`.claude/commands/learn-map.md` steps); it only queues proposals, nothing changes without the owner's approval.")
        print(json.dumps({"systemMessage": text,
                          "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
