#!/usr/bin/env python3
"""Fab lab (v1.109.1, console and checklist since v1.110): collect lessons from a Fab product WITHOUT putting a single file in the project.

A Fab product is zipped whole, so the kit installs nothing in it (no Claude/ folder, no hooks). The learning data
therefore lives in your profile: ~/.claude/fab-lab/<ProductName>/Claude/logs/..., laid out like a map project so the
console and the lesson tools can read it.

Lives in ~/.claude/hooks.

  fab_lab.py hook                      # global PostToolUse / PostToolUseFailure hook (reads the payload on stdin)
  fab_lab.py status <project>          # where the data is, how many MCP calls were recorded
  fab_lab.py path <project>            # the lab folder
  fab_lab.py card <project> [--title T]  # draft closing card (what was done, what failed) in Claude/docs/lessons/
  fab_lab.py propose <project> "<statement>" [--when W] [--do D]   queue a lesson for the owner to approve
  fab_lab.py draft-recipe <project> "<name>"   draft JSON of a mechanic recipe (Verse code, calls that worked); fill the TODOs, then skills_lib.py recipe-add mechanics
  fab_lab.py lessons                   the lessons the owner approved (every Fab product reads them)
  fab_lab.py console <project> [port] [--foreground]  # Agent Console on the lab data (default port 8766)

Rules: only projects registered as "fab" (kit_install.py --kind) are recorded; maps keep using their own hooks.
Nothing is sent anywhere. Nothing is written in the project. The hook never blocks or fails a tool call.
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.join(os.path.expanduser("~"), ".claude")


def lab_base():
    return os.environ.get("UEFN_FAB_LAB_DIR") or os.path.join(HOME, "fab-lab")


def template_hooks():
    tpl = os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(HOME, "kit-template")
    return os.path.join(tpl, "Claude", "hooks")


def _ki():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import kit_install
    return kit_install


def _tpl_mod(name):
    d = template_hooks()
    if d not in sys.path:
        sys.path.insert(0, d)
    return __import__(name)


def safe_name(root):
    n = re.sub(r"[^A-Za-z0-9_.-]+", "_", os.path.basename(os.path.abspath(root))).strip("._")
    return n or "product"


def lab_dir(root):
    return os.path.join(lab_base(), safe_name(root))


def ensure_lab(root):
    lab = lab_dir(root)
    for sub in (("Claude", "logs"), ("Claude", "docs", "lessons")):
        os.makedirs(os.path.join(lab, *sub), exist_ok=True)
    kv =os.path.join(os.path.dirname(template_hooks()), "KIT-VERSION")
    dst = os.path.join(lab, "Claude", "KIT-VERSION")
    try:
        if os.path.isfile(kv):
            with open(kv, encoding="utf-8") as f:
                v = f.read()
            if not os.path.isfile(dst) or open(dst, encoding="utf-8").read() != v:
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(v)
    except OSError:
        pass
    meta = os.path.join(lab, "product.json")
    if not os.path.isfile(meta):
        with open(meta, "w", encoding="utf-8") as f:
            json.dump({"name": os.path.basename(os.path.abspath(root)), "project": os.path.abspath(root), "kind": "fab"}, f, indent=2)
    return lab


def fab_root(base):
    """The UEFN project root of `base` when it is registered as a Fab product, else None."""
    ki = _ki()
    r = ki.find_uefn_root(base)
    if not r:
        return None
    return r[0] if ki.get_kind(r[0]) == "fab" else None


def ledger_path(root):
    return os.path.join(lab_dir(root), "Claude", "logs", "explore-ledger.jsonl")


def record_agent(payload, root):
    """Subagent start/stop line for the Agent Console (same format as a map: agent-console.jsonl), so an agent such as materials-expert
    is seen working while it runs. Returns the line or None."""
    ev = payload.get("hook_event_name")
    if ev == "PreToolUse" and payload.get("tool_name") in ("Task", "Agent"):
        ti = payload.get("tool_input") or {}
        row = {"event": "start", "agent": str(ti.get("subagent_type") or "unknown")[:80], "desc": str(ti.get("description") or "")[:200]}
    elif ev == "SubagentStop" and payload.get("agent_type"):
        row = {"event": "stop", "agent": str(payload["agent_type"])[:80], "desc": ""}
    else:
        return None
    row = dict({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, **row)
    ensure_lab(root)
    with open(os.path.join(lab_dir(root), "Claude", "logs", "agent-console.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def full_args(args, fallback="", limit=8000, text_limit=3000):
    """Arguments as JSON for the lab ledger: whole when they fit in `limit`, else every long string is shortened to `text_limit`."""
    try:
        s = json.dumps(args, ensure_ascii=False)
        if len(s) <= limit:
            return s

        def cut(v):
            if isinstance(v, str):
                return v[:text_limit]
            if isinstance(v, dict):
                return {k: cut(x) for k, x in v.items()}
            if isinstance(v, list):
                return [cut(x) for x in v[:50]]
            return v
        return json.dumps(cut(args), ensure_ascii=False)[:limit * 2]
    except (TypeError, ValueError):
        return fallback


def record(payload):
    """Append the ledger row of one MCP call (or the start/stop line of a subagent). Returns the row or None."""
    base = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = fab_root(base)
    if not root:
        return None
    if payload.get("hook_event_name") == "SubagentStop" or payload.get("tool_name") in ("Task", "Agent"):
        return record_agent(payload, root)
    row = _tpl_mod("mcp_work_log").row_from_payload(payload)
    if not row:
        return None
    # a lesson needs the real values (scripts, parameter names): keep the arguments much longer than the map ledger does
    row["args"] = full_args((payload.get("tool_input") or {}).get("arguments") or {}, row.get("args", ""))
    ensure_lab(root)
    with open(ledger_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_rows(root):
    rows = []
    try:
        with open(ledger_path(root), encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    except OSError:
        pass
    return rows


def status(root):
    rows = read_rows(root)
    bad = [r for r in rows if r.get("r") != "ok"]
    days = sorted({r.get("d", "") for r in rows if r.get("d")})
    cards = []
    try:
        cards = sorted(os.listdir(os.path.join(lab_dir(root), "Claude", "docs", "lessons")))
    except OSError:
        pass
    return {"lab": lab_dir(root), "calls": len(rows), "failed": len(bad), "days": days, "cards": cards}


def card(root, title=None):
    """A draft closing card from the ledger: the calls that changed the editor and the ones that failed. The agent then fills in the
    parts only a human or the agent knows (goal, final parameters, what to do next time)."""
    ec = _tpl_mod("editor_changes")
    rows = read_rows(root)
    ok_w, fails = {}, {}
    for r in rows:
        tool = r.get("tool", "")
        if r.get("r") == "ok" and ec.is_write(tool):
            ok_w[tool] = ok_w.get(tool, 0) + 1
        elif r.get("r") != "ok":
            k = (tool, (r.get("why") or r.get("peek") or "")[:120])
            fails[k] = fails.get(k, 0) + 1
    name = os.path.basename(os.path.abspath(root))
    day = time.strftime("%Y-%m-%d")
    t = title or "Closing card"
    lines = ["# %s - %s (%s)" % (t, name, day), "",
             "Draft made from the MCP ledger of this product (%d calls). Fill in the parts marked TODO, then ask the owner whether to promote it into a skill or recipe." % len(rows),
             "", "## Goal", "TODO: what was built (material / mechanic) and for which use.", "",
             "## What changed in the editor (calls that worked)"]
    lines += ["- %s x%d" % (k, v) for k, v in sorted(ok_w.items())] or ["- nothing recorded"]
    lines += ["", "## The calls that worked, in order (arguments as recorded)"]
    seq = [r for r in rows if r.get("r") == "ok" and ec.is_write(r.get("tool", ""))]
    lines += ["%d. `%s` %s" % (i + 1, r.get("tool", ""), (r.get("args") or "")[:400]) for i, r in enumerate(seq[:40])] or ["- none"]
    if len(seq) > 40:
        lines.append("- ... and %d more in the ledger" % (len(seq) - 40))
    lines += ["", "## What failed along the way"]
    lines += ["- %s x%d: %s" % (k[0], v, k[1]) for k, v in sorted(fails.items())] or ["- no failed calls recorded"]
    lines += ["", "## What worked (final recipe)", "TODO: ordered steps and the final parameter values that gave the result.", "",
              "## What to do differently next time", "TODO: traps, wrong paths, values that did not work.", "",
              "## Third-party assets used", "TODO: name, author, licence, where it is declared (Fab needs this).", ""]
    d = os.path.join(ensure_lab(root), "Claude", "docs", "lessons")
    slug = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "card"
    path = os.path.join(d, "%s-%s.md" % (day, slug))
    n = 2
    while os.path.exists(path):
        path = os.path.join(d, "%s-%s-%d.md" % (day, slug, n))
        n += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _whoami(port):
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/whoami" % port, timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _current_kit_version():
    try:
        with open(os.path.join(os.path.dirname(template_hooks()), "KIT-VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _quit_console(port):
    import urllib.request
    try:
        urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:%d/quit" % port, data=b"{}", method="POST"), timeout=2).read()
    except Exception:
        pass


def autostart(root, port=8766, open_browser=True):
    """Session start of a Fab product: make sure the console of THIS product is running (a newer one replaces an older one) and open it in the
    browser when it was not running yet. Started through PowerShell's Start-Process on Windows (it outlives the hook and the agent's own shell,
    which a plain background command does not). Returns the URL or None."""
    lab = ensure_lab(root)
    here = os.path.normcase(os.path.abspath(lab))
    def find():
        for p in range(port, port + 4):
            w = _whoami(p)
            if w and os.path.normcase(os.path.abspath(w.get("project", ""))) == here:
                return p, w
        return None, None
    p, w = find()
    if w and w.get("kit_version") == _current_kit_version() and "fab_product" in (w.get("caps") or []):
        return "http://127.0.0.1:%d/" % p
    me = os.path.abspath(__file__)
    if os.name == "nt":
        q = lambda x: "'" + x.replace("'", "''") + "'"
        ps = "Start-Process -WindowStyle Hidden -FilePath %s -ArgumentList @(%s,'console',%s,'%d','--foreground')" % (q(sys.executable), q('"' + me + '"'), q('"' + root + '"'), port)
        subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=0x08000000)
    else:
        console(root, port)
    for _ in range(24):
        time.sleep(0.5)
        p, w = find()
        if w and w.get("kit_version") == _current_kit_version():
            break
    if not w:
        return None
    url = "http://127.0.0.1:%d/" % p
    if open_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
    return url


def console(root, port=8766, foreground=False):
    """Start the Agent Console on the lab data. foreground=True keeps it running in THIS terminal (close the window to stop it): use it
    when a background start is killed together with the program that launched it. Returns (ok, message)."""
    lab = ensure_lab(root)
    url = "http://127.0.0.1:%d/" % port
    who = _whoami(port)
    if who and os.path.normcase(os.path.abspath(who.get("project", ""))) == os.path.normcase(os.path.abspath(lab)):
        if who.get("kit_version") == _current_kit_version() and "fab_product" in (who.get("caps") or []):
            return True, "already running: " + url
        _quit_console(port)  # same product but an older console (started before the profile was updated): replace it
        for _ in range(10):
            time.sleep(0.4)
            if not _whoami(port):
                break
        who = _whoami(port)
        if who:  # an old console that cannot be asked to quit: use the next free port instead of showing stale pages
            return console(root, port + 1, foreground)
    if who:
        return False, "port %d is used by another console (%s): choose another port, for example `console <project> %d`" % (port, who.get("project", "?"), port + 1)
    server = os.path.join(template_hooks(), "agent-console-server.py")
    if not os.path.isfile(server):
        return False, "console server not found (%s): run update-my-profile.cmd" % server
    env = dict(os.environ, UEFN_FAB_LAB=lab)
    if foreground:
        print("Console on the lab data of this Fab product: " + url + "  (close this window to stop it)", flush=True)
        subprocess.call([sys.executable, server, str(port)], env=env, cwd=lab)
        return True, "stopped"
    log = os.path.join(lab, "console.log")
    kw = {"stdin": subprocess.DEVNULL, "close_fds": True, "env": env, "cwd": lab}  # cwd = the lab: relative paths must never land in the project
    kw["stdout"] = open(log, "w", encoding="utf-8")
    kw["stderr"] = subprocess.STDOUT
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x01000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | BREAKAWAY_FROM_JOB
    else:
        kw["start_new_session"] = True
    try:
        subprocess.Popen([sys.executable, server, str(port)], **kw)
    except OSError:
        kw["creationflags"] = 0x00000008 | 0x00000200  # breakaway not allowed here
        subprocess.Popen([sys.executable, server, str(port)], **kw)
    for _ in range(12):
        time.sleep(0.5)
        if _whoami(port):
            return True, url
    tail = ""
    try:
        tail = open(log, encoding="utf-8", errors="replace").read()[-400:]
    except OSError:
        pass
    return False, ("the console did not answer on %s. Run it in your own terminal so it stays alive: `fab_lab.py console <project> --foreground`. %s" % (url, tail)).strip()


# ---- lessons: proposals the owner approves (v1.110) -----------------------------

PRIVATE = re.compile(r"[A-Za-z]:\\|/Us" r"ers/|/ho" r"me/|https?:" r"//|\b[BT]-\d{3}\b")


def lessons_file():
    return os.environ.get("UEFN_FAB_LESSONS") or os.path.join(HOME, "fab-lessons.json")


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


def proposals_path(root):
    return os.path.join(lab_dir(root), "proposals.json")


def flag_path(root):
    return os.path.join(lab_dir(root), "learn-request.json")


def _norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def propose(root, statement, when="", do="", source="agent", evidence=""):
    """Queue ONE lesson for the owner to approve. Refuses paths, links, task ids and sentences that are too short or too long. Returns the id or None (duplicate)."""
    import hashlib
    statement = " ".join(str(statement).split())
    for s in (statement, when, do, evidence):
        if PRIVATE.search(s or ""):
            raise ValueError("a lesson is a general rule: no paths, links or task ids")
    if not 20 <= len(statement) <= 400:
        raise ValueError("the statement must be 20 to 400 characters")
    ensure_lab(root)
    items = _jload(proposals_path(root), [])
    approved = _jload(lessons_file(), [])
    key = _norm(statement)
    if any(_norm(x.get("statement", "")) == key for x in items + approved):
        return None
    pid = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    items.append({"id": pid, "statement": statement, "when": " ".join(str(when).split())[:200], "do": " ".join(str(do).split())[:300], "source": source,
                  "evidence": " ".join(str(evidence).split())[:200], "status": "pending", "at": time.strftime("%Y-%m-%d %H:%M")})
    _jsave(proposals_path(root), items)
    return pid


def _arg_keys(row):
    """Parameter NAMES of a call (never the values: they can hold paths or names)."""
    try:
        a = json.loads(row.get("args") or "{}")
    except (TypeError, ValueError):
        return []
    if isinstance(a, dict) and isinstance(a.get("arguments"), dict):
        a = a["arguments"]
    return sorted(a.keys())[:12] if isinstance(a, dict) else []


def ledger_candidates(root, limit=5):
    """Lessons that need no AI, from the ledger: HOW things were done (a call that failed and then worked: what changed; tools that
    worked again and again: the parameters that worked) and what failed. Returns the number of new proposals."""
    rows = read_rows(root)
    n = 0

    def add(statement, when, do, evidence):
        nonlocal n
        try:
            if propose(root, statement, when=when, do=do, source="ledger", evidence=evidence):
                n += 1
        except ValueError:
            pass
    # 1) failed, then fixed: the fix is the know-how
    fixed = 0
    for i, r in enumerate(rows):
        if r.get("r") == "ok" or fixed >= limit:
            continue
        nxt = next((x for x in rows[i + 1:i + 12] if x.get("tool") == r.get("tool") and x.get("r") == "ok"), None)
        if not nxt:
            continue
        bad, good = _arg_keys(r), _arg_keys(nxt)
        why = " ".join(str(r.get("why") or r.get("peek") or "").split())[:120]
        if good and (bad != good or why):
            add("How to call %s: it worked with the parameters %s%s." % (r.get("tool"), ", ".join(good),
                (" (the first try failed with: %s)" % why) if why else ""),
                "when you call %s" % r.get("tool"), "use exactly those parameter names", "failed, then worked in this product")
            fixed += 1
    # 2) tools that worked several times: the shape that works
    ok = {}
    for r in rows:
        if r.get("r") == "ok" and r.get("tool"):
            ok.setdefault(r["tool"], []).append(r)
    for tool, rs in sorted(ok.items(), key=lambda kv: -len(kv[1]))[:limit]:
        if len(rs) >= 3 and _arg_keys(rs[-1]):
            add("%s worked %d times in this product with the parameters %s." % (tool, len(rs), ", ".join(_arg_keys(rs[-1]))),
                "when you need to do what %s does" % tool, "start from this call shape", "worked %d times" % len(rs))
    # 3) what failed (grouped)
    groups = {}
    for r in rows:
        if r.get("r") == "ok":
            continue
        why = " ".join(str(r.get("why") or r.get("peek") or "").split())[:140]
        if why:
            groups[(r.get("tool", ""), why)] = groups.get((r.get("tool", ""), why), 0) + 1
    for (tool, why), c in sorted(groups.items(), key=lambda kv: -kv[1])[:limit]:
        add("The editor tool %s failed with: %s. Look the tool up in the tool table and use the exact parameter names before calling it." % (tool, why),
            "before calling %s" % tool, "read its entry in the tool table (mcp_map.py --find)", "failed %d time(s) in this product" % c)
    return n


def learn_request(root):
    """The owner pressed Learn: add the no-AI candidates now and ask the agent to continue at the end of its next answer."""
    ensure_lab(root)
    n = ledger_candidates(root)
    try:
        ensure_auto_recipe(root, force=True)
    except Exception:
        pass
    _jsave(flag_path(root), {"at": time.strftime("%Y-%m-%d %H:%M"), "state": "waiting"})
    return {"new_candidates": n}


def learn_state(root):
    try:
        ensure_auto_recipe(root)
    except Exception:
        pass
    items = _jload(proposals_path(root), [])
    st = status(root)
    return {"flag": _jload(flag_path(root), None), "proposals": items, "lessons": len(_jload(lessons_file(), [])), "calls": st["calls"], "failed": st["failed"], "cards": st["cards"]}


def act(root, action, pid, text=None):
    items = _jload(proposals_path(root), [])
    it = next((x for x in items if x.get("id") == pid), None)
    if not it:
        raise ValueError("unknown proposal")
    if action == "approve":
        if text:
            for s in (text,):
                if PRIVATE.search(s):
                    raise ValueError("a lesson is a general rule: no paths, links or task ids")
            it["statement"] = " ".join(text.split())[:400]
        les = _jload(lessons_file(), [])
        les.append({"id": it["id"], "statement": it["statement"], "when": it.get("when", ""), "do": it.get("do", ""), "at": time.strftime("%Y-%m-%d")})
        _jsave(lessons_file(), les)
        it["status"] = "approved"
    elif action == "reject":
        it["status"] = "rejected"
    else:
        raise ValueError("unknown action")
    _jsave(proposals_path(root), items)


def lessons_text():
    les = _jload(lessons_file(), [])
    if not les:
        return "no approved Fab lessons yet"
    return "\n".join("- %s%s%s" % (x["statement"], (" WHEN: " + x["when"]) if x.get("when") else "", (" DO: " + x["do"]) if x.get("do") else "") for x in les)


def stop_hook(payload):
    """Stop hook: when the owner pressed Learn on the console, ask the agent to finish the learning at the end of its answer (once)."""
    if payload.get("stop_hook_active"):
        return None
    base = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = fab_root(base)
    if not root:
        return None
    f = _jload(flag_path(root), None)
    if not f or f.get("state") != "waiting":
        return None
    f["state"] = "sent"
    f["sent_at"] = time.strftime("%Y-%m-%d %H:%M")
    _jsave(flag_path(root), f)
    hooks = os.path.dirname(os.path.abspath(__file__))
    msg = ("The owner asked you to LEARN from this Fab product (button on the console). Do it now, briefly: "
           "1) run `python %s card %s` and fill the TODO parts of the closing card from what really happened; "
           "2) propose up to 5 general lessons with `python %s propose %s \"<statement>\" --when \"<when>\" --do \"<what to do>\"` "
           "(mostly HOW to do things: the steps and the settings that worked for a material, widget, mechanic or Verse feature, and in which order; "
           "mistakes only as a short 'avoid' note; no paths, no links, no task ids; only what the ledger or the work really showed); "
           "3) for each material save its recipe with skills_lib.py recipe-add materials; for each stand-alone device, mechanic or template the owner confirmed works, "
           "run `python %s draft-recipe %s \"<name>\"`, fill every TODO from what really happened (devices, settings, wiring, Verse files, assets, how to verify) and save it with skills_lib.py recipe-add mechanics <file> \"<product name>\" "
           "so it can be rebuilt later. "
           "The owner approves the proposals on the console Skills page. Then say in one line what you proposed. If there is nothing to learn, say so and stop."
           % (os.path.join(hooks, "fab_lab.py"), root, os.path.join(hooks, "fab_lab.py"), root, os.path.join(hooks, "fab_lab.py"), root))
    return {"decision": "block", "reason": msg}


# ----------------------------------------------------------------------------- automatic mechanic recipe (no AI, no agent)
def auto_recipe(root):
    """Mechanics recipe prepared by the kit from the product itself (see mechanic_recipes.py). Returns the dict or None."""
    mr = _tpl_mod("mechanic_recipes")
    return mr.build(mr.verse_files(root), os.path.basename(os.path.abspath(root)), doc_root=root, assets_root=os.path.join(root, "Content"))


def ensure_auto_recipe(root, force=False):
    """Prepare and save the mechanics recipe of this product by itself; repeated only when the Verse files changed. Returns the result dict or None."""
    mr = _tpl_mod("mechanic_recipes")
    files = mr.verse_files(root)
    if not files:
        return None
    sig = mr.signature(files)
    mark = os.path.join(lab_dir(root), "auto-recipe.json")
    if not force and _jload(mark, {}).get("sig") == sig:
        return None
    rec = auto_recipe(root)
    if not rec:
        return None
    try:
        r = _tpl_mod("skills_lib").recipe_add("mechanics", rec, safe_name(root))
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if r.get("ok"):
        ensure_lab(root)
        _jsave(mark, {"sig": sig, "name": rec["name"], "at": time.strftime("%Y-%m-%d %H:%M")})
    return dict(r, name=rec["name"])


def draft_recipe(root, name):
    """Draft of a mechanics recipe for this product: its Verse files with the code, the editor calls that worked in order (tool and
    parameter NAMES only), and TODO fields for what only the work knows. Written in the lab folder; returns the path."""
    verse = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("Intermediate", "Saved", "node_modules")]
        for f in sorted(files):
            if f.endswith(".verse") and len(verse) < 12:
                try:
                    with open(os.path.join(base, f), encoding="utf-8", errors="replace") as fh:
                        verse.append({"name": f, "code": fh.read()[:40000]})
                except OSError:
                    pass
    steps, last = [], None
    for r in read_rows(root):
        if r.get("r") != "ok" or not r.get("tool") or r["tool"] == last:
            continue
        last = r["tool"]
        k = _arg_keys(r)
        steps.append("TODO say in words what this did: %s(%s)" % (r["tool"], ", ".join(k)))
    steps = steps[:40]
    rec = {"name": name, "kind": "TODO device | mechanic | template", "use": "TODO what it is for, one or two sentences",
           "steps": steps or ["TODO the ordered steps to rebuild it"], "devices": ["TODO name: what it does"],
           "settings": ["TODO which setting on which device"], "wiring": ["TODO what is connected to what"],
           "files": verse, "assets": ["TODO what it needs and where it comes from"], "verify": "TODO how to see that it works"}
    d = os.path.join(lab_dir(root), "Claude", "docs", "recipes")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, (re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "recipe").strip("._") or "recipe") + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    return path


def main(argv):
    if not argv:
        print(__doc__); return 2
    cmd = argv[0]
    if cmd == "stop":
        try:
            out = stop_hook(json.loads(sys.stdin.read() or "{}"))
            if out:
                print(json.dumps(out))
        except Exception:
            pass
        return 0
    if cmd == "lessons":
        print(lessons_text()); return 0
    if cmd == "hook":
        try:
            p = json.loads(sys.stdin.read() or "{}")
            record(p)
        except Exception:
            pass
        return 0
    if len(argv) < 2:
        print(__doc__); return 2
    root = _ki().find_uefn_root(argv[1])
    root = root[0] if root else None
    if not root:
        print("not a UEFN project folder"); return 1
    if cmd == "path":
        print(lab_dir(root)); return 0
    if cmd == "status":
        if _ki().get_kind(root) != "fab":
            print("this project is not registered as a Fab product (kit_install.py --kind <root> fab): nothing is recorded"); return 3
        s = status(root)
        print("lab: %s\ncalls recorded: %d (failed %d)\ndays: %s\ncards: %s" % (s["lab"], s["calls"], s["failed"], ", ".join(s["days"]) or "-", ", ".join(s["cards"]) or "-"))
        return 0
    if cmd == "card":
        t = argv[argv.index("--title") + 1] if "--title" in argv and argv.index("--title") + 1 < len(argv) else None
        print(card(root, t)); return 0
    if cmd == "draft-recipe":
        if len(argv) < 3:
            print('usage: fab_lab.py draft-recipe <project> "<name>"'); return 2
        print(draft_recipe(root, argv[2])); return 0
    if cmd == "propose":
        a = argv[2:]
        def opt(n):
            return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else ""
        if not a:
            print("usage: fab_lab.py propose <project> \"<statement>\" [--when W] [--do D]"); return 2
        try:
            pid = propose(root, a[0], opt("--when"), opt("--do"))
        except ValueError as e:
            print("refused: %s" % e); return 1
        print("queued %s for the owner to approve on the console Skills page" % pid if pid else "already known: not queued again"); return 0
    if cmd == "console":
        nums = [x for x in argv[2:] if x.isdigit()]
        ok_, msg = console(root, int(nums[0]) if nums else 8766, "--foreground" in argv)
        print(msg); return 0 if ok_ else 1
    print(__doc__); return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] == "hook" else 1)
