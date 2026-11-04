"""Running the tests (or publish.cmd) must never start a console or open the browser: with UEFN_KIT_NO_CONSOLE set, autostart does nothing."""
import os, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "user-level-hooks"))
base = tempfile.mkdtemp()
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(base, "lab")
os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(ROOT, "project-template")
os.environ["UEFN_KIT_NO_CONSOLE"] = "1"
import fab_lab as fl
def boom(*a, **k): raise AssertionError("a console process or a browser was started")
subprocess.Popen = boom
import webbrowser; webbrowser.open = boom
root = os.path.join(base, "root_FAB_rainbow"); os.makedirs(os.path.join(root, "Content"))
assert fl.autostart(root) is None, "autostart must do nothing when UEFN_KIT_NO_CONSOLE is set"
print("no console in tests OK")
