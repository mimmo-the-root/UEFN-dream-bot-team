#!/usr/bin/env python3
"""uefn_mcp.py - keeps the work going when the session loses UEFN's MCP server (v1.124.54).

Claude Code connects to UEFN's MCP server (http://127.0.0.1:8000/mcp) once. When the server drops (a heavy call, a
build, the editor busy for a while) Claude Code may give up on it, and the unreal-mcp tools fail or disappear until
someone types /mcp. Nobody is there at night: the session waited 3 hours for the owner. This script talks to the
server directly, a new connection every time, so it never stays disconnected.

  python Claude/hooks/uefn_mcp.py status                  is the server up? is the editor open?
  python Claude/hooks/uefn_mcp.py wait [--max 3600]       returns as soon as the server answers (exit 0), or 2 at --max
  python Claude/hooks/uefn_mcp.py call TOOL ['{json}']    one tool call, the same guards and log as the unreal-mcp tools
  python Claude/hooks/uefn_mcp.py tools [filter]          the tool names the server offers now

TOOL is the name the session knows (mcp__unreal-mcp__VerseToolset_VerseToolset_BuildAll), the short form without the
prefix, or the server's own dotted name. It never starts, closes or restarts the editor."""
import json, os, re, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcp_map as m

PREFIX = "mcp__unreal-mcp__"


def url():
    try:
        return m.find_url(os.path.join(HERE, "..", ".."))
    except Exception:
        return "http://127.0.0.1:8000/mcp"


def port_up(u=None, wait=1.0):
    try:
        return m.port_open(u or url(), wait)
    except Exception:
        return False


def client(timeout=120.0):
    c = m.Client(url(), timeout)
    c.start()
    return c


def answers(timeout=10.0):
    """True when the server accepts a new MCP connection and lists its tools."""
    if not port_up():
        return False
    try:
        return len(client(timeout).list_tools()) > 0
    except Exception:
        return False


def editor_state():
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "uefn_session.py"), "status", "--no-ports"],
                           capture_output=True, text=True, timeout=30)
        out = (r.stdout or "").strip().splitlines()
        return out[0][:120] if out else "unknown"
    except Exception:
        return "unknown"


def wait(max_s=3600.0, every=15.0, sleep=time.sleep, clock=time.time, up=None):
    up = up or answers
    t0 = clock()
    while True:
        if up():
            return True, int(clock() - t0)
        if clock() - t0 >= max_s:
            return False, int(clock() - t0)
        sleep(every)


def norm(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def resolve(name, names):
    """The server's tool name for what the session calls it (prefix, underscores or dots all accepted)."""
    n = name[len(PREFIX):] if name.startswith(PREFIX) else name
    if n in names:
        return n
    hits = [t for t in names if norm(t) == norm(n)]
    return hits[0] if len(hits) == 1 else None


def guard(tool, args):
    """The PreToolUse guards of the unreal-mcp tools (heavy reads, one writer at a time). Returns a refusal or None."""
    payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": PREFIX + tool.replace(".", "_"), "tool_input": args,
                          "session_id": os.environ.get("CLAUDE_SESSION_ID", "uefn_mcp")})
    for g in ("mcp_heavy_guard.py", "editor_lock.py"):
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, g)], input=payload, capture_output=True, text=True, timeout=15)
            o = json.loads(r.stdout or "{}").get("hookSpecificOutput", {})
            if o.get("permissionDecision") == "deny":
                return o.get("permissionDecisionReason") or g
        except Exception:
            pass
    return None


def log(tool, args, ok, text):
    payload = {"hook_event_name": "PostToolUse" if ok else "PostToolUseFailure", "tool_name": PREFIX + tool.replace(".", "_"),
               "tool_input": args}
    payload["tool_response" if ok else "error"] = text[:2000]
    try:
        subprocess.run([sys.executable, os.path.join(HERE, "mcp_work_log.py")], input=json.dumps(payload), capture_output=True,
                       text=True, timeout=15)
    except Exception:
        pass


def call(name, args):
    if not port_up():
        return 3, "UEFN's MCP server does not answer on %s. Run: python Claude/hooks/uefn_mcp.py wait" % url()
    c = client()
    names = [t["name"] for t in c.list_tools()]
    tool = resolve(name, names)
    if not tool:
        return 4, "No tool %s on the server (python Claude/hooks/uefn_mcp.py tools %s)" % (name, name.split("_")[-1])
    why = guard(tool, args)
    if why:
        return 5, "Refused by the kit's guard: " + why
    try:
        text = c.call(tool, args)
        log(tool, args, True, text)
        return 0, text
    except m.ToolError as e:
        log(tool, args, False, str(e))
        return 1, "Tool error: %s" % e


def main(argv):
    a = argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = a[0]
    if cmd == "status":
        up = answers()
        print(json.dumps({"server": url(), "port_open": port_up(), "answers": up, "editor": editor_state()}))
        return 0 if up else 3
    if cmd == "wait":
        mx = float(a[a.index("--max") + 1]) if "--max" in a else 3600.0
        ok, s = wait(mx)
        print("UEFN's MCP server answers (after %d s): go on. If the unreal-mcp tools still fail, use "
              "`python Claude/hooks/uefn_mcp.py call TOOL '{json}'`." % s if ok else
              "UEFN's MCP server still does not answer after %d s (editor: %s). Go on with the work that does not need the "
              "editor, note it in HANDOFF.md, and run this again later." % (s, editor_state()))
        return 0 if ok else 2
    if cmd == "tools":
        if not answers():
            print("UEFN's MCP server does not answer.")
            return 3
        f = norm(a[1]) if len(a) > 1 else ""
        print("\n".join(t["name"] for t in client().list_tools() if f in norm(t["name"])))
        return 0
    if cmd == "call" and len(a) >= 2:
        try:
            args = json.loads(a[2]) if len(a) > 2 else {}
        except ValueError as e:
            print("The arguments are not JSON: %s" % e)
            return 6
        code, text = call(a[1], args if isinstance(args, dict) else {})
        print(text)
        return code
    print(__doc__)
    return 6


if __name__ == "__main__":
    sys.exit(main(sys.argv))
