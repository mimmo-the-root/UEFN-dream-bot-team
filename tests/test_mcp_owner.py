"""Every UEFN MCP tool has exactly one owner agent; a sub-agent cannot call another agent's tool; the main session is never limited."""
import glob, json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import mcp_owner as O, mcp_heavy_guard as G, mcp_names as N
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)

cat = json.load(open(os.path.join(ROOT, "tests", "fixtures", "catalog43-access.json")))
owners = {}
for k, a in cat.items():
    ts, tl = k.split("/", 1)
    owners[k] = O.owner(ts, tl, a)
check("the 43.00 catalog has %d tools, every one has an owner" % len(cat), len(cat) >= 800 and all(owners.values()))
check("owners are the chief or one of the ten agents", set(owners.values()) <= set(O.AGENTS) | {"chief"})
check("every agent owns at least one tool", all(any(v == a for v in owners.values()) for a in O.AGENTS))
check("the chief keeps few tools (scripts, registry): %d" % sum(1 for v in owners.values() if v == "chief"), sum(1 for v in owners.values() if v == "chief") <= 12)
# a write belongs to its owner only; a shared read (editor core) is open to all agents
writes = [(k, o) for k, o in owners.items() if cat[k] == "write"]
only = all(sum(1 for a in O.AGENTS if O.allowed(a, *k.split("/", 1), access="write")) == (1 if o != "chief" else 0) for k, o in writes)
check("a write tool is allowed to exactly one agent (none for the chief's scripts)", only)
check("an editor read is open to every agent", all(O.allowed(a, "EditorToolset", "FindActors", "read") for a in O.AGENTS))
check("a read of another area is not shared (UMG read for the cinematics agent)", not O.allowed("cinematics", "UMGToolSet", "GetWidgets", "read"))
check("execute_python stays with the chief", not any(O.allowed(a, "editor_toolset", "execute_python") for a in O.AGENTS) and O.allowed("coder", "editor_toolset", "execute_python"))
check("a toolset Epic adds tomorrow goes to the chief", O.owner("BrandNewToolset", "DoIt") == "chief")
check("the world/asset split of the editor core", O.owner("EditorToolset", "AddComponent", "write") == "env-builder" and O.owner("EditorToolset", "AddRow", "write") == "asset-builder")

P = "mcp__unreal-mcp__"
def hook(agent, name):
    pl = {"tool_name": P + name, "tool_input": {}}
    if agent: pl["agent_type"] = agent
    return G.wrong_owner(pl, N.read(pl))
check("a sub-agent calling another area is refused, with the owner named", "device-builder" in hook("ui-builder", "ValkyrieFortniteToolset_PlaceDevice"))
check("a sub-agent calling its own tool is allowed", hook("device-builder", "ValkyrieFortniteToolset_PlaceDevice") == "")
check("the main session (no agent name) is never limited", hook("", "ValkyrieFortniteToolset_PlaceDevice") == "")
check("an agent that is not one of ours is not limited", hook("coder", "ValkyrieFortniteToolset_PlaceDevice") == "")
os.environ["UEFN_KIT_OWNERS"] = "0"
check("UEFN_KIT_OWNERS=0 switches the check off", hook("ui-builder", "ValkyrieFortniteToolset_PlaceDevice") == "")
del os.environ["UEFN_KIT_OWNERS"]

# the agent files exist, are named like the owners and carry the matching area line
for a in O.AGENTS:
    p = os.path.join(ROOT, "user-level-agents", a + ".md")
    t = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    check("agent file %s exists with its name and a description" % a, bool(re.search(r"^name: %s$" % re.escape(a), t, re.M)) and "description:" in t and "mcp_owner.py" in t)
print("%d failed" % len(fails))
sys.exit(1 if fails else 0)
