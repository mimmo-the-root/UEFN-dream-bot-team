#!/usr/bin/env python3
"""Dream Router (v1.124.0) - a local gateway that lets Claude Code (Cod) run on FREE models.

Claude Code talks to it exactly as it talks to Claude (Anthropic Messages API, streaming included) when started with
ANTHROPIC_BASE_URL=http://127.0.0.1:<port>. The router turns each request into the OpenAI chat format that the free
providers speak, tries the providers in order and moves on to the next one when a provider is at its limit or fails.
Mode auto (default): Claude Code's own login and request pass through untouched to Claude; when Claude answers that the plan is
at its limit, the same request goes to the free models and the session never stops; the router goes back to Claude after the reset.
Mode free: the plan is never used. Mode plan: Cod is started without the router (cod.cmd).

What it aggregates (ideas and logic rewritten in Python; see THIRD-PARTY-NOTICES.md):
  * Anthropic <-> OpenAI translation, fallback loop, error classes, tool-call rescue, usage ledger, "routed via" header:
    freellmapi (MIT, Tashfeen Ahmed) and claude-code-router (MIT, musistudio).
  * Three resilience layers - provider circuit breaker, per-key cooldown honouring Retry-After, per-model lockout:
    OmniRoute (MIT, diegosouzapw).
  * Never: web-cookie access, TLS stealth or shared subscriptions (against the providers' terms).

Files (all outside any project and outside the kit repo), in %USERPROFILE%/.dream-router/ (override: DREAM_ROUTER_HOME):
  keys.env        OPENROUTER_API_KEY=..., GEMINI_API_KEY=..., GROQ_API_KEY=..., NVIDIA_API_KEY=...  (never logged)
  routing.json    {"enabled": true, "mode": "auto" | "plan" | "free", "chain": [...]}
                  auto = the owner's plan, passed through untouched, and free models in the SAME session when the plan is at its limit
  providers.json  optional: extra or changed providers (same shape as PROVIDERS below)
  usage.json      tokens per model, written by the router; read by the console page "Models"

Usage: dream_router.py serve [--port 8787] | status | check (tests every key, spends no tokens) | mode (free or plan, for cod.cmd)
Endpoints: POST /v1/messages, POST /v1/messages/count_tokens, GET /v1/models, GET /router/state, POST /router/settings,
POST /router/keys (add, change or remove one key), POST /router/check (test every key, no tokens spent).
Standard library only."""
import hashlib, json, os, random, re, sys, time, threading, urllib.request, urllib.error, uuid  # noqa: E401
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from datetime import datetime, timedelta
try:  # the model history (v1.124.52): optional, a router without it still starts
    import model_history
except Exception:
    model_history = None

VERSION = "1.124.57"
PORT = int(os.environ.get("DREAM_ROUTER_PORT", "8787"))
HOME = os.environ.get("DREAM_ROUTER_HOME") or os.path.join(os.path.expanduser("~"), ".dream-router")

# Built-in free providers (all speak the OpenAI chat format). "prefer" = model id patterns tried in order against the
# provider's live /models list; the first match is used. "models" = fixed ids used when the list cannot be read.
PROVIDERS = {
    "gemini": {"label": "Google Gemini", "signup": "https://aistudio.google.com/apikey", "base": "https://generativelanguage.googleapis.com/v1beta/openai", "key": "GEMINI_API_KEY",
               "prefer": [r"gemini-[0-9.]+-flash$", r"gemini-.*flash(?!.*(lite|image|tts|live))", r"gemini-.*pro$"],
               "models": ["gemini-flash-latest"], "max_tokens": 8192, "strict_schema": True, "thought_signatures": True},
    "nvidia": {"label": "NVIDIA", "signup": "https://build.nvidia.com/settings/api-keys", "base": "https://integrate.api.nvidia.com/v1", "key": "NVIDIA_API_KEY",
               "prefer": [r"minimax-m[0-9.]+-flash", r"qwen3-coder", r"kimi-k[0-9]", r"deepseek-v[0-9]", r"nemotron.*ultra", r"llama-3\.3-70b"],  # probe 058: minimax answered with tool calls in 1-5 s
               "models": ["qwen/qwen3-coder-480b-a35b-instruct"], "max_tokens": 8192, "timeout": 240},
    "openrouter": {"label": "OpenRouter", "signup": "https://openrouter.ai/keys", "base": "https://openrouter.ai/api/v1", "key": "OPENROUTER_API_KEY",
                   "prefer": [r"qwen3-coder.*:free", r"kimi-k[0-9].*:free", r"deepseek.*:free", r"gpt-oss-120b:free", r"glm-[0-9.]+.*:free", r"ling-.*:free", r"llama-3\.3-70b.*:free", r":free$"],
                   "models": ["qwen/qwen3-coder:free"], "max_tokens": 8192},
    "ollama": {"label": "Ollama Cloud", "signup": "https://ollama.com/settings/keys", "base": "https://ollama.com/v1", "key": "OLLAMA_API_KEY",
               "prefer": [r"qwen3-coder", r"kimi-k2", r"deepseek-v[0-9]", r"glm-[0-9]", r"gpt-oss:120b"],
               "models": ["qwen3-coder:480b"], "max_tokens": 8192},
    "zai": {"label": "Z.ai (GLM Flash)", "signup": "https://z.ai/manage-apikey/apikey-list", "base": "https://api.z.ai/api/paas/v4", "key": "ZAI_API_KEY",
            "prefer": [r"^glm-4\.7-flash$", r"^glm-4\.5-flash$"], "only_prefer": True,  # only the models Z.ai lists as free
            "models": ["glm-4.7-flash"], "max_tokens": 8192},
    "kilo": {"label": "Kilo Gateway (no key needed)", "signup": "https://app.kilo.ai", "base": "https://api.kilo.ai/api/gateway/v1", "key": "KILO_API_KEY",
             "keyless": True, "prefer": [r"qwen3-coder.*:free", r"kimi.*:free", r"deepseek.*:free", r"glm.*:free", r"gpt-oss-120b:free", r":free$"],
             "models": ["qwen/qwen3-coder:free"], "max_tokens": 8192},
    "deepseek": {"label": "DeepSeek (paid, cheap)", "signup": "https://platform.deepseek.com/api_keys", "base": "https://api.deepseek.com", "key": "DEEPSEEK_API_KEY",
                 "prefer": [r"^deepseek-flash$", r"v[0-9.]+-flash", r"^deepseek-chat$"], "models": ["deepseek-flash"], "max_tokens": 8192, "paid": True,
                 "timeout": 240},  # not free: about 0.3 USD per million input tokens; last in the chain, used when the free ones fail
    "llm7": {"label": "LLM7.io", "signup": "https://dash.llm7.io", "base": "https://api.llm7.io/v1", "key": "LLM7_API_KEY",  # free token required since 2026
             "prefer": [r"qwen.*coder", r"deepseek-v", r"gpt-oss-120b", r"kimi", r"llama-3\.3-70b"], "models": ["deepseek-v3.1"], "max_tokens": 8192},
    "cohere": {"label": "Cohere (trial key)", "signup": "https://dashboard.cohere.com/api-keys", "base": "https://api.cohere.ai/compatibility/v1", "key": "COHERE_API_KEY",
               "models_url": "https://api.cohere.ai/v1/models?endpoint=chat&page_size=100",   # 1.124.57: the compatibility API has no /models
               "prefer": [r"^command-a(?!.*(vision|translate|reasoning|embed|rerank))", r"^command-r-plus", r"^command-r"], "only_prefer": True,
               "models": ["command-a-03-2025"], "max_tokens": 8000},   # trial: about 20 requests a minute and 1,000 a month
    "cloudflare": {"label": "Cloudflare Workers AI", "signup": "https://dash.cloudflare.com/profile/api-tokens",
                   "base": "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1", "key": "CLOUDFLARE_API_KEY",   # a token, or ACCOUNT_ID:TOKEN
                   "models_url": "https://api.cloudflare.com/client/v4/accounts/{account}/ai/models/search?task=Text%20Generation&per_page=200",
                   "prefer": [r"qwen.*coder", r"llama-4", r"gpt-oss-120b", r"llama-3\.3-70b", r"deepseek"], "models": ["@cf/openai/gpt-oss-120b"], "max_tokens": 8192},
    "zenmux": {"label": "ZenMux (paid, per token)", "signup": "https://zenmux.ai", "base": "https://zenmux.ai/api/v1", "key": "ZENMUX_API_KEY",
               "prefer": [r"free", r"qwen3-coder", r"glm-[0-9.]+", r"kimi-k[0-9]", r"deepseek-v[0-9]", r"minimax"], "models": ["z-ai/glm-4.6"], "max_tokens": 8192,
               "paid": True, "timeout": 240},   # pay-as-you-go key: after the free ones, like DeepSeek
    "groq": {"label": "Groq", "signup": "https://console.groq.com/keys", "base": "https://api.groq.com/openai/v1", "key": "GROQ_API_KEY",
             "prefer": [r"kimi-k2", r"gpt-oss-120b", r"qwen3", r"llama-3\.3-70b"],
             "models": ["openai/gpt-oss-120b"], "max_tokens": 8192, "max_input_tokens": 7500},
}
UPSTREAM = os.environ.get("DREAM_ROUTER_UPSTREAM", "https://api.anthropic.com")
FREE_TOKEN = "dream-router-local"
MODES = ("auto", "plan", "free")  # auto = my plan, then free models at the limit (same session); plan = plan only; free = free only
DEFAULT_SETTINGS = {"enabled": True, "mode": "auto", "safety_check": "short", "spread": True, "explore": 0.05, "free_accept_edits": False, "trim_history": True,
                    "chain": ["gemini", "zai", "nvidia", "openrouter", "kilo", "llm7", "groq", "ollama", "cohere", "cloudflare", "deepseek", "zenmux"]}
LOCK = threading.Lock()
STATE = {"cooldown": {}, "breaker": {}, "lockout": {}, "models": {}, "bad": {}, "checked": {}, "sigs": {}, "last": None, "started": time.time(), "pinned": {}}  # pinned[package_key] = (provider, model)


# ---------- files ----------
def _path(name):
    return os.path.join(HOME, name)


def _tier_path():
    """Path to data/tiers.json (outside kit repo, in the router's home)."""
    return os.path.join(os.path.dirname(__file__), "data", "tiers.json")


def lookup_tier(name):
    """Return the tier for a skill or agent name, or 'T2' if not found.

    This function reads data/tiers.json (built in pkg-211) and returns the tier
    for a given skill/agent name, with a fallback to 'T2' for unknown names.

    Args:
        name: The name of the skill or agent to look up.

    Returns:
        The tier string (e.g., 'T1', 'T2', 'T3') or 'T2' as fallback.
    """
    # Read tiers.json (the file is outside any project, in the router's home)
    try:
        with open(_tier_path(), encoding="utf-8") as f:
            tiers = json.load(f)
    except FileNotFoundError:
        # pkg-211 hasn't been applied yet: fallback to T2
        return "T2"
    except (OSError, ValueError) as e:
        # File exists but cannot be read (locked, corrupted): fallback to T2
        return "T2"

    # Look up in skills or agents
    for category in ("skills", "agents"):
        if category in tiers:
            if name in tiers[category]:
                return tiers[category][name]

    # Not found: fallback to T2 (pkg-211 not applied or name not in table)
    return "T2"


class StateReadError(Exception):
    """A state file exists but cannot be read right now (locked by Windows, half written): never treat it as empty."""


