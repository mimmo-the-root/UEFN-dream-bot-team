"""Long test batteries for UEFN's MCP, driven by the tools' own schemas (no hand-written test per tool).
Run from the project folder (the lab module enforces the safety rules; use a disposable project with LAB_AGGRESSIVE=1):
    py -3 Claude/hooks/mcp_cover.py --suite coverage [--fraction 0.2] [--budget 90]
    py -3 Claude/hooks/mcp_cover.py --suite soak [--n 100]        # repeat create/edit/compile/save/delete, watch the latency drift
    py -3 Claude/hooks/mcp_cover.py --suite session [--n 5]       # game-session loop with timings (always stops the session)
    py -3 Claude/hooks/mcp_cover.py --suite mapcheck              # the map still matches the server after the battery
    py -3 Claude/hooks/mcp_cover.py --suite all
How the coverage suite works: it reads every tool's input and output schema, builds a dependency graph from the TITLES of the
objects (a tool that returns a WidgetBlueprint is a producer of WidgetBlueprints; a tool that needs one is a consumer), makes the
fixtures it needs by calling producers, then calls every tool with arguments it resolved. Several passes: what failed or was
unresolved is retried with the objects created so far. Destructive tools (delete, remove, clear) go last. Results: status per tool in
Claude/docs/mcp/coverage.json and a readable Claude/docs/mcp/COVERAGE.md. With --fraction, each run takes the tools least covered so far."""
import argparse, json, math, os, re, statistics, sys, time, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mcp_lab as L
import mcp_map as m
import toolset_diff as td

OUT = os.path.join(HERE, "..", "docs", "mcp")
DESTRUCTIVE = re.compile(r"delete|remove|clear|reset|destroy|purge", re.I)
PRODUCER = re.compile(r"^(create|add|spawn|place|duplicate|clone|make|new|load)", re.I)
SCOPE_STR = re.compile(r"^(name|filter|query|pattern|search|text)$", re.I)
SCOPE_PATH = re.compile(r"(^|_)(folder|root|dir|directory)(_?path)?$|^folder|^root", re.I)
SIZEISH = re.compile(r"scale|width|height|size|radius|count|num|length|duration|speed|time", re.I)
ABSTRACT = {"/Script/UMG.Widget": "/Script/UMG.Overlay", "/Script/UMG.PanelWidget": "/Script/UMG.Overlay"}
RANK = {"ok": 0, "rejected": 1, "unresolved": 2, "error": 3, "refused": 4, "skipped": 5, "untried": 6}


def out_titles(sch):
    """Titles of the objects a tool returns: returnValue as object, or array of objects."""
    rv = (((sch or {}).get("properties") or {}).get("returnValue")) or {}
    if rv.get("type") == "array":
        rv = rv.get("items") or {}
    t = rv.get("title")
    return [t] if t and "refPath" in (rv.get("properties") or {}) else []


