#!/usr/bin/env python3
"""Console release order: the release with a task In progress is first; finished releases keep their natural place."""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-docs.html")
node = shutil.which("node")
if not node:
    print("test_release_order: skipped (node not found)")
    sys.exit(0)
html = open(PAGE, encoding="utf-8").read()


def fn(name):
    m = re.search(r"^function %s\(.*?^\}" % name, html, re.S | re.M)
    line = re.search(r"^function %s\(.*$" % name, html, re.M).group(0)
    return line if line.rstrip().endswith("}") else m.group(0)


code = "var window = {};\n" + fn("statusBucket") + "\n" + fn("relOrder") + """
const g = (n, st) => ({name: n, rows: [{id: "T-1", status: st}]});
const names = x => relOrder(x).map(o => o.name).join(",");
var out = {};
out.active = names([g("P0-R2", "Done"), g("P0-R3", "To do"), g("P0-R9", "In progress - 50%"), g("Later", "To do")]);
out.noactive = names([g("P0-R2", "Done"), g("P0-R9", "To do"), g("P0-R3", "To do")]);
console.log(JSON.stringify(out));
"""
res = subprocess.run([node, "-e", code], capture_output=True, text=True, encoding="utf-8")
assert res.returncode == 0, res.stderr
out = json.loads(res.stdout.strip().splitlines()[-1])
assert out["active"] == "P0-R9,P0-R3,P0-R2,Later", out
assert out["noactive"] == "P0-R3,P0-R9,P0-R2", out
print("test_release_order: ok")