def _read_json(name, default, keep=False):
    """keep=True for files that are added to (usage, history): if the file exists but cannot be read after a few tries,
    raise instead of returning the empty default, so the caller does not write an empty file over the owner's data
    (1.124.51: usage-72h.json was emptied that way while files were locked)."""
    for i in range(6):
        try:
            with open(_path(name), encoding="utf-8") as f:
                v = json.load(f)
            return v if isinstance(v, type(default)) else default
        except FileNotFoundError:
            return default
        except (OSError, ValueError):
            time.sleep(0.05 * (i + 1))
    if keep:
        raise StateReadError(name)
    return default


def _write_json(name, data):
    os.makedirs(HOME, exist_ok=True)
    tmp = _path(name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    for i in range(6):  # Windows: a reader (the console, an antivirus) can hold the file for a moment
        try:
            os.replace(tmp, _path(name))
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    os.replace(tmp, _path(name))


def settings():
    s = dict(DEFAULT_SETTINGS)
    raw = _read_json("routing.json", {})
    s.update({k: v for k, v in raw.items() if k in DEFAULT_SETTINGS})
    if "mode" not in raw and raw.get("default") == "free":  # settings written by 1.124.0/1.124.1
        s["mode"] = "free"
    if s.get("mode") not in MODES:
        s["mode"] = "auto"
    if raw.get("chain"):  # 1.124.44: names that are not providers (a test that wrote here by mistake) never empty the chain
        known = set(providers())
        chain = [n for n in s["chain"] if n in known]
        s["chain"] = chain or list(DEFAULT_SETTINGS["chain"])
    return s


def keys():
    out = {}
    try:
        with open(_path("keys.env"), encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    for p in providers().values():
        if p["key"] not in out and os.environ.get(p["key"]):
            out[p["key"]] = os.environ[p["key"]]
    return out


def save_key(env_name, value):
    """Add, change or (empty value) remove one key in keys.env, keeping the other lines.
    Only the key names of real providers are written (1.124.44: a test once wrote BUSY_KEY into the owner's file)."""
    if value and env_name not in {p.get("key") for p in providers().values()}:
        return False
    os.makedirs(HOME, exist_ok=True)
    lines, done = [], False
    try:
        with open(_path("keys.env"), encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
    except OSError:
        pass
    out = []
    for line in lines:
        if line.split("=", 1)[0].strip() == env_name:
            if value and not done:
                out.append("%s=%s" % (env_name, value))
            done = True
        else:
            out.append(line)
    if value and not done:
        out.append("%s=%s" % (env_name, value))
    tmp = _path("keys.env.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, _path("keys.env"))


def mask(v):
    return ("…" + v[-4:]) if v else ""


def providers():
    p = {k: dict(v) for k, v in PROVIDERS.items()}
    for k, v in _read_json("providers.json", {}).items():
        if isinstance(v, dict):
            p[k] = dict(p.get(k, {}), **v)
    return p


def cf_account(key):
    """Cloudflare: (account id, token). The key is ACCOUNT_ID:TOKEN, or (1.124.57) the token alone: then the account is the
    first one the token can see (asked once, then kept)."""
    acct, sep, tok = (key or "").partition(":")
    if sep:
        return acct.strip(), tok.strip()
    tok = (key or "").strip()
    cache = STATE.setdefault("cf_acct", {})
    if tok and tok not in cache:
        try:
            r = _http("https://api.cloudflare.com/client/v4/accounts?per_page=5", tok, timeout=20).get("result") or []
            cache[tok] = str(r[0].get("id", "")) if r else ""
        except Exception:
            return "", tok
    return cache.get(tok, ""), tok


def endpoint(prov, key):
    """(base URL, bearer token) for a provider: Cloudflare keys are ACCOUNT_ID:TOKEN; keyless providers work without a key."""
    base = prov["base"].rstrip("/")
    if "{account}" in base:
        acct, tok = cf_account(key)
        return base.replace("{account}", acct), tok
    return base, key or ("anonymous" if prov.get("keyless") else "")


def list_models(prov, key):
    """The provider's model ids: its OpenAI-style /models, or its own list API when it has no /models (Cloudflare)."""
    b, t = endpoint(prov, key)
    if prov.get("models_url"):
        acct = cf_account(key)[0] if "{account}" in prov["models_url"] else ""
        d = _http(prov["models_url"].replace("{account}", acct), t or key, timeout=20)
        return [m.get("name", "") for m in (d.get("result") or d.get("models") or []) if isinstance(m, dict)]
    return [m.get("id", "") for m in _http(b + "/models", t, timeout=20).get("data", [])]


def provider_key(prov, ks):
    """The key to use, or None when the provider cannot be used. Keyless providers always can."""
    k = ks.get(prov.get("key", ""))
    if k:
        return k
    return "" if prov.get("keyless") else None


def redact(text):
    return re.sub(r"(sk-or-|AIza|gsk_|nvapi-|sk-)[A-Za-z0-9_\-]{6,}", r"\1***", str(text))


# ---------- usage ledger ----------
RECENT_HOURS = 72


def recent_models():
    """Models used in the last 72 hours, biggest first (same fields as the monthly list)."""
    cut, rows = int(time.time() // 3600) - RECENT_HOURS, []
    for e in _read_json("usage-72h.json", {}).values():
        hs = [v for x, v in e.get("hours", {}).items() if int(x) > cut]
        if hs:
            rows.append({"provider": e["provider"], "model": e["model"], "input": sum(v[0] for v in hs), "output": sum(v[1] for v in hs),
                         "requests": sum(v[2] for v in hs), "errors": sum(v[3] for v in hs),
                         "last": max(int(x) for x, v in e["hours"].items() if int(x) > cut) * 3600})
    return sorted(rows, key=lambda m: -(m["input"] + m["output"]))


def record_usage(provider, model, tin, tout, ok=True):
    try:
        _record_usage(provider, model, tin, tout, ok)
    except (StateReadError, OSError):
        pass   # better one call not counted than the owner's history overwritten
    STATE["last"] = {"provider": provider, "model": model, "at": time.time(), "ok": ok}


def _record_usage(provider, model, tin, tout, ok=True):
    with LOCK:
        u = _read_json("usage.json", {"models": {}, "month": time.strftime("%Y-%m")}, keep=True)
        if u.get("month") != time.strftime("%Y-%m"):
            u = {"models": {}, "month": time.strftime("%Y-%m"), "previous": u.get("models", {})}
        k = provider + "/" + model
        m = u["models"].setdefault(k, {"provider": provider, "model": model, "input": 0, "output": 0, "requests": 0, "errors": 0})
        m["input"] += int(tin or 0)
        m["output"] += int(tout or 0)
        m["requests"] += 1
        if not ok:
            m["errors"] += 1
        m["last"] = time.time()
        _write_json("usage.json", u)
        # last 72 hours, by hour (the Models page lists only these): its own file, so a new month does not empty it
        r = _read_json("usage-72h.json", {}, keep=True)
        h, cut = str(int(time.time() // 3600)), int(time.time() // 3600) - RECENT_HOURS
        e = r.setdefault(k, {"provider": provider, "model": model, "hours": {}})
        b = e["hours"].setdefault(h, [0, 0, 0, 0])
        b[0] += int(tin or 0); b[1] += int(tout or 0); b[2] += 1; b[3] += 0 if ok else 1
        for kk in list(r):
            r[kk]["hours"] = {x: v for x, v in r[kk]["hours"].items() if int(x) > cut}
            if not r[kk]["hours"]:
                del r[kk]
        _write_json("usage-72h.json", r)
        STATE["last"] = {"provider": provider, "model": model, "at": time.time(), "ok": ok}


# ---------- Anthropic -> OpenAI ----------
def _text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", ""))
        elif isinstance(b, str):
            parts.append(b)
    return "\n".join(parts)


def clean_schema(s, strict=False):
    if isinstance(s, dict):
        drop = {"$schema"} | ({"additionalProperties", "exclusiveMinimum", "exclusiveMaximum", "propertyNames", "const", "$ref", "$defs", "definitions"} if strict else set())
        out = {k: clean_schema(v, strict) for k, v in s.items() if k not in drop}
        if strict and out.get("type") == "string" and out.get("format") not in (None, "enum", "date-time"):
            out.pop("format", None)
        return out
    if isinstance(s, list):
        return [clean_schema(x, strict) for x in s]
    return s


def referenced_tools(req):
    """Names of deferred tools that tool search has loaded in this conversation (tool_reference blocks)."""
    out = set()
    for m in req.get("messages", []):
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result" and isinstance(b.get("content"), list):
                for x in b["content"]:
                    if isinstance(x, dict) and x.get("type") == "tool_reference" and x.get("tool_name"):
                        out.add(x["tool_name"])
    return out


def visible_tools(req):
    """Claude Code marks most MCP tools defer_loading and loads them through tool search: the Anthropic API hides
    them until a tool_reference names them. Free providers do not know this, so the router does it: deferred tools are
    sent only once tool search has loaded them (without that, 800 UEFN tools would be sent, or none would ever appear)."""
    loaded = referenced_tools(req)
    return [t for t in (req.get("tools") or []) if t.get("name") and (not t.get("defer_loading") or t["name"] in loaded)]


ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def compress_text(t, head=14000, tail=6000):
    """Shrink a tool output the same way every time (so a cached prefix stays the same from one turn to the next):
    colour codes and trailing spaces out, runs of blank lines folded, a line repeated many times written once with its
    count, and a huge output (build logs, long listings) kept as its beginning and its end with a note of what was cut."""
    if not t or len(t) < 2000:
        return t
    t = ANSI.sub("", t)
    lines, out, prev, rep_n = t.split("\n"), [], None, 0
    for ln in lines + [None]:
        ln = ln.rstrip() if ln is not None else None
        if ln is not None and ln == prev:
            rep_n += 1
            continue
        if rep_n > 2:
            out.append("[the line above repeated %d more times]" % rep_n)
        elif rep_n:
            out.extend([prev] * rep_n)
        rep_n = 0
        if ln is None:
            break
        if ln == "" and out and out[-1] == "":
            prev = ln
            continue
        out.append(ln)
        prev = ln
    t = "\n".join(out)
    if len(t) > head + tail + 2000:
        cut = len(t) - head - tail
        t = t[:head] + "\n[... %d characters of this output cut by the router to save tokens: rerun the command with a filter to see them ...]\n" % cut + t[-tail:]
    return t


FN_OK = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

# ---------- trimming the history for the free models ----------
TRIM_OVER = 60000          # only when the conversation is bigger than this many characters
TRIM_KEEP = 5              # the last 5 tool results are never cleared: the model needs the recent work
TRIM_DEDUPE = 2000         # a text block of at least this size, repeated, is kept only once (the last copy)
TRIM_MIN = 2000            # a smaller tool result is left alone: clearing it would not save anything
KEEP_TOOLS = {"askuserquestion", "ask_user_question", "exitplanmode"}  # these results are instructions, not output

TRIM_STATE = {"requests": 0, "chars_before": 0, "chars_after": 0}


def _block_text(b):
    """The plain text of a content block (a list of blocks or a string)."""
    if isinstance(b, str):
        return b
    if isinstance(b, list):
        return "\n".join(x.get("text", "") for x in b if isinstance(x, dict) and x.get("type") == "text")
    return ""


def _tool_names(msgs):
    """The name of the tool every tool_result belongs to (the assistant message before it asked for it)."""
    names = {}
    for m in msgs:
        if m.get("role") != "assistant" or not isinstance(m.get("content"), list):
            continue
        for b in m["content"]:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                names[b["id"]] = b.get("name") or "tool"
    return names


def trim_history(req):
    """For the free models only: a long conversation is mostly old tool output the model does not need again.
    Two things are done, and both keep the shape of the conversation:
      * the tool results older than the last TRIM_KEEP become a short note (the tool name and how much was cut);
      * a long text block that appears more than once keeps only its last copy (the earlier ones say so).
    The text the owner wrote is never touched. Returns the request with the trimmed messages."""
    msgs = req.get("messages") or []
    total = sum(len(_block_text(m.get("content"))) for m in msgs)
    if total < TRIM_OVER:
        return req
    names = _tool_names(msgs)
    out = json.loads(json.dumps(req))  # a copy: the caller's request is not changed
    before = after = 0
    # the tool results, oldest first: the last TRIM_KEEP stay as they are
    results = []
    for mi, m in enumerate(out["messages"]):
        if m.get("role") != "user" or not isinstance(m.get("content"), list):
            continue
        for bi, b in enumerate(m["content"]):
            if isinstance(b, dict) and b.get("type") == "tool_result":
                results.append((mi, bi, b))
    for mi, bi, b in (results[:-TRIM_KEEP] if len(results) > TRIM_KEEP else []):
        name = names.get(b.get("tool_use_id"), "tool")
        if name.lower() in KEEP_TOOLS:  # the owner's answers and the plan approval are instructions, not output
            continue
        txt = _block_text(b.get("content"))
        if len(txt) < TRIM_MIN:
            continue
        note = "[old tool result cleared by the router: %s, %d chars]" % (name, len(txt))
        before += len(txt)
        after += len(note)
        out["messages"][mi]["content"][bi]["content"] = note
    # the same long text twice: keep the last copy, the earlier one says so
    seen = {}
    for mi, m in enumerate(out["messages"]):
        cont = m.get("content")
        if not isinstance(cont, list):
            continue
        for bi, b in enumerate(cont):
            if not isinstance(b, dict) or b.get("type") != "text":
                continue
            txt = b.get("text") or ""
            if len(txt) < TRIM_DEDUPE:
                continue
            key = txt.strip()
            if key in seen:
                pi, pbi = seen[key]
                note = "[same text as later in the conversation]"
                before += len(txt)
                after += len(note)
                out["messages"][pi]["content"][pbi]["text"] = note
                del seen[key]
            else:
                seen[key] = (mi, bi)
    TRIM_STATE["requests"] += 1
    TRIM_STATE["chars_before"] += before
    TRIM_STATE["chars_after"] += after
    return out




def wire_names(req):
    """OpenAI-style providers accept function names of at most 64 characters (letters, digits, _ and -); many UEFN MCP tools
    are longer (mcp__unreal-mcp__AIAssistantEditor_AIAssistantToolset_GetProjectContext is 71). A name that does not fit is
    shortened the same way every time (server prefix dropped, then cut with a short hash) and mapped back on the way in.
    Returns (real -> wire, wire -> real); names that already fit are left alone."""
    real = {t.get("name") for t in req.get("tools") or [] if t.get("name")}
    for m in req.get("messages", []):
        if isinstance(m.get("content"), list):
            real.update(b.get("name") for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name"))
    to_w, from_w = {}, {}
    for n in sorted(real, key=lambda x: (not FN_OK.match(x), x)):  # names that fit go first and keep their own name
        w = n
        if not FN_OK.match(n):
            w = re.sub(r"[^A-Za-z0-9_-]", "_", n)
            if w.startswith("mcp__"):
                w = w.split("__", 2)[-1] or w
            if len(w) > 64 or w in from_w or (w in real and w != n):
                w = w[:55] + "_" + hashlib.sha1(n.encode("utf-8")).hexdigest()[:8]
        to_w[n], from_w[w] = w, n
    return to_w, from_w


def to_openai(req, model, prov):
    msgs = []
    to_w, _ = wire_names(req)
    sysm = req.get("system")
    if sysm:
        msgs.append({"role": "system", "content": _text_of(sysm)})
    for m in req.get("messages", []):
        role, content = m.get("role"), m.get("content")
        if isinstance(content, str):
            msgs.append({"role": role, "content": content})
            continue
        if role == "assistant":
            text, calls = [], []
            for b in content or []:
                t = b.get("type")
                if t == "text":
                    text.append(b.get("text", ""))
                elif t == "tool_use":
                    c = {"id": b.get("id"), "type": "function",
                         "function": {"name": to_w.get(b.get("name"), b.get("name")), "arguments": json.dumps(b.get("input", {}))}}
                    if prov.get("thought_signatures"):  # Gemini 3 wants its thought signature back on every function call
                        c["extra_content"] = {"google": {"thought_signature": STATE["sigs"].get(b.get("id")) or "skip_thought_signature_validator"}}
                    calls.append(c)
            a = {"role": "assistant", "content": "\n".join(text) or None}
            if calls:
                a["tool_calls"] = calls
            msgs.append(a)
        else:
            parts, after = [], []
            for b in content or []:
                t = b.get("type")
                if t == "tool_result":
                    c = b.get("content")
                    if isinstance(c, list):  # tool search answers with tool_reference blocks: say which tools are now loaded
                        refs = [x.get("tool_name") for x in c if isinstance(x, dict) and x.get("type") == "tool_reference"]
                        c = _text_of(c) + ("\nTools now available: " + ", ".join(to_w.get(r, r) for r in refs if r) if refs else "")
                    c = _text_of(c) if not isinstance(c, str) else c
                    c = compress_text(c)
                    if b.get("is_error"):
                        c = "ERROR: " + (c or "")
                    msgs.append({"role": "tool", "tool_call_id": b.get("tool_use_id"), "content": c or ""})
                elif t == "text":
                    parts.append({"type": "text", "text": b.get("text", "")})
                elif t == "image" and isinstance(b.get("source"), dict) and b["source"].get("type") == "base64":
                    src = b["source"]
                    parts.append({"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (src.get("media_type"), src.get("data"))}})
                elif t == "document":
                    parts.append({"type": "text", "text": "[document omitted by the free router]"})
            if parts:
                if all(p["type"] == "text" for p in parts):
                    after.append({"role": "user", "content": "\n".join(p["text"] for p in parts)})
                else:
                    after.append({"role": "user", "content": parts})
            msgs.extend(after)
    out = {"model": model, "messages": msgs,
           "max_tokens": min(int(req.get("max_tokens") or 4096), int(prov.get("max_tokens", 8192)))}
    if req.get("temperature") is not None:
        out["temperature"] = req["temperature"]
    if req.get("stop_sequences"):
        out["stop"] = req["stop_sequences"][:4]
    tools = visible_tools(req)
    if tools:
        out["tools"] = [{"type": "function", "function": {"name": to_w.get(t.get("name"), t.get("name")), "description": (t.get("description") or "")[:1024],
                                                          "parameters": clean_schema(t.get("input_schema") or {"type": "object", "properties": {}}, prov.get("strict_schema"))}}
                        for t in tools if t.get("name")]
        tc = req.get("tool_choice") or {}
        if tc.get("type") == "any":
            out["tool_choice"] = "required"
        elif tc.get("type") == "tool":
            out["tool_choice"] = {"type": "function", "function": {"name": to_w.get(tc.get("name"), tc.get("name"))}}
        elif tc.get("type") == "none":
            out["tool_choice"] = "none"
    return out


# ---------- OpenAI -> Anthropic ----------
RESCUE = [re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S),
          re.compile(r"```(?:json)?\s*(\{\s*\"name\".*?\})\s*```", re.S)]


def rescue_tool_calls(text, tool_names):
    """Weak models sometimes write the tool call as text. Turn it into a real call when the name is a known tool."""
    calls, rest = [], text or ""
    for rx in RESCUE:
        for mt in list(rx.finditer(rest)):
            try:
                obj = json.loads(mt.group(1))
            except ValueError:
                continue
            name = obj.get("name") or obj.get("tool")
            args = obj.get("arguments", obj.get("input", obj.get("parameters", {})))
            if name in tool_names:
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                calls.append({"name": name, "input": args if isinstance(args, dict) else {}})
                rest = rest.replace(mt.group(0), "")
    return calls, rest.strip()


def _parse_args(a):
    if isinstance(a, dict):
        return a
    try:
        v = json.loads(a or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        m = re.search(r"\{.*\}", a or "", re.S)  # trailing garbage around the JSON
        try:
            return json.loads(m.group(0)) if m else {}
        except ValueError:
            return {}


def to_anthropic(resp, req, routed):
    ch = (resp.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    text = msg.get("content") or ""
    if isinstance(text, list):
        text = _text_of(text)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    blocks = []
    calls = msg.get("tool_calls") or []
    names = {t.get("name") for t in req.get("tools") or []}
    _, from_w = wire_names(req)
    names |= set(from_w)
    rescued = []
    if not calls and names:
        rescued, text = rescue_tool_calls(text, names)
    # stop sequences (auto mode's safety check ends its answer with one): cut the text there and say which one stopped it
    stop_seq = None
    seqs = [x for x in (req.get("stop_sequences") or []) if x]
    if seqs and not calls:
        hits = [(text.find(x), x) for x in seqs if x in text]
        if hits:
            pos, stop_seq = min(hits)
            text = text[:pos]
        elif ch.get("finish_reason") == "stop" and not names:
            stop_seq = seqs[0]  # OpenAI-style providers stop AT the sequence and drop it
    if text:
        blocks.append({"type": "text", "text": text})
    for c in calls:
        f = c.get("function") or {}
        tid = c.get("id") or "toolu_" + uuid.uuid4().hex[:20]
        sig = ((c.get("extra_content") or {}).get("google") or {}).get("thought_signature")
        if sig:
            STATE["sigs"][tid] = sig
            if len(STATE["sigs"]) > 2000:
                for k in list(STATE["sigs"])[:1000]:
                    STATE["sigs"].pop(k, None)
        blocks.append({"type": "tool_use", "id": tid, "name": from_w.get(f.get("name"), f.get("name")), "input": _parse_args(f.get("arguments"))})
    for c in rescued:
        blocks.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": from_w.get(c["name"], c["name"]), "input": c["input"]})
    fr = ch.get("finish_reason")
    stop = "tool_use" if any(b["type"] == "tool_use" for b in blocks) else ("max_tokens" if fr == "length" else "end_turn")
    if stop_seq and stop == "end_turn":
        stop = "stop_sequence"
    u = resp.get("usage") or {}
    if not blocks:
        blocks.append({"type": "text", "text": ""})
    return {"id": "msg_" + uuid.uuid4().hex[:24], "type": "message", "role": "assistant", "model": routed,
            "content": blocks, "stop_reason": stop, "stop_sequence": stop_seq if stop == "stop_sequence" else None,
            "usage": {"input_tokens": int(u.get("prompt_tokens") or 0), "output_tokens": int(u.get("completion_tokens") or 0)}}


def sse_events(msg):
    """The whole answer as Anthropic stream events (the router asks providers without streaming, then replays)."""
    def ev(name, data):
        return ("event: %s\ndata: %s\n\n" % (name, json.dumps(data))).encode("utf-8")
    head = dict(msg, content=[], stop_reason=None, usage={"input_tokens": msg["usage"]["input_tokens"], "output_tokens": 0})
    yield ev("message_start", {"type": "message_start", "message": head})
    for i, b in enumerate(msg["content"]):
        if b["type"] == "text":
            yield ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}})
            t = b["text"]
            for j in range(0, len(t), 400):
                yield ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": t[j:j + 400]}})
        else:
            yield ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {"type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}})
            yield ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {"type": "input_json_delta", "partial_json": json.dumps(b["input"])}})
        yield ev("content_block_stop", {"type": "content_block_stop", "index": i})
    yield ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": msg["stop_reason"], "stop_sequence": None},
                               "usage": {"output_tokens": msg["usage"]["output_tokens"]}})
    yield ev("message_stop", {"type": "message_stop"})


# ---------- providers, resilience ----------
class ProviderError(Exception):
    def __init__(self, kind, status, detail, retry_after=None):
        Exception.__init__(self, detail)
        self.kind, self.status, self.detail, self.retry_after = kind, status, detail, retry_after


def classify(status, body):
    b = (body or "").lower()
    if status == 402 or "insufficient balance" in b or "insufficient_balance" in b or "top up" in b:
        return "model"  # a paid model, or no credit on the key: set this model aside, try the next free one (LLM7 deepseek-v4-pro, DeepSeek)
    if status == 429 or "rate limit" in b or "quota" in b or "resource_exhausted" in b:
        return "limit"
    if status in (401, 403):
        return "auth"
    if status in (402, 404, 410) or "model not found" in b or "does not exist" in b or "unavailable for free" in b or "usage credits" in b or "subscribe" in b:
        return "model"  # this model is not served to this account for free: set it aside, try the next one
    if status in (400, 413, 422) and ("context" in b or "too long" in b or "too large" in b or "maximum" in b and "token" in b):
        return "too_big"
    if status >= 500 or status == 408:
        return "server"
    return "bad_request"


def _http(url, key, payload=None, timeout=180):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    rq = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "Accept": "application/json",
                                         "User-Agent": "DreamRouter/%s (+https://github.com/mimmo-the-root/UEFN-dream-bot-team)" % VERSION,
                                         "HTTP-Referer": "https://github.com/mimmo-the-root/UEFN-dream-bot-team", "X-Title": "Dream Bot Team"})
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:2000]
        ra = e.headers.get("Retry-After") if e.headers else None
        try:
            ra = float(ra) if ra else None
        except ValueError:
            ra = None
        raise ProviderError(classify(e.code, body), e.code, redact(body)[:300], ra)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ProviderError("server", 0, redact(e)[:300])


def pick_model(name, prov, key):
    """Model for a provider: live /models list matched against the preferences, cached for 6 hours."""
    cached = STATE["models"].get(name)
    if cached and time.time() - cached[1] < 6 * 3600:
        return cached[0]
    model = (prov.get("models") or [None])[0]
    try:
        ids = list_models(prov, key)
        ids = [i[7:] if i.startswith("models/") else i for i in ids]
        STATE.setdefault("counts", {})[name] = len(ids)
        STATE.setdefault("lists", {})[name] = (ids, time.time())
        locked = STATE["lockout"]
        small = re.compile(r"(?<![0-9.])(0\.[0-9]+|[1-9]|1[0-9]|2[0-9])(\.[0-9])?b\b|[-/](mini|nano|tiny|micro)\b", re.I)
        ids = [i for i in ids if not small.search(i)]
        for pat in prov.get("prefer", []):
            hit = [i for i in ids if re.search(pat, i) and locked.get(name + "/" + i, 0) < time.time()]
            if hit:
                def ver(i):
                    return [int(x) for x in re.findall(r"\d+", i.split("/")[-1])[:3]] or [0]
                model = sorted(hit, key=lambda i: ([-v for v in ver(i)], len(i)))[0]
                break
    except ProviderError:
        pass
    if prov.get("only_prefer") and model and not any(re.search(p, model) for p in prov.get("prefer", [])):
        model = (prov.get("models") or [None])[0]
    if model and STATE["lockout"].get(name + "/" + model, 0) > time.time():
        model = None  # the only model left is set aside (e.g. OpenRouter's old free slug): skip this provider, do not call it again and again
    STATE["models"][name] = (model, time.time())
    return model


def pause_seconds(e):
    """How long to leave a provider alone after a failure. A provider that hangs until the read timeout (120-240 s each time)
    or whose daily quota is gone would otherwise be tried first on every request, and a free answer from the next one in
    the chain only arrives after minutes of waiting: pause it for a few minutes instead of a few seconds."""
    if e.kind == "limit":
        return e.retry_after or (600 if "quota" in (e.detail or "").lower() else 60)
    if e.kind == "server" and e.status == 0:
        return 600
    return 0


def save_pauses():
    """Remember the pauses over a restart, so a restart does not make the router wait again for a provider known to hang."""
    now = time.time()
    p = {n: max(STATE["cooldown"].get(n, 0), STATE["breaker"].get(n, {}).get("open_until", 0)) for n in set(STATE["cooldown"]) | set(STATE["breaker"])}
    _write_json("pauses.json", {n: u for n, u in p.items() if u > now})


def available(name):
    now = time.time()
    br = STATE["breaker"].get(name, {})
    return STATE["cooldown"].get(name, 0) <= now and br.get("open_until", 0) <= now


PATIENCE = 180   # 1.124.57: when every free model is busy the router keeps the request and tries again every 3 minutes


def reopen():
    """Every provider and model that is only resting (quota, rate limit, a slow minute) gets one more try now.
    Models set aside as broken (lockout) stay aside."""
    STATE["cooldown"].clear()
    for br in STATE["breaker"].values():
        br["open_until"], br["fails"] = 0, 0
    STATE["mcool"] = {}
    save_pauses()


def route_patiently(req, sleep=time.sleep, clock=time.time, hold=None):
    """route(), but when every free provider failed or is resting it does not give up: it holds the request and, after
    PATIENCE seconds (sooner when a provider's pause ends), tries every provider again. It answers the error only after
    `hold` seconds, with retry-after, so Claude Code asks again and the cycle goes on until a model answers: the session
    never stops to wait for the owner because the free quotas are used up for a while."""
    hold = PATIENCE if hold is None else hold
    try:
        return route(req)
    except ProviderError as e:
        if e.kind != "all_failed" or pinned(req) or not settings().get("patience", True) or hold <= 0:
            raise
        first = e
    end = clock() + hold
    STATE["waiting"] = STATE.get("waiting", 0) + 1
    try:
        while clock() < end:
            sleep(min(15.0, max(0.0, end - clock())))
            ks, pv = keys(), providers()
            if any(available(n) for n in pv if provider_key(pv[n], ks) is not None) and clock() < end - 5:
                try:
                    return route(req)
                except ProviderError as e:
                    first = e
        reopen()
        return route(req)
    except ProviderError as e:
        e.detail = "Every free model was busy for %d s; tried again and still busy. Claude Code will ask again: nothing to do. (%s)" % (hold, (e.detail or first.detail)[:300])
        raise
    finally:
        STATE["waiting"] = max(0, STATE.get("waiting", 1) - 1)


def log_error(provider, model, e, req):
    """One line per provider failure in errors.log (redacted, never the request text): what failed and how big the request was."""
    try:
        size = len(json.dumps(req.get("messages", []))) + len(json.dumps(req.get("system", ""))) + len(json.dumps(req.get("tools", [])))
        line = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "provider": provider, "model": model, "kind": e.kind, "status": e.status,
                "detail": redact(e.detail)[:300], "request_chars": size, "tools": len(req.get("tools") or [])}
        with LOCK:
            os.makedirs(HOME, exist_ok=True)
            p = _path("errors.log")
            lines = []
            try:
                with open(p, encoding="utf-8") as f:
                    lines = f.read().splitlines()[-199:]
            except OSError:
                pass
            lines.append(json.dumps(line))
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
    except Exception:
        pass


def recent_errors(n=120, hours=6):
    """Newest first, only the last few hours (the Models page shows them in pages)."""
    cut = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - hours * 3600))
    out = []
    try:
        with open(_path("errors.log"), encoding="utf-8") as f:
            for x in f.read().splitlines()[::-1]:
                try:
                    e = json.loads(x)
                except ValueError:
                    continue
                if e.get("at", "") < cut or len(out) >= n:
                    break
                out.append(e)
    except OSError:
        pass
    return out


