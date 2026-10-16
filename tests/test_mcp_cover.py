"""mcp_cover / mcp_queue: schema-driven batteries make their own fixtures, call destructive tools last, scope listings, keep the map, and wait for the exploration."""
import os, sys, json, tempfile, threading, time, types
from http.server import BaseHTTPRequestHandler, HTTPServer
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, hooks)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

THING = {"title": "Thing", "type": "object", "properties": {"refPath": {"type": "string"}}, "required": ["refPath"]}
def sch(props, req=()): return {"type": "object", "properties": props, "required": list(req)}
OUT1 = {"type": "object", "properties": {"returnValue": THING}}
OUTL = {"type": "object", "properties": {"returnValue": {"type": "array", "items": THING}}}
TOOLS = [
    ("CreateThing", sch({"folderPath": {"type": "string"}, "assetName": {"type": "string"}}, ["folderPath", "assetName"]), OUT1, None),
    ("GetThing", sch({"thing": THING}, ["thing"]), {}, True),
    ("ListThings", sch({}), OUTL, True),
    ("SetThing", sch({"thing": THING, "label": {"type": "string"}}, ["thing", "label"]), {}, False),
    ("NeedsOther", sch({"other": {"title": "Other", "type": "object", "properties": {"refPath": {"type": "string"}}, "required": ["refPath"]}}, ["other"]), {}, True),
    ("DeleteThing", sch({"thing": THING}, ["thing"]), {}, False),
    ("find_assets", sch({"folder_path": {"type": "string"}, "name": {"type": "string"}}), {}, True),
    ("restart_editor", sch({}), {}, False),
]
CALLS = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        m, i = msg["method"], msg.get("id")
        def send(result):
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Mcp-Session-Id", "s"); self.end_headers()
            self.wfile.write(json.dumps({"jsonrpc": "2.0", "id": i, "result": result}).encode())
        text = lambda t, err=False: send({"content": [{"type": "text", "text": t}], "isError": err})
        if i is None:
            self.send_response(202); self.end_headers(); return
        if m == "initialize": send({"protocolVersion": "2025-11-25", "serverInfo": {}, "capabilities": {}})
        elif m == "tools/list":
            send({"tools": [{"name": "list_toolsets", "inputSchema": sch({})}, {"name": "describe_toolset", "inputSchema": sch({"toolset_name": {}}, ["toolset_name"])},
                            {"name": "call_tool", "inputSchema": sch({"toolset_name": {}, "tool_name": {}, "arguments": {}})}]})
        elif m == "tools/call":
            n, a = msg["params"]["name"], msg["params"]["arguments"]
            if n == "list_toolsets": text("- Lab.Things: fake toolset\n")
            elif n == "describe_toolset":
                text(json.dumps({"name": "Lab.Things", "tools": [{"name": "Lab.Things." + t, "description": "does " + t, "inputSchema": s, "outputSchema": o, **({"annotations": {"readOnlyHint": ro}} if ro is not None else {})} for t, s, o, ro in TOOLS]}))
            else:
                t, args = a["tool_name"], a.get("arguments", {})
                if a["toolset_name"].endswith("SceneTools"): text(json.dumps({"returnValue": "/lab/Main"})); return
                CALLS.append((t, args))
                if t == "CreateThing": text(json.dumps({"returnValue": {"refPath": "/lab/Cover/%s.%s" % (args["assetName"], args["assetName"])}}))
                elif t == "ListThings": text(json.dumps({"returnValue": []}))
                else: text(json.dumps({"returnValue": True}))
        else: send({})
srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
tmp = tempfile.mkdtemp()
os.environ.update(UEFN_MCP_URL="http://127.0.0.1:%d/mcp" % srv.server_port, LAB_AGGRESSIVE="1", LAB_ROOT="/lab", UEFN_KIT_MCP_DIR=tmp)
marker = os.path.join(tmp, "LAB-PROJECT.txt"); open(marker, "w").write("x")
import mcp_lab as L
L.MARKER = marker; L.LEDGER = os.path.join(tmp, "ledger.jsonl"); L.LOGS = tmp
import mcp_cover as C
C.OUT = os.path.join(tmp, "mcp")

