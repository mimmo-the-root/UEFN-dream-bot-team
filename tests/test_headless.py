"""One-shot runs (claude -p, pieces, tests) get no session-start chores; cod.cmd --plan skips the user settings."""
import os, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import kit_sync
for k in ("UEFN_KIT_HEADLESS", "CLAUDE_CODE_ENTRYPOINT"):
    os.environ.pop(k, None)
assert not kit_sync.headless()
os.environ["CLAUDE_CODE_ENTRYPOINT"] = "sdk-cli"; assert kit_sync.headless()
os.environ["CLAUDE_CODE_ENTRYPOINT"] = "cli"; assert not kit_sync.headless()
os.environ["UEFN_KIT_HEADLESS"] = "1"; assert kit_sync.headless()
ps = open(os.path.join(root, "project-template", "Claude", "hooks", "session-start-reminder.ps1"), encoding="utf-8").read()
assert "UEFN_KIT_HEADLESS" in ps and "One-shot run" in ps and ps.index("One-shot run") < ps.index("mailbox worker is not running")
sh = open(os.path.join(root, "project-template", "Claude", "hooks", "session-start-reminder.sh"), encoding="utf-8").read()
assert "UEFN_KIT_HEADLESS" in sh and sh.index("One-shot run") < sh.index("mailbox worker is not running")
assert 'UEFN_KIT_HEADLESS="1"' in open(os.path.join(root, "project-template", "Claude", "hooks", "pieces.py"), encoding="utf-8").read()
cod = open(os.path.join(root, "user-level-hooks", "cod.cmd"), encoding="utf-8").read()
assert "--setting-sources project,local" in cod
print("ok headless")