PIN = "dream:"
KEY_OK = re.compile(r"^[A-Za-z0-9_\-.:+/=]{8,1000}$")  # base64 tokens (LLM7: 150+ characters with + / =) are fine; spaces and quotes are not


def _session_key(headers):
    """Extract a session/package key from the HTTP headers: X-Claude-Session header, or client IP as fallback."""
    return headers.get("X-Claude-Session") or headers.get("x-claude-session", "default")


def pinned(req):
    """`claude --model dream:<provider>/<model>` (used by pieces.py to try a piece on another model): (provider, model) or None."""
    m = str(req.get("model") or "")
    if m.startswith(PIN) and "/" in m:
        prov, model = m[len(PIN):].split("/", 1)
        return prov, model
    return None


def _get_package_key(req, headers):
    """Extract package/session key from request headers or metadata.
    Only returns a key if explicitly provided (X-Package-ID, X-Session-ID, X-Claude-Session headers,
    or metadata.package_id/session_id/task_id).
    Returns None if no explicit key is present (pinning is opt-in, not automatic)."""
    pkg = headers.get("X-Package-ID") or headers.get("X-Session-ID") or headers.get("X-Claude-Session") or headers.get("x-claude-session")
    if pkg:
        return pkg.strip()
    meta = req.get("metadata") if isinstance(req.get("metadata"), dict) else None
    if meta:
        pkg = meta.get("package_id") or meta.get("session_id") or meta.get("task_id")
        if pkg:
            return str(pkg)
    return None


