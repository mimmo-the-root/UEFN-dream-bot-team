#!/usr/bin/env python3
"""verse_map.py next: the learning is cut into slices, each for a fresh agent; the order is genre, code, docs, devices, blueprint; a slice that does not progress is `stuck`, never a loop."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import verse_map as vm

d = tempfile.mkdtemp(); out = os.path.join(d, "Claude", "docs", "map"); os.makedirs(out)
def jd(p, o): json.dump(o, open(os.path.join(out, p), "w"))
def nxt(): return vm.cmd_next(d, out)
jd("meta.json", {"files": {"a.verse": {"sha": "1"}, "b.verse": {"sha": "2"}}})
assert nxt()["slice"] == "genre"                                   # no .genre yet
open(os.path.join(d, "Claude", "docs", ".genre"), "w").write("tycoon")
r = nxt(); assert r == {"slice": "code", "left": 2}, r
jd("learned.json", {"depth": "source", "files": {"a.verse": "1", "b.verse": "2"}})
vm.docs_pending = lambda project, outdir: (False, ["Claude/docs/X.md"])
r = nxt(); assert r["slice"] == "docs", r
vm.docs_pending = lambda project, outdir: (False, [])
assert nxt()["slice"] == "devices"                                 # DEVICES.md missing
open(os.path.join(out, "DEVICES.md"), "w").write("WIRING-READ: yes\nSETTINGS-READ: yes\nISLAND-CONFIG-READ: yes\n")
r = nxt(); assert r["slice"] == "blueprint", r                     # the devices slice already ran after the code: now the blueprint
assert nxt()["slice"] == "blueprint"                               # second ask, same state: still allowed (same=1)
r = nxt(); assert r["slice"] == "stuck" and r["kind"] == "blueprint", r   # third time with no progress: stop, do not loop
jd("profile-learned.json", {"v": 1})
vm.profile_pending = lambda outdir, project=None: False
assert nxt()["slice"] == "done" and not os.path.exists(os.path.join(out, vm.SLICE_FILE))   # done clears the guard
assert vm.cmd_next(d, out, reset=True)["slice"] == "reset"
print("learn next OK")
cmd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", ".claude", "commands")
om, sl = open(os.path.join(cmd, "learn-map.md"), encoding="utf-8").read(), open(os.path.join(cmd, "learn-slice.md"), encoding="utf-8").read()
assert "verse_map.py` `next`" in om.replace("python Claude/hooks/verse_map.py next", "verse_map.py` `next") and "Agent" in om and "stuck" in om and len(om) < 4000, "learn-map is the thin orchestrator"
assert all(k in sl for k in ("genre", "code", "docs", "devices", "blueprint")) and "verse_map.py learn" in sl and len(sl) > 10000, "learn-slice keeps the full steps"
import kit_sync; assert ".claude/commands/learn-slice.md" in kit_sync.MANAGED
print("learn slice files OK")
import subprocess   # the command line must reach cmd_next (it once printed the usage text: `next` was missing from the list of commands)
_o = subprocess.run([sys.executable, os.path.join(os.path.dirname(vm.__file__), "verse_map.py"), "next", "--project", d, "--out", out], capture_output=True, text=True).stdout
assert json.loads(_o.strip().splitlines()[-1])["slice"] in ("genre", "code", "docs", "devices", "blueprint", "done"), _o[:200]
print("learn next CLI OK")
