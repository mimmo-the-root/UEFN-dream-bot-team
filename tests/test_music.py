"""Background music (v1.124.40): every console page has the switch, the servers list and serve Claude/music, the kit ships one track once."""
import glob, os, shutil, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, H)
for p in glob.glob(os.path.join(H, "agent-console*.html")):
    t = open(p, encoding="utf-8").read()
    assert t.count("<!-- kit-music:begin -->") == 1 and 'fetch("/music"' in t, os.path.basename(p)
py = open(os.path.join(H, "agent-console-server.py"), encoding="utf-8").read()
ps = open(os.path.join(H, "agent-console-server.ps1"), encoding="utf-8").read()
assert "def _serve_music" in py and "Accept-Ranges" in py and '"/music/"' in ps and "Content-Range" in ps
assert os.path.isfile(os.path.join(root, "project-template", "Claude", "music", "README.md"))
assert any(n.endswith(".mp3") for n in os.listdir(os.path.join(root, "project-template", "Claude", "music")))
import kit_sync
t = tempfile.mkdtemp(); os.makedirs(os.path.join(t, "Claude"))
kit_sync.sync_files(t, os.path.join(root, "project-template"))
m = os.path.join(t, "Claude", "music"); first = sorted(os.listdir(m))
assert "README.md" in first and any(n.endswith(".mp3") for n in first)
for n in first:
    if n.endswith(".mp3"):
        os.remove(os.path.join(m, n))
open(os.path.join(m, "mine.mp3"), "w").write("x")
kit_sync.sync_files(t, os.path.join(root, "project-template"))
assert sorted(os.listdir(m)) == ["README.md", "mine.mp3"], "a deleted track does not come back, the owner's files stay"
shutil.rmtree(t)
print("ok music")
