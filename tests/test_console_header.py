"""v1.114: every console page has the same header logic (island strip + base cards), the footer link to all commands, and the Docs page has the workflow arrows."""
import glob, os, re, subprocess, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
H = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, os.path.join(ROOT, "tool"))
bad = 0


def ok(c, m):
    global bad
    print(("PASS " if c else "FAIL ") + m)
    bad += 0 if c else 1


pages = sorted(glob.glob(os.path.join(H, "agent-console*.html")))
ok(len(pages) == 8, "eight console pages")
for p in pages:
    t = open(p, encoding="utf-8").read(); n = os.path.basename(p)
    ok(t.count("<!-- kit-head:begin -->") == 1 and "kh-strip" in t, n + ": one shared header block with the island strip")
    ok('href="/manual/commands.html">All commands</a>' in t, n + ": footer link to all commands")
docs = open(os.path.join(H, "agent-console-docs.html"), encoding="utf-8").read()
ok(all(k in docs for k in ('id="pageSteps"', 'id="demoBox"', 'id="pEnv"', 'id="pBuild"', 'id="pAudit"', 'id="pDelivery"', 'id="statusT0"')), "the Docs page has the arrows, the demo box beside them, the four new steps and the new-map block")
ok("data-p=\"env\"" in docs and "jGhost(" in docs, "empty sections are shown as ghosts, not hidden")
# the demo uses the same keys the page maps to arrows
demo = open(os.path.join(ROOT, "user-level-commands", "demo.md"), encoding="utf-8").read()
keys = re.findall(r"^\d\. `(\w+)`", demo, re.M)
ok(keys == ["idea", "spec", "plan", "tasks", "environment", "build", "audit", "delivery"], "demo phases are the eight keys of the arrows: %s" % keys)
# the commands list is written from the command files
import gen_commands
txt = gen_commands.build()
ok("`/demo" in txt and "`/spec" in txt and "`/kit-update" in txt and "`/audit" in txt, "the commands list has the flow, the demo and the kit commands")
ok(open(gen_commands.OUT, encoding="utf-8").read() == txt, "docs/manual/commands.md is up to date (python tool/gen_commands.py)")
sys.exit(1 if bad else 0)
