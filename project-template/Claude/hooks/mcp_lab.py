"""Exploration lab for UEFN's MCP: try every tool, log every call, learn how the toolset really works.
Use from short scratch scripts (run from the project folder):
    import sys; sys.path.insert(0, 'Claude/hooks'); import mcp_lab as L
    print(L.describe('UMGToolSet.UMGToolSet'))            # tool | access guess | required args | what it does
    L.schema('UMGToolSet.UMGToolSet', 'AddWidget')         # full input and output schema
    L.call('UMGToolSet.UMGToolSet', 'GetWidgets', {...})   # ONE call, always logged to Claude/logs/explore-ledger.jsonl

Two modes, both enforced by the code (a refusal is reported, never worked around):
 * NORMAL (a real project): a tool that is not clearly read-only is refused unless every path in its arguments is inside
   <LAB_ROOT>/KitTest, a class (/Script/..., /Engine/..., a *_C widget class), or an object the lab created itself (L.created).
   Level writes need LAB_LEVEL=1; session and Verse-build tools need LAB_SESSION=1; Verse writes only on a new file named *_kit_probe*;
   delete / import / python / console are refused.
 * LABORATORY (LAB_AGGRESSIVE=1): for a disposable project only. It starts ONLY if (1) the file Claude/LAB-PROJECT.txt exists,
   (2) LAB_ROOT is set (for example /lab_mcp) and (3) the open level really lives under LAB_ROOT. Then everything inside LAB_ROOT is
   allowed, including delete, level writes, sessions, Verse edits and Python. Still refused: quitting or restarting the editor and any
   disk path outside the project. A path outside the lab is accepted only as the SOURCE of something the call creates inside the lab
   (template, class, catalog asset; /Niagara, /Engine, /Game, /Script...), never as the target of a write."""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcp_map as m
import toolset_diff as td

AGGR = os.environ.get("LAB_AGGRESSIVE") == "1"

def _default_root():
    """Laboratory mode without LAB_ROOT (a script started without the variable): the project folder's own name
    (<project>/Content/Claude/hooks -> /<project>). lab_check still proves the OPEN LEVEL lives there, so this is no weaker."""
    if not (AGGR and os.path.isfile(os.path.join(HERE, "..", "LAB-PROJECT.txt"))):
        return ""
    proj = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
    return "/" + proj if proj and re.fullmatch(r"[A-Za-z0-9_]+", proj) else ""


ROOT = re.sub(r"^/[0-9a-fA-F-]{36}/", "/", os.environ.get("LAB_ROOT") or "") or _default_root() or ("" if AGGR else "/root_pillars")
SANDBOX = ROOT + "/KitTest"


def _extra_roots():
    """Laboratory mode only: more top-level folders of the SAME disposable project that count as lab (for example an imported
    model in /mech-drone). Declared by the owner in Claude/LAB-PROJECT.txt (a line `extra-root: /mech-drone`) or LAB_EXTRA_ROOTS=/a,/b.
    Never a path of another project: only plain /Folder names, never a mount name such as /Game or /Engine."""
    out = []
    items = [x for x in (os.environ.get("LAB_EXTRA_ROOTS") or "").split(",")]
    try:
        with open(os.path.join(HERE, "..", "LAB-PROJECT.txt"), encoding="utf-8") as f:
            items += [l.split(":", 1)[1] for l in f if l.lower().startswith("extra-root:")]
    except OSError:
        pass
    for x in items:
        x = x.strip().rstrip("/")
        if AGGR and re.fullmatch(r"/[A-Za-z0-9_\-]+", x) and x not in ("/Game", "/Engine", "/Script", "/Niagara", "/Fortnite", "/FortniteGame", "/root_pillars"):
            out.append(x)
    return out


