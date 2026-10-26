#!/usr/bin/env python3
"""Claude/hooks/agent-console-server.py

Cross-platform equivalent of agent-console-server.ps1 (use this on macOS/Linux, or on Windows if
you'd rather use Python than PowerShell) — see that file's header comment for the full
explanation. Same endpoints (/, /stats, /log, /tokens, /mcp, /session, /active-task,
/island-metrics, /island-info), same default port, no third-party dependencies (standard library
only).

/island-metrics and /island-info (added v1.71.0) proxy the public Fortnite Ecosystem API
(api.fortnite.com/ecosystem/v1 — confirmed publicly accessible, no API key/OAuth needed for these
endpoints via a real payload capture, 2026-09-18) for the island code saved in
Claude/docs/.island-code, same pattern as .active-task. The proxy exists (rather than having the
browser call Epic's API directly) for two reasons: it keeps the island code and the fetch logic in
one place instead of duplicated in page JS, and it lets the server cache the response server-side
— Epic's API is documented to 429 under a rate limit, and daily-granularity metrics don't need a
fresh fetch on every page poll anyway. Cache TTL is 5 minutes in memory, backed by a
Claude/logs/fortnite-metrics-cache.json file so a page reload (or a 429) can still show the last
good data instead of an empty page.

Run it from a terminal and leave it running while you work:

    python3 Claude/hooks/agent-console-server.py
    python3 Claude/hooks/agent-console-server.py 9000   # custom port

Then open http://127.0.0.1:8765/ (or your custom port) in your browser.

Also serves "/whoami" -> {"project": "<absolute path to this project's folder>", "started_at":
"<ISO timestamp this server process actually started>"}. "project" is what
session-start-reminder.py/.sh use to tell "this port is already serving THIS project" apart from
"a different/stale project's server is still bound here" when a new session starts. "started_at"
is what the console page itself uses for its "Session running for" stat (v1.44 fix — that stat
used to be computed from the OLDEST line in agent-console.jsonl, which persists across restarts
by design, so it kept showing hours/days of history even seconds after a genuine restart; the
server's own real start time fixes that without touching the history file).

v1.79.3 concurrency fix: this used to run on plain http.server.HTTPServer, which — like
BaseHTTPRequestHandler in general — handles exactly one request at a time on a single thread. The
Docs & Status console page (agent-console-docs.html) fires 6-9 parallel fetch() calls on load, and
/island-metrics, /island-info and /island-rankings each call out to the external Fortnite API with
a 10s timeout; a single slow/unreachable API call therefore blocked every other pending request
from every tab for up to 10 seconds, which is the same "stuck on loading.../connecting forever"
bug documented for agent-console-server.ps1. Fixed by switching to
socketserver.ThreadingHTTPServer (stdlib, no new dependency), which serves each connection on its
own thread so a slow request never blocks the others. The small in-memory Fortnite caches above
are simple dict key assignments, which are already thread-safe enough under the GIL for this
best-effort caching (a worst case is two threads both refreshing the cache at once, not
corruption), matching the equivalent tradeoff made in the PowerShell version's synchronized
hashtable.
"""
import http.server
import socketserver
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(ROOT, "agent-console.html")
STATS_HTML_PATH = os.path.join(ROOT, "agent-console-stats.html")
DOCS_HTML_PATH = os.path.join(ROOT, "agent-console-docs.html")
FLOW_HTML_PATH = os.path.join(ROOT, "agent-console-flow.html")
SKILLS_HTML_PATH = os.path.join(ROOT, "agent-console-skills.html")
NEWS_HTML_PATH = os.path.join(ROOT, "agent-console-news.html")
SCORE_HTML_PATH = os.path.join(ROOT, "agent-console-score.html")
FAB_HTML_PATH = os.path.join(ROOT, "agent-console-fab.html")  # v1.110: the Checklist page, served only for a Fab product (UEFN_FAB_LAB set)
MANUAL_DIR = os.path.join(ROOT, "manual")  # the HTML manual (v1.100): /manual/ and /manual/<chapter>.html
MANUAL_FILE_RE = re.compile(r"/manual/([a-z0-9-]+\.(?:html|css|png))")
# Skill Harness (v1.81+): the Skills page reads/writes the genre skills under ~/.claude/skills/genre
# through skills_lib.py (same folder). If the module is missing the rest of the console still works.
try:
    sys.path.insert(0, ROOT)
    import skills_lib