class Battery:
    def __init__(self, cover_dir):
        self.cover = cover_dir
        self.cat, self.pool, self.status, self.seq = {}, {}, {}, 0
        self.last_asset = None
        self.producers = {}
        self.busy = set()

    # ---- catalog
    def load(self):
        lt = L.client().call("list_toolsets", {})
        sets = m.toolset_names_from_text(lt) if not m.looks_json(lt) else m.toolset_names(m.parse_text(lt))
        for ts in sets:
            L.describe(ts)
        for key, t in L._tools.items():
            ts, tool = key.split("/", 1)
            ro = (t.get("annotations") or {}).get("readOnlyHint")
            acc = "read" if ro is True else "write" if ro is False else td.access(tool)
            self.cat[key] = {"ts": ts, "tool": tool, "in": t.get("inputSchema") or {}, "out": t.get("outputSchema") or {}, "access": acc}
            for title in out_titles(self.cat[key]["out"]):
                if PRODUCER.match(tool):
                    self.producers.setdefault(title, []).append(key)
        return len(self.cat)

    # ---- pool of real objects
    def remember(self, key, reply):
        titles = out_titles(self.cat[key]["out"])
        rv = L.val(reply)
        refs = []
        if isinstance(rv, dict):
            refs = [rv.get("refPath")] if rv.get("refPath") else []
        elif isinstance(rv, list):
            refs = [x.get("refPath") for x in rv if isinstance(x, dict) and x.get("refPath")]
        for t in titles:
            for r in refs:
                if r and r not in self.pool.setdefault(t, []):
                    (self.pool[t].insert(0, r) if PRODUCER.match(self.cat[key]["tool"]) else self.pool[t].append(r))
        # widgets inside a widget blueprint come back nested: harvest any {"widget": {"refPath"}} with its schema title
        if isinstance(rv, dict) and isinstance(rv.get("widget"), dict) and rv["widget"].get("refPath"):
            self.pool.setdefault("/Script/UMG.Widget", []).insert(0, rv["widget"]["refPath"])
        if isinstance(rv, dict) and isinstance(rv.get("returnValue"), str) is False:
            pass
        for r in refs:
            if r and "/" in r and ":" not in r:
                self.last_asset = r.split(".")[0]

    # ---- argument resolution
    def ref(self, title, depth):
        if title.startswith("Class@"):
            cls = title.split("@", 1)[1]
            return {"refPath": ABSTRACT.get(cls, cls)}
        if title in self.pool and self.pool[title]:
            return {"refPath": self.pool[title][0]}
        if depth < 3:
            for key in self.producers.get(title, []):
                if key in self.busy:
                    continue
                if self.run_one(key, depth + 1, quiet=True) == "ok" and self.pool.get(title):
                    return {"refPath": self.pool[title][0]}
        return None

    def value(self, pname, sch, depth, tool_key):
        d = sch.get("default") if "default" in sch else None
        cls = self.cat[tool_key]["ts"].split(".")[-1]
        if d is not None and d != cls and d != "":
            return d
        if sch.get("enum"):
            return sch["enum"][0]
        if sch.get("examples"):
            return sch["examples"][0]
        t = sch.get("type")
        if isinstance(t, list):
            t = next((x for x in t if x != "null"), "string")
        props = sch.get("properties") or {}
        if t == "object" and "refPath" in props:
            return self.ref(sch.get("title", ""), depth)
        if t == "object" or props:
            o = {}
            for k in sch.get("required") or []:
                v = self.value(k, props.get(k, {}), depth + 1, tool_key)
                if v is None:
                    return None
                o[k] = v
            return o
        if t == "array":
            it = sch.get("items") or {}
            if it.get("type") == "object" and "refPath" in (it.get("properties") or {}):
                r = self.ref(it.get("title", ""), depth)
                return [r] if r else None
            if it.get("type") == "string" and re.search(r"path", pname, re.I) and self.last_asset:
                return [self.last_asset]
            return []
        if t in ("integer", "number"):
            return 1 if SIZEISH.search(pname) else 0
        if t == "boolean":
            return False
        if t == "string":
            if re.search(r"folder|dir|root", pname, re.I):
                return self.cover
            if re.search(r"asset.*path|^path$|package|source|target|dest", pname, re.I) and self.last_asset:
                return self.last_asset if not re.search(r"new|dest|target", pname, re.I) else self.cover + "/Cover_" + str(self.seq)
            if re.search(r"name|label|id$", pname, re.I):
                self.seq += 1
                return "Cover_%d" % self.seq
            return ""
        return ""

    def args_for(self, key, depth):
        sch = self.cat[key]["in"]
        props = sch.get("properties") or {}
        args, missing = {}, []
        for k in sch.get("required") or []:
            v = self.value(k, props.get(k, {}), depth, key)
            if v is None:
                missing.append(props.get(k, {}).get("title") or k)
            else:
                args[k] = v
        for k, p in props.items():          # scope listings so they cannot return the whole engine
            if k in args or k in (sch.get("required") or []) or p.get("type") != "string":
                continue
            if SCOPE_PATH.search(k):
                args[k] = self.cover
            elif SCOPE_STR.match(k):
                args[k] = "Cover"
        return args, missing

    # ---- running
    def run_one(self, key, depth=0, quiet=False):
        c = self.cat[key]
        self.busy.add(key)
        try:
            args, missing = self.args_for(key, depth)
            if missing:
                if not quiet:
                    self.status[key] = {"s": "unresolved", "why": sorted(set(missing))[:4]}
                return "unresolved"
            t0 = time.time()
            try:
                r = L.call(c["ts"], c["tool"], args)
            except RuntimeError as e:
                msg = " ".join(str(e).split())[:200]
                s = "refused" if re.search(r"refused|never|laboratory|not the lab", msg, re.I) else "rejected"
                self.status[key] = {"s": s, "why": msg, "args": sorted(args)}
                return s
            except Exception as e:  # noqa
                self.status[key] = {"s": "error", "why": str(e)[:200]}
                return "error"
            self.status[key] = {"s": "ok", "sec": round(time.time() - t0, 2), "args": sorted(args)}
            self.remember(key, r)
            return "ok"
        finally:
            self.busy.discard(key)

    def order(self, keys):
        def rank(k):
            c = self.cat[k]
            if DESTRUCTIVE.search(c["tool"]):
                return 3
            if k in {p for ps in self.producers.values() for p in ps}:
                return 0
            return 1 if c["access"] == "read" else 2
        return sorted(keys, key=lambda k: (rank(k), k))

    def pick(self, fraction, prev):
        keys = list(self.cat)
        if fraction >= 1:
            return keys
        n = max(1, math.ceil(fraction * len(keys)))
        def prio(k):
            p = prev.get(k, {})
            return (RANK.get(p.get("s", "untried"), 6) * -1, p.get("run", 0), k)
        return sorted(keys, key=prio)[:n]

    def coverage(self, budget_s, fraction, prev, passes=3):
        deadline = time.time() + budget_s
        todo = self.order(self.pick(fraction, prev))
        for p in range(passes):
            for key in todo:
                if time.time() > deadline:
                    break
                if self.status.get(key, {}).get("s") == "ok":
                    continue
                self.run_one(key)
            todo = [k for k in todo if self.status.get(k, {}).get("s") != "ok"]
            if not todo:
                break
        return self.status


