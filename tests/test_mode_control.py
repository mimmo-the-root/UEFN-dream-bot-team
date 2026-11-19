#!/usr/bin/env python3
"""T-061/T-062: the Free / Paid / Mixed mode control (pure mapping + fake-fetch) on the Models page and in the header of every console page."""
import glob, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
node = shutil.which("node")
if not node:
    print("test_mode_control: skipped (node not found)")
    sys.exit(0)
pages = sorted(glob.glob(os.path.join(HOOKS, "agent-console*.html")))
blocks = set()
for p in pages:
    html = open(p, encoding="utf-8").read()
    m = re.search(r"/\*kh-mode:begin\*/.*?/\*kh-mode:end\*/", html, re.S)
    assert m, os.path.basename(p) + ": mode block missing"
    blocks.add(m.group(0))
    if p.endswith("agent-console-models.html"):
        assert 'data-v="free"' in html and 'data-v="paid"' in html and 'data-v="mixed"' in html and 'data-v="safe"' in html, "models buttons"
        assert 'data-v="plan"' not in html.split('id="def"')[1].split("</div>")[0]
    # every inline script must still parse
    for i, sc in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
        r = subprocess.run([node, "--check", "-"], input=sc, capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, "%s script %d: %s" % (os.path.basename(p), i, r.stderr[:300])
assert len(blocks) == 1, "the mode block differs between pages"
code = "var window={};\n" + blocks.pop() + """
var out={};
out.map=["free","paid","mixed","safe","bogus"].map(khModeToRouter);
out.ui=["free","paid","plan","auto","safe","x"].map(khModeToUi);
var calls=[];
function fake(status,body){return function(u,o){calls.push([u,o.method,o.headers["X-Router-Action"],o.body]);return Promise.resolve({ok:status<400,status:status,json:function(){return Promise.resolve(body)}});};}
khSetMode("http://r","mixed",fake(200,{ok:true})).then(function(a){out.ok=a;
 return khSetMode("http://r","paid",fake(400,{error:"bad mode"}));}).then(function(b){out.refused=b;
 return khSetMode("http://r","free",function(){return Promise.reject(new Error("x"))});}).then(function(c){out.down=c;out.calls=calls;console.log(JSON.stringify(out));});
"""
r = subprocess.run([node, "-e", code], capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr
o = json.loads(r.stdout.strip().splitlines()[-1])
assert o["map"] == ["free", "paid", "auto", "safe", None], o
assert o["ui"] == ["free", "paid", "paid", "mixed", "safe", None], o
assert o["ok"] == {"ok": True, "mode": "auto"}, o
assert o["refused"] == {"ok": False, "error": "bad mode"}, o
assert o["down"]["ok"] is False and o["down"]["error"], o
c = o["calls"][0]
assert c == ["http://r/router/settings", "POST", "1", '{"mode":"auto"}'], c
print("test_mode_control: ok (%d pages)" % len(pages))