def _get_pinned_model(package_key):
    """Get pinned (provider, model) for package if exists. Returns None otherwise."""
    with LOCK:
        pin = STATE.get("pinned", {}).get(package_key)
        if pin:
            return pin["provider"], pin["model"]
    return None


def _pin_model_for_package(package_key, provider, model):
    """Pin a model to a package key."""
    with LOCK:
        STATE.setdefault("pinned", {})[package_key] = {"provider": provider, "model": model}


def _clear_package_pin(package_key):
    """Clear pin for a package (when package ends)."""
    with LOCK:
        STATE.get("pinned", {}).pop(package_key, None)


PER_MODEL_LIMITS = {"openrouter", "kilo", "nvidia", "llm7", "ollama", "groq", "zenmux", "cloudflare"}  # gateways where a 429 belongs to ONE model, not the account
MODEL_TRIES = 20  # models of the same provider tried in one request before moving to the next provider (a 429 answers in a second)


def perf(k):
    return STATE.setdefault("perf", {}).get(k) or {}


def note_perf(k, ok, ms=None):
    """What each model did: answers, failures and its usual answer time (moving average). Kept in perf.json."""
    p = STATE.setdefault("perf", {}).setdefault(k, {"ok": 0, "fail": 0, "ms": None})
    if ok:
        p["ok"] += 1
        p["ms"] = ms if p.get("ms") is None else round(0.7 * p["ms"] + 0.3 * ms)
    else:
        p["fail"] += 1
    p["at"] = int(time.time())
    if sum(v.get("ok", 0) + v.get("fail", 0) for v in STATE["perf"].values()) % 10 == 0:
        _write_json("perf.json", STATE["perf"])


def by_speed(name, models):
    """Order: models that answered before, fastest first; then the ones never tried (in the order of preference);
    last the ones that mostly failed. So the router learns which free models are quick and good."""
    def key(i):
        m = models[i]
        p = perf(name + "/" + m)
        ok, fail = p.get("ok", 0), p.get("fail", 0)
        if ok and fail <= ok:
            return (0, p.get("ms") or 10 ** 9, i)
        if not ok and not fail:
            return (1, 0, i)
        if time.time() - p.get("at", 0) > 24 * 3600:   # old bad results: one new chance, the free quotas change
            return (1, 1, i)
        return (2, -ok, i)
    return [models[i] for i in sorted(range(len(models)), key=key)]