EXTRA = _extra_roots()
LOGS = os.path.join(HERE, "..", "logs")
LEDGER = os.path.join(LOGS, "explore-ledger.jsonl")
SRC = os.environ.get("LAB_SRC", "agent")
MARKER = os.path.join(HERE, "..", "LAB-PROJECT.txt")
NEVER = re.compile(r"delete|remove_asset|import|StartSession|StopSession|StartGame|StopGame|PushChanges|BuildAll|exit|quit|restart|shutdown|open_level|load_level|new_level|save_level|SetCVar|set_cvar|console|python", re.I)
HARD_NEVER = re.compile(r"exit|quit|restart|shutdown", re.I)
DISK_PATH = re.compile(r"^[A-Za-z]:[\\/]|^\\\\|^/(home|mnt|Users|usr|etc|var)/", re.I)
SESSION_OK = os.environ.get("LAB_SESSION") == "1"
LEVEL_OK = os.environ.get("LAB_LEVEL") == "1"
LEVEL_SETS = re.compile(r"Actor|Scene|Entity|Device|Valkyrie", re.I)
CREATE_RX = re.compile(r"^(spawn|place|create|add|duplicate|clone|make)", re.I)
created = set()
_client = None
_tools = {}
_checked = False


def client():
    global _client
    if _client is None:
        _client = m.Client(m.find_url(os.path.join(HERE, "..", "..")), 90.0)
        _client.start()
    return _client


def describe(ts):
    d = m.parse_text(client().call("describe_toolset", {"toolset_name": ts}))
    out = []
    for t in d.get("tools", []):
        n = t["name"].split(".")[-1]
        _tools[ts + "/" + n] = t
        req = (t.get("inputSchema") or {}).get("required") or []
        out.append("%s | %s | %s | %s" % (n, td.access(n), ",".join(req), td.first_sentence(t.get("description", ""))))
    return "\n".join(out)


def schema(ts, tool):
    if ts + "/" + tool not in _tools:
        describe(ts)
    t = _tools.get(ts + "/" + tool)
    return {"description": t.get("description"), "input": t.get("inputSchema"), "output": t.get("outputSchema"), "annotations": t.get("annotations")} if t else None


def _strings(o, depth=0):
    if isinstance(o, str):
        yield o
        t = o.strip()
        if depth < 4 and t[:1] in "{[" and t[-1:] in "}]":  # B-002: a JSON TEXT in an argument (values="{...}") is inspected too
            try:
                yield from _strings(json.loads(t), depth + 1)
            except Exception:  # noqa
                pass
    elif isinstance(o, dict):
        for v in o.values():
            yield from _strings(v, depth)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v, depth)


_GUID = re.compile(r"^/[0-9a-fA-F-]{36}/")
SRC_ROOTS = re.compile(r"^/(Niagara|Engine|Game|Script|FortniteGame|Fortnite|NiagaraAdditions)(/|\.|$)")
# catalog / plugin mounts (devices, entity components, sample meshes): only as the SOURCE of something CREATED in the lab
# (place a device, create an entity, duplicate a mesh into the lab). add / assign / apply / attach are not enough for these:
# assign_physics_asset(<plugin mesh>, <lab asset>) would change the plugin's mesh.
CAT_ROOTS = re.compile(r"^/(CreativeCoreDevices|VerseDevices|CR_Legacy|EntityFramework|AnimToTexture|FigureCosmetics|" + (os.environ.get("LAB_SOURCE_MOUNTS") or "NoSuchMount").replace(",", "|") + r")(/|\.|$)")
CAT_TOOL = re.compile(r"^(create|duplicate|clone|copy|make|spawn|place|instantiate|addcomponent|addeventbinding)", re.I)
SRC_TOOL = re.compile(r"^(create|duplicate|clone|copy|make|spawn|place|add|apply|assign|attach|instantiate|replace)", re.I)
SRC_DENY = re.compile(r"delete|remove|rename|move|save|import|export|cvar|console|python|exit|quit|restart|shutdown", re.I)
PLACE_TOOL = re.compile(r"^(spawn|place|add_?actor|create_?entity|instantiate)", re.I)


