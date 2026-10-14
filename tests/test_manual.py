"""The HTML manual: sources build to the shipped output, links resolve, no external assets, servers route it, console pages link to it."""
import os, re, subprocess, sys, time, urllib.request, urllib.error
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
man = os.path.join(hooks, "manual")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
rd = lambda p: open(p, encoding="utf-8-sig").read()

r = subprocess.run([sys.executable, os.path.join(root, "tool", "build_manual.py"), "--check"], capture_output=True, text=True)
ok(r.returncode == 0, "the shipped manual matches its sources (run tool/build_manual.py if not)")
import json
cfg = json.load(open(os.path.join(root, "docs", "manual", "manual.json"), encoding="utf-8"))
slugs = [c for p in cfg["parts"] for c in p["chapters"]]
ok(all(os.path.isfile(os.path.join(man, s + ".html")) for s in slugs) and os.path.isfile(os.path.join(man, "index.html")), "every chapter and the index are generated")
ver = rd(os.path.join(root, "project-template", "Claude", "KIT-VERSION")).strip()
ok(ver in rd(os.path.join(man, "index.html")), "the manual states the kit version")
for f in sorted(os.listdir(man)):
    if not f.endswith(".html"):
        continue
    t = rd(os.path.join(man, f))
    ok("<script" not in t and not re.search(r'(src="https?://|<link[^>]*href="https?://|url\(https?://)', t), "%s: no script and no external assets" % f)
    for href in re.findall(r'href="([^"#:]+\.html)(?:#[^"]*)?"', t):
        ok(os.path.isfile(os.path.join(man, href)), "%s: link %s resolves" % (f, href))
    for href, anchor in re.findall(r'href="([^"#:]+\.html)#([^"]+)"', t):
        ok('id="%s"' % anchor in rd(os.path.join(man, href)), "%s: anchor %s#%s exists" % (f, href, anchor))
for page in ("agent-console.html", "agent-console-stats.html", "agent-console-docs.html", "agent-console-flow.html", "agent-console-skills.html", "agent-console-news.html"):
    t = rd(os.path.join(hooks, page))
    m = re.search(r'href="/manual/([a-z-]+\.html)(#[^"]*)?" data-manual-help', t)
    ok(m is not None, "%s links to its manual chapter" % page)
    ok(m.group(1) in os.listdir(man) and (not m.group(2) or 'id="%s"' % m.group(2)[1:] in rd(os.path.join(man, m.group(1)))), "%s: the help link target exists" % page)
    ok("github.com/mimmo-the-root/UEFN-dream-bot-team" in t and "MIT License" in t and "x.com/mimmo_the_root" in t, "%s carries the repo, MIT and author footer" % page)
ps1 = rd(os.path.join(hooks, "agent-console-server.ps1"))
ok("/manual" in ps1 and "manualDir" in ps1, "the PowerShell server routes /manual")

port = 18700 + os.getpid() % 200
p = subprocess.Popen([sys.executable, os.path.join(hooks, "agent-console-server.py"), str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    base = "http://127.0.0.1:%d" % port
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/manual/", timeout=1); break
        except Exception:
            time.sleep(0.1)
    def get(path):
        try:
            x = urllib.request.urlopen(base + path, timeout=3); return x.status, x.headers.get("Content-Type", ""), x.read()
        except urllib.error.HTTPError as e:
            return e.code, "", b""
    s, ct, body = get("/manual/")
    ok(s == 200 and "text/html" in ct and b"the manual" in body, "GET /manual/ serves the index")
    s, ct, _ = get("/manual/manual.css"); ok(s == 200 and "text/css" in ct, "GET /manual/manual.css serves the stylesheet")
    ok(get("/manual/your-team.html")[0] == 200, "GET a chapter works")
    ok(get("/manual/..%2Fagent-console-server.py")[0] == 404 and get("/manual/../agent-console-server.py")[0] in (404, 400), "path traversal is refused")
    ok(get("/manual/nothing.html")[0] == 404, "an unknown page is a 404")
finally:
    p.terminate()
