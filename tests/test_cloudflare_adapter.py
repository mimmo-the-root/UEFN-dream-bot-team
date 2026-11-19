"""T-104: Cloudflare adapter: plain string content, context window skip. No network."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
os.environ["DREAM_ROUTER_HOME"] = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(os.environ["DREAM_ROUTER_HOME"], "claude-settings.json")
import dream_router as dr
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

out = dr.cloudflare_messages([
    {"role": "user", "content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]},
    {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}]},
    {"role": "tool", "tool_call_id": "1", "content": None},
    {"role": "user", "content": "plain"}])
ok(out[0]["content"] == "a\nb", "array content is flattened to one string")
ok(out[1]["content"] == "" and out[1]["tool_calls"] == [{"id": "1"}], "assistant null content becomes '' and tool_calls are kept")
ok(out[2]["content"] == "", "tool null content becomes ''")
ok(out[3]["content"] == "plain", "string content is unchanged")
ok(all(isinstance(m["content"], str) for m in out), "every content is a string")

req = {"model": "x", "max_tokens": 100, "messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]}
cf = dict(dr.PROVIDERS["cloudflare"])
body = dr.to_openai(req, "@cf/meta/llama-3.3-70b-instruct-fp8-fast", cf)
ok(all(isinstance(m["content"], str) for m in body["messages"]), "to_openai sends plain strings to cloudflare")
other = {"base": "http://x", "key": "K", "max_tokens": 100}
ok(dr.to_openai(req, "m", other)["messages"] == dr.to_openai(req, "m", dict(other))["messages"], "other provider body is built the same")
ok("adapter" not in dr.PROVIDERS["groq"] and dr.model_context_limit(dr.PROVIDERS["groq"], "m") is None, "other providers have no context table")

fake = {"adapter": "cloudflare", "context_windows": [(r"coder", 32000), (r"big", 128000)], "context_default": 24000}
ok(dr.model_context_limit(fake, "@cf/qwen/qwen2.5-coder-32b") == 32000, "small model window found")
ok(dr.model_context_limit(fake, "@cf/x/big-model") == 128000, "big model window found")
ok(dr.model_context_limit(fake, "@cf/unknown") == 24000, "unknown model gets the default")
ok(dr.model_context_limit(dr.PROVIDERS["cloudflare"], "@cf/qwen/qwen2.5-coder-32b-instruct") == 32000, "real qwen2.5-coder is 32k")
need = 60000
ok(need > dr.model_context_limit(dr.PROVIDERS["cloudflare"], "@cf/qwen/qwen2.5-coder-32b-instruct"), "a 60k request is over the small window")
ok(need <= dr.model_context_limit(dr.PROVIDERS["cloudflare"], "@cf/openai/gpt-oss-120b"), "a 60k request fits the big window")
