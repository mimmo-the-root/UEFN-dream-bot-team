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
GUID = "/09e4e8d3-83f9-4ee0-9777-072ed3984380"
ok(LA.refusal("editor_toolset.toolsets.scene.SceneTools", "remove_from_scene", {"actor": {"refPath": GUID + "/lab_mcp.lab_mcp:PersistentLevel.T008_Cube"}}) == "", "lab: an actor of the open level, named /<guid>/<project>.<project>:PersistentLevel.X, counts as inside the lab")
ok("outside /lab_mcp" in LA.refusal("editor_toolset.toolsets.scene.SceneTools", "remove_from_scene", {"actor": {"refPath": GUID + "/root_pillars.root_pillars:PersistentLevel.X"}}), "lab: the same form of ANOTHER project is still refused")
ok("outside /lab_mcp" in LA.refusal("editor_toolset.toolsets.scene.SceneTools", "remove_from_scene", {"actor": "/lab_mcp_other/x"}), "lab: a name that only starts like the lab root is refused")
ok(LA.refusal("NiagaraTools", "CreateNiagaraSystem", {"template": "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight", "path": "/lab_mcp/Fx/NS_A"}) == "", "lab: a catalog template is accepted as the source of a new asset inside the lab")
ok(LA.refusal("editor_toolset.toolsets.actor.ActorTools", "spawn_actor", {"class": "/Game/Valkyrie/Devices/BP_X.BP_X_C"}) == "", "lab: a catalog class may be spawned into the lab level")
ok("outside /lab_mcp" in LA.refusal("editor_toolset.toolsets.asset.AssetTools", "duplicate", {"path": "/Game/Real/A", "new_path": "/root_pillars/B"}), "lab: a source is not enough when the result goes outside the lab")
ok("outside /lab_mcp" in LA.refusal("editor_toolset.toolsets.asset.AssetTools", "set_properties", {"instance": "/Game/Real/A", "values": "{}"}), "lab: a catalog asset is never the target of a write")
ok("outside /lab_mcp" in LA.refusal("editor_toolset.toolsets.asset.AssetTools", "delete_assets", {"p": "/Game/Real/A"}), "lab: a catalog asset is never deleted")
ok(LA.refusal("DevTools", "PlaceDevice", {"assetPath": {"refPath": "/CreativeCoreDevices/SetupAssets/PID_Device_Timer.PID_Device_Timer"}, "transform": {}}) == "", "lab: a catalog device may be placed in the lab level")
ok(LA.refusal("EntityTools", "CreateEntity", {"class": "/EntityFramework/Foo.Foo", "parent": GUID + "/lab_mcp.lab_mcp:PersistentLevel.LevelEntity"}) == "", "lab: an entity class from the catalog may be created in the lab")
ok(LA.refusal("EntityTools", "AddComponent", {"entity": {"refPath": GUID + "/lab_mcp.lab_mcp:PersistentLevel.E1"}, "component": "/EntityFramework/_Verse/VNI/Entity.tag_component"}) == "", "lab: a catalog component class may be added to a lab entity")
ok(LA.refusal("AssetTools", "duplicate", {"path": "/AnimToTexture/M/SM.SM", "new_path": GUID + "/lab_mcp/Mesh/SM_Copy"}) == "", "lab: a plugin mesh may be duplicated INTO the lab")
ok("outside /lab_mcp" in LA.refusal("StaticMeshTools", "add_socket", {"mesh": "/AnimToTexture/M/SM.SM", "socket": "S"}), "lab: a plugin mesh is never edited in place")
ok("outside /lab_mcp" in LA.refusal("StaticMeshTools", "assign_physics_asset", {"mesh": "/AnimToTexture/M/SM.SM", "asset": "/lab_mcp/PA"}), "lab: assigning a lab asset to a plugin mesh is still refused")
ok(LA.refusal("EntityTools", "set_properties", {"instance": GUID + "/lab_mcp.lab_mcp:PersistentLevel.D1", "values": GUID + "/_Verse.lab_mcp-probe"}) == "", "lab: the lab's own Verse class is inside the lab")
ok(LA.refusal("VerseTools", "Grep", {"pattern": "/Bad.*Value"}) == "", "lab: a regex that starts with / is not an asset path")
ok(LA.refusal("OutlinerTools", "SelectOutlinerFolders", {"folders": ["/"]}) == "", "lab: the root folder / is harmless")
ok("outside /lab_mcp" in LA.refusal("ObjectTools", "set_properties", {"instance": GUID + "/lab_mcp.lab_mcp:PersistentLevel.D1", "values": "{\"Script\": \"/root_pillars/Real/X\"}"}), "lab: a path hidden in a JSON-text argument (B-002) is inspected")
ok(LA.refusal("ObjectTools", "set_properties", {"instance": GUID + "/lab_mcp.lab_mcp:PersistentLevel.D1", "values": "{\"Scalar\": 0.9, \"Color\": \"(R=1,G=0,B=0)\"}"}) == "", "lab: a JSON-text argument with plain numbers and colors is fine")
ok("outside /lab_mcp" in LA.refusal(A, "duplicate", {"path": GUID + "/mech-drone/textures/Drone.Drone", "new_path": GUID + "/mech-drone/textures/D2"}), "lab: a sibling folder is not lab unless the owner declares it")
LE = load(LAB_AGGRESSIVE="1", LAB_ROOT="/lab_mcp", LAB_EXTRA_ROOTS="/mech-drone,/Game,/root_pillars")
LE.MARKER = marker
LE.client = lambda: FakeClient(GUID + "/lab_mcp")
ok(LE.refusal(A, "duplicate", {"path": GUID + "/mech-drone/textures/Drone.Drone", "new_path": GUID + "/mech-drone/textures/D2"}) == "", "lab: a declared extra root (imported model) counts as lab")
ok("outside" in LE.refusal(A, "delete", {"p": "/Game/Real/A"}) and "outside" in LE.refusal(A, "delete", {"p": "/root_pillars/Real"}), "lab: an extra root can never be a catalog mount or another project")
ok("never" in LA.refusal(A, "shutdown_editor", {}), "lab: never quits the editor")
ok("disk" in LA.refusal(A, "move", {"p": "C:\\Windows\\x"}), "lab: never touches the disk outside the project")
LB = load(LAB_AGGRESSIVE="1", LAB_ROOT="/lab_mcp")
LB.MARKER = marker
LB.client = lambda: FakeClient("/root_pillars/root_pillars")
ok("NOT the laboratory" in LB.refusal(A, "delete", {"p": "/lab_mcp/x"}), "lab: refuses when the open level is not under the lab root")
LC = load(LAB_AGGRESSIVE="1")
LC.MARKER = marker
ok("LAB_ROOT" in LC.refusal(A, "delete", {}), "lab: needs LAB_ROOT")
import time
with tempfile.TemporaryDirectory() as _d:
    LS = load()
    LS.LOGS = _d
    ok(LS._src() == "agent", "src: agent without a marker")
    open(os.path.join(_d, "replay.on"), "w").close()
    ok(LS._src() == "replay", "src: replay while replay.on is fresh (calls made by a script too)")
    _old = time.time() - 13 * 3600
    os.utime(os.path.join(_d, "replay.on"), (_old, _old))
    ok(LS._src() == "agent", "src: a forgotten marker is ignored")
    LS.SRC = "battery"
    ok(LS._src() == "battery", "src: LAB_SRC wins over the marker")
