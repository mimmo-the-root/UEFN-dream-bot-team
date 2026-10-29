import os, sys, tempfile
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import ui_lint as u
canon = u.canonical()
assert canon.get("--bg") == "#060810", "tokens file found"
d = tempfile.mkdtemp(); p = os.path.join(d, "x.html")
open(p, "w").write("<style>:root{--bg:#000000}@keyframes a{0%{box-shadow:0 0 1px red}100%{transform:none}}.x{animation:a 1s}</style>")
msgs = [m for _, _, m in u.lint(p, canon)]
assert any("token --bg" in m for m in msgs) and any("box-shadow" in m for m in msgs) and any("reduced-motion" in m for m in msgs), msgs
for f in os.listdir(H):
    if f.startswith("agent-console") and f.endswith(".html"):
        assert not [x for x in u.lint(os.path.join(H, f), canon) if x[0] == "ERROR"], f
print("ok ui_lint")