def provider_models(name, prov, key, limit=MODEL_TRIES, explore=False):
    """The free models of one provider worth a try, best first: its live list (cached 6 h) matched against the preferences,
    without small models, models set aside, or models resting after their own rate limit.
    If explore=True, return ONLY models outside the prefer patterns (for 1-in-20 exploration)."""
    cached = STATE.get("lists", {}).get(name)
    ids = cached[0] if cached and time.time() - cached[1] < 6 * 3600 else None
    if ids is None:
        try:
            ids = [i[7:] if i.startswith("models/") else i for i in list_models(prov, key)]
            STATE.setdefault("lists", {})[name] = (ids, time.time())
            STATE.setdefault("counts", {})[name] = len(ids)
        except ProviderError:
            ids = list(prov.get("models") or [])
    small = re.compile(r"(?<![0-9.])(0\.[0-9]+|[1-9]|1[0-9]|2[0-9])(\.[0-9])?b\b|[-/](mini|nano|tiny|micro)\b", re.I)
    now, got = time.time(), []
    prefer = prov.get("prefer", [])
    if explore:
        # Exploration: ONLY return models NOT matching prefer patterns (so we discover new ones)
        for i in ids:
            k = name + "/" + i
            if not any(re.search(p, i) for p in prefer) and not small.search(i) and STATE["lockout"].get(k, 0) < now and STATE.get("mcool", {}).get(k, 0) < now:
                got.append(i)
    else:
        # Normal: models matching prefer patterns (the proven ones)
        for pat in prefer:
            for i in ids:
                k = name + "/" + i
                if i not in got and re.search(pat, i) and not small.search(i) and STATE["lockout"].get(k, 0) < now and STATE.get("mcool", {}).get(k, 0) < now:
                    got.append(i)
        if prov.get("only_prefer"):
            got = [i for i in got if any(re.search(p, i) for p in prefer)]
    return by_speed(name, got)[:limit]


def candidates(n=20):
    """Free models worth a try, best first, across providers (ready, not paused, not set aside): "provider/model"."""
    s, provs, ks, out = settings(), providers(), keys(), []
    per = {}
    for name in s.get("chain") or DEFAULT_SETTINGS["chain"]:
        prov = provs.get(name)
        key = provider_key(prov, ks) if prov else None
        if not prov or key is None or not available(name) or name in STATE["bad"]:
            continue
        per[name] = provider_models(name, prov, key, 4)
    while len(out) < n and any(per.values()):  # one model per provider in turn: different providers fail for different reasons
        for name in list(per):
            if per[name]:
                out.append("%s/%s" % (name, per[name].pop(0)))
    return out[:n]


TRANSCRIPT_RX = re.compile(r"<transcript>(.*?)</transcript>", re.S)
SAFETY_KEEP_TAIL = 16000   # characters of the most recent part of the session kept for the safety check
SAFETY_USER_LINE = 1200    # each owner message kept (what the owner asked is what the check needs most)


def is_safety_check(req):
    """Claude Code's auto-mode safety check (free-claude-code, MIT, detection.py): no tools and a <transcript> in the messages."""
    if req.get("tools"):
        return False
    for m in req.get("messages", []):
        if m.get("role") != "system" and "<transcript>" in _text_of(m.get("content")):
            return True
    return "<transcript>" in _text_of(req.get("system") or "") and "security monitor" in _text_of(req.get("system") or "")


def _shrink_transcript(t):
    """Keep every owner message (shortened) and the last part of the session; drop the middle (old tool outputs)."""
    if len(t) <= SAFETY_KEEP_TAIL + 4000:
        return t
    head, tail = t[:-SAFETY_KEEP_TAIL], t[-SAFETY_KEEP_TAIL:]
    asks = [ln[:SAFETY_USER_LINE] for ln in re.split(r"\n(?=\S)", head) if ln.startswith(("User:", "user:", "Human:"))]
    cut = tail.find("\n")
    if 0 <= cut < 400:   # start the kept part at a line boundary
        tail = tail[cut + 1:]
    note = "[... %d characters of older tool calls and outputs left out by the router; the owner's messages above show the intent ...]" % len(head)
    return "\n" + "\n".join(asks[-30:]) + "\n" + note + "\n" + tail


def _sample_safety_check(req):
    """Keep the SHAPE of the last safety check on this PC (~/.dream-router/last-safety-check.json): sizes, tags and the first
    and last 1500 characters of each part. It shows where the session text really is, so the shrinking can target it."""
    try:
        def part(t):
            return {"chars": len(t), "tags": sorted(set(re.findall(r"<([a-z_]{3,30})>", t)))[:40], "start": t[:1500], "end": t[-1500:] if len(t) > 3000 else ""}
        sysm = req.get("system")
        sys_parts = [sysm] if isinstance(sysm, str) else [b.get("text", "") for b in (sysm or []) if isinstance(b, dict)]
        msg_parts = [_text_of(m.get("content")) for m in req.get("messages", [])]
        _write_json("last-safety-check.json", {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "system": [part(t) for t in sys_parts],
                                               "messages": [part(t) for t in msg_parts], "max_tokens": req.get("max_tokens")})
    except Exception:
        pass


def shrink_safety_check(req):
    """The safety check of auto mode re-sends the whole session (~45k tokens) for every action. Free models get the owner's
    messages and the most recent part only: same question, a fraction of the tokens. Plan requests are never touched."""
    out = dict(req)
    msgs, before, after = [], 0, 0
    _sample_safety_check(req)
    sysm = req.get("system")   # the session can also travel in the instructions (owner's log: 35k of 42k there)
    if isinstance(sysm, str) and "<transcript>" in sysm:
        before += len(sysm)
        sysm = TRANSCRIPT_RX.sub(lambda x: "<transcript>" + _shrink_transcript(x.group(1)) + "</transcript>", sysm)
        after += len(sysm)
        out["system"] = sysm
    elif isinstance(sysm, list):
        ns = []
        for b in sysm:
            if isinstance(b, dict) and b.get("type") == "text" and "<transcript>" in b.get("text", ""):
                before += len(b["text"])
                b = dict(b, text=TRANSCRIPT_RX.sub(lambda x: "<transcript>" + _shrink_transcript(x.group(1)) + "</transcript>", b["text"]))
                after += len(b["text"])
            ns.append(b)
        out["system"] = ns
    for m in req.get("messages", []):
        c = m.get("content")
        if isinstance(c, str) and "<transcript>" in c:
            before += len(c)
            c = TRANSCRIPT_RX.sub(lambda x: "<transcript>" + _shrink_transcript(x.group(1)) + "</transcript>", c)
            after += len(c)
        elif isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "text" and "<transcript>" in b.get("text", "") for b in c):
            # 1.124.46: Claude Code sends the transcript split over several text blocks (the opening and closing tags are in
            # different blocks), so shrinking block by block saved nothing (owner's page: 5.0M -> 5.0M). Join the text blocks
            # of this message, shrink once, send one text block (other blocks, e.g. images, are kept after it).
            texts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            joined = "\n".join(texts)
            before += len(joined)
            joined = TRANSCRIPT_RX.sub(lambda x: "<transcript>" + _shrink_transcript(x.group(1)) + "</transcript>", joined)
            after += len(joined)
            c = [{"type": "text", "text": joined}] + [b for b in c if not (isinstance(b, dict) and b.get("type") == "text")]
        msgs.append(dict(m, content=c))
    out["messages"] = msgs
    st = STATE.setdefault("safety", {"checks": 0, "chars_before": 0, "chars_after": 0})
    st["checks"] += 1
    st["chars_before"] += before
    st["chars_after"] += after
    return out


def note_daily_history():
    """History of the free models: one line per model per day, written at the first request after midnight."""
    today = time.strftime("%Y-%m-%d")
    if STATE.get("_last_daily_write", "") == today:
        return
    try:
        model_history.write_daily_history(today)
    except Exception:
        pass
    STATE["_last_daily_write"] = today
    try:
        _write_json("daily_write.json", {"date": today})
    except OSError:
        pass


def vault_path():
    """The second brain vault path (rule 11 of ~/.claude/CLAUDE.md), or None when it is not set."""
    claude_md = os.path.join(os.path.expanduser("~"), ".claude", "CLAUDE.md")
    try:
        with open(claude_md, encoding="utf-8") as f:
            for line in f:
                if "Second brain path" in line and ":" in line:
                    p = line.split(":", 1)[1].strip().strip("`")
                    if p and "SecondBrainOssidian" not in p:
                        return p if os.path.isdir(p) else None
                    return None
    except OSError:
        pass
    return None


def note_weekly_vault():
    """Weekly page in the second brain: Monday, first router start of the week."""
    try:
        now = datetime.now()
        if now.weekday() != 0:  # Monday only
            return
        week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        mark = _read_json("weekly_vault.json", {})
        if mark.get("week") == week:
            return
        vp = vault_path()
        if vp:
            model_history.write_weekly_vault_page(vp)
        _write_json("weekly_vault.json", {"week": week})
    except Exception:
        pass