except Exception:  # pragma: no cover - missing/broken module must never take the console down
    skills_lib = None
# Fab lab (v1.109.1): a Fab product holds no kit files, so its learning data lives in ~/.claude/fab-lab/<Product>/ (laid out like a project).
# fab_lab.py console starts this server with UEFN_FAB_LAB pointing at that folder.
FAB_LAB = os.environ.get("UEFN_FAB_LAB") or ""
PROJECT_DIR = FAB_LAB if FAB_LAB else os.path.dirname(os.path.dirname(ROOT))
_DATA = os.path.join(FAB_LAB, "Claude") if FAB_LAB else os.path.dirname(ROOT)


def _fab_mod():
    """fab_checklist.py lives in the profile (~/.claude/hooks), never in a project. Returns (module, project root, lab) or raises."""
    if not FAB_LAB:
        raise RuntimeError("not a Fab product")
    hd = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
    if hd not in sys.path:
        sys.path.insert(0, hd)
    import fab_checklist
    with open(os.path.join(FAB_LAB, "product.json"), encoding="utf-8") as f:
        root = json.load(f)["project"]
    return fab_checklist, root, FAB_LAB


def _fab_lab_mod():
    """fab_lab.py (profile hooks) and the project root of this Fab lab."""
    if not FAB_LAB:
        raise RuntimeError("not a Fab product")
    hd = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
    if hd not in sys.path:
        sys.path.insert(0, hd)
    import fab_lab
    with open(os.path.join(FAB_LAB, "product.json"), encoding="utf-8") as f:
        return fab_lab, json.load(f)["project"]


def _fab_product_info():
    """What the kit really knows about this Fab product (a map's genre and blueprint do not apply): Verse files of the product, approved lessons, recipes, recorded calls."""
    out = {"name": os.path.basename(FAB_LAB), "verse_files": 0, "verse_sample": [], "lessons": 0, "recipes": 0, "calls": 0, "failed": 0, "cards": 0}
    try:
        fl, root = _fab_lab_mod()
        out["name"] = os.path.basename(os.path.normpath(root))
        names = []
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("Intermediate", "Saved", "node_modules")]
            names += [os.path.relpath(os.path.join(base, f), root).replace("\\", "/") for f in files if f.endswith(".verse")]
        out["verse_files"] = len(names)
        out["verse_sample"] = sorted(names)[:6]
        out["lessons"] = len(fl._jload(fl.lessons_file(), []))
        st = fl.status(root)
        out.update(calls=st["calls"], failed=st["failed"], cards=len(st["cards"]))
        try:
            key = skills_lib._map_key(os.path.basename(FAB_LAB))
            out["recipes"] = sum(1 for sl in ("materials", "mechanics") for r in skills_lib.recipes_list(sl).get("recipes", []) if key in r.get("maps", []))
            out["recipe_list"] = skills_lib.recipes_of(os.path.basename(FAB_LAB))
        except Exception:
            pass
    except Exception:
        pass
    return out


SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
try:
    with open(os.path.join(os.path.dirname(ROOT), "KIT-VERSION"), encoding="utf-8") as _kv:
        KIT_VERSION_AT_START = _kv.read().strip()
except OSError:
    KIT_VERSION_AT_START = ""
