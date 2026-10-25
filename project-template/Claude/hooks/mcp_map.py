#!/usr/bin/env python3
"""The kit maps UEFN's MCP server by itself, tests the safe tools, and notices what Epic adds. Zero AI tokens.

It talks to the MCP server like any MCP client (JSON over HTTP, default http://127.0.0.1:8000/mcp), lists every
toolset and tool, and saves ONE map for all projects on this computer (toolset_diff.py holds the storage):
~/.claude/skills/mcp-tool-contracts/references/map/  (override UEFN_KIT_MCP_DIR). The map holds Epic's tool
descriptions, so it stays on this computer and is never published.

Tests: only tools that are read-only (the server says so, or the name starts with get/list/find/describe/query/
search/count/is/has) AND need no arguments are ever called. Writers are never called. Each is recorded ok or err;
a tool that worked last time and fails now is reported as "stopped working".

Modes
  mcp_map.py --now            map + test now (UEFN must be open), prints one JSON line
  mcp_map.py --auto           what a session start does: if the last full map is older than 6 hours and the MCP
                              answers, run --now in the background. Silent when UEFN is closed.
  mcp_map.py --find WORDS     search the saved map: tool, toolset, read/write, tested, what it does
  mcp_map.py --summary        the saved map in numbers, as JSON (the Console's Skills page shows it)
  mcp_map.py --probe FILE     dump the raw replies (to adapt the parser when Epic changes the format)
States of --now: first_snapshot, unchanged, changed (exit 0/0/1), not_reachable (2), odd_reply (3).
Never a guess: no answer or an odd reply means the saved map stays as it was.
"""
import argparse, json, os, re, socket, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import toolset_diff as td  # noqa: E402

STRICT_READ = ("get", "list", "find", "describe", "query", "search", "count", "is", "has")
INTERVAL_HOURS = 6.0


# The MCP server is on this computer: never go through a proxy configured in Windows or in the environment (a proxy answered 404 for 127.0.0.1
# and the map was reported as "odd reply" instead of "UEFN closed").
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Unreachable(Exception):
    pass


class Odd(Exception):
    pass


class Skip(Exception):
    pass


class ToolError(Exception):
    pass


def find_url(project=None):
    if os.environ.get("UEFN_MCP_URL"):
        return os.environ["UEFN_MCP_URL"]
    files = []
    if project:
        files.append(os.path.join(project, ".mcp.json"))
    files.append(os.path.join(os.path.expanduser("~"), ".claude.json"))
    for f in files:
        try:
            servers = json.load(open(f, encoding="utf-8-sig")).get("mcpServers") or {}
        except (OSError, ValueError, AttributeError):
            continue
        for name, cfg in servers.items():
            u = cfg.get("url") if isinstance(cfg, dict) else None
            if u and ("unreal" in name.lower() or "uefn" in name.lower() or "127.0.0.1" in u or "localhost" in u):
                return u
    return "http://127.0.0.1:8000/mcp"


def port_open(url, wait=0.4):
    try:
        u = urllib.parse.urlparse(url)
        s = socket.create_connection((u.hostname or "127.0.0.1", u.port or 80), wait)
        s.close()
        return True
    except (OSError, ValueError):
        return False