def route(req):
    s = settings()
    if not s.get("enabled"):
        raise ProviderError("off", 503, "Free routing is switched off on the Models page of the console.")
    note_daily_history()
    note_weekly_vault()
    provs, ks, errors = providers(), keys(), []
    if s.get("safety_check", "short") == "short" and is_safety_check(req):
        req = shrink_safety_check(req)
    if s.get("trim_history", True):  # once per request, before any provider (the plan path never reaches here)
        req = trim_history(req)
    chain = list(s.get("chain") or DEFAULT_SETTINGS["chain"])
    pin = pinned(req)
    if pin:
        chain = [pin[0]]

    # Package/session pinning (T-023): with spread on, pin model per package/session
    package_key = None
    pinned_model = None
    if s.get("spread", True) and not pin:
        package_key = _get_package_key(req, {})
        if package_key:
            pinned_model = _get_pinned_model(package_key)
            if pinned_model:
                chain = [pinned_model[0]]
                req["_pinned_model"] = pinned_model
    if not pinned_model:
        last = STATE.get("last_ok")
        if s.get("spread", True) and not pin:
            # Spread the load (1.124.37): the providers that answered in the last 30 minutes take turns, so no single free
            # quota is used up first; the others follow in their usual order as fallbacks.
            # 1.124.45: every provider that has a key and is not resting takes its turn (before: only the ones that had answered
            # in the last 30 minutes, so one fast provider took everything and the others never got a chance to answer)
            ks0, pv0 = keys(), providers()
            good = [n for n in chain if n in pv0 and provider_key(pv0[n], ks0) is not None and available(n) and n not in STATE["bad"]]
            if len(good) > 1:
                STATE["turn"] = (STATE.get("turn", -1) + 1) % len(good)
                first = good[STATE["turn"]:] + good[:STATE["turn"]]
                chain = first + [n for n in chain if n not in first]
            elif last in chain and available(last):
                chain.remove(last)
                chain.insert(0, last)
        elif last in chain and available(last):  # the provider that answered last goes first: no minutes lost on the ones that keep failing
            chain.remove(last)
            chain.insert(0, last)
    for name in chain:
        prov = provs.get(name)
        key = provider_key(prov, ks) if prov else None
        if not prov or key is None:
            continue
        if not available(name):
            errors.append("%s: paused" % name)
            continue
        need = (len(json.dumps(req.get("messages", []))) + len(json.dumps(req.get("system", ""))) + len(json.dumps(req.get("tools", [])))) // 4
        if prov.get("max_input_tokens") and need > int(prov["max_input_tokens"]):
            errors.append("%s: request of about %d tokens is over its free limit of %s" % (name, need, prov["max_input_tokens"]))
            continue
        # Package/session pinning (T-023): use pinned model if available for this package
        if package_key and pinned_model and name == pinned_model[0]:
            # We're using the pinned provider, use the pinned model
            models = [pinned_model[1]]
        elif pin:
            models = [pin[1]]
        else:
            # several free models of this provider in turn (1.124.41): on gateways a rate limit belongs to one model, and the
            # next model of the same provider usually answers at once. With "spread" the starting model rotates too.
            models = provider_models(name, prov, key) or [m for m in [pick_model(name, prov, key)] if m]
            proven = [m for m in models if perf(name + "/" + m).get("ok")][:3]
            if s.get("spread", True) and len(proven) > 1:  # the quick ones take turns; the rest stay behind as fallbacks
                mt = STATE.setdefault("mturn", {})
                mt[name] = (mt.get(name, -1) + 1) % len(proven)
                first = proven[mt[name]:] + proven[:mt[name]]
                models = first + [m for m in models if m not in first]
            # Exploration (1.124.43): about 1 request in 20 starts with a model never tried, so the ranking keeps improving
            # by itself. Never for the auto-mode safety check (it must be quick) and never for pinned requests.
            fresh = [m for m in models if not perf(name + "/" + m)]
            if fresh and not is_safety_check(req) and random.random() < float(s.get("explore", 0.05) or 0):
                models = [fresh[0]] + [m for m in models if m != fresh[0]]
                STATE["explored"] = STATE.get("explored", 0) + 1
            else:
                # Also try to explore: get 1 model from outside prefer patterns (if explore=True)
                extra = provider_models(name, prov, key, limit=1, explore=True)
                if extra and not is_safety_check(req) and random.random() < float(s.get("explore", 0.05) or 0):
                    models = [extra[0]] + [m for m in models if m != extra[0]]
                    STATE["explored"] = STATE.get("explored", 0) + 1
            models = models[:MODEL_TRIES if name in PER_MODEL_LIMITS else 1]
        if not models:
            errors.append("%s: no free model left for now" % name)
            continue
        limited = 0
        for model in models:
          try:
              b, t = endpoint(prov, key)
              t0 = time.time()
              ak = name + "/" + model
              with LOCK:
                  act = STATE.setdefault("active", {})
                  act[ak] = act.get(ak, 0) + 1
              try:
                  resp = _http(b + "/chat/completions", t, to_openai(req, model, prov), timeout=int(prov.get("timeout", 120)))
              finally:
                  with LOCK:
                      STATE["active"][ak] -= 1
                      if STATE["active"][ak] <= 0:
                          STATE["active"].pop(ak, None)
              if resp.get("error"):
                  e = resp["error"]
                  raise ProviderError(classify(int(e.get("code") or 400) if str(e.get("code", "")).isdigit() else 400, json.dumps(e)), 400, redact(json.dumps(e))[:300])
              STATE["breaker"][name] = {"fails": 0}
              STATE["bad"].pop(name, None)
              STATE["last_ok"] = name
              STATE.setdefault("ok_at", {})[name] = time.time()
              STATE.setdefault("timeouts", {}).pop(name + "/" + model, None)
              note_perf(name + "/" + model, True, int((time.time() - t0) * 1000))
              out = to_anthropic(resp, req, "%s/%s" % (name, model))
              record_usage(name, model, out["usage"]["input_tokens"], out["usage"]["output_tokens"])
              return out, "%s/%s" % (name, model), errors
          except ProviderError as e:
              errors.append("%s/%s: %s %s" % (name, model, e.kind, e.detail[:120]))
              log_error(name, model, e, req)
              record_usage(name, model, 0, 0, ok=False)
              note_perf(name + "/" + model, False)
              if e.kind == "limit" and name in PER_MODEL_LIMITS and not pin:
                  STATE.setdefault("mcool", {})[name + "/" + model] = time.time() + max(60, pause_seconds(e))
              elif e.kind == "limit":
                  STATE["cooldown"][name] = time.time() + pause_seconds(e)
              elif e.kind == "model":
                  STATE["lockout"][name + "/" + model] = time.time() + 6 * 3600
                  _write_json("lockout.json", {k: v for k, v in STATE["lockout"].items() if v > time.time()})  # survives a restart
                  STATE["models"].pop(name, None)
              elif e.kind == "auth":
                  STATE["cooldown"][name] = time.time() + 3600
                  STATE["bad"][name] = "the provider refused the key (HTTP %s)" % e.status
              elif e.kind == "server":
                  if STATE.get("last_ok") == name:
                      STATE["last_ok"] = None
                  if e.status == 0:  # a model that hangs twice in a row is set aside like a model that is not free: the next pick is another model
                      tk = name + "/" + model
                      STATE.setdefault("timeouts", {})[tk] = STATE["timeouts"].get(tk, 0) + 1
                      if STATE["timeouts"][tk] >= 2:
                          STATE["lockout"][tk] = time.time() + 30 * 60  # 30 minutes: a slow hour does not cost the model for the day
                          _write_json("lockout.json", {k: v for k, v in STATE["lockout"].items() if v > time.time()})
                          STATE["models"].pop(name, None)
                          STATE["timeouts"].pop(tk, None)
                  br = STATE["breaker"].setdefault(name, {"fails": 0})
                  br["fails"] = br.get("fails", 0) + 1
                  if pause_seconds(e):
                      br["open_until"] = time.time() + pause_seconds(e)
                      br["fails"] = 0
                  elif br["fails"] >= 3:
                      br["open_until"] = time.time() + 60
                      br["fails"] = 0
              save_pauses()
              if e.kind == "limit" and name in PER_MODEL_LIMITS and not pin:
                  limited += 1
                  continue      # the next model of the same provider
              if e.kind == "model" and not pin:
                  continue      # set aside: the next model of the same provider
              break             # server trouble, wrong key: the next provider
        else:
            if limited:
                STATE["cooldown"][name] = time.time() + 60   # every model tried was resting: leave the provider a minute
            continue
        continue
    if not errors:
        raise ProviderError("no_keys", 503, "No free provider key found. Put the keys in %s" % _path("keys.env"))
    raise ProviderError("all_failed", 529, "All free providers failed or are paused: " + " | ".join(errors))


USAGE_RX = re.compile(rb'"(input_tokens|output_tokens|cache_read_input_tokens|cache_creation_input_tokens)"\s*:\s*(\d+)')
SKIP_IN = {"host", "content-length", "accept-encoding", "connection", "keep-alive", "transfer-encoding"}
SKIP_OUT = {"content-length", "transfer-encoding", "connection", "content-encoding", "keep-alive"}


def router_env(mode, enabled=True):
    """What Claude Code needs in each mode. Ideas from free-claude-code (AGPL, ideas only) and freellmapi (MIT):
    CLAUDE_CODE_AUTO_MODE_SERVER=0 makes auto mode send its safety check as an ordinary request (through the router),
    instead of asking Anthropic's server check that only Claude can answer; the watchdogs are off and the timeout long
    because the router waits for a whole free answer and may try several providers before the first byte."""
    if not enabled or mode == "plan":
        return {}
    env = {"ANTHROPIC_BASE_URL": "http://127.0.0.1:%d" % PORT, "CLAUDE_CODE_AUTO_MODE_SERVER": "0", "ENABLE_TOOL_SEARCH": "true",
           "CLAUDE_ENABLE_STREAM_WATCHDOG": "0", "CLAUDE_ENABLE_BYTE_WATCHDOG": "0", "API_TIMEOUT_MS": "900000"}
    if mode == "free":
        env.update({"ANTHROPIC_AUTH_TOKEN": FREE_TOKEN, "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"})
    return env


def session_settings(mode):
    """For cod.cmd --auto/--plan/--free: a settings file passed with `claude --settings`, which outranks the "env" the router
    wrote in the user's settings.json. So a forced mode wins for this one session, without changing the Models page.
    Plan blanks every value the router may have set (an empty value means "not set" for Claude Code), except
    ANTHROPIC_AUTH_TOKEN which is OMITTED entirely (an empty string is treated as "not set" and falls back to
    settings.json, which would leak the router's auth token into the plan request — issue #1 of test 060)."""
    want = router_env(mode if mode in MODES else "auto", True)
    env = {k: "" for k in router_env("free", True)}
    env.update(want)
    if not want:  # plan only: talk to Claude directly, whatever the router wrote in settings.json
        env["ANTHROPIC_BASE_URL"] = UPSTREAM
        env.pop("ANTHROPIC_AUTH_TOKEN", None)  # omit, not blank: empty string falls back to settings.json
    path = _path("cod-%s.json" % mode)
    out = {"env": env}
    if mode == "free" and settings().get("free_accept_edits", False):
        out["permissions"] = {"defaultMode": "acceptEdits"}
    _write_json(os.path.basename(path), out)
    return path


