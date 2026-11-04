"""Autodiscovery of UEFN MCP tools: renamed tools are not 'new', first-seen dates are kept, a silent change is noticed by the cheap check."""
import os, sys, json, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, hooks)
import toolset_diff as td, mcp_map  # noqa: E402
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

# 1. the diff
d = tempfile.mkdtemp()
base = {"EditorToolset.EditorAppToolset/GetCurrentLevel": "Gets the level.", "editor_toolset.toolsets.scene.SceneTools/find_actors": "Finds actors in the level by name.", "A/Old": "Does an old thing."}
r, c = td.apply_map(base, d, "", True)
ok(r["state"] == "first_snapshot" and c == 0, "first map saved")
m = json.load(open(os.path.join(d, "latest.json")))
ok(all(e["fs"] == "" for e in m["tools"].values()) and m["fp"], "first map: nothing counts as a discovery; the fingerprint is kept")
now = {"EditorToolset/GetCurrentLevel": "Gets the level.", "EditorToolset/FindActors": "Finds actors in the level by name.", "VerseToolset/BuildAll": "Builds Verse.", "A/Old": "Does an old thing, reworded."}
r, c = td.apply_map(now, d, "", True)
ok(r["state"] == "changed" and c == 1, "a changed catalog is reported")
ok(r["renamed_total"] == 2 and r["added_total"] == 1 and r["removed_total"] == 0, "two renamed tools are not new; one really new")
ok([a["tool"] for a in r["added"]] == ["VerseToolset/BuildAll"], "the new tool is named")
m = json.load(open(os.path.join(d, "latest.json")))["tools"]
ok(m["VerseToolset/BuildAll"]["fs"] == td.today() and m["EditorToolset/FindActors"]["fs"] == "", "only the really new tool gets a first-seen date; renamed ones keep theirs")
ok(m["A/Old"].get("ch") == td.today(), "a reworded tool gets a changed date")
r2, c2 = td.apply_map(now, d, "", True)
ok(r2["state"] == "unchanged" and c2 == 0, "the same catalog is unchanged")
ok(td.fingerprint(now) != td.fingerprint(base) and td.fingerprint(now) == td.fingerprint(dict(now)), "the fingerprint follows the content")
# the shipped table feeds the rename match
tbl = td.names_43()
ok(tbl and any(v.startswith("EditorToolset/") for v in tbl.values()), "the 43.00 name table is shipped")
# a renamed tool whose arguments changed is NOT the same tool
d9 = tempfile.mkdtemp()
td.apply_map({"X.Y/GetA": "Reads a."}, d9, "", True, "", {"X.Y/GetA": {"properties": {"a": {}}}})
r, c = td.apply_map({"X/GetA": "Reads a."}, d9, "", True, "", {"X/GetA": {"properties": {"b": {}}}})
ok(r["renamed_total"] == 1 and r["changed_total"] == 1, "same name and text but other arguments: renamed AND changed (must be replayed)")
# recipes follow a rename
import recipes_status as RS
rows = [{"state": "changed", "date": "2026-11-03", "uefn": "", "removed": ["editor_toolset.toolsets.scene.SceneTools/get_current_level"], "changed": [], "renamed": []}]
rec = {"editor_toolset.toolsets.scene.SceneTools/get_current_level": {}}
tb = td.names_43()
rec2 = {k: {} for k in list(tb)[:3]}
rows2 = [{"state": "changed", "date": "2026-11-03", "uefn": "", "removed": list(rec2), "changed": [], "renamed": []}]
ok(RS.stale(rec2, rows2) == [], "recipes whose tool only moved to its 43.00 name are not stale")
rows3 = [{"state": "changed", "date": "2026-11-03", "uefn": "", "removed": [], "changed": [tb[k] for k in rec2], "renamed": [[k, tb[k]] for k in rec2]}]
ok(len(RS.stale(rec2, rows3)) == 3 and RS.stale(rec2, rows3)[0][1] == "tool changed", "...but are stale when the moved tool was reworded or its arguments changed")
# 2. the summary box
s = mcp_map.summary(d)
disc = s["discovery"]
ok(disc["new_7d"] == 1 and disc["new_total"] == 1 and disc["recent"][0]["tool"] == "VerseToolset/BuildAll" and disc["baseline"] == td.today(), "summary: just discovered counts, recent list and baseline date")
ok(disc["changes"] and disc["changes"][-1]["renamed"] == 2 and disc["reworded_30d"] == 1, "summary: change history with renamed and reworded counts")