def _lab_form(s):
    """UEFN names objects of the open project /<project-guid>/<project-name>...: same thing as /<project-name>..."""
    return _GUID.sub("/", s, 1) if (AGGR and _GUID.match(s)) else s


def _source_ref_ok(tool, s, strs):
    """Laboratory only: a SOURCE reference outside the lab (a template, a class, a catalog asset) is fine when the tool creates
    something new, and the result lands inside the lab (another path of the call is inside it) or in the level (the level is the lab)."""
    if not AGGR or SRC_DENY.search(tool):
        return False
    if not ((SRC_ROOTS.match(s) and SRC_TOOL.match(tool)) or (CAT_ROOTS.match(s) and CAT_TOOL.match(tool))):
        return False
    return bool(PLACE_TOOL.match(tool)) or any(x.startswith("/") and x != s and _path_ok(x) for x in strs)


def _path_ok(s):
    s = _lab_form(s)
    if AGGR and (s == "/" or re.search(r"[\s*?\[\]()|\\^$+]", s)):
        return True  # the root folder, or a regex / glob pattern (Grep "/Bad.*Value"): not an asset path
    if AGGR and re.match(r"/_Verse\.%s-" % re.escape(ROOT.strip("/")), s):
        return True  # the lab's own Verse classes (/<guid>/_Verse.<project>-<module>)
    if AGGR and any(re.match(re.escape(r) + r"([/.:]|$)", s) for r in [ROOT] + EXTRA):
        return True
    base = s.split(":", 1)[0]
    if s.startswith(("/Script/", "/Engine/")) or (s.endswith("_C") and s.startswith(("/Game/Valkyrie/UMG/", ROOT + "/VerseUIKit/Widgets/"))):
        return True
    if s in created or base in created or any(s.startswith(c) for c in created):
        return True
    return s.startswith(ROOT + "/") if AGGR else s.startswith(SANDBOX)


def _is_read(ts, tool):
    ro = (((_tools.get(ts + "/" + tool) or {}).get("annotations")) or {}).get("readOnlyHint")
    if ro is True:
        return True
    return ro is None and td.access(tool) == "read"


def lab_check():
    """Laboratory mode only: prove this really is the disposable project. Returns '' when fine, else the reason."""
    if not AGGR:
        return ""
    if not os.path.isfile(MARKER):
        return "laboratory mode needs the file Claude/LAB-PROJECT.txt (the owner creates it in the disposable project)"
    if not ROOT.startswith("/") or len(ROOT) < 3:
        return "laboratory mode needs LAB_ROOT, for example /lab_mcp"
    lvl, err = "", None
    for _try in range(2):  # one retry: right after a session change the MCP can answer HTTP 400 / time out once
        try:
            lvl = m.parse_text(client().call("call_tool", {"toolset_name": "editor_toolset.toolsets.scene.SceneTools", "tool_name": "get_current_level", "arguments": {}}))
            lvl = (lvl or {}).get("returnValue", "") if isinstance(lvl, dict) else ""
            err = None
            break
        except Exception as e:  # noqa
            err = e
            time.sleep(2)
    if err is not None:
        return "could not read the open level to confirm the laboratory: %s" % str(err)[:80]
    lv = str(lvl)
    # UEFN reports the project's own level as /<project-guid>/<project-name>: accept it when the name is the LAB_ROOT name
    guid_ok = re.fullmatch(r"/[0-9a-fA-F-]{36}/" + re.escape(ROOT.strip("/")) + r"(/.*)?", lv) is not None
    if not (lv == ROOT or lv.startswith(ROOT + "/") or guid_ok):
        return "the open level is %r, not under %s: this is NOT the laboratory project, nothing was done" % (lvl, ROOT)
    return ""