def apply_mode_to_claude(mode, enabled=True, settings_path=None):
    """Make the chosen mode work however Cod is started: write it in the "env" of the user's Claude Code settings
    (%USERPROFILE%/.claude/settings.json), which every new session applies. The router remembers exactly what it wrote
    (claude-env.json) and only ever changes or removes those values: anything the owner set himself is kept.
    A copy of the settings is kept as settings.json.dream-router.bak. Returns what it did."""
    sp = settings_path or os.environ.get("DREAM_ROUTER_CLAUDE_SETTINGS") or os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    try:
        with open(sp, encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except (OSError, ValueError):
        return "settings.json unreadable: not changed"
    if not isinstance(data, dict):
        return "settings.json unexpected: not changed"
    env = dict(data.get("env")) if isinstance(data.get("env"), dict) else {}
    mine = _read_json("claude-env.json", {}).get(sp, {})
    legacy = {"ANTHROPIC_BASE_URL": "http://127.0.0.1:%d" % PORT, "ANTHROPIC_AUTH_TOKEN": FREE_TOKEN, "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
    new_env = {k: v for k, v in env.items() if not (mine.get(k, legacy.get(k)) == v)}
    want = router_env(mode, enabled)
    new_env.update(want)
    track = _read_json("claude-env.json", {})
    track[sp] = want
    # Free only + "accept edits" switch: Cod starts in accept-edits permission mode, so auto mode's safety check (a second
    # request with the whole session for every action) never runs. Only the value the router wrote is ever removed.
    perms = dict(data.get("permissions")) if isinstance(data.get("permissions"), dict) else {}
    pk = sp + "#defaultMode"
    mine_perm = track.get(pk)
    want_perm = "acceptEdits" if (enabled and mode == "free" and settings().get("free_accept_edits", False)) else None
    new_perms = dict(perms)
    if want_perm and perms.get("defaultMode") != want_perm:
        if "defaultMode" in perms and perms["defaultMode"] != mine_perm:
            track[pk + "#before"] = perms["defaultMode"]
        new_perms["defaultMode"] = want_perm
        track[pk] = want_perm
    elif not want_perm and mine_perm and perms.get("defaultMode") == mine_perm:
        before = track.pop(pk + "#before", None)
        if before:
            new_perms["defaultMode"] = before
        else:
            new_perms.pop("defaultMode", None)
        track.pop(pk, None)
    _write_json("claude-env.json", track)
    perm_changed = new_perms != perms
    if perm_changed:
        if new_perms:
            data["permissions"] = new_perms
        else:
            data.pop("permissions", None)
    if new_env == env and not perm_changed:
        return "unchanged"
    try:
        if os.path.isfile(sp):
            with open(sp, encoding="utf-8-sig") as f, open(sp + ".dream-router.bak", "w", encoding="utf-8") as g:
                g.write(f.read())
        if new_env:
            data["env"] = new_env
        elif new_env != env:
            data.pop("env", None)
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        tmp = sp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, sp)
        return "written: " + (mode if want else "removed")
    except OSError as e:
        return "not written: %s" % e


def plan_credentials(headers):
    """True when Claude Code sent its own login (the owner's plan), not the free-mode placeholder token."""
    auth = headers.get("Authorization") or ""
    return bool(headers.get("x-api-key")) or (auth.startswith("Bearer ") and auth[7:].strip() not in ("", FREE_TOKEN))


def plan_available():
    return STATE.get("plan_until", 0) <= time.time()


def _plan_pause(seconds, why):
    STATE["plan_until"] = time.time() + max(60, seconds)
    STATE["plan_why"] = why


def forward_plan(handler, raw, model):
    """Pass the request, untouched, to Claude with the session's own login. Never reads or stores the login.
    Returns "done" (answer sent), "limit" (plan at its limit: use free models) or "unavailable" (login not accepted / no network)."""
    hdrs = {k: v for k, v in handler.headers.items() if k.lower() not in SKIP_IN}
    rq = urllib.request.Request(UPSTREAM.rstrip("/") + handler.path, data=raw, method=handler.command, headers=hdrs)
    try:
        r = urllib.request.urlopen(rq, timeout=600)
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.code == 429:
            ra = e.headers.get("retry-after") or ""
            reset = e.headers.get("anthropic-ratelimit-unified-reset") or ""
            wait = 900
            try:
                wait = float(ra) if ra else (float(reset) - time.time() if reset else 900)
            except ValueError:
                pass
            _plan_pause(wait, "limit")
            return "limit"
        if e.code in (401, 403):
            _plan_pause(600, "login not accepted through the router (%d)" % e.code)
            return "unavailable"
        handler.send_response(e.code)  # any other plan error goes back to Claude Code as it is (it retries by itself)
        for k, v in e.headers.items():
            if k.lower() not in SKIP_OUT:
                handler.send_header(k, v)
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        return "done"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        _plan_pause(120, "Claude not reachable: %s" % redact(e)[:80])
        return "unavailable"
    handler.send_response(r.status)
    for k, v in r.headers.items():
        if k.lower() not in SKIP_OUT:
            handler.send_header(k, v)
    handler.send_header("X-Routed-Via", "claude-plan/" + model)
    handler.send_header("Connection", "close")
    handler.end_headers()
    use, tail = {}, b""
    try:
        while True:
            chunk = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
            if not chunk:
                break
            handler.wfile.write(chunk)
            handler.wfile.flush()
            for k, v in USAGE_RX.findall(tail + chunk):
                use[k] = max(use.get(k, 0), int(v))
            tail = chunk[-200:]
    finally:
        r.close()
    if handler.path.split("?")[0] == "/v1/messages":
        record_usage("claude-plan", model or "claude", use.get(b"input_tokens", 0) + use.get(b"cache_read_input_tokens", 0) + use.get(b"cache_creation_input_tokens", 0), use.get(b"output_tokens", 0))
    return "done"


def note_size(req):
    """Measure before changing: where the tokens of each Claude Code request go (instructions, tools, conversation)."""
    try:
        tl = req.get("tools") or []
        STATE["shape"] = {"at": time.strftime("%H:%M:%S"), "tools": len(tl), "deferred": sum(1 for t in tl if t.get("defer_loading")),
                          "mcp": sum(1 for t in tl if str(t.get("name", "")).startswith("mcp__")),
                          "loaded_by_search": sorted(referenced_tools(req))[:20], "first_tools": [t.get("name") for t in tl[:25]]}
        sz = {"system": len(json.dumps(req.get("system", ""), ensure_ascii=False)) // 4, "tools": len(json.dumps(req.get("tools", []), ensure_ascii=False)) // 4,
              "messages": len(json.dumps(req.get("messages", []), ensure_ascii=False)) // 4, "n_tools": len(req.get("tools") or []), "at": time.time(),
              "side": not tl}
        if not tl:  # a request with no tools is Claude Code's own side work (the auto-mode safety check, titles, summaries): measured apart
            STATE["side_sample"] = {"at": time.strftime("%H:%M:%S"), "system_start": _text_of(req.get("system") or "")[:160],
                                    "system": sz["system"], "messages": sz["messages"], "model": str(req.get("model", ""))[:60]}
        STATE.setdefault("sizes", []).append(sz)
        del STATE["sizes"][:-200]
    except Exception:
        pass


def size_summary():
    """The work requests (with tools) and Claude Code's side requests (no tools: auto-mode safety check, titles, summaries) apart."""
    allz = STATE.get("sizes") or []
    if not allz:
        return None
    side = [x for x in allz if x.get("side")]
    z = [x for x in allz if not x.get("side")] or allz
    avg = lambda k, l: int(sum(x[k] for x in l) / len(l)) if l else 0
    return {"requests": len(z), "system": avg("system", z), "tools": avg("tools", z), "messages": avg("messages", z), "n_tools": avg("n_tools", z),
            "biggest": max(x["system"] + x["tools"] + x["messages"] for x in z),
            "side": {"requests": len(side), "avg": avg("system", side) + avg("messages", side), "system": avg("system", side),
                     "messages": avg("messages", side), "sample": STATE.get("side_sample")} if side else None}


def state_view():
    s, ks, provs = settings(), keys(), providers()
    u = _read_json("usage.json", {"models": {}})
    rows = sorted(u.get("models", {}).values(), key=lambda m: -(m.get("input", 0) + m.get("output", 0)))
    now = time.time()
    pv = []
    for name in s.get("chain") or []:
        if name not in provs:  # a provider removed from the kit (e.g. Cloudflare) but still in an old routing.json
            continue
        p = provs[name]
        st = "no key" if provider_key(p, ks) is None else ("failed" if name in STATE["bad"] else ("checking" if name not in STATE["checked"] else ("paused" if not available(name) else "ready")))
        until = max(STATE["cooldown"].get(name, 0), STATE["breaker"].get(name, {}).get("open_until", 0))
        pv.append({"name": name, "status": st, "resume_in": max(0, int(until - now)) if st == "paused" else 0,
                   "model": (STATE["models"].get(name) or [None])[0], "key_name": p.get("key"), "why": STATE["bad"].get(name, ""), "label": p.get("label", name),
                   "key_hint": mask(ks.get(p.get("key", ""), "")), "keyless": bool(p.get("keyless")), "key_format": "ACCOUNT_ID:API_TOKEN" if "{account}" in p.get("base", "") else "",
                   "models_count": STATE.get("counts", {}).get(name), "signup": p.get("signup", "")})
    errs = recent_errors()
    plan = {"login_seen": STATE.get("plan_login_seen"), "claude_env": STATE.get("claude_env", ""), "available": plan_available(), "resume_in": max(0, int(STATE.get("plan_until", 0) - now)), "why": STATE.get("plan_why", "")}
    return {"version": VERSION, "running": True, "settings": s, "providers": pv, "models": recent_models(), "models_month": len(rows), "active": sorted(STATE.get("active", {})),
            "learned": {"tried": len(STATE.get("perf", {})), "answering": sum(1 for v in STATE.get("perf", {}).values() if v.get("ok")), "explored": STATE.get("explored", 0)}, "safety": STATE.get("safety"), "recent_hours": RECENT_HOURS, "plan": plan, "errors": errs, "sizes": size_summary(), "shape": STATE.get("shape"),
            "trim": {"requests": TRIM_STATE["requests"], "chars_before": TRIM_STATE["chars_before"], "chars_after": TRIM_STATE["chars_after"]},
            "month": u.get("month"), "last": STATE["last"], "uptime": int(now - STATE["started"])}


# ---------- HTTP ----------
ALLOWED_ORIGINS = re.compile(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$")


class Handler(BaseHTTPRequestHandler):
    server_version = "DreamRouter/" + VERSION

    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        o = self.headers.get("Origin") or ""
        if ALLOWED_ORIGINS.match(o):
            self.send_header("Access-Control-Allow-Origin", o)
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Router-Action")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, code, obj, extra=None):
        b = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self._cors()
        self.end_headers()
        self.wfile.write(b)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}") if n else {}
        except ValueError:
            return None

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/health", "/router/health"):
            return self._json(200, {"ok": True, "version": VERSION, "busy": STATE.get("inflight", 0),
                                    "idle": int(time.time() - STATE.get("idle_since", STATE["started"]))})
        if p == "/router/state":
            return self._json(200, state_view())
        if p == "/router/candidates":
            q = re.search(r"[?&]n=(\d+)", self.path)
            return self._json(200, {"models": candidates(int(q.group(1)) if q else 20)})
        if p == "/v1/models":
            return self._json(200, {"data": [{"id": "claude-free-router", "type": "model", "display_name": "Dream Router (free models)"}]})
        self._other(None)

    def _other(self, raw):
        """Any other Claude Code call (for example the server-side safety check of auto mode): with the plan's own login it
        goes to Claude untouched; with free models only there is nothing to answer it, so the reason is logged and returned."""
        if plan_credentials(self.headers) and settings()["mode"] in ("auto", "plan"):
            if forward_plan(self, raw, "") == "done":
                return
        log_error("claude-code", self.path.split("?")[0], ProviderError("not_served", 404, "Claude Code asked for %s %s, which only Claude itself can answer (free mode has no plan login)" % (self.command, self.path.split("?")[0])), {})
        self._json(404, {"type": "error", "error": {"type": "not_found_error", "message": "The free router cannot answer %s: only Claude can (it needs your plan). In Free only mode use a permission mode other than auto." % self.path.split("?")[0]}})

    def do_POST(self):
        """Counts the requests in flight, so the guardian replaces an old router only when nothing is running (1.124.34)."""
        with LOCK:
            STATE["inflight"] = STATE.get("inflight", 0) + 1
        try:
            self._do_post()
        finally:
            with LOCK:
                STATE["inflight"] -= 1
                STATE["idle_since"] = time.time()

    def _do_post(self):
        p = self.path.split("?")[0]
        if p == "/router/settings":
            if not ALLOWED_ORIGINS.match(self.headers.get("Origin") or "http://127.0.0.1") or self.headers.get("X-Router-Action") != "1":
                return self._json(403, {"ok": False})
            body = self._body() or {}
            cur = _read_json("routing.json", {})
            if isinstance(body.get("enabled"), bool):
                cur["enabled"] = body["enabled"]
            if body.get("mode") in MODES:
                cur["mode"] = body["mode"]
                cur.pop("default", None); cur.pop("continue_on_limit", None)
            if isinstance(body.get("free_accept_edits"), bool):
                cur["free_accept_edits"] = body["free_accept_edits"]
            if isinstance(body.get("spread"), bool):
                cur["spread"] = body["spread"]
            if body.get("safety_check") in ("short", "full"):
                cur["safety_check"] = body["safety_check"]
            if isinstance(body.get("chain"), list) and all(isinstance(x, str) for x in body["chain"]):
                cur["chain"] = body["chain"]
            _write_json("routing.json", cur)
            st_now = settings()
            STATE["claude_env"] = apply_mode_to_claude(st_now["mode"], st_now.get("enabled", True))
            return self._json(200, {"ok": True, "settings": settings()})
        if p == "/router/quit":
            if self.client_address[0] not in ("127.0.0.1", "::1") or self.headers.get("X-Router-Action") != "1":
                return self._json(403, {"ok": False})
            body = self._body() or {}
            if body.get("stop_all"):  # the last Claude Code session ended: the guardian must not start it again
                try:
                    with open(_path("STOP"), "w") as f:
                        f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
                except OSError:
                    pass
            # Write daily history at quit (one line per model per day, never duplicates)
            try:
                model_history.write_daily_history(time.strftime("%Y-%m-%d"))
            except Exception:
                pass
            self._json(200, {"ok": True})
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return
        if p == "/router/history":
            if not ALLOWED_ORIGINS.match(self.headers.get("Origin") or "http://127.0.0.1") or self.headers.get("X-Router-Action") != "1":
                return self._json(403, {"ok": False})
            # Return the model history summary as HTML-safe text
            weeks = 4
            try:
                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                for part in qs.split("&"):
                    if part.startswith("weeks="):
                        weeks = int(part.split("=", 1)[1])
                        break
            except Exception:
                pass
            try:
                md = model_history.summary(weeks=weeks) if model_history else "No history yet."
            except Exception:
                md = "No history yet."
            # Escape for HTML
            safe = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            return self._json(200, {"ok": True, "text": safe})
        if p == "/router/check":
            if not ALLOWED_ORIGINS.match(self.headers.get("Origin") or "http://127.0.0.1") or self.headers.get("X-Router-Action") != "1":
                return self._json(403, {"ok": False})
            return self._json(200, {"ok": True, "results": check_all()})
        if p == "/router/keys":
            if not ALLOWED_ORIGINS.match(self.headers.get("Origin") or "http://127.0.0.1") or self.headers.get("X-Router-Action") != "1":
                return self._json(403, {"ok": False})
            body = self._body() or {}
            prov = providers().get(body.get("provider", ""))
            val = (body.get("key") or "").strip()
            if not prov or (val and not KEY_OK.match(val)):
                return self._json(400, {"ok": False, "error": "unknown provider or key with spaces/odd characters"})
            save_key(prov["key"], val)
            STATE["bad"].pop(body["provider"], None)
            STATE["checked"].pop(body["provider"], None)
            threading.Thread(target=check_all, daemon=True).start()
            STATE["cooldown"].pop(body["provider"], None)
            STATE["models"].pop(body["provider"], None)
            return self._json(200, {"ok": True})
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            req = json.loads(raw.decode("utf-8") or "{}")
        except ValueError:
            return self._json(400, {"type": "error", "error": {"type": "invalid_request_error", "message": "bad JSON"}})
        mode = settings()["mode"]
        if p == "/v1/messages":
            note_size(req)
        if p == "/v1/messages" and mode == "auto":
            STATE["plan_login_seen"] = plan_credentials(self.headers)
        if p in ("/v1/messages", "/v1/messages/count_tokens") and mode in ("auto", "plan") and plan_credentials(self.headers) and not pinned(req):
            if mode == "plan" or plan_available():
                if forward_plan(self, raw, req.get("model", "")) == "done":
                    return
            if mode == "plan":
                return self._json(503, {"type": "error", "error": {"type": "api_error", "message": "Your Claude plan is not reachable through the router (" + STATE.get("plan_why", "") + ") and the mode is Plan only."}})
        if p == "/v1/messages/count_tokens":
            n = len(json.dumps(req.get("messages", []))) + len(json.dumps(req.get("system", ""))) + len(json.dumps(req.get("tools", [])))
            return self._json(200, {"input_tokens": n // 4})
        if p != "/v1/messages":
            return self._other(raw)
        try:
            msg, routed, _ = route_patiently(req)
        except ProviderError as e:
            kind = {"limit": "rate_limit_error", "off": "api_error", "no_keys": "authentication_error", "all_failed": "overloaded_error"}.get(e.kind, "api_error")
            extra = {"retry-after": "5"} if e.kind == "all_failed" else None
            return self._json(e.status if e.status >= 400 else 529, {"type": "error", "error": {"type": kind, "message": e.detail}}, extra)
        if req.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Routed-Via", routed)
            self.end_headers()
            for chunk in sse_events(msg):
                self.wfile.write(chunk)
                self.wfile.flush()
            return
        self._json(200, msg, {"X-Routed-Via": routed})


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        # Claude Code closing a connection early (Ctrl+C, a retry) is normal: not worth a traceback in router.log
        if isinstance(sys.exc_info()[1], (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        ThreadingHTTPServer.handle_error(self, request, client_address)


def serve(port=PORT):
    os.makedirs(HOME, exist_ok=True)
    try:  # a hidden router has no window: what it prints (and any crash) goes to router.log, kept short
        lp = _path("router.log")
        if os.path.isfile(lp) and os.path.getsize(lp) > 200000:
            os.replace(lp, lp + ".old")
        sys.stdout = sys.stderr = open(lp, "a", encoding="utf-8", buffering=1)
        print("---- %s start" % time.strftime("%Y-%m-%d %H:%M:%S"))
    except OSError:
        pass
    QuietServer.allow_reuse_address = os.name != "nt"  # on Windows SO_REUSEADDR lets two routers share the port
    try:
        srv = QuietServer(("127.0.0.1", port), Handler)
    except OSError:
        print("Port %d is busy: another Dream Router is running (dream_router.py quit stops it)." % port, flush=True)
        sys.exit(1)
    print("Dream Router %s on http://127.0.0.1:%d  (files in %s)" % (VERSION, port, HOME), flush=True)

    try:  # keep Claude Code's settings in step with the mode chosen on the Models page
        st0 = settings()
        STATE["claude_env"] = apply_mode_to_claude(st0["mode"], st0.get("enabled", True))
        print("Claude Code settings:", STATE["claude_env"])
    except Exception as e:
        print("Claude Code settings not updated:", e)

    STATE["cooldown"].update({k: v for k, v in _read_json("pauses.json", {}).items() if isinstance(v, (int, float)) and v > time.time()})
    STATE["lockout"].update({k: v for k, v in _read_json("lockout.json", {}).items() if isinstance(v, (int, float)) and v > time.time()})
    STATE["perf"] = {k: v for k, v in _read_json("perf.json", {}).items() if isinstance(v, dict)}  # what each model did before the restart

    def checker():
        while True:
            try:
                check_all()
            except Exception:
                pass
            time.sleep(1800)
    threading.Thread(target=checker, daemon=True).start()
    srv.serve_forever()


def check_all():
    """Ask every provider that has a key for its model list: tells which keys work, without spending tokens."""
    ks, out = keys(), []
    for name, p in providers().items():
        k = provider_key(p, ks)
        if k is None:
            out.append({"provider": name, "ok": False, "why": "no key"})
            continue
        try:
            n = len(list_models(p, k))
            STATE.setdefault("counts", {})[name] = n
            STATE["models"].pop(name, None)
            STATE["cooldown"].pop(name, None)
            STATE["bad"].pop(name, None)
            STATE["checked"][name] = time.time()
            out.append({"provider": name, "ok": True, "models": n, "model": pick_model(name, p, k)})
        except ProviderError as e:
            why = {"auth": "the provider refused the key (HTTP %s)" % e.status, "limit": "at its limit right now"}.get(e.kind, "could not reach it (HTTP %s)" % e.status)
            if "1010" in e.detail or "cloudflare" in e.detail.lower():
                why = "the provider's firewall blocked the router (not the key)"
            if e.kind != "limit":
                STATE["bad"][name] = why
            STATE["checked"][name] = time.time()
            out.append({"provider": name, "ok": False, "why": why, "detail": e.detail[:160]})
    return out


def check():
    res = check_all()
    for r in res:
        print("%-11s %s" % (r["provider"], ("OK  %d models, will use %s" % (r["models"], r["model"])) if r["ok"] else "FAIL " + r["why"] + " " + r.get("detail", "")))
    return 0 if all(r["ok"] or r["why"] == "no key" for r in res) else 1


def _health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT, timeout=3) as r:
            return json.loads(r.read().decode("utf-8")).get("version", "?")
    except (OSError, ValueError):
        return None


def _busy():
    """(requests in flight, seconds since the last one ended) of the running router, or (0, big) when unknown."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % PORT, timeout=3) as r:
            d = json.loads(r.read().decode("utf-8"))
            return int(d.get("busy", 0)), int(d.get("idle", 9999))
    except (OSError, ValueError):
        return 0, 9999


def _file_version():
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as f:
            m = re.search(r'^VERSION = "([0-9.]+)"', f.read(), re.M)
            return m.group(1) if m else VERSION
    except OSError:
        return VERSION


REPLACE_IDLE = 20        # an updated router replaces the running one only after 20 s without requests...
REPLACE_MAX_WAIT = 900   # ...or after 15 minutes of waiting, whatever comes first (a session never loses a request mid-way)


def supervise(every=5, sleep=time.sleep, start=None, health=None, max_rounds=None, busy=None, clock=time.time):
    """The guardian (v1.124.16): keeps the router alive. Every few seconds it asks the router if it is there; if not
    (crashed, killed, never started) it starts it again; if an older version answers after an update, it replaces it.
    It stops only when the last Claude Code session ends (STOP file written by /router/quit with stop_all).
    One guardian at a time (guardian.json); after 5 failed starts in a row it waits a minute before trying again."""
    os.makedirs(HOME, exist_ok=True)
    health = health or _health
    log = lambda m: _append_log("guardian: " + m)
    def _start():
        kw = {"creationflags": 0x08000000} if os.name == "nt" else {"start_new_session": True}
        import subprocess
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "serve"], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    start = start or _start
    busy = busy or _busy
    fails, rounds, waiting_since = 0, 0, None
    _write_json("guardian.json", {"pid": os.getpid(), "ts": time.time()})
    log("on (pid %d)" % os.getpid())
    while max_rounds is None or rounds < max_rounds:
        rounds += 1
        if os.path.isfile(_path("STOP")):
            try:
                os.remove(_path("STOP"))
            except OSError:
                pass
            log("off: the last session ended")
            return "stopped"
        have = health()
        want = _file_version()
        if have is not None and have != want and have != "?":
            n, idle = busy()
            if waiting_since is None:
                waiting_since = clock()
                log("router %s is older than %s: replacing it when idle" % (have, want))
            if (n > 0 or idle < REPLACE_IDLE) and clock() - waiting_since < REPLACE_MAX_WAIT:
                sleep(every)
                continue
        if have is None or (have != want and have != "?"):
            waiting_since = None
            if have is not None:
                try:
                    urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:%d/router/quit" % PORT, data=b"{}", method="POST",
                                                                  headers={"X-Router-Action": "1"}), timeout=3).close()
                except OSError:
                    pass
                sleep(1)
                log("replacing router %s with %s" % (have, want))
            else:
                log("router not answering: starting it")
            start()
            sleep(3)
            if health() is None:
                fails += 1
                log("start %d failed (see router.log)" % fails)
                if fails >= 5:
                    sleep(60)
                    fails = 0
                continue
            fails = 0
        _write_json("guardian.json", {"pid": os.getpid(), "ts": time.time()})
        sleep(every)
    return "rounds"


def _append_log(msg):
    try:
        with open(_path("guardian.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    a = sys.argv[1:] or ["serve"]
    if a[0] == "serve":
        serve(int(a[a.index("--port") + 1]) if "--port" in a else PORT)
    elif a[0] == "supervise":
        supervise()
    elif a[0] == "mode":
        # for cod.cmd: "free" when Cod must start on the free router, else "plan"
        st = settings()
        print(st["mode"] if st.get("enabled") else "plan")
    elif a[0] == "session-settings":
        print(session_settings(a[1] if len(a) > 1 else settings()["mode"]))
    elif a[0] == "check":
        sys.exit(check())
    elif a[0] == "quit":
        try:
            rq = urllib.request.Request("http://127.0.0.1:%d/router/quit" % PORT, data=b"{}", method="POST", headers={"X-Router-Action": "1"})
            urllib.request.urlopen(rq, timeout=3).close()
            time.sleep(1)
        except OSError:
            pass
    elif a[0] == "status":
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/router/state" % PORT, timeout=3) as r:
                print(r.read().decode("utf-8"))
        except OSError:
            print('{"running": false}')
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(2)
