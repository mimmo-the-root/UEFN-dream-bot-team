#!/usr/bin/env python3
"""T-091: the agent rule for the debug flags is in the template, and kit_doctor prints the six flags (also with one off)."""
import os, re, subprocess, sys, tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import kit_config  # noqa: E402
import kit_doctor  # noqa: E402

fails = []


def check(c, m):
    if not c:
        fails.append(m)


rd = lambda *p: open(os.path.join(ROOT, *p), encoding="utf-8").read()
cm = rd("project-template", "CLAUDE.md")
m = re.search(r"<!-- KIT:BEGIN debug-flags -->(.*?)<!-- KIT:END debug-flags -->", cm, re.S)
check(m and "kit-settings.json" in m.group(1) and "debug_log.py" in m.group(1), "CLAUDE.md template has the flags rule")
for f in kit_config.DEBUG_FLAGS:
    check(m and f in m.group(1), "rule names flag " + f)
check("kit-settings.json" in rd("project-template", "Claude", "plan", "ANSWERS.md"), "ANSWERS.md template has the rule")

def doctor(project):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "project-template", "Claude", "hooks", "kit_doctor.py"), "--project", project],
                       capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace",
                       env=dict(os.environ, UEFN_HOME=project, UEFN_KIT_TEMPLATE=os.path.join(project, "none")))
    return [l for l in r.stdout.splitlines() if "Debug flags:" in l]

with tempfile.TemporaryDirectory() as d:
    out = doctor(d)
    check(len(out) == 1 and all(f + "=" in out[0] for f in kit_config.DEBUG_FLAGS), "doctor prints the six flags (no file)")
    check(out and "safety_samples=off" in out[0] and "exchange_log=on" in out[0], "defaults shown")
    kit_config.set("debug.exchange_log", False, d)
    out = doctor(d)
    check(out and "exchange_log=off" in out[0] and "problems_log=on" in out[0], "flag off is shown as off")
    open(kit_config.path(d), "w").write("{broken")
    out = doctor(d)
    check(out and "broken" in out[0] and "exchange_log=on" in out[0], "broken file: defaults and a note")

if fails:
    print("FAIL: " + "\n".join(fails))
    sys.exit(1)
print("agent flags tests OK")
