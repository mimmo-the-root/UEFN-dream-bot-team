"""T-089: GET /config and POST /config of the console server (temp project, ephemeral port, localhost only)."""
import importlib.util, json, os, sys, tempfile, threading, http.server, socketserver, urllib.request, urllib.error
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hooks = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, os.path.join(root, "tools"))
tmp = tempfile.mkdtemp(prefix="cfgep_")
os.environ["KIT_GLOBAL_SETTINGS"] = os.path.join(tmp, "global.json")
os.environ["CLAUDE_PROJECT_DIR"] = tmp
spec = importlib.util.spec_from_file_location("console_server", os.path.join(hooks, "agent-console-server.py"))
srv = importlib.util.module_from_spec(spec)
saved_argv = sys.argv
sys.argv = ["x", "0"]
spec.loader.exec_module(srv)
sys.argv = saved_argv
srv.PROJECT_DIR = tmp


class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


httpd = S(("127.0.0.1", 0), srv.Handler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port
fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def call(method, path, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


OK = {"X-Router-Action": "1"}
try:
    c, d = call("GET", "/config")
    items = {i["key"]: i for i in d.get("settings", [])}
    check("get lists settings with descriptions", c == 200 and "debug.exchange_log" in items and items["debug.exchange_log"]["description"] and "console.palette" in items)
    c, d = call("POST", "/config", {"key": "console.palette", "value": "light"}, OK)
    check("valid set answers the new value", c == 200 and d["value"] == "light" and d["old"] == "dark")
    c, d = call("GET", "/config")
    check("get shows the change", {i["key"]: i for i in d["settings"]}["console.palette"]["value"] == "light")
    c, d = call("POST", "/config", {"key": "debug.exchange_log", "value": "errors"}, OK)
    check("debug level accepted", c == 200 and d["value"] == "errors")
    c, d = call("POST", "/config", {"key": "nope.key", "value": 1}, OK)
    check("unknown key rejected", c == 400 and not d["ok"])
    c, d = call("POST", "/config", {"key": "console.palette", "value": "pink"}, OK)
    check("invalid value rejected", c == 400)
    c, d = call("POST", "/config", {"key": "console.page_size", "value": "20"}, OK)
    check("wrong type rejected", c == 400)
    c, d = call("POST", "/config", {"key": "budget.weekly_used_pct", "value": 5}, OK)
    check("owner-only key rejected", c == 400)
    c, d = call("POST", "/config", {"key": "console.palette", "value": "dark"})
    check("missing header forbidden", c == 403)
    c, d = call("POST", "/config", {"key": "console.palette", "value": "dark"}, dict(OK, Origin="http://evil.example"))
    check("foreign origin forbidden", c == 403)
    check("rejected calls changed nothing", srv._kit_config_mod().get("console.palette", tmp) == "light")
    kc = srv._kit_config_mod()
    kc._set_raw("safety_check.mode", "on", tmp)
    c, d = call("POST", "/config", {"key": "safety_check.mode", "value": "off"}, OK)
    check("risky key without confirm refused", c == 403 and kc.get("safety_check.mode", tmp) == "on")
    c, d = call("POST", "/config", {"key": "safety_check.mode", "value": "off", "confirm": True}, OK)
    check("risky key with confirm changes", c == 200 and kc.get("safety_check.mode", tmp) == "off")
    h = kc.history(50, tmp)
    last = [e for e in h if e["key"] == "console.palette"]
    check("change logged in config-changes.log", os.path.isfile(os.path.join(tmp, "Claude", "logs", "config-changes.log")) and last and last[-1]["new"] == "light" and last[-1]["scope"] == "project" and len(last) == 1)
finally:
    httpd.shutdown()
sys.exit(1 if fails else 0)
