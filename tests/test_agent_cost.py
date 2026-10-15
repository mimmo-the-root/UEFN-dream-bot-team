"""agent_cost: tokens per agent from sub-agent transcripts; each request counted once; honest when nothing is found."""
import os, sys, json, tempfile, importlib.util, re, time
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("agent_cost", os.path.join(root, "project-template", "Claude", "hooks", "agent_cost.py"))
ac = importlib.util.module_from_spec(spec); spec.loader.exec_module(ac)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

home = tempfile.mkdtemp(); proj = os.path.join(tempfile.mkdtemp(), "My Proj_1")
os.makedirs(proj)
os.environ["CLAUDE_CONFIG_DIR"] = home
tdir = ac.transcripts_dir(proj)
ok(os.path.basename(tdir) == re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(proj)), "folder name follows Claude Code's rule")
ok(ac.summary(proj)["available"] is False, "no transcripts -> not available, not zero")

def line(rid, inp, out, cr, cc, model="claude-haiku-5-5"):
    return json.dumps({"type": "assistant", "requestId": rid, "uuid": rid + str(out), "attributionAgent": "planner-docs", "timestamp": "2026-10-01T10:00:00Z",
                       "message": {"model": model, "usage": {"input_tokens": inp, "output_tokens": out, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cc}}})
def agent(sess, aid, name, lines):
    d = os.path.join(tdir, sess, "subagents"); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "agent-%s.jsonl" % aid), "w", encoding="utf-8").write("\n".join(lines) + "\n{not json}\n")
    open(os.path.join(d, "agent-%s.meta.json" % aid), "w", encoding="utf-8").write(json.dumps({"agentType": name}))

# req r1 written on 3 lines with growing output: counted once, from the largest
agent("s1", "a1", "planner-docs", [line("r1", 10, 5, 100, 20), line("r1", 10, 9, 100, 20), line("r1", 10, 40, 100, 20), line("r2", 7, 3, 50, 0)])
agent("s1", "a2", "planner-docs", [line("r3", 1, 1, 1, 1)])
agent("s2", "a3", "coder", [line("r4", 100, 200, 300, 400, "claude-sonnet-5-5")])
r = ac.summary(proj)
by = {a["agent"]: a for a in r["agents"]}
ok(r["available"] and r["complete"] and r["runs"] == 3, "3 runs found, scan complete")
p = by["planner-docs"]
ok((p["runs"], p["calls"], p["input"], p["output"], p["cache_read"], p["cache_creation"]) == (2, 3, 18, 44, 151, 21), "each request counted once (largest line), sums per agent")
ok(by["coder"]["models"] == ["claude-sonnet-5-5"] and p["models"] == ["claude-haiku-5-5"], "model kept per agent")
ok(r["total"] == sum(a["total"] for a in r["agents"]) and r["agents"][0]["total"] >= r["agents"][1]["total"], "total matches and biggest first")
ok(os.path.isfile(os.path.join(proj, "Claude", "logs", "agent-costs-cache.json")), "cache written under Claude/logs")
# cached second run gives the same answer even with a zero time budget; a changed file is re-read
ok(ac.summary(proj, budget=0)["agents"] == r["agents"], "cached result reused (no re-read)")
agent("s2", "a3", "coder", [line("r4", 100, 200, 300, 400, "claude-sonnet-5-5"), line("r5", 1, 1, 1, 1, "claude-sonnet-5-5")])
time.sleep(0.01)
os.utime(os.path.join(tdir, "s2", "subagents", "agent-a3.jsonl"), (time.time() + 5, time.time() + 5))
ok({a["agent"]: a for a in ac.summary(proj)["agents"]}["coder"]["calls"] == 2, "a changed file is read again")
r0 = ac.summary(proj, days=30, budget=-1)
ok(r0["complete"] is True or r0["pending"] >= 0, "time budget never raises")
old = os.path.join(tdir, "s1", "subagents", "agent-a1.jsonl"); os.utime(old, (1, 1))
ok(by["planner-docs"]["runs"] == 2 and {a["agent"]: a for a in ac.summary(proj)["agents"]}["planner-docs"]["runs"] == 1, "files older than the window are left out")

# --- the console server serves it (/agent-costs), also when nothing is found ---
import subprocess, urllib.request, socket
srv = os.path.join(root, "project-template", "Claude", "hooks", "agent-console-server.py")
proj_kit = os.path.dirname(os.path.dirname(os.path.dirname(srv)))
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
env = dict(os.environ, CLAUDE_CONFIG_DIR=tempfile.mkdtemp(), UEFN_KIT_CACHE_DIR=tempfile.mkdtemp())   # empty config dir: no transcripts
pr = subprocess.Popen([sys.executable, srv, str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    body = None
    for _ in range(40):
        try:
            body = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/agent-costs" % port, timeout=3).read()); break
        except Exception:
            time.sleep(0.25)
    ok(body is not None and body.get("available") is False and "reason" in body, "server: /agent-costs says 'not available' with a reason when there are no transcripts")
    tdir2 = os.path.join(env["CLAUDE_CONFIG_DIR"], "projects", re.sub(r"[^A-Za-z0-9]", "-", proj_kit), "s1", "subagents"); os.makedirs(tdir2)
    open(os.path.join(tdir2, "agent-z1.jsonl"), "w", encoding="utf-8").write(line("q1", 5, 6, 7, 8) + "\n")
    open(os.path.join(tdir2, "agent-z1.meta.json"), "w", encoding="utf-8").write(json.dumps({"agentType": "qa-regression"}))
    body = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/agent-costs" % port, timeout=5).read())
    ok(body.get("available") and body["agents"][0]["agent"] == "qa-regression" and body["agents"][0]["total"] == 26, "server: /agent-costs returns the per-agent table")
finally:
    pr.terminate()
