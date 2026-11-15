#!/usr/bin/env python3
"""mcp_reconnect.py - the session never sits waiting for the owner because UEFN's MCP server dropped (v1.124.54).

Two hooks, no AI:
  PostToolUseFailure (unreal-mcp tools): the error says the server is gone (refused, closed, not connected, timed out).
      The hook waits here, up to 8 minutes, until the server answers again, then tells the session to retry once and,
      if the tool still fails, to go on with `uefn_mcp.py call` (a fresh connection on every call).
  Stop (`mcp_reconnect.py stop`): the session is about to end its turn saying the MCP / the editor is down or that it
      waits for the owner because of it. The stop is refused once with what to do instead: `uefn_mcp.py wait`, then go on.
      At most 6 times in 12 hours and never twice within 5 minutes, so it cannot loop.

Switch off with UEFN_KIT_RECONNECT=0. Any error inside the hook lets everything through."""
import json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GONE = re.compile(r"econnrefused|econnreset|connection (refused|closed|reset|aborted)|not connected|fetch failed|socket hang up|"
                  r"timed? ?out|no answer from uefn|server (is )?(down|unavailable|disconnected)|-32000|transport|disconnected", re.I)
SAYS_DOWN = re.compile(r"(mcp|uefn|unreal|editor|8000)[^.\n]{0,100}(disconnect|not connected|econnrefused|is down|went down|dropped|"
                       r"unreachable|not reachable|does not answer|doesn't answer|no longer|unavailable|lost|scollegat|non rispond)|"
                       r"(disconnect|dropped|lost|scollegat)[^.\n]{0,60}(mcp|uefn|unreal|editor)|"
                       r"(wait|waiting|aspett)[^.\n]{0,60}(owner|you|proprietario|te\b)[^.\n]{0,80}(mcp|editor|uefn|reconnect|/mcp)|"
                       r"/mcp\b[^.\n]{0,40}(reconnect|riconnett)", re.I)
WAIT_IN_HOOK = 480.0
MARKS = "mcp-reconnect.json"


def logs():
    d = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.path.join(HERE, "..", ".."), "Claude", "logs")
    if not os.path.isdir(d):
        d = os.path.join(HERE, "..", "logs")
    os.makedirs(d, exist_ok=True)
    return d


def note(line):
    try:
        with open(os.path.join(logs(), "mcp-reconnect.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + line + "\n")
    except OSError:
        pass


def after_failure(p, wait=None):
    if not str(p.get("tool_name", "")).startswith("mcp__unreal-mcp__"):
        return None
    err = p.get("error")
    err = err if isinstance(err, str) else json.dumps(err, default=str)
    if not GONE.search(err or ""):
        return None
    import uefn_mcp as U
    wait = wait or (lambda: U.wait(WAIT_IN_HOOK, 10.0))
    ok, s = wait()
    note("%s failed (%s): server %s after %d s" % (p.get("tool_name"), (err or "")[:80], "back" if ok else "still down", s))
    if ok:
        gone = ("again (it was gone for about %d s)" % s) if s else "now"
        return ("UEFN's MCP server answers " + gone + ". Retry the call once. If the unreal-mcp tool still "
                "fails or is missing, Claude Code's own connection stayed closed: do the rest of the work with "
                "`python Claude/hooks/uefn_mcp.py call <tool name> '<arguments as JSON>'` (same guards, a new connection every "
                "call). Do not stop to wait for the owner.")
    return ("UEFN's MCP server has not answered for %d s. Do not stop to wait for the owner: run "
            "`python Claude/hooks/uefn_mcp.py wait --max 3600` (it returns as soon as the server is back), and meanwhile do "
            "the work that does not need the editor. Write in HANDOFF.md what waits for the editor." % s)


def last_text(transcript):
    try:
        with open(transcript, encoding="utf-8") as f:
            lines = f.readlines()[-200:]
    except (OSError, TypeError):
        return ""
    for line in reversed(lines):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        msg = o.get("message") or {}
        if o.get("type") == "assistant" or msg.get("role") == "assistant":
            c = msg.get("content")
            if isinstance(c, str):
                return c
            t = " ".join(b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
            if t.strip():
                return t
    return ""


def at_stop(p, now=None):
    now = now or time.time()
    if p.get("stop_hook_active"):
        return None
    text = p.get("last_assistant_message") or last_text(p.get("transcript_path"))
    if not SAYS_DOWN.search(text or ""):
        return None
    path = os.path.join(logs(), MARKS)
    try:
        marks = [t for t in json.load(open(path, encoding="utf-8")) if now - t < 12 * 3600]
    except (OSError, ValueError, TypeError):
        marks = []
    if len(marks) >= 6 or (marks and now - marks[-1] < 300):
        return None
    marks.append(now)
    try:
        json.dump(marks, open(path, "w", encoding="utf-8"))
    except OSError:
        pass
    note("stop refused: the turn ended on a lost MCP connection")
    return ("Do not end the turn waiting for the owner because of the MCP connection: nobody may be there. Run "
            "`python Claude/hooks/uefn_mcp.py wait --max 3600`; when it says the server answers, go on with the task "
            "(use `python Claude/hooks/uefn_mcp.py call <tool> '<json>'` if the unreal-mcp tools are still missing). "
            "If it is still down after the wait, do the work that does not need the editor and write in HANDOFF.md what waits.")


def main(argv):
    if os.environ.get("UEFN_KIT_RECONNECT") == "0":
        return 0
    try:
        p = json.loads(sys.stdin.read() or "{}")
        if len(argv) > 1 and argv[1] == "stop":
            why = at_stop(p)
            if why:
                print(json.dumps({"decision": "block", "reason": why}))
        else:
            ctx = after_failure(p)
            if ctx:
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUseFailure", "additionalContext": ctx}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
