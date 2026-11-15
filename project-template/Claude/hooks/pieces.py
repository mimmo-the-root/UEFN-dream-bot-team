#!/usr/bin/env python3
"""pieces.py - the orchestrator for big tasks (v1.124.24): small pieces, each in a fresh short session, that never stop.

Measured on the owner's runs: 67% of every request is the conversation itself, re-read on every call (about 58k tokens;
free models then take minutes per answer). So a big task is cut into small pieces and each piece runs in a FRESH, short
session that reads only its brief and the notes of the pieces before it.

A piece that fails was too big: it goes back to the orchestrator and is cut again into 2-6 smaller pieces (up to 3 levels).
A piece that still fails at the smallest size is tried on other free models, one after the other (at least 10 when the
router offers them: `dream:<provider>/<model>`). Only when every model failed is it SKIPPED, and the run goes on with the
next pieces, which are told what was skipped. The run never stops on a failure: it completes as many pieces as it can.

  python Claude/hooks/pieces.py split T-012 "goal | files | done when" ...
  python Claude/hooks/pieces.py status [T-012]
  python Claude/hooks/pieces.py next T-012              the brief of the next piece (to do it by hand in a fresh session)
  python Claude/hooks/pieces.py done T-012 2.1 --note "what changed, where, what the next piece must know"
  python Claude/hooks/pieces.py fail T-012 2.1 --note "exact error"
  python Claude/hooks/pieces.py run T-012 [--mode free|auto|plan] [--max 40] [--timeout 900] [--models 12]

Pieces live in Claude/docs/pieces/<task>.json; every try is recorded in the piece (model, result). Standard library only."""
import json, os, re, subprocess, sys, time, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DIR = os.path.join(ROOT, "Claude", "docs", "pieces")
DONE_RX = re.compile(r"PIECE DONE:\s*(.+)")
BLOCK_RX = re.compile(r"PIECE BLOCKED:\s*(.+)")
SUB_RX = re.compile(r"^\s*SUBPIECE:\s*(.+)$", re.M)
NOTE_MAX = 400
MAX_DEPTH = 3          # a piece can be cut again twice (1 -> 1.2 -> 1.2.3)
MIN_MODELS = 10        # models tried on a piece that still fails at the smallest size
ROUTER = "http://127.0.0.1:8787"


def _path(task):
    if not re.match(r"^[A-Za-z0-9_.-]{1,40}$", task or ""):
        raise SystemExit("task id must be letters, digits, - _ . (e.g. T-012)")
    return os.path.join(DIR, task + ".json")