class Client:
    def __init__(self, url, timeout=15.0):
        self.url, self.timeout, self.sid, self.n, self.server, self.proto = url, timeout, None, 0, {}, None
        self.raw, self.limit = [], 6000

    def rpc(self, method, params=None, notify=False):
        self.n += 1
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = self.n
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        if self.proto:
            h["MCP-Protocol-Version"] = self.proto
        req = urllib.request.Request(self.url, data=json.dumps(msg).encode("utf-8"), headers=h, method="POST")
        try:
            resp = _OPENER.open(req, timeout=self.timeout)
            body = resp.read().decode("utf-8", "replace")
            ctype = resp.headers.get("Content-Type", "")
            sid = resp.headers.get("Mcp-Session-Id")
            if sid:
                self.sid = sid
        except urllib.error.HTTPError as e:
            try:
                eb = e.read().decode("utf-8", "replace")[:300]
            except Exception:  # noqa: BLE001
                eb = ""
            self.raw.append({"method": method, "params": params, "status": e.code, "body": eb})
            raise Odd("HTTP %s from the MCP server on %s%s" % (e.code, method, (": " + " ".join(eb.split())[:120]) if eb else ""))
        except (urllib.error.URLError, OSError, socket.timeout) as e:
            raise Unreachable(e.__class__.__name__)
        self.raw.append({"method": method, "params": params, "headers": {k: v for k, v in resp.headers.items() if k.lower() in ("content-type", "mcp-session-id", "mcp-protocol-version", "allow")}, "reply": body[:self.limit]})
        if notify:
            return None
        obj = None
        if "event-stream" in ctype:
            for line in body.splitlines():
                if line.startswith("data:"):
                    try:
                        o = json.loads(line[5:].strip())
                    except ValueError:
                        continue
                    if isinstance(o, dict) and o.get("id") == msg["id"]:
                        obj = o
        else:
            try:
                obj = json.loads(body)
            except ValueError:
                obj = None
        if not isinstance(obj, dict):
            raise Odd("reply to %s is not JSON-RPC" % method)
        if "error" in obj:
            raise ToolError(str(obj["error"])[:200])
        return obj.get("result") or {}

    def start(self):
        r = self.rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "uefn-dream-bot-team", "version": "1"}})
        self.server = r.get("serverInfo") or {}
        # The server names the protocol version it speaks; every later request must carry that exact version.
        self.proto = r.get("protocolVersion") if isinstance(r.get("protocolVersion"), str) else None
        try:
            self.rpc("notifications/initialized", None, notify=True)
        except Odd:
            pass  # best effort: some servers refuse the notification and still answer the requests that follow

    def list_tools(self):
        out, cursor = [], None
        for _ in range(50):
            r = self.rpc("tools/list", {"cursor": cursor} if cursor else {})
            out += [t for t in r.get("tools", []) if isinstance(t, dict) and isinstance(t.get("name"), str)]
            cursor = r.get("nextCursor")
            if not cursor:
                break
        return out

    def call(self, name, args):
        r = self.rpc("tools/call", {"name": name, "arguments": args})
        text = "\n".join(c.get("text", "") for c in r.get("content", []) if isinstance(c, dict))
        if r.get("isError"):
            raise ToolError(text[:200])
        return text


def parse_text(t):
    try:
        return json.loads(t)
    except ValueError:
        pass
    dec = json.JSONDecoder()
    for i, ch in enumerate(t):
        if ch in "[{":
            try:
                return dec.raw_decode(t[i:])[0]
            except ValueError:
                continue
    return None


def toolset_names_from_text(text):
    """list_toolsets as text: lines like '- EditorToolset.EditorAppToolset: description' (descriptions may wrap)."""
    return re.findall(r"^\s*[-*]\s+`?([A-Za-z0-9_.]+)`?\s*:", text, re.M)


def tool_entries_from_text(text):
    """describe_toolset as text: bullets '- Name: description' or headings '## Name'. Returns [] when nothing fits."""
    for pat in (r"^[-*]\s+`?([A-Za-z_][A-Za-z0-9_.]*)`?\s*(?:\([^)]*\))?\s*:\s*(.*)$", r"^#{2,4}\s+`?([A-Za-z_][A-Za-z0-9_.]*)`?\s*$"):
        found = re.findall(pat, text, re.M)
        if found:
            return [{"name": f[0] if isinstance(f, tuple) else f, "description": (f[1] if isinstance(f, tuple) and len(f) > 1 else "")} for f in found]
    return []


def looks_json(text):
    return text.lstrip()[:1] in ("{", "[")


def toolset_names(obj):
    if isinstance(obj, dict):
        for k in ("toolsets", "result", "items"):
            if k in obj:
                return toolset_names(obj[k])
        return [k for k, v in obj.items() if isinstance(v, (dict, str, int, list))]
    if isinstance(obj, list):
        out = []
        for x in obj:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                n = x.get("name") or x.get("toolset") or x.get("id")
                if isinstance(n, str):
                    out.append(n)
        return out
    return []


