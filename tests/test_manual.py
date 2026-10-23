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
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t)
    ok(all(json.loads(b) for b in blocks) and len(blocks) == 1, "%s: one JSON-LD block for search engines, valid JSON" % f)
    t2 = re.sub(r'<script type="application/ld\+json">.*?</script>', "", t)
    t2 = re.sub(r'<link rel="canonical"[^>]*>', "", t2)  # a canonical link points at the public page; it loads nothing
    ok("<script" not in t2 and not re.search(r'(src="https?://|<link[^>]*href="https?://|url\(https?://)', t2), "%s: no script and no external assets" % f)
    ok(re.search(r'<meta name="description" content="[^"]{60,200}">', t) and '<link rel="canonical"' in t, "%s: has a description of 60-200 characters and a canonical link" % f)
    for href in re.findall(r'href="([^"#:]+\.html)(?:#[^"]*)?"', t):
        ok(os.path.isfile(os.path.join(man, href)), "%s: link %s resolves" % (f, href))
    for href, anchor in re.findall(r'href="([^"#:]+\.html)#([^"]+)"', t):
        ok('id="%s"' % anchor in rd(os.path.join(man, href)), "%s: anchor %s#%s exists" % (f, href, anchor))
for page in ("agent-console.html", "agent-console-stats.html", "agent-console-docs.html", "agent-console-flow.html", "agent-console-skills.html", "agent-console-news.html"):
    t = rd(os.path.join(hooks, page))
    m = re.search(r'href="/manual/([a-z-]+\.html)(#[^"]*)?" data-manual-help', t)
    ok(m is not None, "%s links to its manual chapter" % page)
    ok(m.group(1) in os.listdir(man) and (not m.group(2) or 'id="%s"' % m.group(2)[1:] in rd(os.path.join(man, m.group(1)))), "%s: the help link target exists" % page)
    ok('class="kit-logo"' in t and 'rel="icon"' in t, "%s shows the logo and has a tab icon" % page)
    ok("github.com/mimmo-the-root/UEFN-dream-bot-team" in t and "MIT License" in t and "x.com/mimmo_the_root" in t, "%s carries the repo, MIT and author footer" % page)
ps1 = rd(os.path.join(hooks, "agent-console-server.ps1"))
ok("/manual" in ps1 and "manualDir" in ps1, "the PowerShell server routes /manual")

# alignment: the manual must keep up with the kit (a new agent, skill or console page without a mention fails here)
srcdir = os.path.join(root, "docs", "manual")
md = lambda n: rd(os.path.join(srcdir, n + ".md"))
agents = sorted(f[:-3] for f in os.listdir(os.path.join(root, "user-level-agents")) if f.endswith(".md"))
team = md("your-team")
ok(all("`%s`" % a in team or "**%s**" % a in team or a in team for a in agents), "every agent is described in Your team (%d agents)" % len(agents))
ok(len(agents) == 22 and len([a for a in agents if a.startswith("mcp-")]) == 5 and "17 agents" in md("quick-start") and "17 agents" in rd(os.path.join(srcdir, "manual.json")), "the manual says 17 agents (+5 MCP sub-agents), and there are %d files" % len(agents))
skills = sorted(d for d in os.listdir(os.path.join(root, "user-level-skills")) if os.path.isdir(os.path.join(root, "user-level-skills", d)))
cat = md("skill-catalog") + md("skills-and-lessons")
ok(all(sk in cat for sk in skills), "every user-level skill is in the Skills catalog")
con = md("the-console")
ok(all(("## " + n) in con for n in ("Console", "Stats", "Docs", "Flow", "Skills", "What's new")), "every console page has a section in The console")
for f in sorted(os.listdir(srcdir)):
    if f.endswith(".md"):
        for img in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md(f[:-3])):
            ok(os.path.isfile(os.path.join(srcdir, "images", img)), "%s: image %s exists" % (f, img))
for f in os.listdir(os.path.join(srcdir, "images")):
    ok(os.path.getsize(os.path.join(srcdir, "images", f)) < 400 * 1024, "images/%s stays under 400 KB (it ships to every project)" % f)

pg = rd(os.path.join(root, ".github", "workflows", "pages.yml"))
ok("deploy-pages" in pg and "build_manual.py --check" in pg and "Back to the console" in pg, "the GitHub Pages workflow checks the build and publishes the manual without the local-console link")
sg = rd(os.path.join(root, "SETUP-GUIDE.md"))
ok(len(sg.splitlines()) < 40 and "github.io/UEFN-dream-bot-team" in sg, "SETUP-GUIDE.md stays a short pointer to the manual")

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
    s, ct, body = get("/manual/shot-console.png"); ok(s == 200 and ct == "image/png" and body[:4] == b"\x89PNG", "GET a screenshot serves a PNG")
    ok(get("/manual/..%2Fagent-console-server.py")[0] == 404 and get("/manual/../agent-console-server.py")[0] in (404, 400), "path traversal is refused")
    ok(get("/manual/nothing.html")[0] == 404, "an unknown page is a 404")
finally:
    p.terminate()