with tempfile.TemporaryDirectory() as _e:
    LX = load()
    LX.EXPLORE = os.path.join(_e, "_explore")
    os.makedirs(LX.EXPLORE)
    good = os.path.join(LX.EXPLORE, "a.csv")
    open(good, "w").close()
    ok(LX._explore_ok("import_file", good) and LX._explore_ok("export_png", good), "P2: import_file and export_png may use a file inside _explore")
    ok(not LX._explore_ok("other_write", good), "P2: any other tool still refuses a disk path")
    ok(not LX._explore_ok("import_file", os.path.join(LX.EXPLORE, "..", "x.csv")), "P2: a `..` escape is refused")
    ok(not LX._explore_ok("import_file", os.path.join(_e, "other.csv")), "P2: a file outside _explore is refused")
print("mcp_lab ok")
ok("save_assets without" in L.refusal(A, "save_assets", {}), "save_assets with no asset_paths is refused (it would save everything)")
ok("save_assets without" in L.refusal(A, "save_assets", {"asset_paths": []}), "save_assets with an empty list is refused")
ok("save_assets without" in L.refusal(A, "save_assets", {"arguments": "{\"asset_paths\": []}"}), "an empty list inside a JSON text is refused too")
ok("save_assets without" not in L.refusal(A, "save_assets", {"asset_paths": ["/root_pillars/KitTest/DT_X"]}), "save_assets with named assets passes this check")
ok("save_assets without" not in L.refusal(A, "save_assets", {"allow_save_all": True}), "allow_save_all is the deliberate way out")