LOGS_DIR = os.path.join(_DATA, "logs")
LOG_FILE = os.path.join(LOGS_DIR, "agent-console.jsonl")
TOKENS_FILE = os.path.join(LOGS_DIR, "agent-console-tokens.json")
MCP_FILE = os.path.join(LOGS_DIR, "agent-console-mcp.jsonl")
SESSION_FILE = os.path.join(LOGS_DIR, "agent-console-session.json")
DOCS_DIR = os.path.join(_DATA, "docs")
ACTIVE_TASK_FILE = os.path.join(DOCS_DIR, ".active-task")
# Whitelist of the real project docs the Docs & Status console (agent-console-docs.html) is
# allowed to read via /doc?name=<key> — deliberately NOT an arbitrary-path read. Added v1.78.0:
# that page used to show hardcoded sample markdown for every one of these regardless of what (if
# anything) actually existed in Claude/docs/, which is exactly the "still a mockup" complaint this
# release fixes. Keys are lowercase, short, and stable so the page's own JS doesn't need to know
# the real filename casing.
DOC_FILES = {
    "status": "STATUS.md",
    "roadmap": "ROADMAP.md",
    "bugs": "BUGS.md",
    "spec": "SPEC.md",
    "retention": "RETENTION-NOTES.md",
    "release": "RELEASE-READINESS.md",
}
GENRE_FILE = os.path.join(DOCS_DIR, ".genre")
COMMUNITY_SUMMARY_FILE = os.path.join(os.path.dirname(ROOT), "community", "community-summary.json")
ISLAND_CODE_FILE = os.path.join(DOCS_DIR, ".island-code")
METRICS_CACHE_FILE = os.path.join(LOGS_DIR, "fortnite-metrics-cache.json")
INFO_CACHE_FILE = os.path.join(LOGS_DIR, "fortnite-island-info-cache.json")
RANKINGS_CACHE_FILE = os.path.join(LOGS_DIR, "fortnite-island-rankings-cache.json")
FORTNITE_API_BASE = "https://api.fortnite.com/ecosystem/v1"
METRICS_CACHE_TTL_SECONDS = 5 * 60
INFO_CACHE_TTL_SECONDS = 60 * 60  # island title/tags change rarely — cache longer than metrics
RANKINGS_CACHE_TTL_SECONDS = 5 * 60

_metrics_mem_cache = {"at": 0, "body": None}
_info_mem_cache = {"at": 0, "body": None}
_rankings_mem_cache = {"at": 0, "body": None}


def _read_island_code():
    if not os.path.exists(ISLAND_CODE_FILE):
        return None
    with open(ISLAND_CODE_FILE, "r", encoding="utf-8") as f:
        code = f.read().strip()
    return code or None


def _http_get_json(url, timeout=10):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "UEFN-Claude-Kit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _load_json_file(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_json_file(path, obj):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)
    except OSError:
        pass