b = C.Battery("/lab/Cover")
ok(b.load() == 8, "catalog read from the server")
ok(C.out_titles(b.cat["Lab.Things/CreateThing"]["out"]) == ["Thing"] and "Lab.Things/CreateThing" in b.producers["Thing"], "a tool that returns an object is a producer of that kind")
b.coverage(60, 1.0, {})
st = b.status
ok(st["Lab.Things/CreateThing"]["s"] == "ok" and st["Lab.Things/GetThing"]["s"] == "ok" and st["Lab.Things/SetThing"]["s"] == "ok", "fixtures are made by producers, then consumers run with them")
ok(st["Lab.Things/NeedsOther"]["s"] == "unresolved" and "Other" in st["Lab.Things/NeedsOther"]["why"][0], "an object nobody can make is reported as unresolved, by kind")
ok(st["Lab.Things/restart_editor"]["s"] == "refused", "the lab's hard rule is reported as refused")
names = [c[0] for c in CALLS]
ok(names.index("CreateThing") < names.index("GetThing") and names[-1] == "DeleteThing", "producers first, destructive tools last: %s" % names)
fa = next(a for t, a in CALLS if t == "find_assets")
ok(fa.get("folder_path") == "/lab/Cover" and fa.get("name") == "Cover", "listing tools are scoped so they cannot return everything")
ok(next(a for t, a in CALLS if t == "SetThing")["thing"]["refPath"].startswith("/lab/Cover/"), "the argument is the real object that was created")
cnt = C.write_reports(b, {}, 1, 1.0)
cov = json.load(open(os.path.join(C.OUT, "coverage.json")))
ok(cnt["ok"] == 6 and os.path.isfile(os.path.join(C.OUT, "COVERAGE.md")) and "Other" in open(os.path.join(C.OUT, "COVERAGE.md")).read(), "reports written with the objects we cannot make yet")
b2 = C.Battery("/lab/Cover"); b2.load()
pick = b2.pick(0.25, cov)
ok(len(pick) == 2 and all(cov[k]["s"] != "ok" for k in pick), "a partial run takes the least covered tools first: %s" % pick)
# suites do not crash on a server that lacks their tools
class A: pass
a = A(); a.budget = 1.0; a.n = 2; a.fraction = 1.0; a.wait = 1.0
ok(C.suite_soak(a)["suite"] == "soak" and C.suite_session(a)["loops"] == 2, "soak and session suites survive missing tools; the session is stopped in a finally")
# queue
import mcp_queue as Q
led = os.path.join(tmp, "led.jsonl"); flag = os.path.join(tmp, "done.flag")
ok(Q.exploration_finished(15, ledger=led, done=flag)[0] is False, "queue: no ledger yet means the exploration has not started")
open(led, "w").write("{}\n")
ok(Q.exploration_finished(15, ledger=led, done=flag)[0] is False, "queue: a recently used ledger means the exploration is still going")
ok(Q.exploration_finished(15, now=time.time() + 16 * 60, ledger=led, done=flag)[0] is True, "queue: a quiet ledger means it is finished")
open(flag, "w").write("x")
ok(Q.exploration_finished(15, ledger=led, done=flag)[0] is True, "queue: the done flag wins")
Q.LOGS = tmp; Q.DOCS = os.path.join(tmp, "qdocs"); Q.STATE = os.path.join(tmp, "qs.json"); Q.LOG = os.path.join(tmp, "q.log")
args = types.SimpleNamespace(idle=15, coverage_budget=1.0, soak_budget=1.0, soak_n=2, session_n=1, n=2, wait=1.0)
Q.run_queue(args, wait=False)
st = json.load(open(Q.STATE))
ok(set(st["done"]) == set(Q.ORDER) and os.path.isfile(os.path.join(Q.DOCS, "QUEUE-REPORT.md")) and os.path.isfile(os.path.join(tmp, "queue-done.flag")), "queue: all four suites ran one after the other and the report was written")
Q.run_queue(args, wait=False)
ok(open(Q.LOG).read().count("skip coverage") == 1, "queue: a second start skips what already ran")
# a suite that could not reach the MCP does not count as done and does not write the done flag
Q.STATE = os.path.join(tmp, "qs2.json"); os.path.isfile(os.path.join(tmp, "queue-done.flag")) and os.remove(os.path.join(tmp, "queue-done.flag"))
real_suites = dict(C.SUITES)
C.SUITES["soak"] = lambda ns: {"suite": "soak", "crash": "URLError"}
rc = Q.run_queue(args, wait=False)
st2 = json.load(open(Q.STATE))
ok(rc == 1 and "soak" not in st2["done"] and "soak" in st2.get("failed", {}) and not os.path.isfile(os.path.join(tmp, "queue-done.flag")), "queue: a crashed suite is not done, and no queue-done.flag is written")
C.SUITES.update(real_suites)
rc = Q.run_queue(args, wait=False)
ok(rc == 0 and os.path.isfile(os.path.join(tmp, "queue-done.flag")), "queue: the failed suite runs again at the next start and then the flag is written")
Q.mcp_up = lambda: False
ok(Q.run_queue(args, wait=False) == 2, "queue: an unreachable MCP means nothing is run")
print("mcp_cover ok")
