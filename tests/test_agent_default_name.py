import os
h = os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks")
for f in ("agent-console-log.ps1", "agent-console-log.sh"):
    t = open(os.path.join(h, f), encoding="utf-8").read()
    # no subagent_type = the Agent tool runs general-purpose, and the stop event reports that name: the card must use it too
    assert '"unknown"' not in t, f + ": a start without subagent_type must be named general-purpose, not unknown"
    assert "general-purpose" in t, f
print("agent default name OK")