def write_reports(b, prev, run_no, seconds):
    os.makedirs(OUT, exist_ok=True)
    merged = dict(prev)
    for k, v in b.status.items():
        v = dict(v)
        v["run"] = run_no
        merged[k] = v
    json.dump(merged, open(os.path.join(OUT, "coverage.json"), "w", encoding="utf-8"), indent=1)
    total = len(b.cat)
    cnt = {s: sum(1 for v in merged.values() if v["s"] == s) for s in ("ok", "rejected", "unresolved", "error", "refused")}
    md = ["# MCP coverage", "", "Run %d, %.0f s. %d tools in the catalog." % (run_no, seconds, total), "",
          "| Status | Tools | Share |", "|---|---|---|"]
    for s, n in cnt.items():
        md.append("| %s | %d | %.0f%% |" % (s, n, 100.0 * n / max(1, total)))
    md.append("| never tried | %d | %.0f%% |" % (total - sum(cnt.values()), 100.0 * (total - sum(cnt.values())) / max(1, total)))
    md += ["", "ok = called and answered; rejected = answered with an error about its arguments (alive, recipe still needed); unresolved = no way yet to make the objects it needs; refused = the lab's safety rules.", ""]
    kinds = {}
    for v in merged.values():
        for w in v.get("why", []) if v["s"] == "unresolved" else []:
            kinds[w] = kinds.get(w, 0) + 1
    if kinds:
        md += ["## Objects we cannot make yet", ""] + ["- %s (blocks %d tools)" % (k, n) for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])[:25]] + [""]
    by = {}
    for k, v in merged.items():
        by.setdefault(k.split("/")[0], []).append((k.split("/", 1)[1], v))
    md += ["## By toolset", ""]
    for ts in sorted(by):
        oks = sum(1 for _, v in by[ts] if v["s"] == "ok")
        md.append("### %s: %d ok of %d tried" % (ts, oks, len(by[ts])))
        for tool, v in sorted(by[ts]):
            if v["s"] != "ok":
                md.append("- `%s` %s: %s" % (tool, v["s"], str(v.get("why", ""))[:120]))
        md.append("")
    open(os.path.join(OUT, "COVERAGE.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    return cnt


def load_prev():
    try:
        return json.load(open(os.path.join(OUT, "coverage.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def suite_coverage(a):
    t0 = time.time()
    b = Battery(L.ROOT + "/Cover")
    n = b.load()
    prev = load_prev()
    run_no = 1 + max([v.get("run", 0) for v in prev.values()] or [0])
    b.coverage(a.budget * 60, a.fraction, prev)
    cnt = write_reports(b, prev, run_no, time.time() - t0)
    return {"suite": "coverage", "catalog": n, "run": run_no, "this_run": len(b.status), "totals": cnt}


def suite_soak(a):
    """Repeat a full create-edit-compile-save-delete cycle and watch the editor's latency drift."""
    b = Battery(L.ROOT + "/Cover")
    b.load()
    steps = ["UMGToolSet.UMGToolSet/CreateWidgetBlueprint", "UMGToolSet.UMGToolSet/AddWidget", "UMGToolSet.UMGToolSet/CompileWidgetBlueprint",
             "editor_toolset.toolsets.asset.AssetTools/save_assets", "editor_toolset.toolsets.asset.AssetTools/delete"]
    steps = [s for s in steps if s in b.cat]
    probe = "EditorToolset.EditorAppToolset/GetCameraTransform"
    times = {s: [] for s in steps + [probe]}
    fails = 0
    t_end = time.time() + a.budget * 60
    for i in range(a.n):
        if time.time() > t_end:
            break
        b.pool.clear()
        for s in steps:
            t0 = time.time()
            b.status.pop(s, None)
            r = b.run_one(s)
            times[s].append(time.time() - t0)
            if r != "ok":
                fails += 1
        if probe in b.cat:
            t0 = time.time()
            b.run_one(probe)
            times[probe].append(time.time() - t0)
            if times[probe][-1] > 20:
                break
    drift = {}
    for s, v in times.items():
        if len(v) >= 20:
            first, last = statistics.mean(v[:10]), statistics.mean(v[-10:])
            drift[s.split("/")[-1]] = {"first10_s": round(first, 3), "last10_s": round(last, 3), "slower": last > 2 * first + 0.05}
    res = {"suite": "soak", "iterations": len(times[steps[0]]) if steps else 0, "failed_steps": fails, "drift": drift}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "soak.json"), "w", encoding="utf-8"), indent=1)
    return res


def suite_session(a):
    """Game-session loop: start, wait, read, stop. Timings per step, flakiness. The session is ALWAYS stopped."""
    S = "ValkyrieToolset.SessionToolset"
    out, ok_loops = [], 0
    b = Battery(L.ROOT + "/Cover")
    b.load()
    def step(tool, **kw):
        t0 = time.time()
        try:
            r = L.call(S, tool, kw)
            return True, round(time.time() - t0, 2), L.val(r)
        except Exception as e:  # noqa
            return False, round(time.time() - t0, 2), str(e)[:120]
    for i in range(a.n):
        rec = {"loop": i + 1}
        try:
            rec["start"] = step("StartSession")
            t0 = time.time()
            status = None
            bad = 0
            while time.time() - t0 < getattr(a, 'wait', 180):
                good, _, status = step("GetSessionStatus")
                if good and str(status).lower().startswith("connected"):
                    break
                bad = 0 if good else bad + 1
                if bad >= 3:
                    break                      # the tool itself does not answer: do not wait the full three minutes
                time.sleep(3)
            rec["connected_after_s"] = round(time.time() - t0, 1)
            rec["status"] = str(status)[:60]
            rec["game"] = step("StartGame")
            time.sleep(5)
            rec["state"] = step("GetGameState")
            rec["log"] = step("GetClientLogEntries", **({"pattern": "Error"} if "pattern" in (b.cat.get(S + "/GetClientLogEntries", {}).get("in", {}).get("properties") or {}) else {}))
            rec["stop_game"] = step("StopGame")
        finally:
            rec["stop_session"] = step("StopSession")
        loop_ok = all(v[0] for k, v in rec.items() if isinstance(v, tuple))
        ok_loops += 1 if loop_ok else 0
        out.append(rec)
    res = {"suite": "session", "loops": a.n, "clean_loops": ok_loops, "detail": out}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "session-loop.json"), "w", encoding="utf-8"), indent=1)
    return res


def suite_mapcheck(a):
    """After the battery the saved map must still match the server and nothing that worked may have stopped working."""
    r, code = m.now(tests=False)
    return {"suite": "mapcheck", "state": r.get("state"), "count": r.get("count"), "message": r.get("message", ""), "exit": code}


SUITES = {"coverage": suite_coverage, "soak": suite_soak, "session": suite_session, "mapcheck": suite_mapcheck}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="coverage", choices=list(SUITES) + ["all"])
    ap.add_argument("--fraction", type=float, default=1.0)
    ap.add_argument("--budget", type=float, default=90.0, help="minutes per suite")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--wait", type=float, default=180.0, help="seconds to wait for a game session to connect")
    a = ap.parse_args(argv)
    names = list(SUITES) if a.suite == "all" else [a.suite]
    results = []
    for n in names:
        try:
            results.append(SUITES[n](a))
        except Exception:  # noqa
            results.append({"suite": n, "crash": traceback.format_exc()[-500:]})
    print(json.dumps(results, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