def _get_island_metrics():
    now = time.time()
    if _metrics_mem_cache["body"] is not None and (now - _metrics_mem_cache["at"]) < METRICS_CACHE_TTL_SECONDS:
        return _metrics_mem_cache["body"]

    code = _read_island_code()
    if not code:
        return {"error": "no-island-code"}

    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=7)
    url = (f"{FORTNITE_API_BASE}/islands/{code}/metrics/day"
           f"?from={from_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}&to={to_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    try:
        payload = _http_get_json(url)
        body = {"payload": payload, "cachedAt": datetime.now(timezone.utc).isoformat(), "rateLimited": False}
        _metrics_mem_cache["at"] = now
        _metrics_mem_cache["body"] = body
        _save_json_file(METRICS_CACHE_FILE, body)
        return body
    except urllib.error.HTTPError as e:
        stale = _load_json_file(METRICS_CACHE_FILE)
        if e.code == 429 and stale:
            stale = dict(stale)
            stale["rateLimited"] = True
            _metrics_mem_cache["at"] = now  # don't hammer the API again until TTL passes
            _metrics_mem_cache["body"] = stale
            return stale
        return {"error": f"Fortnite API error {e.code}" + (" - Epic has no public data for this island yet (not published?). The kit works without it: the genre is taken from the code." if e.code in (401, 403, 404) else "")}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        stale = _load_json_file(METRICS_CACHE_FILE)
        if stale:
            stale = dict(stale)
            stale["rateLimited"] = False
            return stale
        return {"error": f"could not reach the Fortnite API ({e})"}


def _get_island_rankings():
    # GET /islands/{code}/rankings — confirmed via real payload capture (2026-09-19): with no
    # from/to it returns only the latest single hourly snapshot; with from/to set to a 7-day
    # window it returns an HOURLY-granularity series (167 points observed for one real island),
    # each shaped {timestamp, genres:[{genreSlug, genre, rank}]}. A `to` in the future produces a
    # real 400, so `to` is always clamped to "now" here, same as _get_island_metrics.
    now = time.time()
    if _rankings_mem_cache["body"] is not None and (now - _rankings_mem_cache["at"]) < RANKINGS_CACHE_TTL_SECONDS:
        return _rankings_mem_cache["body"]

    code = _read_island_code()
    if not code:
        return {"error": "no-island-code"}

    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=7)
    url = (f"{FORTNITE_API_BASE}/islands/{code}/rankings"
           f"?from={from_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}&to={to_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    try:
        payload = _http_get_json(url)
        body = {"payload": payload, "cachedAt": datetime.now(timezone.utc).isoformat(), "rateLimited": False}
        _rankings_mem_cache["at"] = now
        _rankings_mem_cache["body"] = body
        _save_json_file(RANKINGS_CACHE_FILE, body)
        return body
    except urllib.error.HTTPError as e:
        stale = _load_json_file(RANKINGS_CACHE_FILE)
        if e.code == 429 and stale:
            stale = dict(stale)
            stale["rateLimited"] = True
            _rankings_mem_cache["at"] = now
            _rankings_mem_cache["body"] = stale
            return stale
        return {"error": f"Fortnite API error {e.code}" + (" - Epic has no public data for this island yet (not published?). The kit works without it: the genre is taken from the code." if e.code in (401, 403, 404) else "")}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        stale = _load_json_file(RANKINGS_CACHE_FILE)
        if stale:
            stale = dict(stale)
            stale["rateLimited"] = False
            return stale
        return {"error": f"could not reach the Fortnite API ({e})"}


GENRE_SKILLS_DIR = os.path.expanduser("~/.claude/skills/genre")
TAGS_KNOWN_FILE = os.path.join(GENRE_SKILLS_DIR, "fortnite-tags-known.json")


def _update_known_tags(tags, island_code):
    # Best-effort tracking of real tag usage against the official closed list shipped in
    # fortnite-tags-known.json (see that file's own header for the source). Never creates the
    # file from scratch here — it ships with the kit already populated with the official 149-tag
    # list; this only appends usage observations to its existing `observedOnIslands` array. Any
    # failure here must never break the /island-info response, hence the broad except.
    if not tags:
        return
    try:
        data = _load_json_file(TAGS_KNOWN_FILE)
        if not data:
            return
        observed = data.get("observedOnIslands", [])
        by_tag = {o.get("tag"): o for o in observed}
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        changed = False
        for tag in tags:
            entry = by_tag.get(tag)
            if entry is None:
                entry = {"tag": tag, "firstSeen": today, "lastSeen": today,
                          "timesObserved": 1, "islandsObservedOn": [island_code]}
                observed.append(entry)
                by_tag[tag] = entry
                changed = True
            else:
                if entry.get("lastSeen") != today:
                    entry["lastSeen"] = today
                    entry["timesObserved"] = entry.get("timesObserved", 0) + 1
                    changed = True
                if island_code not in entry.get("islandsObservedOn", []):
                    entry.setdefault("islandsObservedOn", []).append(island_code)
                    changed = True
        if changed:
            data["observedOnIslands"] = observed
            _save_json_file(TAGS_KNOWN_FILE, data)
    except Exception:
        pass


def _get_island_info():
    now = time.time()
    if _info_mem_cache["body"] is not None and (now - _info_mem_cache["at"]) < INFO_CACHE_TTL_SECONDS:
        return _info_mem_cache["body"]

    code = _read_island_code()
    if not code:
        return {"error": "no-island-code"}

    try:
        payload = _http_get_json(f"{FORTNITE_API_BASE}/islands/{code}")
        _info_mem_cache["at"] = now
        _info_mem_cache["body"] = payload
        _save_json_file(INFO_CACHE_FILE, payload)
        if isinstance(payload, dict) and isinstance(payload.get("tags"), list):
            _update_known_tags(payload["tags"], code)
        return payload
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        stale = _load_json_file(INFO_CACHE_FILE)
        return stale if stale else {"error": "could not reach the Fortnite API"}


def _read_jsonl(path):
    entries = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _read_json_object(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content
    return default


def _kit_status():
    """Is a newer kit installed in the user profile than this project's files? (v1.86.8)"""
    def rd(path):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""
    tpl = os.environ.get("UEFN_KIT_TEMPLATE") or os.path.join(os.path.expanduser("~"), ".claude", "kit-template")
    proj_v = rd(os.path.join(PROJECT_DIR, "Claude", "KIT-VERSION"))
    tpl_v = rd(os.path.join(tpl, "Claude", "KIT-VERSION"))
    def t(v):
        return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)
    return {"project": proj_v, "template": tpl_v, "outdated": bool(tpl_v) and t(tpl_v) > t(proj_v)}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # keep the terminal quiet — the browser polls this every second

    def _send_json_bytes(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/log"):
            self._send_json_bytes(json.dumps(_read_jsonl(LOG_FILE)).encode("utf-8"))
        elif self.path.startswith("/tokens"):
            self._send_json_bytes(_read_json_object(TOKENS_FILE, "{}").encode("utf-8"))
        elif self.path.startswith("/mcp"):
            self._send_json_bytes(json.dumps(_read_jsonl(MCP_FILE)).encode("utf-8"))
        elif self.path.startswith("/session"):
            self._send_json_bytes(_read_json_object(SESSION_FILE, '{"active":false}').encode("utf-8"))
        elif self.path.startswith("/active-task"):
            text = ""
            if os.path.exists(ACTIVE_TASK_FILE):
                with open(ACTIVE_TASK_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/doc?") or self.path == "/doc":
            # /doc?name=<key> — see DOC_FILES above. Always returns 200 + JSON {name, exists,
            # content}, never a bare 404: a missing file is real, expected state for a fresh
            # project (no SPEC.md yet, etc.), not an error, so the response says so explicitly
            # instead of making the page's fetch() guess from an HTTP status code.
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            key = (qs.get("name") or [""])[0]
            filename = DOC_FILES.get(key)
            if not filename:
                self._send_json_bytes(json.dumps({"error": "unknown doc key"}).encode("utf-8"))
                return
            path = os.path.join(DOCS_DIR, filename)
            exists = os.path.isfile(path)
            content = ""
            if exists:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    exists = False
            self._send_json_bytes(json.dumps({"name": filename, "exists": exists, "content": content}).encode("utf-8"))
        elif self.path.startswith("/project-genre"):
            # Serves the raw content of Claude/docs/.genre — the genre slug the OWNER assigned to
            # this project (via CLAUDE.md's "Genre check" rule / project-bootstrap's Step 0.5).
            # Deliberately a separate source from whatever genre the live Fortnite API happens to
            # report in /island-rankings — those usually agree but aren't the same thing, and the
            # Stats page shows both labeled distinctly rather than only the API-derived one.
            text = ""
            if os.path.exists(GENRE_FILE):
                with open(GENRE_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/kit-status"):
            self._send_json_bytes(json.dumps(_kit_status()).encode("utf-8"))
        elif self.path.startswith("/whoami"):
            self._send_json_bytes(json.dumps({"project": PROJECT_DIR, "started_at": SERVER_STARTED_AT, "kit_version": KIT_VERSION_AT_START, "fab": bool(FAB_LAB), "caps": ["quit", "fab_product"]}).encode("utf-8"))
        elif self.path.startswith("/island-metrics"):
            self._send_json_bytes(json.dumps(_get_island_metrics()).encode("utf-8"))
        elif self.path.startswith("/island-info"):
            self._send_json_bytes(json.dumps(_get_island_info()).encode("utf-8"))
        elif self.path.startswith("/island-rankings"):
            self._send_json_bytes(json.dumps(_get_island_rankings()).encode("utf-8"))
        elif self.path.startswith("/learning-data"):
            # State of the learning of THIS project (steps, blueprint state, log) + genre/type proposal. State files only.
            try:
                d = skills_lib.console_learning(PROJECT_DIR)
                if FAB_LAB:
                    d["fab_product"] = _fab_product_info()
                else:
                    d["learn_flag"] = skills_lib.map_learn_flag(PROJECT_DIR)
                    d["recipe_list"] = skills_lib.recipes_of(skills_lib.project_name(PROJECT_DIR))
                self._send_json_bytes(json.dumps(d).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"error": "could not read the learning state: %s" % e}).encode("utf-8"))
        elif self.path.startswith("/recipe-inbox"):
            try:
                self._send_json_status(200, skills_lib.recipe_inbox() if skills_lib else {"pending": [], "decided": 0})
            except Exception as e:
                self._send_json_status(200, {"pending": [], "decided": 0, "error": "%s" % e})
        elif self.path.startswith("/community-state"):
            # The switch "Contribute to the community", what was shared, and whether this project's map is published.
            try:
                self._send_json_status(200, skills_lib.community_info(PROJECT_DIR) if skills_lib else {"error": "skills_lib.py not found"})   # no CORS header: other web pages cannot read it
            except Exception as e:
                self._send_json_bytes(json.dumps({"error": "could not read the community state: %s" % e}).encode("utf-8"))
        elif self.path.startswith("/community-summary"):
            # What's new page: summary of the last release (shipped with the kit); empty object when the file is not there yet.
            self._send_json_bytes(_read_json_object(COMMUNITY_SUMMARY_FILE, "{}").encode("utf-8"))
        elif self.path.startswith("/uefn-mcp-map"):
            # UEFN MCP map in numbers for the Skills page (mcp_map.py); reads saved files only, never an error status.
            try:
                import mcp_map
                self._send_json_bytes(json.dumps(mcp_map.summary()).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"available": False, "reason": "could not read the MCP map (%s)" % e.__class__.__name__}).encode("utf-8"))
        elif self.path.startswith("/agent-costs"):
            # Tokens per sub-agent for the Console's table; counts only (agent_cost.py). Never an error status: "available": false says why.
            try:
                import agent_cost
                self._send_json_bytes(json.dumps(agent_cost.summary(PROJECT_DIR, 30, 4.0)).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"available": False, "reason": "could not read the transcripts (%s)" % e.__class__.__name__}).encode("utf-8"))
        elif self.path.startswith("/score-data"):
            # Score page data, computed live from ROADMAP / BUGS / RELEASE-READINESS (score.py); never an error status.
            try:
                import score
                self._send_json_bytes(json.dumps(score.compute(PROJECT_DIR)).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"available": False, "reason": "could not compute the score (%s)" % e.__class__.__name__}).encode("utf-8"))
        elif self.path.startswith("/fab-data"):
            try:
                fc, root, lab = _fab_mod()
                self._send_json_bytes(json.dumps(fc.build(root, lab)).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"error": "%s" % e}).encode("utf-8"))
        elif self.path.startswith("/fab-learn"):
            try:
                fl, root = _fab_lab_mod()
                self._send_json_bytes(json.dumps(fl.learn_state(root)).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"error": "%s" % e}).encode("utf-8"))
        elif self.path.startswith("/fab-file"):
            try:
                from urllib.parse import urlparse, parse_qs
                fc, root, lab = _fab_mod()
                key = parse_qs(urlparse(self.path).query).get("key", [""])[0]
                label, text = fc.read_product_file(root, key)
                self._send_json_bytes(json.dumps({"name": label, "text": text}).encode("utf-8"))
            except Exception as e:
                self._send_json_bytes(json.dumps({"error": "%s" % e}).encode("utf-8"))
        elif self.path.startswith("/checklist") or self.path.startswith("/agent-console-fab.html"):
            self._serve_html_file(FAB_HTML_PATH)
        elif self.path.startswith("/skills-data"):
            # Real data only, computed from the local genre-skill files by skills_lib.summary().
            if skills_lib is None:
                self._send_json_bytes(json.dumps({"error": "skills_lib.py not found next to the server"}).encode("utf-8"))
            else:
                try:
                    d = skills_lib.summary()
                    d["current_project"] = os.path.basename(FAB_LAB) if FAB_LAB else skills_lib.project_name(PROJECT_DIR)
                    d["current_kind"] = "fab" if FAB_LAB else "map"
                    self._send_json_bytes(json.dumps(d).encode("utf-8"))
                except Exception as e:
                    self._send_json_bytes(json.dumps({"error": "could not read skills: %s" % e}).encode("utf-8"))
        elif self.path == "/manual" or self.path.startswith("/manual/") or self.path.startswith("/manual?"):
            self._serve_manual()
        elif self.path.startswith("/news") or self.path.startswith("/agent-console-news.html"):
            self._serve_html_file(NEWS_HTML_PATH)
        elif self.path.startswith("/score") or self.path.startswith("/agent-console-score.html"):
            self._serve_html_file(SCORE_HTML_PATH)
        elif self.path.startswith("/skills") or self.path.startswith("/agent-console-skills.html"):
            self._serve_html_file(SKILLS_HTML_PATH)
        elif self.path.startswith("/stats") or self.path.startswith("/agent-console-stats.html"):
            self._serve_html_file(STATS_HTML_PATH)
        elif self.path.startswith("/docs") or self.path.startswith("/agent-console-docs.html"):
            self._serve_html_file(DOCS_HTML_PATH)
        elif self.path.startswith("/flow") or self.path.startswith("/agent-console-flow.html"):
            self._serve_html_file(FLOW_HTML_PATH)
        elif self.path.startswith("/agent-console.html") or self.path == "/" or self.path.startswith("/?"):
            self._serve_html_file(HTML_PATH)
        else:
            # Anything else (e.g. an unrecognized path) falls back to the main console rather
            # than a bare 404, matching this server's original behavior for unknown paths.
            self._serve_html_file(HTML_PATH)

    def _origin_ok(self):
        # Browsers always send Origin on a cross-site POST; only accept our own origin (or none,
        # i.e. a local script). Together with the custom header this blocks drive-by web pages.
        origin = self.headers.get("Origin")
        if origin in (None, "http://127.0.0.1:%d" % PORT, "http://localhost:%d" % PORT):
            return self.headers.get("X-Skills-Action") == "1"
        return False

    def _send_json_status(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path.startswith("/quit"):  # v1.110: lets a newer fab_lab.py replace an out-of-date console of the same product
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self._send_json_status(403, {"ok": False})
            self._send_json_status(200, {"ok": True})
            import threading
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return
        # Owner decisions on the Skills page: approve / edit / reject a lesson, run the privacy check.
        if self.path.startswith("/fab-learn-act"):
            return self._fab_learn_act()
        if self.path.startswith("/map-learn"):
            return self._map_learn()
        if self.path.startswith("/fab-act"):
            return self._fab_act()
        if skills_lib is None or not (self.path.startswith("/skills-act") or self.path.startswith("/skills-check") or self.path.startswith("/genre-confirm") or self.path.startswith("/community-act") or self.path.startswith("/recipe-share")):
            return self._send_json_status(404, {"ok": False, "error": "unknown endpoint"})
        if not self._origin_ok():
            return self._send_json_status(403, {"ok": False, "error": "forbidden origin"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 65536:
                return self._send_json_status(413, {"ok": False, "error": "body too large"})
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            if self.path.startswith("/recipe-share") and data.get("inbox"):
                res = skills_lib.recipe_inbox_act(str(data.get("id") or ""), str(data.get("decision") or ""))
            elif self.path.startswith("/recipe-share"):
                res = skills_lib.recipe_share(str(data.get("skill") or ""), str(data.get("name") or ""), str(data.get("decision") or ""))
            elif self.path.startswith("/community-act"):
                res = skills_lib.community_act(data, PROJECT_DIR)
            elif self.path.startswith("/genre-confirm"):
                res = skills_lib.confirm_genre(PROJECT_DIR, data.get("genre"), data.get("variant"))
            elif self.path.startswith("/skills-check"):
                res = skills_lib.check(data.get("genre"))
            else:
                res = skills_lib.act(data.get("genre"), data.get("proposal"), data.get("action"),
                                     data.get("statement"), data.get("exclude") or [])
            self._send_json_status(200, res)
        except (ValueError, KeyError, TypeError) as e:
            self._send_json_status(400, {"ok": False, "error": str(e)})

    def _map_learn(self):
        # Skills page, map project: the Learn button (same idea as the Fab product button).
        if not self._origin_ok():
            return self._send_json_status(403, {"ok": False, "error": "forbidden origin"})
        if FAB_LAB or skills_lib is None:
            return self._send_json_status(400, {"ok": False, "error": "not a map project"})
        try:
            self._send_json_status(200, dict(skills_lib.map_learn_request(PROJECT_DIR), ok=True))
        except (ValueError, OSError) as e:
            self._send_json_status(400, {"ok": False, "error": str(e)})

    def _fab_learn_act(self):
        # Skills page, Fab product: press Learn, approve / edit / reject a proposed lesson.
        if not self._origin_ok():
            return self._send_json_status(403, {"ok": False, "error": "forbidden origin"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 65536:
                return self._send_json_status(413, {"ok": False, "error": "body too large"})
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            fl, root = _fab_lab_mod()
            a = data.get("action")
            if a == "request":
                res = fl.learn_request(root)
                return self._send_json_status(200, dict(res, ok=True))
            fl.act(root, a, str(data.get("id") or ""), data.get("text"))
            self._send_json_status(200, {"ok": True})
        except (ValueError, KeyError, TypeError, RuntimeError, OSError) as e:
            self._send_json_status(400, {"ok": False, "error": str(e)})

    def _fab_act(self):
        # Checklist page actions (Fab product only): tick an item, record the UEFN validation log, rescan, make / re-read the zip.
        if not self._origin_ok():
            return self._send_json_status(403, {"ok": False, "error": "forbidden origin"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 1048576:
                return self._send_json_status(413, {"ok": False, "error": "body too large"})
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            fc, root, lab = _fab_mod()
            a = data.get("action")
            if a == "tick":
                fc.set_tick(lab, str(data.get("id") or ""), bool(data.get("on")))
            elif a == "validation":
                fc.save_validation(lab, str(data.get("text") or ""), bool(data.get("skip_fixup")))
            elif a == "scan":
                fc.refresh(root, lab)
            elif a == "zip":
                if not fc.build(root, lab)["can_zip"]:
                    return self._send_json_status(200, {"ok": False, "error": "stations 1 to 4 still have a block: fix them first"})
                import fab_pack
                out, probs = fab_pack.zip_package(root)
                if probs:
                    return self._send_json_status(200, {"ok": False, "error": "; ".join(probs[:3])})
                fc.scan_state(root, lab)
                return self._send_json_status(200, {"ok": True, "zip": out})
            elif a == "reread":
                fc.reread_zip(root, lab)
            else:
                return self._send_json_status(400, {"ok": False, "error": "unknown action"})
            self._send_json_status(200, {"ok": True})
        except (ValueError, KeyError, TypeError, RuntimeError, OSError) as e:
            self._send_json_status(400, {"ok": False, "error": str(e)})

    def _serve_manual(self):
        # Only plain chapter names (a-z, 0-9, dash) with .html, .css or .png, read from the manual folder: no path can climb out of it.
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path == "/manual":
            self.send_response(302)
            self.send_header("Location", "/manual/")
            self.end_headers()
            return
        if path == "/manual/":
            path = "/manual/index.html"
        m = MANUAL_FILE_RE.fullmatch(path)
        # The file name used below comes from the folder listing, never from the request string, so request data cannot steer the path.
        name = ""
        if m:
            for entry in os.listdir(MANUAL_DIR) if os.path.isdir(MANUAL_DIR) else ():
                if entry == m.group(1):
                    name = entry
                    break
        target = os.path.join(MANUAL_DIR, name) if name else ""
        if not name or not os.path.isfile(target):
            self.send_response(404)
            self.end_headers()
            return
        with open(target, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8" if name.endswith(".css") else "image/png" if name.endswith(".png") else "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html_file(self, file_path):
        # Shared by the main console and its Stats/Docs/Flow pages — both the short server routes
        # (/stats, /docs, /flow) and the pages' own plain relative <a href> filenames
        # (agent-console-stats.html etc., used so each page also works standalone via file://)
        # resolve here to the SAME file, so navigation behaves identically whichever form of the
        # link was clicked (v1.77.2 fix — the two forms used to be handled inconsistently, which
        # is why some links silently rendered the wrong page over http://).
        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            return
        with open(file_path, "rb") as f:
            body = f.read()
        if FAB_LAB:  # a Fab product: the Checklist tab is added here, on the server, so it never depends on the browser cache or a script
            real = b'<a href="agent-console-fab.html">Checklist</a>'  # the REAL link: the fallback script also contains the text href="agent-console-fab.html"
            m = re.search(rb'<a\b[^>]*href="agent-console-score\.html"[^>]*>Score</a>', body)
            has = re.search(rb'<a\b[^>]*href="agent-console-fab\.html"[^>]*>Checklist</a>', body)  # the Checklist page carries its own tab (with class="on")
            if m and not has:
                body = body[:m.end()] + real + body[m.end():]
        self.send_response(200)
        if FAB_LAB:
            self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    # ThreadingHTTPServer (not HTTPServer) — see the v1.79.3 concurrency-fix note in the module
    # docstring above. daemon_threads=True so a slow in-flight request thread doesn't keep the
    # process alive after Ctrl+C.
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Agent Console running at http://127.0.0.1:{PORT}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
