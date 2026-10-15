"""mcp_map: the kit maps the MCP by itself (meta and direct servers, JSON and event-stream), tests only safe tools, notices changes, never guesses."""
import os, sys, json, tempfile, threading, subprocess, time, importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, hooks)
import mcp_map  # noqa: E402
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

S = {"text": False, "strict": False, "mode": "meta", "sse": False, "called": [], "fail": set(), "sets": {}}
S["sets"] = {
    "Widgets": [("GetWidgets", "Reads the widget tree. Extra.", [], True), ("AddWidget", "Adds a widget.", ["name"], False), ("ListThings", "Lists things.", [], None)],
    "Assets": [("find_assets", "Finds assets by name.", ["query"], True), ("save_assets", "Saves assets.", [], None), ("GetCount", "Counts assets.", [], None)],
}

def schema(req):
    return {"type": "object", "properties": {r: {"type": "string"} for r in req}, "required": req}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        m, i = msg["method"], msg.get("id")
        if S["strict"] and m != "initialize" and self.headers.get("MCP-Protocol-Version") != "2025-11-25":
            self.send_response(400); self.end_headers(); self.wfile.write(b"bad protocol version"); return
        if S["strict"] and i is None:
            self.send_response(400); self.end_headers(); return
        def send(result):
            body = json.dumps({"jsonrpc": "2.0", "id": i, "result": result})
            if S["sse"]:
                body = "event: message\ndata: %s\n\n" % body
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream" if S["sse"] else "application/json")
            self.send_header("Mcp-Session-Id", "abc")
            self.end_headers(); self.wfile.write(body.encode())
        if i is None:
            self.send_response(202); self.end_headers(); return
        text = lambda t, err=False: send({"content": [{"type": "text", "text": t}], "isError": err})
        if m == "initialize":
            send({"protocolVersion": "2025-11-25", "serverInfo": {"name": "fake-uefn", "version": "9.9"}, "capabilities": {}})
        elif m == "tools/list":
            if S["mode"] == "meta":
                send({"tools": [
                    {"name": "list_toolsets", "description": "x", "inputSchema": schema([])},
                    {"name": "describe_toolset", "description": "x", "inputSchema": schema(["toolset_name"])},
                    {"name": "call_tool", "description": "x", "inputSchema": {"type": "object", "properties": {"toolset_name": {}, "tool_name": {}, "arguments": {}}}}]})
            else:
                send({"tools": [{"name": "%s.%s" % (ts, n), "description": d, "inputSchema": schema(r), **({"annotations": {"readOnlyHint": ro}} if ro is not None else {})} for ts, tl in S["sets"].items() for n, d, r, ro in tl]})
        elif m == "tools/call":
            n, a = msg["params"]["name"], msg["params"]["arguments"]
            if n == "list_toolsets" and S["text"]:
                text("\n".join("- %s: Tools for %s,\nwrapped line." % (t, t) for t in S["sets"]))
            elif n == "describe_toolset" and S["text"]:
                text("Toolset %s\n" % a["toolset_name"] + "\n".join("- %s: %s" % (x, d) for x, d, r, ro in S["sets"][a["toolset_name"]]))
            elif n == "list_toolsets":
                text(json.dumps({"toolsets": [{"name": t} for t in S["sets"]]}))
            elif n == "describe_toolset":
                text(json.dumps({"toolset": a["toolset_name"], "tools": [{"name": x, "description": d, "inputSchema": schema(r), **({"annotations": {"readOnlyHint": ro}} if ro is not None else {})} for x, d, r, ro in S["sets"][a["toolset_name"]]]}))
            else:
                tool = a["tool_name"] if n == "call_tool" else n
                S["called"].append(tool)
                text("boom" if tool in S["fail"] else "fine", tool in S["fail"])
        else:
            send({})

srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/mcp" % srv.server_port

def fresh(): return tempfile.mkdtemp()