def tool_entries(obj):
    best = []

    def walk(o):
        nonlocal best
        if isinstance(o, list):
            ds = [x for x in o if isinstance(x, dict) and isinstance(x.get("name"), str)]
            if len(ds) > len(best):
                best = ds
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            if isinstance(o.get("tools"), list) and o["tools"] and all(isinstance(x, str) for x in o["tools"]) and len(o["tools"]) > len(best):
                best = [{"name": x} for x in o["tools"]]
            for v in o.values():
                walk(v)
    walk(obj)
    return best


def required_of(t):
    for k in ("inputSchema", "input_schema", "parameters", "schema"):
        v = t.get(k)
        if isinstance(v, dict) and ("required" in v or "properties" in v):
            return list(v.get("required") or [])
    return None


def readonly_of(t):
    a = t.get("annotations")
    if isinstance(a, dict) and "readOnlyHint" in a:
        return bool(a["readOnlyHint"])
    return None


def fetch(client, deadline):
    """Return (catalog {Toolset/Tool: description}, entries {key: info}, mode, meta)."""
    client.start()
    tools = client.list_tools()
    names = {t["name"]: t for t in tools}
    entries, catalog = {}, {}
    if "list_toolsets" in names and "describe_toolset" in names:
        lt = client.call("list_toolsets", {})
        sets = toolset_names(parse_text(lt)) if looks_json(lt) else toolset_names_from_text(lt)
        if not sets:
            raise Odd("list_toolsets returned no toolsets")
        dprops = ((names["describe_toolset"].get("inputSchema") or {}).get("properties") or {})
        dreq = (names["describe_toolset"].get("inputSchema") or {}).get("required") or []
        pkey = (dreq or list(dprops) or ["name"])[0]
        for ts in sets:
            if time.time() > deadline:
                raise Odd("ran out of time before all toolsets were read")
            try:
                dt = client.call("describe_toolset", {pkey: ts})
                got = tool_entries(parse_text(dt)) if looks_json(dt) else tool_entries_from_text(dt)
            except ToolError:
                got = []
            for t in got:
                key = "%s/%s" % (ts, td.short(t["name"]))
                catalog[key] = str(t.get("description", ""))
                entries[key] = {"toolset": ts, "name": td.short(t["name"]), "required": required_of(t), "readonly": readonly_of(t),
                                "schema": t.get("inputSchema") if isinstance(t.get("inputSchema"), dict) else None}
        mode, meta = "meta", names.get("call_tool")
    else:
        for t in tools:
            ts = t["name"].split(".")[0] if "." in t["name"] else (t["name"].split("__")[0] if "__" in t["name"] else "server")
            key = "%s/%s" % (ts, td.short(t["name"]))
            catalog[key] = str(t.get("description", ""))
            entries[key] = {"toolset": ts, "name": td.short(t["name"]), "call": t["name"], "required": required_of(t), "readonly": readonly_of(t),
                             "schema": t.get("inputSchema") if isinstance(t.get("inputSchema"), dict) else None}
        mode, meta = "direct", None
    if not catalog:
        raise Odd("no tools found in the replies")
    return catalog, entries, mode, meta


def safe_to_call(e):
    if e["readonly"] is False or e["required"] is None or e["required"]:
        return False
    if e["readonly"] is True:
        return True
    first = td.re.split(r"[_\s]|(?<=[a-z0-9])(?=[A-Z])", e["name"].strip("_"))[0].lower()
    return first in STRICT_READ


