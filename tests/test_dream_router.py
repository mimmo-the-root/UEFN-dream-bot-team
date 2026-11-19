"""Dream Router: translation, streaming, fallback on limit, tool-call rescue, key editing - against fake providers, no network."""
import json, os, sys, tempfile, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "user-level-hooks")):
    if os.path.isfile(os.path.join(p, "dream_router.py")):
        sys.path.insert(0, p)
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")  # never the real profile
PLAN = {"status": 200, "seen": []}
import dream_router as dr
dr.DEFAULT_SETTINGS["explore"] = 0  # deterministic tests: exploration is tested on its own (section 28)
dr.check_all = lambda: []  # no background key check racing the routing tests (saving a key starts one)
dr.PORT = 1  # never the owner's live router on 8787: the guardian tests send /router/quit to dr.PORT

CALLS = []


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, hdr=None):
        b = json.dumps(obj).encode()
        self.send_response(code)
        for k, v in (hdr or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._send(200, {"data": [{"id": "small-model"}, {"id": "good-coder-model"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.startswith("/v1/some"):  # another Claude-only endpoint
            return self._send(200, {"classifier": "ok"})
        if self.path.startswith("/v1/messages"):  # the fake Claude behind the plan
            PLAN["seen"].append(self.headers.get("Authorization"))
            if PLAN["status"] == 429:
                return self._send(429, {"type": "error", "error": {"type": "rate_limit_error", "message": "usage limit"}}, {"retry-after": "300"})
            b = b'event: message_start\ndata: {"type":"message_start","message":{"usage":{"input_tokens":40,"output_tokens":1}}}\n\nevent: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":7}}\n\n'
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        CALLS.append((self.path.split("/")[1], body))
        if self.path.startswith("/busy"):
            return self._send(429, {"error": {"message": "rate limit"}}, {"Retry-After": "120"})
        last = body["messages"][-1]
        if body.get("tools") and last["role"] == "user":
            if "rescue" in str(last["content"]):
                msg = {"role": "assistant", "content": 'I will read it.\n<tool_call>{"name": "Read", "arguments": {"file_path": "a.txt"}}</tool_call>'}
            else:
                msg = {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "Read", "arguments": '{"file_path": "a.txt"}'}}]}
            fr = "tool_calls"
        else:
            msg, fr = {"role": "assistant", "content": "<think>x</think>Hello from the free model"}, "stop"
        self._send(200, {"choices": [{"message": msg, "finish_reason": fr}], "usage": {"prompt_tokens": 100, "completion_tokens": 20}})


fake = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=fake.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % fake.server_port
dr.UPSTREAM = base
json.dump({"busy": {"base": base + "/busy", "key": "BUSY_KEY", "prefer": ["good"]},
           "ok": {"base": base + "/ok", "key": "OK_KEY", "prefer": ["good"]}}, open(os.path.join(home, "providers.json"), "w"))
json.dump({"chain": ["busy", "ok"], "mode": "free"}, open(os.path.join(home, "routing.json"), "w"))
dr.save_key("BUSY_KEY", "busy-key-123456")
dr.save_key("OK_KEY", "ok-key-1234567")

router = ThreadingHTTPServer(("127.0.0.1", 0), dr.Handler)
threading.Thread(target=router.serve_forever, daemon=True).start()
R = "http://127.0.0.1:%d" % router.server_port


def post(path, obj, hdr=None):
    rq = urllib.request.Request(R + path, json.dumps(obj).encode(), headers=dict({"Content-Type": "application/json"}, **(hdr or {})))
    with urllib.request.urlopen(rq, timeout=10) as r:
        return r.read().decode(), dict(r.headers)


TOOLS = [{"name": "Read", "description": "read a file", "input_schema": {"$schema": "x", "type": "object", "properties": {"file_path": {"type": "string"}}}}]

# 1. plain text, busy provider skipped, cooldown honours Retry-After
out, h = post("/v1/messages", {"model": "claude-sonnet", "max_tokens": 100, "system": [{"type": "text", "text": "be brief"}], "messages": [{"role": "user", "content": "hi"}]})
m = json.loads(out)
assert m["content"][0]["text"] == "Hello from the free model", m
assert h["X-Routed-Via"] == "ok/good-coder-model", h
assert dr.STATE["cooldown"]["busy"] > time.time() + 100
assert CALLS[-1][1]["messages"][0] == {"role": "system", "content": "be brief"}
# 2. busy is now paused: not called again
n = len(CALLS)
post("/v1/messages", {"model": "x", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]})
assert [c[0] for c in CALLS[n:]] == ["ok"], CALLS[n:]
# 3. tools: translated, schema cleaned, tool_use returned, streamed as Anthropic events
out, _ = post("/v1/messages", {"model": "x", "max_tokens": 10, "stream": True, "tools": TOOLS, "messages": [{"role": "user", "content": [{"type": "text", "text": "read a.txt"}]}]})
assert "$schema" not in json.dumps(CALLS[-1][1]["tools"])
assert "event: message_start" in out and '"input_json_delta"' in out and '"stop_reason": "tool_use"' in out, out
# 4. tool results go back as tool messages
post("/v1/messages", {"model": "x", "max_tokens": 10, "tools": TOOLS, "messages": [
    {"role": "user", "content": "read a.txt"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1", "name": "Read", "input": {"file_path": "a.txt"}}]},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": [{"type": "text", "text": "hello"}]}]}]})
