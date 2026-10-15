"""mcp_lab: the exploration lab refuses what is unsafe (normal mode) and starts the aggressive mode only inside a proven disposable project."""
import os, sys, json, tempfile, importlib
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
sys.path.insert(0, hooks)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def load(**env):
    for k in ("LAB_AGGRESSIVE", "LAB_ROOT", "LAB_LEVEL", "LAB_SESSION"):
        os.environ.pop(k, None)
    os.environ.update(env)
    sys.modules.pop("mcp_lab", None)
    return importlib.import_module("mcp_lab")

U, A = "UMGToolSet.UMGToolSet", "editor_toolset.toolsets.asset.AssetTools"
L = load(LAB_ROOT="/root_pillars")
L._tools[U + "/GetWidgets"] = {"annotations": {"readOnlyHint": True}}
ok(L.refusal(U, "GetWidgets", {"x": "/root_pillars/VerseUIKit/a"}) == "", "normal: reading a real project asset is fine")
ok(L.refusal(U, "AddWidget", {"b": {"refPath": "/root_pillars/KitTest/W.W"}, "c": {"refPath": "/Script/UMG.Overlay"}}) == "", "normal: a write inside the sandbox is fine")
ok("outside the sandbox" in L.refusal(U, "AddWidget", {"b": {"refPath": "/root_pillars/Real/W.W"}}), "normal: a write on a real asset is refused")
ok("never-list" in L.refusal(A, "delete", {}), "normal: delete is refused")
ok("level write" in L.refusal("editor_toolset.toolsets.actor.ActorTools", "set_actor_transform", {}), "normal: level writes need LAB_LEVEL")
ok("never" in L.refusal(A, "restart_editor", {}), "quitting or restarting is never allowed")
ok("disk" in L.refusal(A, "update_metadata_tags", {"p": "C:\\Users\\x\\file.txt"}), "a write naming a disk path is refused")
ok("_kit_probe" in L.refusal("ValkyrieToolset.VerseToolset", "WriteVerseFile", {"path": "custom_verse/real.verse"}), "normal: Verse writes only on a _kit_probe file")
L.created.add("/root_pillars/Level/Actor1")
L2 = load(LAB_ROOT="/root_pillars", LAB_LEVEL="1")
L2.created.add("/root_pillars/Level/Actor1")
ok(L2.refusal("editor_toolset.toolsets.actor.ActorTools", "delete_actors", {"a": "/root_pillars/Level/Actor1"}) == "", "normal: it may clean up objects it created itself")
ok("never-list" in L2.refusal("editor_toolset.toolsets.actor.ActorTools", "delete_actors", {"a": "/root_pillars/Level/Other"}), "normal: but not other objects")

# laboratory mode
class FakeClient:
    def __init__(self, level): self.level = level
    def call(self, name, args): return json.dumps({"returnValue": self.level})
tmp = tempfile.mkdtemp(); marker = os.path.join(tmp, "LAB-PROJECT.txt")
LA = load(LAB_AGGRESSIVE="1", LAB_ROOT="/lab_mcp")
LA.MARKER = marker
LA.client = lambda: FakeClient("/lab_mcp/Main")
ok("LAB-PROJECT.txt" in LA.refusal(A, "delete", {"p": "/lab_mcp/x"}), "lab: refuses to start without the marker file")
open(marker, "w").write("disposable project")
LA._checked = False
ok(LA.refusal(A, "delete", {"p": "/lab_mcp/x"}) == "", "lab: with marker and the right level, delete inside the lab is allowed")
ok(LA.refusal("editor_toolset.toolsets.actor.ActorTools", "spawn_actor", {"a": "/lab_mcp/y"}) == "", "lab: level writes and sessions need no extra switch")
ok("outside /lab_mcp" in LA.refusal(A, "delete", {"p": "/root_pillars/Real"}), "lab: still refuses a path outside the lab root")
ok("never" in LA.refusal(A, "shutdown_editor", {}), "lab: never quits the editor")
ok("disk" in LA.refusal(A, "move", {"p": "C:\\Windows\\x"}), "lab: never touches the disk outside the project")
LB = load(LAB_AGGRESSIVE="1", LAB_ROOT="/lab_mcp")
LB.MARKER = marker
LB.client = lambda: FakeClient("/root_pillars/root_pillars")
ok("NOT the laboratory" in LB.refusal(A, "delete", {"p": "/lab_mcp/x"}), "lab: refuses when the open level is not under the lab root")
LC = load(LAB_AGGRESSIVE="1")
LC.MARKER = marker
ok("LAB_ROOT" in LC.refusal(A, "delete", {}), "lab: needs LAB_ROOT")
print("mcp_lab ok")
