import os, sys, tempfile, shutil
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import demo_timer as t
d = tempfile.mkdtemp(); t.DOCS = d; t.P = os.path.join(d, "DEMO-TIMER.md")
assert t.main(["stop"]) == 1, "stop without start"
assert t.main(["start", "--mode", "auto"]) == 0
assert t.main(["start"]) == 1, "double start"
assert t.main(["mark", "spec"]) == 0 and t.main(["stop"]) == 0
assert t.main(["mark", "x"]) == 1, "mark after stop"
txt = open(t.P, encoding="utf-8").read()
assert "Mode: auto" in txt and "stopped" in txt and "| spec |" in txt
assert t.load()["end"]
d2 = open(os.path.join(H, "agent-console-docs.html"), encoding="utf-8").read()
assert "demoClock" in d2 and "/demo --auto" in d2
shutil.rmtree(d); print("ok demo_timer")