msgs = CALLS[-1][1]["messages"]
assert msgs[-2]["tool_calls"][0]["function"]["name"] == "Read" and msgs[-1] == {"role": "tool", "tool_call_id": "call_1", "content": "hello"}, msgs
# 5. a tool call written as text is rescued
m = json.loads(post("/v1/messages", {"model": "x", "max_tokens": 10, "tools": TOOLS, "messages": [{"role": "user", "content": "rescue please"}]})[0])
assert m["stop_reason"] == "tool_use" and m["content"][-1]["input"] == {"file_path": "a.txt"} and m["content"][0]["text"] == "I will read it.", m
# 6. usage ledger and state for the console page, sorted by tokens, keys masked
st = json.loads(urllib.request.urlopen(R + "/router/state").read())
assert st["models"][0]["model"] == "good-coder-model" and st["models"][0]["input"] >= 500, st["models"]
assert "ok-key-1234567" not in json.dumps(st) and st["providers"][1]["key_hint"] == "…4567"
# 7. settings and keys need the console header; key edit and removal
try:
    post("/router/settings", {"enabled": False})
    raise SystemExit("settings without header accepted")
except urllib.error.HTTPError as e:
    assert e.code == 403
dr.STATE["bad"]["ok"] = "the provider refused the key (HTTP 403)"
st = json.loads(urllib.request.urlopen(R + "/router/state").read())
assert [x for x in st["providers"] if x["name"] == "ok"][0]["status"] == "failed", "a refused key is red, never ready"
post("/router/keys", {"provider": "ok", "key": "new-key-abcdef12"}, {"X-Router-Action": "1"})
assert "ok" not in dr.STATE["bad"], "a new key clears the failure"
assert dr.keys()["OK_KEY"] == "new-key-abcdef12" and dr.keys()["BUSY_KEY"] == "busy-key-123456"
post("/router/keys", {"provider": "busy", "key": ""}, {"X-Router-Action": "1"})
assert "BUSY_KEY" not in dr.keys()
# 9. mode auto: the plan request passes through untouched; at the plan limit the SAME request goes to the free models
post("/router/settings", {"mode": "auto"}, {"X-Router-Action": "1"})
assert dr.settings()["mode"] == "auto"
post("/router/settings", {"safety_samples": True}, {"X-Router-Action": "1"})  # T-081: the debug flag can be turned on from the console
assert dr.settings()["safety_samples"] is True
post("/router/settings", {"safety_samples": False}, {"X-Router-Action": "1"})
assert dr.settings()["safety_samples"] is False
out, h = post("/v1/messages?beta=true", {"model": "claude-sonnet", "max_tokens": 10, "stream": True, "messages": [{"role": "user", "content": "hi"}]}, {"Authorization": "Bearer plan-login-abc"})
assert h["X-Routed-Via"] == "claude-plan/claude-sonnet" and "message_delta" in out and PLAN["seen"][-1] == "Bearer plan-login-abc", h
PLAN["status"] = 429
out, h = post("/v1/messages", {"model": "claude-sonnet", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}, {"Authorization": "Bearer plan-login-abc"})
assert h["X-Routed-Via"].startswith("ok/") and json.loads(out)["content"][0]["text"] == "Hello from the free model"
n = len(PLAN["seen"])
post("/v1/messages", {"model": "claude-sonnet", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}, {"Authorization": "Bearer plan-login-abc"})
assert len(PLAN["seen"]) == n, "while the plan is paused it is not asked again"
st = json.loads(urllib.request.urlopen(R + "/router/state").read())
assert not st["plan"]["available"] and st["plan"]["resume_in"] > 200
dr.STATE["plan_until"] = 0; PLAN["status"] = 200
post("/v1/messages", {"model": "claude-sonnet", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}, {"Authorization": "Bearer dream-router-local"})
assert len(PLAN["seen"]) == n, "the free-mode token is never sent to Claude"
use = json.load(open(os.path.join(home, "usage.json")))["models"]
assert use["claude-plan/claude-sonnet"]["input"] == 40 and use["claude-plan/claude-sonnet"]["output"] == 7, use
# other Claude Code calls (auto-mode safety check...): passed to Claude with the plan login, refused with a reason in free mode
out, h = post("/v1/some/classifier", {"x": 1}, {"Authorization": "Bearer plan-login-abc"})
assert "classifier" in out, "forwarded upstream with the plan login"
post("/router/settings", {"enabled": False, "mode": "free"}, {"X-Router-Action": "1"})
try:
    post("/v1/some/classifier", {"x": 1}, {"Authorization": "Bearer dream-router-local"})
    raise SystemExit("free mode answered a Claude-only call")
except urllib.error.HTTPError as e:
    assert e.code == 404 and "permission mode" in e.read().decode()
assert any(x["provider"] == "claude-code" for x in dr.recent_errors(50))
assert dr.settings()["mode"] == "free"
try:
    post("/v1/messages", {"model": "x", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]})
    raise SystemExit("off router answered")
except urllib.error.HTTPError as e:
    assert e.code == 503
