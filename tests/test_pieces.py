"""pieces.py: a failed piece is cut again (up to 3 levels), then tried on 10+ other models, then skipped; the run never stops."""
import os, shutil, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import pieces as P
P.DIR = tempfile.mkdtemp()
P.session_settings = lambda mode: None
MODELS = ["p%d/m%d" % (i, i) for i in range(14)]

ps = P.split("T-9", ["Add the score counter | ScoreManager.verse | compiles", "Show it on the HUD | Hud.verse | value read back", "Playtest note"])
assert len(ps) == 3 and ps[0]["files"] == "ScoreManager.verse" and ps[2]["check"] == ""
d = P.load("T-9"); b = P.brief(d, P.nxt(d))
assert "piece 1 of 3" in b and "ScoreManager.verse" in b and "PIECE DONE" in b and "never stop" in b

calls = []
def runner(prompt, cmd):
    model = cmd[cmd.index("--model") + 1] if "--model" in cmd else "default"
    calls.append((prompt.split("\n")[0], model))
    if prompt.startswith("You are the orchestrator"):
        if "piece 2:" in prompt or "Piece 2 failed" in prompt:
            return "SUBPIECE: HUD widget | Hud.verse | compiles\nSUBPIECE: bind the score | Hud.verse | value read back"
        return "no idea"   # the splitter could not cut piece 2.2 further
    prompt = prompt.split("\n")[0] if not prompt.startswith("You are") else prompt
    if "piece 1 " in prompt:
        return "PIECE DONE: counter in ScoreManager.verse, event ScoreChanged"
    if "piece 2 " in prompt:
        return "PIECE BLOCKED: too much at once"
    if "piece 2.1 " in prompt:
        return "PIECE DONE: widget made"
    if "piece 2.2 " in prompt:
        return "PIECE DONE: bound" if model == "dream:p4/m4" else "PIECE BLOCKED: model cannot do it"
    if "piece 3 " in prompt:
        return "PIECE BLOCKED: no editor"
    return ""
log = P.run("T-9", runner=runner, models=lambda n: MODELS[:n])
st = {p["n"]: p["status"] for p in P.load("T-9")["pieces"]}
assert st == {"1": "done", "2": "split", "2.1": "done", "2.2": "done", "3": "skipped"}, st
assert ("2.2", "done on p4/m4") in log, log
t3 = [c for c in calls if c[0].startswith("Task T-9, piece 3 ")]
assert len({m for _, m in t3}) >= 11, "piece 3 tried on the default and at least 10 other models"
d = P.load("T-9"); assert "event ScoreChanged" in P.brief(d, P.find(d, "2.1")), "notes of the pieces before travel"
assert "SKIPPED" not in P.brief(d, P.find(d, "2.2"))
assert "3 of 4 pieces done, 1 skipped" in P.status_text(d), P.status_text(d)
assert P.nxt(d) is None
# a piece deep enough is not cut again: it goes straight to other models
P.split("T-10", ["x"]); d = P.load("T-10"); d["pieces"][0]["depth"] = P.MAX_DEPTH; P.save("T-10", d)
seen = []
P.run("T-10", runner=lambda pr, c: (seen.append(pr[:30]), "PIECE BLOCKED: no")[1], models=lambda n: MODELS[:n])
assert not any(s.startswith("You are the orchestrator") for s in seen) and P.load("T-10")["pieces"][0]["status"] == "skipped"
try:
    P.split("../x", ["a"]); raise AssertionError("bad id accepted")
except SystemExit:
    pass
shutil.rmtree(P.DIR)
print("ok pieces")
