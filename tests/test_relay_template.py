#!/usr/bin/env python3
"""The mailbox ships with the kit: folders, protocol, command and rule."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
R = os.path.join(ROOT, "project-template", "Claude", "relay")
fails = []
def need(c, m):
    if not c: fails.append(m)
for d in ("inbox", "running", "done", "outbox"):
    need(os.path.isfile(os.path.join(R, d, ".gitkeep")), "relay/%s/.gitkeep missing" % d)
readme = open(os.path.join(R, "RELAY-README.md"), encoding="utf-8").read()
for k in ("HEARTBEAT", "STOP", "approved: yes", "needs_mcp", "running/", "not connected", "never edit", "Never:"):
    need(k.lower() in readme.lower(), "RELAY-README missing: " + k)
cmd = open(os.path.join(ROOT, "user-level-commands", "relay.md"), encoding="utf-8").read()
need("RELAY-README.md" in cmd and "STOP" in cmd and "HEARTBEAT" in cmd, "/relay command incomplete")
cl = open(os.path.join(ROOT, "project-template", "CLAUDE.md"), encoding="utf-8").read()
need("KIT:BEGIN relay" in cl and "KIT:END relay" in cl, "CLAUDE.md relay rule missing")
if fails:
    print("FAIL relay template"); [print(" -", f) for f in fails]; sys.exit(1)
print("PASS Relay mailbox template, command and rule")
