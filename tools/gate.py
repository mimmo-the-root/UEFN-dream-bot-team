#!/usr/bin/env python3
"""Contracts and gate built on plan.json (see tools/plan_json.py).

Usage:
  gate.py contracts --plan PLAN.json              print one contract per task as JSON
  gate.py check --plan PLAN.json --task T-NNN --state STATE.json [--dry-run] [--cwd DIR]

A contract: id, inputs, outputs, acceptance (command), tier.
check runs the acceptance command of a finished package (only if it starts with
python/python3/node/pytest, no shell). Verdicts: PASS (exit 0), FAIL (exit 1),
BLOCKED (exit 2). The 3rd failure of a package returns BLOCKED and a blocked
package is never run again: the rework counter lives in the STATE json file.
--dry-run only prints the command.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys

MAX_FAILS = 3
ALLOWED = ("python", "python3", "node", "pytest")
DEFAULT_TIER = "T2"


def make_contract(item):
    return {
        "id": item["id"],
        "inputs": list(item.get("inputs") or []),
        "outputs": list(item.get("outputs") or []),
        "acceptance": item.get("command", ""),
        "tier": item.get("tier") or DEFAULT_TIER,
    }


def build_contracts(plan):
    return [make_contract(it) for it in plan.get("items", [])]


def runnable(command):
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if parts and parts[0] in ALLOWED:
        return parts
    return None


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(path, state):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def gate(contract, state_path, dry_run=False, cwd=None, timeout=120):
    """Return (verdict, detail). Updates the state file unless dry_run."""
    state = load_state(state_path)
    fails = int(state.get(contract["id"], 0))
    if fails >= MAX_FAILS:
        return "BLOCKED", "already %d failures, no more reworks" % fails
    parts = runnable(contract["acceptance"])
    if dry_run:
        return "DRY-RUN", contract["acceptance"] + ("" if parts else "  (would NOT run: not an allowed command)")
    reason = None
    if parts is None:
        reason = "acceptance not runnable (must start with python/python3/node/pytest)"
    else:
        try:
            r = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            if r.returncode != 0:
                reason = "acceptance exit %d" % r.returncode
        except (OSError, subprocess.TimeoutExpired) as e:
            reason = "acceptance error: %s" % e
    if reason is None:
        missing = [o for o in contract["outputs"] if not os.path.exists(os.path.join(cwd or ".", o))]
        if missing:
            reason = "missing outputs: " + ", ".join(missing)
    if reason is None:
        return "PASS", "acceptance ok"
    fails += 1
    state[contract["id"]] = fails
    save_state(state_path, state)
    if fails >= MAX_FAILS:
        return "BLOCKED", "%s (failure %d of %d)" % (reason, fails, MAX_FAILS)
    return "FAIL", "%s (failure %d of %d)" % (reason, fails, MAX_FAILS)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["contracts", "check"])
    ap.add_argument("--plan", required=True)
    ap.add_argument("--task")
    ap.add_argument("--state")
    ap.add_argument("--cwd")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    with open(a.plan, "r", encoding="utf-8") as f:
        contracts = build_contracts(json.load(f))
    if a.mode == "contracts":
        print(json.dumps(contracts, indent=2, ensure_ascii=False))
        return 0
    if not a.task or not a.state:
        ap.error("check needs --task and --state")
    match = [c for c in contracts if c["id"] == a.task]
    if not match:
        print("FAIL no contract for " + a.task)
        return 1
    verdict, detail = gate(match[0], a.state, a.dry_run, a.cwd)
    print("%s %s %s" % (verdict, a.task, detail))
    return {"PASS": 0, "DRY-RUN": 0, "FAIL": 1, "BLOCKED": 2}[verdict]


if __name__ == "__main__":
    sys.exit(main())