# 8. count_tokens and redaction
assert json.loads(post("/v1/messages/count_tokens", {"messages": [{"role": "user", "content": "x" * 400}]})[0])["input_tokens"] > 90
assert "AIza***" in dr.redact("key AIzaSyABCDEFGHIJK leaked")
# 10. the mode reaches Claude Code however it is started: the "env" of the user's settings.json, only our 3 keys
sp = os.path.join(home, "settings.json")
json.dump({"model": "opus", "env": {"MY_VAR": "x"}}, open(sp, "w"))
assert dr.apply_mode_to_claude("free", True, sp).startswith("written")
d = json.load(open(sp)); assert d["model"] == "opus" and d["env"]["MY_VAR"] == "x" and d["env"]["ANTHROPIC_AUTH_TOKEN"] == "dream-router-local" and d["env"]["ANTHROPIC_BASE_URL"].startswith("http://127.0.0.1")
dr.apply_mode_to_claude("auto", True, sp); d = json.load(open(sp)); assert "ANTHROPIC_AUTH_TOKEN" not in d["env"] and "ANTHROPIC_BASE_URL" in d["env"] and d["env"]["CLAUDE_CODE_AUTO_MODE_SERVER"] == "0"
dr.apply_mode_to_claude("plan", True, sp); d = json.load(open(sp)); assert d["env"] == {"MY_VAR": "x"}, d
assert dr.apply_mode_to_claude("plan", True, sp) == "unchanged" and os.path.isfile(sp + ".dream-router.bak")
json.dump({"env": {"ANTHROPIC_BASE_URL": "https://my-company-gateway"}}, open(sp, "w"))
dr.apply_mode_to_claude("plan", True, sp); assert json.load(open(sp))["env"]["ANTHROPIC_BASE_URL"] == "https://my-company-gateway", "never removes the owner's own values"
# 10b. Free only + accept edits: Cod starts in accept-edits mode (no auto-mode safety check); the owner's own mode comes back
assert dr.settings()["free_accept_edits"] is False, "auto mode stays the default"
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), free_accept_edits=True))
json.dump({"permissions": {"defaultMode": "auto", "allow": ["Read"]}}, open(sp, "w"))
dr.apply_mode_to_claude("free", True, sp); d = json.load(open(sp)); assert d["permissions"] == {"defaultMode": "acceptEdits", "allow": ["Read"]}, d
dr.apply_mode_to_claude("auto", True, sp); d = json.load(open(sp)); assert d["permissions"]["defaultMode"] == "auto", d
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), free_accept_edits=False))
dr.apply_mode_to_claude("free", True, sp); assert json.load(open(sp))["permissions"]["defaultMode"] == "auto", "switch off: not touched"
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), free_accept_edits=True))
json.dump({}, open(sp, "w")); dr.apply_mode_to_claude("free", True, sp); assert json.load(open(sp))["permissions"]["defaultMode"] == "acceptEdits"
dr.apply_mode_to_claude("plan", True, sp); assert "permissions" not in json.load(open(sp)), json.load(open(sp))
assert json.load(open(dr.session_settings("free")))["permissions"]["defaultMode"] == "acceptEdits"
# 11. Gemini 3 thought signatures go back with the tool call; unknown ones get the documented placeholder
resp = {"choices": [{"message": {"content": None, "tool_calls": [{"id": "c9", "type": "function", "function": {"name": "Read", "arguments": "{}"},
        "extra_content": {"google": {"thought_signature": "SIG123"}}}]}, "finish_reason": "tool_calls"}], "usage": {}}
dr.to_anthropic(resp, {"tools": TOOLS}, "gemini/x")
back = dr.to_openai({"messages": [{"role": "assistant", "content": [{"type": "tool_use", "id": "c9", "name": "Read", "input": {}},
                                                                   {"type": "tool_use", "id": "other", "name": "Read", "input": {}}]}]}, "g", {"thought_signatures": True})
tc = back["messages"][0]["tool_calls"]
assert tc[0]["extra_content"]["google"]["thought_signature"] == "SIG123" and tc[1]["extra_content"]["google"]["thought_signature"] == "skip_thought_signature_validator"
assert "extra_content" not in dr.to_openai({"messages": [{"role": "assistant", "content": [{"type": "tool_use", "id": "c9", "name": "Read", "input": {}}]}]}, "m", {})["messages"][0]["tool_calls"][0]
# 12. stop sequences: the text is cut there and the answer says which sequence stopped it
r = dr.to_anthropic({"choices": [{"message": {"content": "<block>no</block> extra"}, "finish_reason": "stop"}]}, {"stop_sequences": ["</block>"]}, "x")
assert r["content"][0]["text"] == "<block>no" and r["stop_reason"] == "stop_sequence" and r["stop_sequence"] == "</block>", r
r = dr.to_anthropic({"choices": [{"message": {"content": "<block>yes"}, "finish_reason": "stop"}]}, {"stop_sequences": ["</block>"]}, "x")
assert r["stop_reason"] == "stop_sequence" and r["stop_sequence"] == "</block>"
P = dr.PROVIDERS
assert len(dr.DEFAULT_SETTINGS["chain"]) == 12 and set(dr.DEFAULT_SETTINGS["chain"]) == set(P) and "mistral" not in P and "longcat" not in P, "ten free providers + DeepSeek and ZenMux (paid, last)"
assert dr.DEFAULT_SETTINGS["chain"][-2:] == ["deepseek", "zenmux"] and P["zenmux"]["paid"] and P["deepseek"]["paid"]
dr.STATE.setdefault("cf_acct", {})["cfut_tok"] = "acct9"   # 1.124.57: a Cloudflare token alone; the account is looked up once
assert dr.endpoint(P["cloudflare"], "cfut_tok") == ("https://api.cloudflare.com/client/v4/accounts/acct9/ai/v1", "cfut_tok")
assert dr.endpoint({"base": "https://x/{account}/v1"}, "acc123:tok456") == ("https://x/acc123/v1", "tok456")  # ACCOUNT:TOKEN keys still work for custom providers
assert dr.provider_key(P["kilo"], {}) == "" and dr.endpoint(P["kilo"], "")[1] == "anonymous" and dr.provider_key(P["zai"], {}) is None
# 13. the guardian starts the router when it does not answer, replaces an old version, and stops at STOP
# the busy probe is stubbed: without it the test asks the REAL router on port 8787 (a live request resets
# its idle counter, so the guardian waits and the test fails depending on what the owner is doing)
idle_ok = lambda: (0, 9999)
seq = [None, "1.124.16"]; started = []
h = lambda: seq.pop(0) if seq else dr._file_version()
assert dr.supervise(every=0, sleep=lambda x: None, start=lambda: started.append(1), health=h, max_rounds=3, busy=idle_ok) == "rounds" and started == [1]
old = ["0.0.1"]; started = []
h2 = lambda: old.pop(0) if old else dr._file_version()
dr.supervise(every=0, sleep=lambda x: None, start=lambda: started.append(1), health=h2, max_rounds=2, busy=idle_ok); assert started == [1], "an older router is replaced"
# 13b. an updated router waits until nothing is running (no request lost mid-way), at most 15 minutes
old = lambda: "0.0.1"; started = []; bz = [(1, 0), (0, 3), (0, 25)]
dr.supervise(every=0, sleep=lambda x: None, start=lambda: started.append(1), health=old, max_rounds=3, busy=lambda: bz.pop(0) if bz else (0, 99))
assert started == [1], "replaced only at the third round, when idle 25 s"
t = [0]; started = []
def clk():
    t[0] += 400; return t[0]
