"""uefn_mcp.py + mcp_reconnect.py: the session gets UEFN's MCP back by itself (v1.124.54)."""
import json, os, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, HOOKS)
proj = tempfile.mkdtemp()
os.makedirs(os.path.join(proj, "Claude", "logs"))
os.environ["CLAUDE_PROJECT_DIR"] = proj
import uefn_mcp as U
import mcp_reconnect as R

CALLS = []


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        meth, rid = req.get("method"), req.get("id")
        if rid is None:
            self.send_response(202); self.end_headers(); return
        if meth == "initialize":
            res = {"protocolVersion": "2025-11-25", "serverInfo": {"name": "fake"}}
        elif meth == "tools/list":
            res = {"tools": [{"name": "VerseToolset.VerseToolset.BuildAll"}, {"name": "LevelToolset.LevelToolset.GetActors"}]}
        else:
            CALLS.append(req["params"])
            res = {"content": [{"type": "text", "text": "built: 0 errors"}]}
        b = json.dumps({"jsonrpc": "2.0", "id": rid, "result": res}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Mcp-Session-Id", "s1")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["UEFN_MCP_URL"] = "http://127.0.0.1:%d/mcp" % srv.server_address[1]

# 1. the session's tool name, the short one and the dotted one all reach the same tool
names = ["VerseToolset.VerseToolset.BuildAll", "LevelToolset.LevelToolset.GetActors"]
for n in ("mcp__unreal-mcp__VerseToolset_VerseToolset_BuildAll", "VerseToolset_VerseToolset_BuildAll", "VerseToolset.VerseToolset.BuildAll"):
    assert U.resolve(n, names) == "VerseToolset.VerseToolset.BuildAll", n
assert U.resolve("Nope", names) is None
# 2. a call goes through on a fresh connection and is logged like the unreal-mcp tools
assert U.answers()
code, text = U.call("mcp__unreal-mcp__VerseToolset_VerseToolset_BuildAll", {})
assert code == 0 and "0 errors" in text and CALLS[-1]["name"] == "VerseToolset.VerseToolset.BuildAll", (code, text)
ledger = open(os.path.join(proj, "Claude", "logs", "explore-ledger.jsonl"), encoding="utf-8").read()
assert "BuildAll" in ledger, ledger
# 3. the guards still apply: a FindAssets with no filter is refused before it reaches the editor
assert U.guard("AssetToolset.AssetToolset.FindAssets", {}) , "heavy read refused"
# 4. wait returns as soon as the server answers, or gives up at --max
seq = iter([False, False, True])
ok, s = U.wait(100, 5, sleep=lambda x: None, clock=time.time, up=lambda: next(seq))
assert ok
t = [0.0]
ok, s = U.wait(30, 10, sleep=lambda x: t.__setitem__(0, t[0] + x), clock=lambda: t[0], up=lambda: False)
assert not ok and s == 30
# 5. failure hook: a lost connection waits for the server and says how to go on; other errors are left alone
ctx = R.after_failure({"tool_name": "mcp__unreal-mcp__X", "error": "MCP error: connect ECONNREFUSED 127.0.0.1:8000"}, wait=lambda: (True, 40))
assert "about 40 s" in ctx and "uefn_mcp.py call" in ctx
ctx = R.after_failure({"tool_name": "mcp__unreal-mcp__X", "error": "fetch failed"}, wait=lambda: (False, 480))
assert "uefn_mcp.py wait" in ctx and "owner" in ctx
assert R.after_failure({"tool_name": "mcp__unreal-mcp__X", "error": "Actor not found: Foo"}, wait=lambda: (True, 0)) is None
assert R.after_failure({"tool_name": "Bash", "error": "ECONNREFUSED"}) is None
# 6. stop hook: a turn that ends waiting for the owner because of the MCP is refused, at most once in 5 minutes
tr = os.path.join(proj, "t.jsonl")
with open(tr, "w", encoding="utf-8") as f:
    f.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text":
            "The MCP server dropped (ECONNREFUSED on port 8000). Waiting for the owner to reconnect with /mcp."}]}}) + "\n")
why = R.at_stop({"transcript_path": tr}, now=1000.0)
assert why and "uefn_mcp.py wait" in why
assert R.at_stop({"transcript_path": tr}, now=1100.0) is None, "not again within 5 minutes"
assert R.at_stop({"transcript_path": tr, "stop_hook_active": True}, now=5000.0) is None
assert R.at_stop({"last_assistant_message": "Done: T-012 built and tested."}, now=9000.0) is None
srv.shutdown()
print("ok uefn_mcp")
