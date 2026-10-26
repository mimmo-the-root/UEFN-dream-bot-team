"""Console endpoints for sharing lessons: state, switch, export; same routes in the PowerShell server; the page carries the published-map note."""
import json, os, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
env = dict(os.environ, UEFN_SKILLS_DIR=os.path.join(d, "skills"))
srv = subprocess.Popen([sys.executable, os.path.join(hooks, "agent-console-server.py"), str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
base = "http://127.0.0.1:%d" % port


def call(path, body=None, headers=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers=dict({"Content-Type": "application/json"}, **(headers or {})))
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


try:
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/session", timeout=1); break
        except Exception:
            time.sleep(0.2)
    A = {"X-Skills-Action": "1"}
    c, st = call("/community-state")
    ok(c == 200 and st.get("share") is True and "published" in st, "GET /community-state: switch on by default, published state reported")
    c, r = call("/community-act", {"action": "on"})
    ok(c == 403, "POST without the action header is refused")
    c, r = call("/community-act", {"action": "on"}, dict(A, Origin="http://evil.example"))
    ok(c == 403, "POST from another origin is refused")
    c, r = call("/community-act", {"action": "on"}, A)
    ok(c == 200 and r.get("share") is True and call("/community-state")[1]["share"] is True, "POST on turns the switch on")
    c, r = call("/community-act", {"action": "export", "genre": "survival", "id": "p-000000000000"}, A)
    ok(c in (200, 400) and r.get("ok") is False, "export of an unknown lesson is refused")
    c, r = call("/community-act", {"action": "export", "genre": "../../etc", "id": "p-000000000000"}, A)
    ok(c in (200, 400) and not r.get("ok"), "a genre that is not a listed slug is refused, no path is built from it")
    c, r = call("/community-act", {"action": "nope"}, A)
    ok(c in (200, 400) and r.get("ok") is False, "unknown action refused")
    c, r = call("/community-act", {"action": "off"}, A)
    ok(r.get("share") is False, "POST off turns it off again")
    c, r = call("/community-summary")
    ok(c == 200 and isinstance(r, dict), "GET /community-summary answers (empty object until the release ships one)")
finally:
    srv.terminate()
ps1 = open(os.path.join(hooks, "agent-console-server.ps1"), encoding="utf-8-sig").read()
for route in ("/community-state", "/community-act", "/community-summary"):
    ok(route in ps1, "the PowerShell server has the route %s" % route)
html = open(os.path.join(hooks, "agent-console-skills.html"), encoding="utf-8").read()
ok("Only lessons learned from a published map can be shared" in html and "stay on this computer" in html, "the Skills page carries the published-map note")
ok('id="kCommunity"' in html and "/community-act" in html and "/community-state" in html, "the Skills page has the community section wired to the endpoints")