def run_tests(client, entries, mode, meta, deadline, cap=150):
    res, skipped = {}, 0
    props = ((meta or {}).get("inputSchema") or {}).get("properties") or {}
    low = {k.lower(): k for k in props}
    tkey = next((low[k] for k in low if "toolset" in k), None)
    nkey = next((low[k] for k in low if k in ("tool", "tool_name", "toolname", "name")), None)
    akey = next((low[k] for k in low if any(w in k for w in ("arg", "param", "input"))), None)
    for key in sorted(entries):
        e = entries[key]
        if not safe_to_call(e):
            skipped += 1
            continue
        if len(res) >= cap or time.time() > deadline:
            break
        try:
            if mode == "direct":
                client.call(e.get("call", e["name"]), {})
            else:
                if not (tkey and nkey and meta):
                    raise Skip("call shape unknown")
                payload = {tkey: e["toolset"], nkey: e["name"]}
                if akey:
                    payload[akey] = {}
                client.call(meta["name"], payload)
            res[key] = "ok"
        except Skip:
            return res, skipped, "The call_tool shape is unknown, so nothing was tested (use --probe to see it)."
        except ToolError as ex:
            res[key] = "err: " + str(ex)[:80]
        except (Odd, Unreachable):
            res[key] = "err: no answer"
    return res, skipped, ""


NEVER_DEEP = set("capture screenshot export download render generate compile build save open load python execute run play start stop push delete remove set add create rename move replace duplicate import spawn".split())


def sample_value(sch, depth=0):
    """A harmless made-up value for a JSON-schema fragment. Real data is never guessed: the point is to see whether the tool answers."""
    if not isinstance(sch, dict):
        return ""
    if "default" in sch:
        return sch["default"]
    if sch.get("enum"):
        return sch["enum"][0]
    if sch.get("examples"):
        return sch["examples"][0]
    t = sch.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if t in ("integer", "number"):
        return 0
    if t == "boolean":
        return False
    if t == "array":
        return []
    if t == "object" or "properties" in sch:
        out = {}
        if depth < 3:
            props = sch.get("properties") or {}
            for k in sch.get("required") or []:
                out[k] = sample_value(props.get(k, {}), depth + 1)
        return out
    return ""


def sample_args(schema, name="", toolset=""):
    props = (schema or {}).get("properties") or {}
    args = {}
    cls = toolset.split(".")[-1]
    for k in (schema or {}).get("required") or []:
        sch = props.get(k, {})
        if cls and sch.get("default") == cls:
            sch = {kk: vv for kk, vv in sch.items() if kk != "default"}  # the generator put the class name as a placeholder default
        v = sample_value(sch)
        if v == "" and re.search(r"categor", k, re.I):
            v = "LogTemp"
        if v == "" and re.search(r"path|folder|dir", k, re.I):
            v = "/Game"
        args[k] = v
    return args


def deep_candidates(entries):
    out = {}
    for key, e in entries.items():
        words = [w.lower() for w in td.re.split(r"[_\s]|(?<=[a-z0-9])(?=[A-Z])", e["name"].strip("_")) if w]
        if e.get("readonly") is False or "Python" in e.get("toolset", "") or not words or NEVER_DEEP & set(words):
            continue
        first = words[0]
        if e.get("readonly") is True or first in STRICT_READ:
            out[key] = e
    return out


def _fingerprints(d):
    import hashlib
    r = {}
    for n in ("latest.json", "MAP.md", "tests.json", "news.json", "NEWS.md", "auto.json"):
        try:
            r[n] = hashlib.sha256(open(os.path.join(d, n), "rb").read()).hexdigest()[:12]
        except OSError:
            r[n] = ""
    return r