dr.supervise(every=0, sleep=lambda x: None, start=lambda: started.append(1), health=old, max_rounds=4, busy=lambda: (2, 0), clock=clk)
assert started, "after 15 minutes of waiting it replaces it anyway"
open(os.path.join(home, "STOP"), "w").write("x")

assert dr.supervise(every=0, sleep=lambda x: None, start=lambda: None, health=lambda: None, max_rounds=5, busy=idle_ok) == "stopped" and not os.path.exists(os.path.join(home, "STOP"))
started = []; fails = lambda: None
dr.supervise(every=0, sleep=lambda x: None, start=lambda: started.append(1), health=fails, max_rounds=7, busy=idle_ok); assert len(started) == 7, "keeps trying when the start fails"
# 14. deferred MCP tools are sent only after tool search loaded them; tool outputs are shrunk the same way every time
req = {"tools": [{"name": "Read"}, {"name": "mcp__unreal-mcp__spawn", "defer_loading": True}, {"name": "mcp__unreal-mcp__list", "defer_loading": True}],
       "messages": [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "tool_reference", "tool_name": "mcp__unreal-mcp__spawn"}]}]}]}
assert [t["name"] for t in dr.visible_tools(req)] == ["Read", "mcp__unreal-mcp__spawn"]
o = dr.to_openai(req, "m", {})
assert [t["function"]["name"] for t in o["tools"]] == ["Read", "mcp__unreal-mcp__spawn"] and "Tools now available: mcp__unreal-mcp__spawn" in o["messages"][-1]["content"]
log = "\x1b[31mERR\x1b[0m  \n" + "same line\n" * 50 + "\n\n\n\nend" + "x" * 3000
c = dr.compress_text(log)
assert "\x1b" not in c and "repeated 49 more times" in c and "\n\n\n" not in c and c == dr.compress_text(log)
big = "\n".join("line %d" % i for i in range(20000))
cb = dr.compress_text(big); assert len(cb) < 25000 and "cut by the router" in cb and cb.startswith("line 0") and cb.endswith("line 19999")
# 15. tool names a provider would refuse (over 64 characters) are shortened on the way out and mapped back on the way in
LONG = "mcp__unreal-mcp__AIAssistantEditor_AIAssistantToolset_GetProjectContext"
LONG2 = "mcp__unreal-mcp__animation_toolset_toolsets_controlrig_sequencer_SequencerControlRigTools_set_world_transform"
req = {"tools": [{"name": "Read"}, {"name": LONG}, {"name": LONG2}],
       "messages": [{"role": "assistant", "content": [{"type": "tool_use", "id": "c1", "name": LONG, "input": {}}]}]}