# 3. the cheap check against a fake direct server
SETS = {"EditorToolset": [("GetThing", "Reads a thing.")]}
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        mth, i = msg["method"], msg.get("id")
        def send(res):
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Mcp-Session-Id", "x"); self.end_headers()
            self.wfile.write(json.dumps({"jsonrpc": "2.0", "id": i, "result": res}).encode())
        if i is None:
            self.send_response(202); self.end_headers(); return
        if mth == "initialize":
            send({"protocolVersion": "2025-11-25", "serverInfo": {"name": "fake", "version": ""}, "capabilities": {}})
        elif mth == "tools/list":
            send({"tools": [{"name": "%s_%s" % (ts, n), "description": dd, "inputSchema": {"type": "object", "properties": {}, "required": []}, "annotations": {"readOnlyHint": True}} for ts, tl in SETS.items() for n, dd in tl]})
        else:
            send({"content": [{"type": "text", "text": "ok"}], "isError": False})
srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/mcp" % srv.server_port
d3 = tempfile.mkdtemp()
r, c = mcp_map.check(None, URL, d3)
ok(r.get("trigger") == "no_map" and os.path.isfile(os.path.join(d3, "latest.json")), "check with no map yet makes the first map")
r, c = mcp_map.check(None, URL, d3)
ok(r["state"] == "same" and c == 0, "check with the same catalog does nothing more")
SETS["EditorToolset"].append(("SetThing", "Writes a thing."))
r, c = mcp_map.check(None, URL, d3)
ok(r.get("trigger") == "differs" and r["state"] == "changed", "a silent change (one tool added, no version change) is noticed")
disc = mcp_map.summary(d3)["discovery"]
ok(disc["new_7d"] == 1 and disc["last_check"] > 0, "the summary shows it as just discovered")
srv.shutdown()
r, c = mcp_map.check(None, URL, d3, timeout=2)
ok(r["state"] == "not_reachable" and c == 2, "UEFN closed: not reachable, the saved map stays")
print("autodiscovery tests OK")

# 4. one set of states over tools and over recipes
import recipes_status as RS2
rec = {"A.B/Old": {"status": "unverified"}, "A.B/Gone": {"status": "tool-ok"}, "A.B/Fail": {"status": "unverified"}}
merged = {"A.B/Old": {"status": "proven", "ok": 1, "failed": 0, "last_failure": ""}, "A.B/Gone": {"status": "proven", "ok": 1, "failed": 0, "last_failure": ""}, "A.B/Fail": {"status": "unverified", "ok": 0, "failed": 2, "last_failure": "x"}}
tools = {"N/Old": {}, "N/Gone": {}, "N/Fail": {}, "N/Fresh": {}, "N/Tested": {}}
import toolset_diff as TD2
old_tbl = TD2.names_43
TD2.names_43 = lambda: {"A.B/Old": "N/Old", "A.B/Gone": "N/Gone", "A.B/Fail": "N/Fail"}
st = RS2.tool_states(merged, tools, stale_keys=["A.B/Gone"], tests={"N/Tested": "ok"})
TD2.names_43 = old_tbl
ok(st["proven"] == 1 and st["replay"] == 2 and st["answered"] == 1 and st["not_tried"] == 1 and st["total"] == 5, "tool states: proven, answered by a test, replay (stale or failed), not tried add up to all tools")
ok(sum(a["total"] for a in st["areas"]) == 5 and all(a["proven"] + a["tool_ok"] + a["unverified"] + a["replay"] == a["total"] for a in st["areas"]), "areas use the same four states and add up")
print("states tests OK")

# 5. a recipe's argument names against the saved map, offline
mp = {"EditorToolset/GetReferencers": {"pn": ["assetPath"], "rq": ["assetPath"]}, "ConsoleToolset/GetLogEntries": {"pn": ["logCategory", "maxEntries"]}}
rec = {"A.B/GetReferencers": {"args": {"asset_path": "/x"}}, "A.B/GetLogEntries": {"args": {"category": "Log", "maxEntries": 5}}, "A.B/Fine": {"args": {}}}
TD2.names_43 = lambda: {"A.B/GetReferencers": "EditorToolset/GetReferencers", "A.B/GetLogEntries": "ConsoleToolset/GetLogEntries"}
res = RS2.arg_check(rec, mp)
TD2.names_43 = old_tbl
ok(res["A.B/GetReferencers"]["fix"] == {"asset_path": "assetPath"} and not res["A.B/GetReferencers"]["unknown"], "asset_path -> assetPath is a writing-style rename, fixed automatically")
ok(res["A.B/GetLogEntries"]["unknown"] == ["category"] and "A.B/Fine" not in res, "a name with no counterpart needs a person; recipes without arguments are left alone")
print("argument tests OK")
