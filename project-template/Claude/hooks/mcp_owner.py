#!/usr/bin/env python3
"""mcp_owner.py - which agent owns which UEFN MCP tool. One owner per tool, decided by rules, so a tool Epic adds tomorrow already has an owner.

    python mcp_owner.py Toolset/Tool [read|write]     prints the owner
    python mcp_owner.py --list                        prints the agents and what each one owns (from the saved map, if there is one)

Owners: the chief (the main session: scripts, the registry, anything new and unknown) and ten agents:
  scene-scout   reads of the editor (actors, assets, levels, materials...) and the scene capture; allowed to every agent as a shared read
  env-builder   level and world writes: actors, components, folders, data layers, camera, procedural generation (PCG), geometry, physics assets
  asset-builder asset writes: materials, textures, data tables, collections, meshes (LODs, collisions, sockets), imports and exports
  device-builder devices and gameplay: place devices, properties, event bindings, gameplay tags
  entity-builder entities, prefabs and their components (Scene Graph)
  verse-dev     Verse build and session: build, push, start and stop a game, logs, the Verse and symbol search
  ui-builder    UMG widgets, view models (MVVM), widget animations, widget analysis, Verse fields
  fx-audio      Niagara systems and MetaSound
  perf-profiler Spatial Profiler and Insights
  cinematics    Sequencer (animation_toolset)

The guard (mcp_heavy_guard.py) uses this when a hook payload names a sub-agent: a tool that belongs to another agent is refused, with the
name of the owner. The main session is never limited. Switch off with UEFN_KIT_OWNERS=0. Nothing here calls the editor."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AGENTS = ("scene-scout", "env-builder", "asset-builder", "device-builder", "entity-builder", "verse-dev", "ui-builder", "fx-audio", "perf-profiler", "cinematics")
READ_RX = re.compile(r"^(get|list|find|is|has|exists|describe|query|search|diff|read|count|can|validate|preview|resolve|grep)", re.I)
# EditorToolset writes: the ones about the world (actors, components, levels) go to env-builder, the rest are assets
ENV_RX = re.compile(r"(Actor|Scene|Component|Level|DataLayer|Selected|Focus|Camera|LookAt|^Move$|Pivot|Label|Parent|Hidden|Visible|^Add(Cone|Cube|Cylinder|Sphere)$|^(Add|Remove)Tag$|Viewport)", re.I)
SESSION_RX = re.compile(r"^(StartSession|StopSession|StartGame|StopGame|PushChanges|GetSessionStatus|GetGameState|GetVerseOutput|GetClientLogEntries|ListClients)$")

# first match wins: (toolsets, tool regex or None, owner)
RULES = [
    (("ToolsetRegistry", "AIAssistantEditor"), None, "chief"),
    (("editor_toolset",), r"^(execute_python|execute_tool_script|get_execution_environment)$", "chief"),
    (("editor_toolset", "VerseToolset", "ConsoleToolset"), None, "verse-dev"),
    (("ValkyrieFortniteToolset",), SESSION_RX.pattern, "verse-dev"),
    (("ValkyrieFortniteToolset", "FortGameplayToolset", "GameplayTagsToolset"), None, "device-builder"),
    (("ValkyrieToolset",), None, "entity-builder"),
    (("UMGToolSet", "MVVMToolset", "WidgetAnimationToolset", "WidgetStaticAnalysisToolset", "VerseFieldsToolset"), None, "ui-builder"),
    (("NiagaraToolsets", "MetaSoundToolset"), None, "fx-audio"),
    (("SpatialProfilerToolset", "InsightsToolset"), None, "perf-profiler"),
    (("animation_toolset",), None, "cinematics"),
    (("PCGToolset", "geometry_toolset", "PhysicsToolsets"), None, "env-builder"),
    (("SceneCaptureToolset",), None, "scene-scout"),
]


def access_of(tool, access=None):
    if access in ("read", "write"):
        return access
    return "read" if READ_RX.match(tool or "") else "write"


def owner(toolset, tool, access=None):
    """The one owner of a tool. Unknown toolsets belong to the chief (the main session) until a rule names them."""
    ts = str(toolset or "").split(".")[0]
    for sets, rx, who in RULES:
        if ts in sets and (rx is None or re.search(rx, tool)):
            return who
    if ts == "EditorToolset":
        if access_of(tool, access) == "read":
            return "scene-scout"
        return "env-builder" if ENV_RX.search(tool) else "asset-builder"
    return "chief"


def allowed(agent, toolset, tool, access=None):
    """True when `agent` may call the tool: it owns it, or it is a read of the editor (shared with every agent). The chief may call anything."""
    if agent not in AGENTS:
        return True
    who = owner(toolset, tool, access)
    if who == agent:
        return True
    return who == "scene-scout" and (toolset or "").split(".")[0] == "EditorToolset" and access_of(tool, access) == "read"


def refusal(agent, toolset, tool, access=None):
    who = owner(toolset, tool, access)
    return ("Refused by the kit: %s_%s belongs to %s, not to %s. Ask the main session to hand this step to %s (one agent per tool area keeps two writers "
            "from fighting over the editor). Do not work around this refusal." % (toolset, tool, "the main session" if who == "chief" else who, agent, "the main session" if who == "chief" else who))


def split_map(path=None):
    """{owner: [keys]} over a saved tool map (latest.json); {} when there is none."""
    path = path or os.path.join(os.environ.get("UEFN_KIT_MCP_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills", "mcp-tool-contracts", "references", "map"), "latest.json")
    try:
        tools = json.load(open(path, encoding="utf-8-sig")).get("tools", {})
    except (OSError, ValueError):
        return {}
    out = {}
    for k, v in tools.items():
        ts, tl = k.split("/", 1)
        out.setdefault(owner(ts, tl, (v or {}).get("a")), []).append(k)
    return out


def main(argv):
    if argv and argv[0] == "--list":
        sm = split_map(argv[1] if len(argv) > 1 else None)
        if not sm:
            print("no saved tool map on this computer")
            return 0
        for who in sorted(sm, key=lambda x: -len(sm[x])):
            print("%-14s %4d" % (who, len(sm[who])))
        return 0
    if argv and "/" in argv[0]:
        ts, tl = argv[0].split("/", 1)
        print(owner(ts, tl, argv[1] if len(argv) > 1 else None))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