o = dr.to_openai(req, "m", {})
wn = [t["function"]["name"] for t in o["tools"]]
assert wn[0] == "Read" and all(dr.FN_OK.match(n) for n in wn) and len(set(wn)) == 3, wn
assert o["messages"][0]["tool_calls"][0]["function"]["name"] == wn[1], "history uses the same short name"
resp = {"choices": [{"message": {"tool_calls": [{"id": "x", "function": {"name": wn[2], "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]}
assert dr.to_anthropic(resp, req, "p/m")["content"][0]["name"] == LONG2, "the real name comes back"
assert dr.to_openai({"tools": [{"name": "Read"}], "messages": []}, "m", {})["tools"][0]["function"]["name"] == "Read"
# 16. a provider that hangs or has no quota left is paused for minutes, so the next one in the chain answers without a long wait
PE = dr.ProviderError
assert dr.pause_seconds(PE("server", 0, "The read operation timed out")) == 600 and dr.pause_seconds(PE("server", 503, "busy")) == 0
assert dr.pause_seconds(PE("limit", 429, "You exceeded your current quota")) == 600 and dr.pause_seconds(PE("limit", 429, "slow down")) == 60
assert dr.pause_seconds(PE("limit", 429, "x", retry_after=7)) == 7
dr.STATE["cooldown"]["zz"] = time.time() + 300; dr.save_pauses()
assert dr._read_json("pauses.json", {}).get("zz", 0) > time.time(); dr.STATE["cooldown"].pop("zz")
# 17. the provider that answered last goes first; a model that hangs twice is set aside; a provider whose only model is set aside is skipped
assert dr.classify(410, "model retired") == "model" and dr.STATE["last_ok"] == "ok", "the provider that answered is remembered"
pv = {"key": "K", "models": ["only-one"]}
dr.STATE["lockout"]["xx/only-one"] = time.time() + 60; dr.STATE["models"].pop("xx", None)
dr.list_models = lambda prov, key: (_ for _ in ()).throw(dr.ProviderError("server", 0, "no list"))  # last section: no live list
assert dr.pick_model("xx", pv, "k") is None, "locked fallback model is not used again"
dr.STATE["lockout"].pop("xx/only-one")
# 17b. every provider says how many models it offers (Models page counter)
st = json.loads(urllib.request.urlopen(R + "/router/state").read())
assert any(isinstance(p.get("models_count"), int) and p["models_count"] >= 1 for p in st["providers"]), st["providers"]
# 18. cod.cmd --plan/--free: a per-session settings file that outranks the env written in settings.json
f = dr.session_settings("plan"); e = json.load(open(f))["env"]
# plan mode: BASE_URL points at Anthropic, AUTH_TOKEN key is ABSENT (not empty-string: an empty string
# falls back to settings.json which would leak the router token into the plan request — issue #1 of test 060)
assert e["ANTHROPIC_BASE_URL"] == dr.UPSTREAM and "ANTHROPIC_AUTH_TOKEN" not in e and f.endswith("cod-plan.json")
e = json.load(open(dr.session_settings("free")))["env"]
assert e["ANTHROPIC_BASE_URL"].startswith("http://127.0.0.1") and e["ANTHROPIC_AUTH_TOKEN"] == dr.FREE_TOKEN
e = json.load(open(dr.session_settings("auto")))["env"]
assert e["ANTHROPIC_AUTH_TOKEN"] == "" and e["ANTHROPIC_BASE_URL"].startswith("http://127.0.0.1")
# 19. a piece can be pinned to one provider/model (dream:<provider>/<model>); candidates lists models across providers
post("/router/settings", {"enabled": True, "mode": "free"}, {"X-Router-Action": "1"}); dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear()
out, h = post("/v1/messages", {"model": "dream:ok/pinned-model", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]})
assert h["X-Routed-Via"] == "ok/pinned-model" and CALLS[-1][1]["model"] == "pinned-model", h
dr.list_models = lambda prov, key: ["good-coder-model", "small-1b", "other-good"]
dr.STATE.pop("lists", None)
c = json.loads(urllib.request.urlopen(R + "/router/candidates?n=5").read())["models"]
assert c and all("/" in x for x in c) and not any("small-1b" in x for x in c), c
# 20. the Models page lists only the last 72 hours
h = int(time.time() // 3600)
dr._write_json("usage-72h.json", {"a/old": {"provider": "a", "model": "old", "hours": {str(h - 80): [9, 9, 1, 0]}},
                                  "b/new": {"provider": "b", "model": "new", "hours": {str(h - 2): [5, 1, 1, 0], str(h): [5, 0, 1, 1]}}})
rm = dr.recent_models(); assert [m["model"] for m in rm] == ["new"] and rm[0]["input"] == 10 and rm[0]["errors"] == 1, rm
# 21. long base64 keys (LLM7) are accepted: + / = and 150+ characters
b64 = "Ab1+/x" * 25 + "=="
post("/router/keys", {"provider": "ok", "key": b64}, {"X-Router-Action": "1"})
assert dr.keys()["OK_KEY"] == b64 and not dr.KEY_OK.match("has space here") and not dr.KEY_OK.match('quo"te12345')
# 22. side requests (no tools: auto-mode safety check, titles) are measured apart from the work requests
dr.STATE["sizes"] = []
dr.note_size({"system": "x" * 4000, "tools": [{"name": "Read"}], "messages": [{"role": "user", "content": "y" * 400}]})
dr.note_size({"system": "You are a security monitor " + "z" * 40000, "messages": [{"role": "user", "content": "w" * 4000}]})
z = dr.size_summary(); assert z["requests"] == 1 and z["system"] < 1100 and z["side"]["requests"] == 1 and z["side"]["system"] > 9000, z
assert z["side"]["sample"]["system_start"].startswith("You are a security monitor")
assert dr.DEFAULT_SETTINGS["chain"][-1] == "zenmux" and dr.PROVIDERS["deepseek"]["paid"] and dr.PROVIDERS["zenmux"]["paid"]
# 23. the auto-mode safety check is sent short to the free models: owner messages + the recent part of the session
tr = "User: build the score counter in ScoreManager.verse\n" + "".join("Bash: step %d\n  output %s\n" % (i, "x" * 300) for i in range(400)) + "User: now run the tests\nBash: python test_calc.py\n"
sc = {"model": "claude-sonnet", "max_tokens": 64, "system": "You are a security monitor. Respond with <block>yes</block> or <block>no</block>.",
      "messages": [{"role": "user", "content": [{"type": "text", "text": "<transcript>\n" + tr + "</transcript>\nShould the last action be blocked?"}]}]}
assert dr.is_safety_check(sc) and not dr.is_safety_check(dict(sc, tools=[{"name": "Read"}]))
small = dr.shrink_safety_check(sc); txt = small["messages"][0]["content"][0]["text"]
assert len(txt) < len(sc["messages"][0]["content"][0]["text"]) / 5, len(txt)
assert "User: build the score counter" in txt and "User: now run the tests" in txt and "Bash: python test_calc.py" in txt and txt.endswith("Should the last action be blocked?")
assert "left out by the router" in txt and dr.STATE["safety"]["checks"] >= 1
assert dr.shrink_safety_check({"messages": [{"role": "user", "content": "<transcript>\nUser: hi\n</transcript>"}]})["messages"][0]["content"] == "<transcript>\nUser: hi\n</transcript>"
# 23b. the session can travel in the instructions too: shrunk there as well, and the shape of the last check is kept
sc2 = {"model": "claude-sonnet", "max_tokens": 64, "system": [{"type": "text", "text": "You are a security monitor.\n<transcript>\n" + tr + "</transcript>"}],
       "messages": [{"role": "user", "content": "Judge the last action."}]}
assert dr.is_safety_check(sc2)
small2 = dr.shrink_safety_check(sc2); assert len(small2["system"][0]["text"]) < len(sc2["system"][0]["text"]) / 5
assert dr._read_json("last-safety-check.json", {})["system"][0]["chars"] > 10000
# 24. spread the load: providers that answered recently take turns
dr.STATE["ok_at"] = {"busy": time.time(), "ok": time.time()}; dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["bad"].clear(); dr.STATE["checked"] = {"busy": time.time(), "ok": time.time()}
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=True, chain=["busy", "ok"]))
dr.save_key("BUSY_KEY", "busy-key-123456")
seen = []
real_http = dr._http
dr._http = lambda url, key, payload=None, timeout=180: (seen.append(url.split("/")[3]), {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}})[1]
for _ in range(4):
    dr.STATE["bad"].clear()  # the background key check of an earlier section may still be running
    dr.route({"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
dr._http = real_http
assert seen[:4] in (["busy", "ok", "busy", "ok"], ["ok", "busy", "ok", "busy"]), seen

# 24b. T-023 pinning: with spread on, model chosen once per package/session key and kept until that package ends
# Test: 20 packages, model chosen once per package, count switches inside/outside packages
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=True, chain=["busy", "ok"]))
dr.save_key("BUSY_KEY", "busy-key-123456")
dr.save_key("OK_KEY", "ok-key-1234567")

# Clear any prior pinning state
dr.STATE["pinned"] = {}
dr.STATE["last_ok"] = None

# Mock HTTP for this test
real_http_pin = dr._http
dr._http = lambda url, key, payload=None, timeout=180: ({"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {"input_tokens": 5, "output_tokens": 5}})

pkg_calls_per_package = 3  # how many route calls per package
pkg_model_counts = {}  # package_key -> model

for pkg_idx in range(20):
    pkg_key = "pkg-%d" % pkg_idx
    req = {"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}],
           "metadata": {"package_id": pkg_key}}
    # Make multiple calls within the same package - model should stay pinned
    chosen_model = None
    for _ in range(pkg_calls_per_package):
        out, via, errors = dr.route(req)
        if via:
            m = via.split("/")[-1] if "/" in via else via
            if chosen_model is None:
                chosen_model = m
            else:
                assert m == chosen_model, "Model switched inside package %s: %s then %s" % (pkg_key, chosen_model, m)
    # Record what model was pinned for this package
    pinned = dr.STATE.get("pinned", {}).get(pkg_key)
    if pinned and chosen_model:
        pkg_model_counts[pkg_key] = pinned["model"]

# Restore HTTP
dr._http = real_http_pin

# Count switches between packages
pkg_switches = 0
pkg_keys_sorted = sorted(pkg_model_counts.keys())
prev_model = None
for k in pkg_keys_sorted:
    m = pkg_model_counts[k]
    if prev_model is not None and m != prev_model:
        pkg_switches += 1
    prev_model = m

# Assert: each package has exactly one model pinned
for k, m in pkg_model_counts.items():
    pin_entry = dr.STATE.get("pinned", {}).get(k)
    assert pin_entry is not None, "Package %s has no pin entry" % k
    assert pin_entry["model"] == m, "Package %s pinned model changed" % k

# Assert: there should be switches between packages (spread is working across packages)
assert pkg_switches > 0, "Expected some model switches between packages with spread=True, but none occurred"

print("T-023 Pinning test PASSED: model pinned per package, switches between packages = %d" % pkg_switches)

# Store numbers in plan/telemetry (as task requires)
import os
telemetry_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plan", "telemetry")
os.makedirs(telemetry_dir, exist_ok=True)
telemetry_file = os.path.join(telemetry_dir, "t-023-pinning.json")
telemetry_data = {
    "test": "T-023 pinning",
    "packages_tested": 20,
    "calls_per_package": pkg_calls_per_package,
    "model_switches_between_packages": pkg_switches,
    "packages_with_single_model": len(pkg_model_counts),
    "spread_enabled": True,
    "timestamp": time.time()
}
dr._write_json(telemetry_file, telemetry_data)
print("Telemetry written to %s" % telemetry_file)

# 25. on a gateway a rate limit rests ONE model: the next models of the same provider are tried before the next provider
dr.PER_MODEL_LIMITS.add("busy"); dr.STATE["last_ok"] = None; dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["mcool"] = {}
dr.STATE.setdefault("lists", {})["busy"] = (["good-a", "good-b", "good-c", "good-d"], time.time())
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=False, chain=["busy", "ok"]))
dr.save_key("BUSY_KEY", "busy-key-123456")
n = len(CALLS)
out, h = post("/v1/messages", {"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
tried = [c for c in CALLS[n:] if c[0] == "busy"]
assert len(tried) == 4 and len({c[1]["model"] for c in tried}) == 4, "every free model of the provider is tried: %s" % tried
assert h["X-Routed-Via"].startswith("ok/") and all(k.startswith("busy/") for k in dr.STATE["mcool"]), h
# per-model cooldown is in mcool, not cooldown: all 4 models of 'busy' are resting
assert len(dr.STATE["mcool"]) >= 4 and all(v > time.time() + 30 for v in dr.STATE["mcool"].values()), "all tried models resting"
# 26. trim_history: old tool results are replaced with a note, the last 5 stay whole, user text is untouched
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), trim_history=True))
req = {"model": "x", "max_tokens": 64, "messages": []}
assert dr.trim_history(req) is req, "a short conversation is not trimmed"
msgs = [{"role": "user", "content": "x" * 61000}]  # force total > TRIM_OVER
for i in range(10):  # 10 tool results: the first 5 are old, the last 5 stay
    msgs.append({"role": "assistant", "content": [{"type": "tool_use", "id": str(i), "name": "tool%d" % i, "input": {}}]})
    msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": str(i), "content": "x" * 2500}]})
msgs.append({"role": "user", "content": "final user message"})
req["messages"] = msgs
t = dr.trim_history(req)
trb = [b for m in t["messages"] for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "tool_result"]
assert len(trb) == 10, "all 10 tool_result blocks are still present"
for i in range(5, 10):
    assert trb[i]["type"] == "tool_result" and trb[i]["tool_use_id"] == str(i) and trb[i]["content"] == "x" * 2500, "last 5 stay whole"
for i in range(5):
    assert trb[i]["type"] == "tool_result" and "cleared by the router" in trb[i]["content"], "first 5 become a note"
assert "final user message" in t["messages"][-1]["content"], "user text is untouched"
# instruction tool results are never cleared
msgs = []
for i in range(3):
    msgs.append({"role": "assistant", "content": [{"type": "tool_use", "id": str(i), "name": "askuserquestion", "input": {}}]})
    msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": str(i), "content": "yes"}]})
t = dr.trim_history({"model": "x", "max_tokens": 64, "messages": msgs})
trb = [b for m in t["messages"] for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "tool_result"]
assert len(trb) == 3, "the owner's answers are instructions, not output"
# dedupe: a long text block repeated keeps only the last copy
msgs = [{"role": "user", "content": "x" * 61000},
        {"role": "user", "content": [{"type": "text", "text": "x" * 3000}]},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "t1", "name": "tool1", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "y" * 3000}]}]},
        {"role": "user", "content": [{"type": "text", "text": "x" * 3000}]}]