def deep_test(project=None, url=None, dirpath=None, timeout=20.0, budget=170.0, pause=0.15, heavy_too=False):
    """Calls every read-only tool once with harmless made-up arguments. Writes ONLY deep-tests.json and DEEP-TESTS.md; the map is never touched."""
    d = dirpath or td.default_dir()
    url = url or find_url(project)
    client = Client(url, timeout)
    deadline = time.time() + budget
    try:
        catalog, entries, mode, meta = fetch(client, deadline)
    except Unreachable as e:
        return {"state": "not_reachable", "message": "UEFN's MCP did not answer (%s)." % e}, 2
    except (Odd, ToolError) as e:
        return {"state": "odd_reply", "message": str(e)}, 3
    before = _fingerprints(d)
    props = ((meta or {}).get("inputSchema") or {}).get("properties") or {}
    low = {k.lower(): k for k in props}
    tkey = next((low[k] for k in low if "toolset" in k), None)
    nkey = next((low[k] for k in low if k in ("tool", "tool_name", "toolname", "name")), None)
    akey = next((low[k] for k in low if any(w in k for w in ("arg", "param", "input"))), None)
    cands = deep_candidates(entries)
    heavy = []
    if not heavy_too:
        try:
            prev = json.load(open(os.path.join(d, "deep-tests.json"), encoding="utf-8")).get("results", {})
            heavy = sorted(k for k, v in prev.items() if v.get("n", 0) > 1000000 and k in cands)
        except (OSError, ValueError):
            pass
        for k in heavy:
            cands.pop(k)
    res, silent, stopped = {}, 0, ""
    for key in sorted(cands):
        e = cands[key]
        if time.time() > deadline:
            stopped = "time budget reached"
            break
        if silent >= 3:
            stopped = "three silent answers in a row: UEFN may be busy, stopped on purpose"
            break
        args = sample_args(e.get("schema"), e["name"], e.get("toolset", ""))
        try:
            if mode == "direct":
                out = client.call(e.get("call", e["name"]), args)
            else:
                if not (tkey and nkey and akey and meta):
                    stopped = "call shape unknown"
                    break
                out = client.call(meta["name"], {tkey: e["toolset"], nkey: e["name"], akey: args})
            res[key] = {"r": "ok", "args": sorted(args), "n": len(out), "peek": " ".join(out.split())[:100]}
            silent = 0
        except ToolError as ex:
            res[key] = {"r": "rejected", "args": sorted(args), "why": " ".join(str(ex).split())[:140]}
            silent = 0
        except (Odd, Unreachable) as ex:
            res[key] = {"r": "no_answer", "args": sorted(args), "why": str(ex)[:100]}
            silent += 1
        time.sleep(pause)
    after = _fingerprints(d)
    cnt = {k: sum(1 for v in res.values() if v["r"] == k) for k in ("ok", "rejected", "no_answer")}
    out = {"state": "deep_done", "date": time.strftime("%Y-%m-%d %H:%M"), "candidates": len(cands), "tried": len(res), "counts": cnt,
           "stopped": stopped, "skipped_heavy": heavy, "map_untouched": before == after, "results": res}
    for k in heavy:
        res.setdefault(k, {"r": "ok", "args": [], "n": 1000001, "peek": "(skipped: answer was over 1 MB last time)"})
    try:
        os.makedirs(d, exist_ok=True)
        json.dump(out, open(os.path.join(d, "deep-tests.json"), "w", encoding="utf-8"), indent=1)
        lines = ["# Deep test of read-only tools", "", "Made %s. ok = answered; rejected = answered with an error about the made-up arguments (the tool is alive); no_answer = silent." % out["date"], "",
                 "%d tried of %d candidates: %d ok, %d rejected, %d no answer. %s" % (len(res), len(cands), cnt["ok"], cnt["rejected"], cnt["no_answer"], stopped), "",
                 "| Tool | Result | Note |", "|---|---|---|"]
        for k, v in sorted(res.items()):
            lines.append("| %s | %s | %s |" % (k, v["r"], (v.get("peek") or v.get("why") or "").replace("|", "/")[:90]))
        open(os.path.join(d, "DEEP-TESTS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    except OSError:
        pass
    out.pop("results")
    return out, 0


def _note_error(d, text):
    try:
        os.makedirs(d, exist_ok=True)
        a = os.path.join(d, "auto.json")
        data = {}
        if os.path.isfile(a):
            data = json.load(open(a, encoding="utf-8"))
        data["last_error"] = {"when": time.strftime("%Y-%m-%d %H:%M"), "text": text[:300]}
        json.dump(data, open(a, "w", encoding="utf-8"))
    except (OSError, ValueError):
        pass


def now(project=None, url=None, dirpath=None, timeout=15.0, tests=True, budget=100.0):
    d = dirpath or td.default_dir()
    url = url or find_url(project)
    client = Client(url, timeout)
    deadline = time.time() + budget
    try:
        catalog, entries, mode, meta = fetch(client, deadline)
    except Unreachable as e:
        _note_error(d, "not_reachable: %s" % e)
        return {"state": "not_reachable", "message": "UEFN's MCP did not answer (%s). The saved map stays as it was." % e}, 2
    except (Odd, ToolError) as e:
        _note_error(d, "odd_reply: %s" % e)
        try:
            client.limit = 20000
            json.dump(client.raw, open(os.path.join(d, "last-odd.json"), "w", encoding="utf-8"), indent=1)
        except OSError:
            pass
        return {"state": "odd_reply", "message": "The MCP answered in a way this kit does not understand (%s). The saved map stays as it was; run --probe to see the raw replies." % e}, 3
    res, code = td.apply_map(catalog, d, str(client.server.get("version", "")), True, str(client.server.get("name", "")))
    res["mode"] = mode
    note = ""
    if tests:
        results, skipped, note = run_tests(client, entries, mode, meta, deadline)
        tp = os.path.join(d, "tests.json")
        try:
            before = json.load(open(tp, encoding="utf-8")).get("results", {})
        except (OSError, ValueError, AttributeError):
            before = {}
        broke = sorted(k for k, v in results.items() if v != "ok" and before.get(k) == "ok")
        res["tests"] = {"tried": len(results), "ok": sum(1 for v in results.values() if v == "ok"), "failed": sum(1 for v in results.values() if v != "ok"), "not_called": skipped, "stopped_working": broke}
        if note:
            res["tests"]["note"] = note
        try:
            os.makedirs(d, exist_ok=True)
            merged = dict(before)
            merged.update(results)
            for k in [k for k in merged if k not in catalog]:
                del merged[k]
            json.dump({"date": time.strftime("%Y-%m-%d"), "results": merged}, open(tp + ".tmp", "w", encoding="utf-8"), indent=1)
            os.replace(tp + ".tmp", tp)
            if broke:
                with open(os.path.join(d, "NEWS.md"), "a", encoding="utf-8", newline="\n") as f:
                    f.write("\n## Stopped working (%d)\n\n" % len(broke) + "\n".join("- `%s`: %s" % (k, results[k]) for k in broke) + "\n")
                open(os.path.join(d, "NEWS.pending"), "w").write(time.strftime("%Y-%m-%d"))
                try:
                    nj = json.load(open(os.path.join(d, "news.json"), encoding="utf-8"))
                except (OSError, ValueError):
                    nj = {"date": time.strftime("%Y-%m-%d"), "state": "tests", "added": [], "added_total": 0, "removed_total": 0, "changed_total": 0}
                nj["stopped_working"] = broke
                json.dump(nj, open(os.path.join(d, "news.json"), "w", encoding="utf-8"))
                code = 1
        except OSError:
            pass
    try:
        a = os.path.join(d, "auto.json")
        data = {}
        if os.path.isfile(a):
            data = json.load(open(a, encoding="utf-8"))
        data["last_full"] = time.time()
        data.pop("last_error", None)
        json.dump(data, open(a, "w", encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return res, code


def session_check(project=None, dirpath=None, url=None, interval_hours=INTERVAL_HOURS):
    """Called at session start. Returns a message for the agent or None. Never raises, never waits for the MCP."""
    try:
        d = dirpath or td.default_dir()
        msg = None
        pend = os.path.join(d, "NEWS.pending")
        if os.path.isfile(pend):
            first = ""
            try:
                first = open(os.path.join(d, "NEWS.md"), encoding="utf-8").read().splitlines()[2]
            except (OSError, IndexError):
                pass
            os.remove(pend)
            msg = ("MCP news: %s Read %s (NEWS.md) and, in your FIRST reply, tell the owner in two short lines what is new and what it could do for their maps. "
                   "Propose only; change nothing because of it." % (first, d))
        url = url or find_url(project)
        a = os.path.join(d, "auto.json")
        data = {}
        try:
            data = json.load(open(a, encoding="utf-8"))
        except (OSError, ValueError):
            pass
        due = time.time() - max(data.get("last_full", 0), data.get("last_try", 0)) > interval_hours * 3600
        if due and port_open(url):
            os.makedirs(d, exist_ok=True)
            data["last_try"] = time.time()
            json.dump(data, open(a, "w", encoding="utf-8"))
            cmd = [sys.executable, os.path.abspath(__file__), "--now", "--quiet", "--url", url, "--dir", d]
            kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "stdin": subprocess.DEVNULL}
            if os.name == "nt":
                kw["creationflags"] = 0x00000008 | 0x08000000
            else:
                kw["start_new_session"] = True
            subprocess.Popen(cmd, **kw)
        return msg
    except Exception:  # noqa: BLE001
        return None


def summary(dirpath=None):
    """What the Console shows: counts, kit coverage, test results and the latest news. Reads saved files only; never raises."""
    d = dirpath or td.default_dir()
    try:
        m = json.load(open(os.path.join(d, "latest.json"), encoding="utf-8"))
        tools = m["tools"]
    except (OSError, ValueError, KeyError):
        err = None
        try:
            err = json.load(open(os.path.join(d, "auto.json"), encoding="utf-8")).get("last_error")
        except (OSError, ValueError):
            pass
        why = "No map yet. The kit makes it by itself the first time a session starts with UEFN open (or run /mcp-snapshot)."
        if err:
            why = "No map yet. The last attempt (%s) failed: %s" % (err.get("when", ""), err.get("text", ""))
        return {"available": False, "reason": why, "last_error": err}
    known = td.kit_known()
    used = sum(1 for k in tools if td.is_known(k, known))
    out = {"available": True, "saved": m.get("saved", ""), "uefn_version": m.get("uefn_version", ""), "count": len(tools),
           "toolsets": len({k.split("/")[0] for k in tools if "/" in k}), "kit_uses": used, "kit_uses_pct": round(100.0 * used / max(1, len(tools)), 1),
           "read": sum(1 for e in tools.values() if e.get("a") == "read"), "write": sum(1 for e in tools.values() if e.get("a") == "write")}
    try:
        t = json.load(open(os.path.join(d, "tests.json"), encoding="utf-8"))
        r = t.get("results", {})
        out["tests"] = {"date": t.get("date", ""), "ok": sum(1 for v in r.values() if v == "ok"), "failed": sum(1 for v in r.values() if v != "ok"),
                        "failed_names": [td.short(k) + " (" + str(v)[:60] + ")" for k, v in sorted(r.items()) if v != "ok"][:8]}
    except (OSError, ValueError):
        out["tests"] = None
    try:
        out["news"] = json.load(open(os.path.join(d, "news.json"), encoding="utf-8"))
    except (OSError, ValueError):
        out["news"] = None
    try:
        out["last_full"] = json.load(open(os.path.join(d, "auto.json"), encoding="utf-8")).get("last_full", 0)
    except (OSError, ValueError):
        out["last_full"] = 0
    try:
        import recipes_status
        out["recipes"] = recipes_status.progress(tools=list(tools)) or None
    except Exception:
        out["recipes"] = None
    return out


def lab_known():
    """What the lab learned about each tool (mcp-known-tools.json, built by tool/build_known_tools.py). {} if absent."""
    try:
        return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp-known-tools.json"), encoding="utf-8")).get("tools", {})
    except (OSError, ValueError):
        return {}


def lab_text(row):
    """' | lab: ok' / ' | lab: refused (why) | ask the owner first' - empty when the lab knows nothing."""
    if not row:
        return ""
    s = row.get("s", "never")
    out = " | lab: " + {"never": "not tried"}.get(s, s) + (" (%s)" % row["why"] if row.get("why") else "")
    return out + (" | ask the owner first" if row.get("c") else "")


def find(words, dirpath=None, limit=25):
    d = dirpath or td.default_dir()
    try:
        tools = json.load(open(os.path.join(d, "latest.json"), encoding="utf-8"))["tools"]
    except (OSError, ValueError, KeyError):
        lab = lab_known()
        if not lab:
            print("No MCP map yet. With UEFN open run: mcp_map.py --now")
            return 2
        # no live map on this computer yet: search the names the kit already knows (388 tools, name + area + lab status)
        ws = [w.lower() for w in words]
        hits = sorted(((-sum(1 for w in ws if w in (k + " " + str(e.get("a", ""))).lower()), k) for k, e in lab.items()))
        hits = [h for h in hits if h[0]]
        print("(no live map yet: names known to the kit; run mcp_map.py --now with UEFN open for descriptions)")
        for _, k in hits[:limit]:
            print("%s | %s%s" % (k, lab[k].get("a", "?"), lab_text(lab[k])))
        if not hits:
            print("No known tool matches %s." % " ".join(words))
        return 0
    try:
        tested = json.load(open(os.path.join(d, "tests.json"), encoding="utf-8")).get("results", {})
    except (OSError, ValueError):
        tested = {}
    known = td.kit_known()
    lab = lab_known()
    ws = [w.lower() for w in words]
    scored = []
    for k, e in tools.items():
        text = (k + " " + e.get("d", "")).lower()
        n = sum(1 for w in ws if w in text)
        if n:
            scored.append((-n, k))
    scored.sort()
    for _, k in scored[:limit]:
        e = tools[k]
        t = tested.get(k)
        print("%s | %s | %s%s%s | %s" % (k, e.get("a", "?"), "tested ok" if t == "ok" else ("test failed" if t else "not tested"), " | kit uses it" if td.is_known(k, known) else "", lab_text(lab.get(k)), e.get("d", "")))
    if not scored:
        print("No tool matches %s in the map (%d tools)." % (" ".join(words), len(tools)))
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--find", nargs="+", metavar="WORD")
    ap.add_argument("--probe", metavar="FILE")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--heavy", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--url")
    ap.add_argument("--dir")
    ap.add_argument("--project")
    ap.add_argument("--timeout", type=float, default=15.0)
    a = ap.parse_args()
    if a.summary:
        print(json.dumps(summary(a.dir), ensure_ascii=True))
        return 0
    if a.find:
        return find(a.find, a.dir)
    if a.probe:
        c = Client(a.url or find_url(a.project), a.timeout)
        c.limit = 200000
        try:
            c.start()
            tools = c.list_tools()
            if any(t["name"] == "list_toolsets" for t in tools):
                lt = c.call("list_toolsets", {})
                sets = toolset_names(parse_text(lt)) if looks_json(lt) else toolset_names_from_text(lt)
                dtool = next((t for t in tools if t["name"] == "describe_toolset"), {})
                props = (dtool.get("inputSchema") or {}).get("properties") or {}
                req = (dtool.get("inputSchema") or {}).get("required") or []
                pkey = (req or list(props) or ["name"])[0]
                for ts in sets[:3]:
                    c.call("describe_toolset", {pkey: ts})
        except (Unreachable, Odd, ToolError) as e:
            c.raw.append({"error": str(e)})
        json.dump(c.raw, open(a.probe, "w", encoding="utf-8"), indent=1)
        print("raw replies written to %s" % a.probe)
        return 0
    if a.auto:
        m = session_check(a.project, a.dir, a.url)
        print(json.dumps({"state": "checked", "news": m or ""}))
        return 0
    if a.deep:
        res, code = deep_test(a.project, a.url, a.dir, max(a.timeout, 20.0), heavy_too=a.heavy)
        print(json.dumps(res, ensure_ascii=True))
        return code
    res, code = now(a.project, a.url, a.dir, a.timeout, not a.no_tests)
    if not a.quiet:
        print(json.dumps(res, ensure_ascii=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
