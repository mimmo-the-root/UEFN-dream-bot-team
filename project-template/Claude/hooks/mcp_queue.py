"""Run the long MCP batteries one after the other, starting only when the current exploration has finished.
Start it in a SECOND terminal, in the project's Content folder, with the laboratory switches set (it uses no Claude tokens while it waits):
    $env:LAB_AGGRESSIVE = "1"; $env:LAB_ROOT = "/root_ai_lab"
    py -3 Claude/hooks/mcp_queue.py
It waits until the exploration is done: the file Claude/logs/lab-done.flag exists, OR the call ledger (Claude/logs/explore-ledger.jsonl)
has been silent for --idle minutes (default 40: the explorer can think and write for a long time between calls; the flag is the reliable signal) after it started. Then it runs coverage, soak, session and mapcheck in that order
(a failure in one never stops the next) and writes Claude/docs/mcp/QUEUE-REPORT.md and Claude/logs/queue-done.flag.
It remembers what already ran (Claude/logs/queue-state.json), so you can stop and start it again. --now skips the waiting."""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
LOGS = os.path.join(HERE, "..", "logs")
DOCS = os.path.join(HERE, "..", "docs", "mcp")
LEDGER = os.path.join(LOGS, "explore-ledger.jsonl")
DONE = os.path.join(LOGS, "lab-done.flag")
STATE = os.path.join(LOGS, "queue-state.json")
LOG = os.path.join(LOGS, "queue.log")
ORDER = ("coverage", "soak", "session", "mapcheck")


def say(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        os.makedirs(LOGS, exist_ok=True)
        open(LOG, "a", encoding="utf-8").write(line + "\n")
    except OSError:
        pass


def exploration_finished(idle_min, now=None, ledger=LEDGER, done=DONE):
    """True when the explorer said it is done, or the ledger has gone quiet for idle_min minutes (and was used at all)."""
    now = now or time.time()
    if os.path.isfile(done):
        return True, "lab-done.flag found"
    try:
        quiet = (now - os.path.getmtime(ledger)) / 60.0
    except OSError:
        return False, "no ledger yet"
    if quiet >= idle_min:
        return True, "ledger quiet for %.0f minutes" % quiet
    return False, "ledger active %.0f min ago" % quiet


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {"done": {}}


def run_queue(args, wait=True, poll=30.0):
    st = load_state()
    if wait:
        say("waiting for the exploration to finish (flag or %d quiet minutes)..." % args.idle)
        while True:
            fin, why = exploration_finished(args.idle)
            if fin:
                say("exploration finished: " + why)
                break
            time.sleep(poll)
    import mcp_cover as C
    ns = argparse.Namespace(fraction=1.0, budget=args.coverage_budget, n=args.n, suite="", wait=getattr(args, "wait", 180.0))
    for name in ORDER:
        if name in st["done"]:
            say("skip %s (already done)" % name)
            continue
        ns.budget = {"coverage": args.coverage_budget, "soak": args.soak_budget}.get(name, 30.0)
        ns.n = {"soak": args.soak_n, "session": args.session_n}.get(name, args.n)
        say("start %s" % name)
        t0 = time.time()
        try:
            res = C.SUITES[name](ns)
        except Exception as e:  # noqa
            res = {"suite": name, "crash": str(e)[:300]}
        res["minutes"] = round((time.time() - t0) / 60.0, 1)
        st["done"][name] = res
        os.makedirs(LOGS, exist_ok=True)
        json.dump(st, open(STATE, "w", encoding="utf-8"), indent=1)
        say("done %s in %.1f min: %s" % (name, res["minutes"], json.dumps(res)[:300]))
    md = ["# Queue report", "", "Finished %s." % time.strftime("%Y-%m-%d %H:%M"), ""]
    for name in ORDER:
        r = st["done"].get(name, {})
        md.append("- **%s** (%s min): %s" % (name, r.get("minutes", "?"), json.dumps({k: v for k, v in r.items() if k not in ("detail", "minutes", "drift")})[:400]))
        if r.get("drift"):
            md.append("  - latency drift: " + json.dumps(r["drift"])[:400])
    md += ["", "Details: coverage.json and COVERAGE.md, soak.json, session-loop.json in this folder."]
    os.makedirs(DOCS, exist_ok=True)
    open(os.path.join(DOCS, "QUEUE-REPORT.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    open(os.path.join(LOGS, "queue-done.flag"), "w").write(time.strftime("%Y-%m-%d %H:%M"))
    say("queue finished: QUEUE-REPORT.md written")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", action="store_true", help="do not wait for the exploration")
    ap.add_argument("--idle", type=int, default=40)
    ap.add_argument("--coverage-budget", type=float, default=120.0)
    ap.add_argument("--soak-budget", type=float, default=40.0)
    ap.add_argument("--soak-n", type=int, default=100)
    ap.add_argument("--session-n", type=int, default=5)
    ap.add_argument("--n", type=int, default=50)
    a = ap.parse_args(argv)
    return run_queue(a, wait=not a.now)


if __name__ == "__main__":
    sys.exit(main())