t = dr.trim_history({"model": "x", "max_tokens": 64, "messages": msgs})
txtb = [b for m in t["messages"] for b in (m.get("content") or []) if isinstance(b, dict) and b.get("type") == "text"]
assert len(txtb) == 2, txtb
assert "[same text as later in the conversation]" in txtb[0]["text"], "the earlier copy becomes a note"
assert txtb[1]["text"] == "x" * 3000, "the last copy stays whole"
# the trim is counted and shown in the state
st = json.loads(urllib.request.urlopen(R + "/router/state").read())
assert st["trim"]["requests"] >= 1 and st["trim"]["chars_before"] >= st["trim"]["chars_after"], st["trim"]
# a request over the limit through the router arrives trimmed at the provider
dr.STATE["trim"] = dr.TRIM_STATE if hasattr(dr, "TRIM_STATE") else dr.TRIM_STATE
big = [{"role": "user", "content": [{"type": "text", "text": "z" * 61000}]}]
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), trim_history=True, chain=["ok"]))
n = len(CALLS)
post("/v1/messages", {"model": "x", "max_tokens": 5, "messages": big})
sent = CALLS[n][1] if CALLS else {}
assert len(json.dumps(sent.get("messages", []))) < 61000 * 2, "the huge request arrives smaller"
# 26. the router learns which models are quick: answered before, fastest first; never tried next; mostly failing last
dr.STATE["perf"] = {"p/slow": {"ok": 3, "fail": 0, "ms": 9000}, "p/fast": {"ok": 2, "fail": 1, "ms": 1200}, "p/bad": {"ok": 0, "fail": 4, "ms": None}}
assert dr.by_speed("p", ["bad", "new", "slow", "fast"]) == ["fast", "slow", "new", "bad"]
# 28. exploration: about 1 request in 20 starts with a model never tried; old bad results get a new chance after 24 h
import random as _r
dr.STATE["perf"] = {"p/a": {"ok": 5, "fail": 0, "ms": 900, "at": time.time()}, "p/old": {"ok": 0, "fail": 3, "ms": None, "at": time.time() - 90000}}
assert dr.by_speed("p", ["old", "a"]) == ["a", "old"] and dr.by_speed("p", ["old", "new", "a"])[1:] == ["new", "old"]
dr.STATE["perf"]["p/old"]["at"] = time.time()
assert dr.by_speed("p", ["old", "new", "a"]) == ["a", "new", "old"], "recent failures stay last"
dr.STATE.setdefault("lists", {})["busy"] = (["good-a", "good-b", "good-c"], time.time())
dr.STATE["perf"] = {"busy/good-a": {"ok": 9, "fail": 0, "ms": 500, "at": time.time()}}
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=False, explore=1.0, chain=["busy"]))
dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["mcool"] = {}; dr.STATE["last_ok"] = None
first = []
real_http = dr._http
dr._http = lambda url, key, payload=None, timeout=180: (first.append(payload["model"]), {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}})[1]
dr.route({"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
dr.route({"model": "dream:busy/good-a", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
dr._http = real_http
assert first[0] in ("good-b", "good-c") and first[1] == "good-a", first
assert json.loads(urllib.request.urlopen(R + "/router/state").read())["learned"]["explored"] >= 1
# 28b. exploration also finds models outside prefer patterns
dr.STATE.setdefault("lists", {})["busy"] = (["good-a", "other-b", "other-c"], time.time())
dr.STATE["perf"] = {"busy/good-a": {"ok": 9, "fail": 0, "ms": 500, "at": time.time()}}
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=False, explore=1.0, chain=["busy"]))
dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["mcool"] = {}; dr.STATE["last_ok"] = None
first = []
dr._http = lambda url, key, payload=None, timeout=180: (first.append(payload["model"]), {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}})[1]
dr.route({"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
dr._http = real_http
# With explore=1.0, it should try one of the non-prefer models (other-b or other-c)
assert first[0] in ("other-b", "other-c"), first
assert json.loads(urllib.request.urlopen(R + "/router/state").read())["learned"]["explored"] >= 2
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), explore=0))
# 29. a test can never break the owner's settings: unknown chain names fall back to the default chain, unknown key names are not written
saved = dr._read_json("routing.json", {})
dr._write_json("routing.json", dict(saved, chain=["nobody", "nothing"]))
assert dr.settings()["chain"] == dr.DEFAULT_SETTINGS["chain"]
dr._write_json("routing.json", saved)
assert dr.save_key("NOT_A_PROVIDER_KEY", "abcdefgh12") is False and "NOT_A_PROVIDER_KEY" not in dr.keys()
# 30. spread: a provider that has not answered recently still gets its turn; models in flight are listed for the page
dr.STATE["ok_at"] = {"ok": time.time()}; dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["mcool"] = {}; dr.STATE["bad"].clear()
dr._write_json("routing.json", dict(dr._read_json("routing.json", {}), enabled=True, spread=True, explore=0, chain=["busy", "ok"]))
dr.save_key("BUSY_KEY", "busy-key-123456")
seen = []; inflight = []
real_http = dr._http
def fake_http(url, key, payload=None, timeout=180):
    seen.append(url.split("/")[3]); inflight.append(list(dr.STATE.get("active", {})))
    return {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}}
