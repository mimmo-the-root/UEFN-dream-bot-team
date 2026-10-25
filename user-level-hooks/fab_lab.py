#!/usr/bin/env python3
"""Fab lab (v1.109.1): collect lessons from a Fab product WITHOUT putting a single file in the project.

A Fab product is zipped whole, so the kit installs nothing in it (no Claude/ folder, no hooks). The learning data
therefore lives in your profile: ~/.claude/fab-lab/<ProductName>/Claude/logs/..., laid out like a map project so the
console and the lesson tools can read it.

Lives in ~/.claude/hooks.

  fab_lab.py hook                      # global PostToolUse / PostToolUseFailure hook (reads the payload on stdin)
  fab_lab.py status <project>          # where the data is, how many MCP calls were recorded
  fab_lab.py path <project>            # the lab folder
  fab_lab.py card <project> [--title T]  # draft closing card (what was done, what failed) in Claude/docs/lessons/
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


def console(root, port=8766, foreground=False):
    """Start the Agent Console on the lab data. foreground=True keeps it running in THIS terminal (close the window to stop it): use it
    when a background start is killed together with the program that launched it. Returns (ok, message)."""
    lab = ensure_lab(root)
    url = "http://127.0.0.1:%d/" % port
    who = _whoami(port)
    if who:
        if os.path.normcase(os.path.abspath(who.get("project", ""))) == os.path.normcase(os.path.abspath(lab)):
            return True, "already running: " + url
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


def main(argv):
    if not argv:
        print(__doc__); return 2
    cmd = argv[0]
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