d = fresh()
res, code = mcp_map.now(url=URL, dirpath=d)
ok(code == 0 and res["state"] == "first_snapshot" and res["count"] == 6 and res["mode"] == "meta", "meta server: every toolset and tool is mapped by itself")
ok(res["tests"]["tried"] == 3 and sorted(S["called"]) == ["GetCount", "GetWidgets", "ListThings"], "only read tools without arguments were called: %s" % S["called"])
ok("AddWidget" not in S["called"] and "save_assets" not in S["called"] and "find_assets" not in S["called"], "writers and tools needing arguments were never called")
ok(os.path.isfile(os.path.join(d, "MAP.md")) and os.path.isfile(os.path.join(d, "NEWS.pending")), "map and news written")
res, code = mcp_map.now(url=URL, dirpath=d)
ok(res["state"] == "unchanged" and code == 0, "second run: unchanged")
S["sets"]["Widgets"].append(("RenderPreview", "Renders a picture.", [], True))
S["fail"].add("GetWidgets")
res, code = mcp_map.now(url=URL, dirpath=d)
ok(res["state"] == "changed" and res["added"][0]["tool"] == "Widgets/RenderPreview", "a new tool is noticed with what it does")
ok(res["tests"]["stopped_working"] == ["Widgets/GetWidgets"] and code == 1, "a tool that worked and now fails is reported as stopped working")
news = open(os.path.join(d, "NEWS.md"), encoding="utf-8").read()
ok("RenderPreview" in news and "Stopped working" in news, "NEWS.md says both")
# session start: news become one message, once
msg = mcp_map.session_check(dirpath=d, url=URL, interval_hours=9999)
ok(msg and "MCP news" in msg and "FIRST reply" in msg, "session start hands the news to the agent")
ok(mcp_map.session_check(dirpath=d, url=URL, interval_hours=9999) is None, "and only once")
# direct server and event-stream replies
S.update(mode="direct", sse=True, called=[], fail=set())
d2 = fresh()
res, code = mcp_map.now(url=URL, dirpath=d2)
ok(res["state"] == "first_snapshot" and res["mode"] == "direct" and res["count"] == 7, "direct server with event-stream replies is mapped too")
ok(res["tests"]["tried"] >= 3 and "Widgets.AddWidget" not in S["called"], "server read-only hints are honored, writers untouched")
# --find
out = subprocess.run([sys.executable, os.path.join(hooks, "mcp_map.py"), "--find", "widget", "--dir", d2], capture_output=True, text=True).stdout
ok("GetWidgets" in out and "read" in out and "tested ok" in out, "--find searches the saved map")
# not reachable / odd: the saved map stays
dead = "http://127.0.0.1:1/mcp"
res, code = mcp_map.now(url=dead, dirpath=d2, timeout=1)
ok(code == 2 and res["state"] == "not_reachable", "UEFN closed -> not_reachable, nothing written")
class Junk(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"])); self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers(); self.wfile.write(b"hello")
j = HTTPServer(("127.0.0.1", 0), Junk); threading.Thread(target=j.serve_forever, daemon=True).start()
before = open(os.path.join(d2, "latest.json")).read()
res, code = mcp_map.now(url="http://127.0.0.1:%d/mcp" % j.server_port, dirpath=d2)
ok(code == 3 and res["state"] == "odd_reply" and open(os.path.join(d2, "latest.json")).read() == before, "an odd reply is never turned into a map")
# the session check never waits and stays silent when UEFN is closed
t = time.time()
ok(mcp_map.session_check(dirpath=fresh(), url=dead, interval_hours=0) is None and time.time() - t < 3, "closed UEFN: silent and instant")
# url discovery from .mcp.json
p = fresh(); json.dump({"mcpServers": {"unreal-mcp": {"url": "http://127.0.0.1:8123/mcp"}}}, open(os.path.join(p, ".mcp.json"), "w"))
ok(mcp_map.find_url(p) == "http://127.0.0.1:8123/mcp", "the MCP address is read from the project's .mcp.json")
# the session-start hook (kit_sync) hands the news to the agent end to end
mp = fresh(); proj = fresh(); tpl = fresh()
open(os.path.join(mp, "NEWS.md"), "w").write("# UEFN MCP news\n\n2026-10-15. 5 tools in 2 toolsets.\n"); open(os.path.join(mp, "NEWS.pending"), "w").write("x")
env = dict(os.environ, CLAUDE_PROJECT_DIR=proj, UEFN_KIT_MCP_DIR=mp, UEFN_KIT_TEMPLATE=tpl, UEFN_MCP_URL="http://127.0.0.1:1/mcp", HOME=tpl, USERPROFILE=tpl)
r = subprocess.run([sys.executable, os.path.join(hooks, "kit_sync.py")], capture_output=True, text=True, env=env)
ok("MCP news" in r.stdout and "additionalContext" in r.stdout, "kit_sync (session start) carries the MCP news to the agent")
# the Console: summary numbers, the server route, the Skills page section
sm = mcp_map.summary(d2)
ok(sm["available"] and sm["count"] == 7 and sm["kit_uses"] >= 1 and sm["tests"]["ok"] >= 1 and sm["news"]["date"], "summary gives counts, kit coverage, tests and news")
ok(mcp_map.summary(fresh())["available"] is False, "no map yet -> available false with a reason")
import socket, urllib.request, re
srv_py = os.path.join(hooks, "agent-console-server.py")
s_ = socket.socket(); s_.bind(("127.0.0.1", 0)); port = s_.getsockname()[1]; s_.close()
envs = dict(os.environ, UEFN_KIT_MCP_DIR=d2)
pr = subprocess.Popen([sys.executable, srv_py, str(port)], env=envs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    body = None
    for _ in range(40):
        try:
            body = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/uefn-mcp-map" % port, timeout=3).read()); break
        except Exception:
            time.sleep(0.25)
    ok(body and body["available"] and body["count"] == 7, "server: /mcp-map returns the summary")
finally:
    pr.terminate()
page = open(os.path.join(hooks, "agent-console-skills.html"), encoding="utf-8").read()
ok('id="kMcp"' in page and 'fetch("/uefn-mcp-map"' in page and "The kit uses " in page, "the Skills page has the UEFN MCP section")
ps1 = open(os.path.join(hooks, "agent-console-server.ps1"), encoding="utf-8").read()
ok('"/uefn-mcp-map"' in ps1 and "mcp_map.py" in ps1, "the PowerShell server serves /mcp-map too")
# the real server (seen in the field) wants the version it negotiated in every header and refuses the notification
S.update(strict=True, mode="meta", sse=False, called=[], fail=set())
d3 = fresh()
res, code = mcp_map.now(url=URL, dirpath=d3)
ok(res["state"] == "first_snapshot" and res["count"] == 7, "a strict server (negotiated version header required, notification refused) is still mapped")
S["strict"] = False
# a failed attempt is remembered and told, never hidden
res, code = mcp_map.now(url="http://127.0.0.1:1/mcp", dirpath=d3, timeout=1)
err = json.load(open(os.path.join(d3, "auto.json")))["last_error"]
ok("not_reachable" in err["text"], "a failed attempt is remembered in auto.json")
d4 = fresh(); mcp_map._note_error(d4, "odd_reply: HTTP 400")
ok("failed" in mcp_map.summary(d4)["reason"] and "HTTP 400" in mcp_map.summary(d4)["reason"], "the Console reason names the last failure")
# the real server (seen in the field): three meta-tools, list_toolsets as TEXT with dotted names and wrapped lines
text_list = "- Editor.EditorApp: Tools for querying and modifying\nUnreal Editor state: console variables.\n- Widgets.UMG: Widget trees.\n"
ok(mcp_map.toolset_names_from_text(text_list) == ["Editor.EditorApp", "Widgets.UMG"], "list_toolsets text: names found even when descriptions wrap")
ok([t["name"] for t in mcp_map.tool_entries_from_text("Toolset X\n- GetWidgets: reads the tree\n- AddWidget (name, parent): adds one\n")] == ["GetWidgets", "AddWidget"], "describe_toolset text: bullet tools found")
ok([t["name"] for t in mcp_map.tool_entries_from_text("## GetWidgets\nreads\n## AddWidget\nadds\n")] == ["GetWidgets", "AddWidget"], "describe_toolset text: headings found")
ok(mcp_map.tool_entries_from_text("nothing useful here") == [], "unrecognised text gives nothing, never garbage")
# end to end with the text format of the real server
S.update(text=True, strict=True, mode="meta", called=[], fail=set())
d5 = fresh()
res, code = mcp_map.now(url=URL, dirpath=d5)
ok(res["state"] == "first_snapshot" and res["count"] == 7 and res["tests"]["tried"] == 0, "text-format server: mapped; tools whose arguments are unknown are not called")
S["text"] = False; S["strict"] = False

# deep test: every read-only tool is tried once with made-up arguments; the map itself is never touched
S.update(mode="meta", text=False, strict=False, sse=False, called=[], fail=set())
S["sets"]["Widgets"] = [("GetWidgets", "Reads the widget tree.", [], True), ("AddWidget", "Adds a widget.", ["name"], False), ("ListThings", "Lists things.", [], None)]
S["sets"]["Assets"] = [("find_assets", "Finds assets by name.", ["query"], True), ("save_assets", "Saves assets.", [], None), ("GetCount", "Counts assets.", [], None), ("CaptureShot", "Takes a picture.", [], True)]
d6 = fresh()
mcp_map.now(url=URL, dirpath=d6)
snap = {n: open(os.path.join(d6, n), "rb").read() for n in ("latest.json", "MAP.md")}
S["called"] = []
res, code = mcp_map.deep_test(url=URL, dirpath=d6)
ok(res["state"] == "deep_done" and res["map_untouched"] is True, "deep test leaves the map files untouched")
ok("find_assets" in S["called"] and "GetWidgets" in S["called"], "deep test also calls read tools that need arguments (with made-up ones)")
ok("AddWidget" not in S["called"] and "save_assets" not in S["called"] and "CaptureShot" not in S["called"], "deep test never calls writers or capture tools")
ok(all(open(os.path.join(d6, n), "rb").read() == v for n, v in snap.items()), "latest.json and MAP.md are byte-identical after the deep test")
ok(os.path.isfile(os.path.join(d6, "deep-tests.json")) and os.path.isfile(os.path.join(d6, "DEEP-TESTS.md")), "results go to their own files")
ok(mcp_map.sample_args({"properties": {"a": {"type": "integer"}, "b": {"enum": ["x", "y"]}, "folderPath": {"type": "string"}, "c": {"type": "boolean"}}, "required": ["a", "b", "folderPath", "c"]}) == {"a": 0, "b": "x", "folderPath": "/Game", "c": False}, "made-up arguments follow the schema")
ok(mcp_map.sample_args({"properties": {"category": {"type": "string", "default": "LogsToolset"}}, "required": ["category"]}, "GetLogEntries", "EditorToolset.LogsToolset") == {"category": "LogTemp"}, "a placeholder default equal to the toolset class name is not used")