def refusal(ts, tool, args):
    global _checked
    if AGGR and not _checked:
        bad = lab_check()
        if bad:
            return bad
        _checked = True
    strs = list(_strings(args))
    if HARD_NEVER.search(tool):
        return "never: quitting or restarting the editor ends the MCP server"
    if any(DISK_PATH.match(s) for s in strs) and not _is_read(ts, tool):
        return "refused: a path on the disk outside the project"
    if AGGR:
        if _is_read(ts, tool):
            return ""
        for s in strs:
            if s.startswith("/") and not _path_ok(s) and not _source_ref_ok(tool, s, strs):
                return "refused even in the laboratory, path outside %s: %s" % (ROOT, s[:80])
        return ""
    if NEVER.search(tool):
        if re.search(r"StartSession|StopSession|StartGame|StopGame|PushChanges|BuildAll", tool) and SESSION_OK:
            return ""
        refs = [s for s in strs if s.startswith("/")]
        if re.search(r"delete|remove", tool, re.I) and LEVEL_OK and LEVEL_SETS.search(ts) and refs and all(r in created or r.split(":", 1)[0] in created for r in refs):
            return ""  # clean-up of objects this lab created itself
        return "never-list: report it to the owner instead"
    if "VerseToolset" in ts and not _is_read(ts, tool) and not any("_kit_probe" in s for s in strs):
        return "Verse writes only on a NEW file whose name contains _kit_probe"
    if _is_read(ts, tool):
        return ""
    for s in strs:
        if s.startswith("/") and not _path_ok(s):
            return "write refused, path outside the sandbox: " + s[:90]
    if LEVEL_SETS.search(ts) and not LEVEL_OK:
        return "level write refused: set LAB_LEVEL=1 first (the owner approves it)"
    return ""


def _log(rec):
    os.makedirs(LOGS, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def call(ts, tool, args=None, peek=600):
    """One logged call. Returns the parsed reply or raises RuntimeError with the server's message."""
    args = args or {}
    if ts + "/" + tool not in _tools:
        try:
            describe(ts)
        except Exception:  # noqa
            pass
    why = refusal(ts, tool, args)
    rec = {"t": time.strftime("%H:%M:%S"), "toolset": ts, "tool": tool, "args": json.dumps(args)[:400]}
    if SRC != "agent":
        rec["src"] = SRC  # "battery": made by mcp_cover (coverage, soak, session); these rows are not lessons
    if why:
        rec.update(r="refused", why=why)
        _log(rec)
        raise RuntimeError(why)
    t0 = time.time()
    try:
        text = client().call("call_tool", {"toolset_name": ts, "tool_name": tool, "arguments": args})
    except m.ToolError as e:
        rec.update(r="rejected", why=" ".join(str(e).split())[:300], sec=round(time.time() - t0, 2))
        _log(rec)
        raise RuntimeError(str(e))
    except Exception as e:  # noqa
        rec.update(r="no_answer", why=str(e)[:200])
        _log(rec)
        raise
    rec.update(r="ok", n=len(text), peek=" ".join(text.split())[:peek], sec=round(time.time() - t0, 2))
    _log(rec)
    parsed = m.parse_text(text)
    if CREATE_RX.match(tool) and not _is_read(ts, tool):
        for s in _strings(parsed):
            if s.startswith("/"):
                created.add(s.split(":", 1)[0])
    return parsed if parsed is not None else text


def val(r):
    return r.get("returnValue") if isinstance(r, dict) else r


def coverage():
    """Distinct tools with at least one ok / rejected call, from the ledger."""
    ok, rej = set(), set()
    try:
        for line in open(LEDGER, encoding="utf-8"):
            r = json.loads(line)
            k = r["toolset"] + "/" + r["tool"]
            if r["r"] == "ok":
                ok.add(k)
            elif r["r"] == "rejected":
                rej.add(k)
    except OSError:
        pass
    return {"ok": len(ok), "alive_only": len(rej - ok), "of": 388}