def load(task):
    try:
        with open(_path(task), encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError:
        raise SystemExit("no pieces for %s: split it first" % task)
    for p in d["pieces"]:   # files written by 1.124.21 used a number
        p["n"] = str(p["n"])
        p.setdefault("depth", p["n"].count(".") + 1)
        p.setdefault("tries", [])
        if isinstance(p["tries"], int):
            p["tries"] = [{"model": "default", "result": "failed"}] * p["tries"]
    return d


def save(task, d):
    os.makedirs(DIR, exist_ok=True)
    tmp = _path(task) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    os.replace(tmp, _path(task))


def _piece(n, spec, depth):
    parts = [x.strip() for x in spec.split("|")]
    return {"n": n, "goal": parts[0], "files": parts[1] if len(parts) > 1 else "", "check": parts[2] if len(parts) > 2 else "",
            "status": "todo", "depth": depth, "tries": [], "note": ""}


def split(task, specs):
    pieces = [_piece(str(i), s, 1) for i, s in enumerate(specs, 1) if s.split("|")[0].strip()]
    if not pieces:
        raise SystemExit("give at least one piece: \"goal | files | done when\"")
    save(task, {"task": task, "created": time.strftime("%Y-%m-%d %H:%M"), "pieces": pieces})
    return pieces


def nxt(d):
    for p in d["pieces"]:
        if p["status"] in ("todo", "failed"):
            return p
    return None


def find(d, n):
    for p in d["pieces"]:
        if p["n"] == str(n):
            return p
    raise SystemExit("no piece %s in %s" % (n, d["task"]))


def brief(d, p):
    """The whole prompt of a piece: short on purpose. The notes of the pieces before it replace the old conversation."""
    before = [q for q in d["pieces"][:d["pieces"].index(p)] if q["status"] in ("done", "skipped")]
    notes = ["- piece %s %s: %s" % (q["n"], "done" if q["status"] == "done" else "SKIPPED (not done, work around it)", q["note"]) for q in before if q["note"]][-5:]
    lines = ["Task %s, piece %s of %d. Do ONLY this piece, in at most about 15 tool calls." % (d["task"], p["n"], sum(1 for q in d["pieces"] if q["status"] != "split")),
             "Goal: " + p["goal"]]
    if p["files"]:
        lines.append("Files (read only these, and only the parts you need): " + p["files"])
    if p["check"]:
        lines.append("Done when: " + p["check"])
    if notes:
        lines.append("Notes from the pieces before:")
        lines += notes
    if p["tries"]:
        lines.append("Earlier tries of this piece failed: " + "; ".join(t.get("why", t["result"])[:120] for t in p["tries"][-2:]) + " - do not repeat them.")
    lines += ["Follow CLAUDE.md (task %s is the active task; do not open new tasks, do not mark it Done)." % d["task"],
              "If something is missing, find a way around it inside this piece; never stop to ask.",
              "End with ONE line: `PIECE DONE: <what changed, where, what the next piece must know>` (under 300 characters),",
              "or `PIECE BLOCKED: <the exact reason>` if you cannot finish it."]
    return "\n".join(lines)


def split_brief(d, p):
    why = "; ".join(t.get("why", t["result"])[:150] for t in p["tries"][-2:])
    return "\n".join([
        "You are the orchestrator of task %s. Piece %s failed, so it is too big for one short session: cut it into 2 to 6 smaller pieces." % (d["task"], p["n"]),
        "Piece goal: " + p["goal"], "Files: " + (p["files"] or "-"), "Done when: " + (p["check"] or "-"), "Why it failed: " + (why or "unknown"),
        "Each smaller piece must be finishable in about 10 tool calls, have its own check, and together they must reach the goal.",
        "Read at most the files named, only what you need. Do not do the work.",
        "Answer ONLY with 2 to 6 lines, each: `SUBPIECE: goal | files | done when`."])


def mark(task, n, status, note, model="by hand"):
    d = load(task)
    p = find(d, n)
    p["status"], p["note"] = status, (note or "")[:NOTE_MAX]
    if status == "failed":
        p["tries"].append({"model": model, "result": "failed", "why": (note or "")[:200]})
    save(task, d)
    return p


def status_text(d):
    live = [p for p in d["pieces"] if p["status"] != "split"]
    out = ["%s: %d of %d pieces done, %d skipped" % (d["task"], sum(p["status"] == "done" for p in live), len(live), sum(p["status"] == "skipped" for p in live))]
    for p in d["pieces"]:
        out.append("  %s%s [%s] %s%s" % ("  " * (p["depth"] - 1), p["n"], p["status"], p["goal"][:80], ("  - " + p["note"][:110]) if p["note"] else ""))
    return "\n".join(out)


def session_settings(mode):
    """Same per-session settings as cod.cmd (dream_router.py session-settings): a forced mode for the piece sessions."""
    r = os.path.join(os.path.expanduser("~"), ".claude", "hooks", "dream_router.py")
    if not mode or not os.path.isfile(r):
        return None
    try:
        out = subprocess.run([sys.executable, r, "session-settings", mode], capture_output=True, text=True, timeout=20).stdout.strip()
        return out if out and os.path.isfile(out) else None
    except (OSError, subprocess.SubprocessError):
        return None


def router_candidates(n):
    """Free models the router offers right now, best first, one provider after the other."""
    try:
        with urllib.request.urlopen(ROUTER + "/router/candidates?n=%d" % n, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("models", [])
    except (OSError, ValueError):
        return []


def _claude(prompt, sf, model, claude, timeout):
    cmd = [claude, "-p", prompt, "--permission-mode", "acceptEdits"] + (["--settings", sf] if sf else []) + (["--model", "dream:" + model] if model else [])
    try:
        env = dict(os.environ, UEFN_KIT_HEADLESS="1", UEFN_KIT_NO_NUDGE="1")  # a piece does only its brief: no session-start chores
        return cmd, subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace", env=env).stdout or ""
    except subprocess.TimeoutExpired:
        return cmd, "PIECE BLOCKED: no answer in %d s" % timeout
    except OSError as e:
        return cmd, "PIECE BLOCKED: cannot start claude (%s)" % e


def run(task, mode=None, max_pieces=40, timeout=900, n_models=12, claude="claude", runner=None, models=None):
    """Run the pieces until none is left to try. runner(prompt, cmd) -> output and models(n) -> list are replaceable in tests.
    Returns [(piece, result)]: done / split into N / done on <model> / skipped."""
    sf = session_settings(mode)
    get_models = models or (router_candidates if mode != "plan" else (lambda n: []))
    call = (lambda prompt, model: (lambda c: (c, runner(prompt, c)))([claude, "-p", prompt] + (["--model", "dream:" + model] if model else []))) if runner \
        else (lambda prompt, model: _claude(prompt, sf, model, claude, timeout))
    log, started = [], 0
    while started < max_pieces:
        d = load(task)
        p = nxt(d)
        if not p:
            break
        started += 1
        _, out = call(brief(d, p), None)
        if _ok(task, p["n"], out, "default", log):
            continue
        # too big: back to the orchestrator, cut again
        d = load(task); p = find(d, p["n"])
        if p["depth"] < MAX_DEPTH:
            _, sub = call(split_brief(d, p), None)
            specs = [x for x in SUB_RX.findall(sub or "") if x.split("|")[0].strip()][:6]
            if len(specs) >= 2:
                i = d["pieces"].index(p)
                kids = [_piece("%s.%d" % (p["n"], k), s, p["depth"] + 1) for k, s in enumerate(specs, 1)]
                p["status"], p["note"] = "split", "cut into %d smaller pieces" % len(kids)
                d["pieces"][i + 1:i + 1] = kids
                save(task, d)
                log.append((p["n"], "split into %d" % len(kids)))
                continue
        # smallest size: try other models, one after the other
        tried = {t["model"] for t in p["tries"]}
        done = False
        for m in [x for x in get_models(max(n_models, MIN_MODELS)) if x not in tried]:
            d = load(task); p = find(d, p["n"])
            _, out = call(brief(d, p), m)
            if _ok(task, p["n"], out, m, log):
                done = True
                break
        if not done:
            d = load(task); p = find(d, p["n"])
            p["status"] = "skipped"
            p["note"] = "not done after %d tries (%s)" % (len(p["tries"]), (p["tries"][-1].get("why", "") if p["tries"] else "")[:150])
            save(task, d)
            log.append((p["n"], "skipped"))
    return log


def _ok(task, n, out, model, log):
    m, b = DONE_RX.search(out or ""), BLOCK_RX.search(out or "")
    d = load(task); p = find(d, n)
    if m and not b:
        p["status"], p["note"] = "done", m.group(1).strip()[:NOTE_MAX]
        p["tries"].append({"model": model, "result": "done"})
        save(task, d)
        log.append((n, "done" if model == "default" else "done on " + model))
        return True
    why = b.group(1).strip() if b else "no PIECE DONE line; last output: " + (out or "").strip()[-160:]
    p["status"] = "failed"
    p["tries"].append({"model": model, "result": "failed", "why": why[:200]})
    save(task, d)
    return False


def main(a):
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); return 0
    cmd = a[0]
    if cmd == "split":
        ps = split(a[1], a[2:]); print("%s split in %d pieces. Run: python Claude/hooks/pieces.py run %s" % (a[1], len(ps), a[1])); return 0
    if cmd == "status":
        if len(a) > 1:
            print(status_text(load(a[1])))
        else:
            fs = sorted(f[:-5] for f in os.listdir(DIR) if f.endswith(".json")) if os.path.isdir(DIR) else []
            print("\n".join(status_text(load(t)) for t in fs) or "no split task")
        return 0
    if cmd == "next":
        d = load(a[1]); p = nxt(d)
        print(brief(d, p) if p else "%s: no piece left. Hand the task to the reviewers." % a[1]); return 0
    if cmd in ("done", "fail"):
        note = a[a.index("--note") + 1] if "--note" in a else ""
        p = mark(a[1], a[2], "done" if cmd == "done" else "failed", note); print("piece %s: %s" % (p["n"], p["status"])); return 0
    if cmd == "run":
        opt = lambda k, dflt: a[a.index(k) + 1] if k in a else dflt
        res = run(a[1], opt("--mode", None), int(opt("--max", 40)), int(opt("--timeout", 900)), int(opt("--models", 12)))
        for n, r in res:
            print("piece %s: %s" % (n, r))
        print(status_text(load(a[1])))
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