dr._http = fake_http
for _ in range(4):
    dr.route({"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}]})
dr._http = real_http
assert "busy" in seen and "ok" in seen, seen
assert inflight[0] and not dr.STATE.get("active"), (inflight, dr.STATE.get("active"))
# 31. the transcript split over several text blocks (as Claude Code sends it) is shrunk too
parts = [{"type": "text", "text": "CLAUDE.md of the owner"}, {"type": "text", "text": "<transcript>\n"}] + \
        [{"type": "text", "text": '{"Bash":"step %d %s"}\n' % (i, "x" * 300)} for i in range(150)] + [{"type": "text", "text": "</transcript>\nGrade it."}]
before = dr.STATE.get("safety", {}).get("chars_after", 0)
small = dr.shrink_safety_check({"system": "You are a security monitor", "messages": [{"role": "user", "content": parts}]})
txt = small["messages"][0]["content"][0]["text"]
assert len(small["messages"][0]["content"]) == 1 and len(txt) < 25000 and "CLAUDE.md of the owner" in txt and txt.endswith("Grade it.") and "step 149" in txt, len(txt)
# 32. a usage file that cannot be read is never overwritten with an empty one (the owner's 72-hour history was lost so)
with open(os.path.join(home, "usage-72h.json"), "w") as f:
    f.write('{"half written')
dr.record_usage("x", "y", 10, 1)
assert open(os.path.join(home, "usage-72h.json")).read() == '{"half written', "kept as it was"
assert dr.STATE["last"]["model"] == "y"
dr._write_json("usage-72h.json", {})
# 33. the router starts even when model_history.py was not installed next to it (owner's router died so, 1.124.51)
import shutil, subprocess, tempfile
lone = tempfile.mkdtemp()
shutil.copy(dr.__file__, lone)
r = subprocess.run([sys.executable, "-c", "import dream_router as d; print(d.model_history)"], cwd=lone, capture_output=True, text=True,
                   env=dict(os.environ, PYTHONPATH="", DREAM_ROUTER_HOME=home))
assert r.returncode == 0 and "None" in r.stdout, r.stderr
# 34. every free model busy: the router holds the request and tries again (every 3 minutes), it does not hand the error to Cod at once
calls = []; real_route = dr.route
def busy_then_ok(req):
    calls.append(1)
    if len(calls) < 3:
        raise dr.ProviderError("all_failed", 529, "All free providers failed or are paused: x")
    return ({"content": []}, "ok/m", None)
dr.route = busy_then_ok
clock = [0.0]
msg, routed, _ = dr.route_patiently({"messages": []}, sleep=lambda x: clock.__setitem__(0, clock[0] + x), clock=lambda: clock[0], hold=180)
assert routed == "ok/m" and len(calls) == 3 and clock[0] <= 180, (calls, clock)
calls.clear(); dr.route = lambda req: (calls.append(1), (_ for _ in ()).throw(dr.ProviderError("all_failed", 529, "busy")))[1]
clock = [0.0]
try:
    dr.route_patiently({"messages": []}, sleep=lambda x: clock.__setitem__(0, clock[0] + x), clock=lambda: clock[0], hold=180)
    assert False, "still busy: the error goes back"
except dr.ProviderError as e:
    assert "Every free model was busy for 180 s" in e.detail and clock[0] >= 180, (e.detail, clock)
dr.route = lambda req: (_ for _ in ()).throw(dr.ProviderError("no_keys", 503, "no keys"))
try:
    dr.route_patiently({"messages": []}, sleep=lambda x: None, clock=time.time, hold=180)
    assert False
except dr.ProviderError as e:
    assert e.kind == "no_keys", "a missing key is not waited for"
dr.route = real_route
router.shutdown(); fake.shutdown()
print("ok dream_router")
