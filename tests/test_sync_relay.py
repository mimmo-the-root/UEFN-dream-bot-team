"""An old project updated by the kit gets the mailbox (Claude/relay: README and the four folders), so /relay and the Fix button work there."""
import os, shutil, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import kit_sync
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
p = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(p, "Claude"))
    tpl = os.path.join(root, "project-template")
    ch, ad, bk = kit_sync.sync_files(p, tpl)
    ok(os.path.isfile(os.path.join(p, "Claude", "relay", "RELAY-README.md")), "the mailbox protocol is installed in an old project")
    ok(all(os.path.isdir(os.path.join(p, "Claude", "relay", d)) for d in ("inbox", "running", "done", "outbox")), "the four mailbox folders exist after the update")
    # a command waiting in the inbox is never touched by a later update
    open(os.path.join(p, "Claude", "relay", "inbox", "001-x.md"), "w").write("id: 001\n")
    open(os.path.join(p, "Claude", "relay", "RELAY-README.md"), "w").write("old")
    ch2, ad2, bk2 = kit_sync.sync_files(p, tpl)
    ok(os.path.isfile(os.path.join(p, "Claude", "relay", "inbox", "001-x.md")), "a waiting command survives the update")
    ok(open(os.path.join(p, "Claude", "relay", "RELAY-README.md")).read() != "old", "the README is refreshed (managed)")
finally:
    shutil.rmtree(p, ignore_errors=True)
