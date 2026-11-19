#!/usr/bin/env python3
"""T-106: the console's weighted percent (Done = 100, In progress = its own %, parents = average of children).
Extracts the pure functions from agent-console-docs.html and evaluates them with node."""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-docs.html")
node = shutil.which("node")
if not node:
    print("test_weighted_progress: skipped (node not found)")
    sys.exit(0)
with open(PAGE, encoding="utf-8") as f:
    html = f.read()


def fn(name):
    m = re.search(r"^function %s\(.*?^\}|^function %s\([^\n]*\{.*\}$" % (name, name), html, re.S | re.M)
    line = re.search(r"^function %s\(.*$" % name, html, re.M).group(0)
    return line if line.rstrip().endswith("}") else m.group(0)


names = ["statusBucket", "rmKids", "taskPct", "taskPctOwn", "taskWeight", "weightedPct"]
code = "var window = {};\n" + "\n".join(fn(n) for n in names) + """
var out = {};
out.mixed = weightedPct([{id:"T-1",status:"Done"},{id:"T-2",status:"In progress 50% - half"}]);
out.empty = weightedPct([]);
window.RM_ALLROWS = [{id:"T-9",feature:"[Pkg T-3] a",status:"Done"},{id:"T-8",feature:"[Pkg T-3] b",status:"In progress 50%"}];
out.parent = weightedPct([{id:"T-3",status:"In progress"}]);
out.todo = weightedPct([{id:"T-4",status:"To do"},{id:"T-5",status:"Done"}]);
console.log(JSON.stringify(out));
"""
res = subprocess.run([node, "-e", code], capture_output=True, text=True, encoding="utf-8")
assert res.returncode == 0, res.stderr
out = json.loads(res.stdout.strip().splitlines()[-1])
assert out["mixed"] == 75, out
assert out["empty"] == 0, out
assert out["parent"] == 75, out
assert out["todo"] == 50, out
print("test_weighted_progress: ok")
