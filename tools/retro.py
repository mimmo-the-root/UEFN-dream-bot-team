#!/usr/bin/env python3
"""Retro agent (free): weekly read of telemetry, proposes at most 3 config changes.

Reads (read-only): <telemetry-dir>/*.json and <usage-dir>/*.json (e.g. token-ledger.json).
Writes ONLY the one pipeline JSON given with --pipeline. Never edits the real config.
The current config (optional --config) is only read, to fill rollback values.

  retro.py propose --telemetry-dir D [--usage-dir D] [--config F] --pipeline P [--debug]
  retro.py check   --telemetry-dir D [--usage-dir D] --pipeline P [--debug]

check re-reads the metrics and marks a proposal "rolled_back" (status + rollback
value to apply) when its metric got worse than the baseline stored at proposal time.
"""
import argparse
import json
import sys
import time
from pathlib import Path

MAX_CHANGES = 3
DEBUG = False


def dbg(msg):
    """Diagnostic logging, gated by the --debug flag."""
    if DEBUG:
        print("[retro] " + msg, file=sys.stderr)


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        dbg("skip unreadable file " + str(path))
        return {}


def read_dir(d):
    out = {}
    if d and Path(d).is_dir():
        for p in sorted(Path(d).glob("*.json")):
            out[p.name] = _load(p)
    return out


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def compute_metrics(telemetry, usage):
    """Flat dict of metric name -> float, built from whatever files exist."""
    m = {}
    for name, d in telemetry.items():
        tested, single = _num(d.get("packages_tested")), _num(d.get("packages_with_single_model"))
        if tested and single is not None:
            m["pinning_ratio"] = single / tested
            m["pinning_spread_enabled"] = 1.0 if d.get("spread_enabled") else 0.0
        fails, calls = _num(d.get("failures")), _num(d.get("calls"))
        if calls and fails is not None:
            m["failure_rate"] = fails / calls
    for name, d in usage.items():
        tot = d.get("total")
        if isinstance(tot, dict):
            paid, free = _num(tot.get("paid")) or 0.0, _num(tot.get("free")) or 0.0
            if paid + free > 0:
                m["paid_share"] = paid / (paid + free)
    return m


def get_path(cfg, dotted, default):
    cur = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# direction: "up" = higher is better, "down" = lower is better
def build_proposals(m, cfg):
    props = []
    if m.get("paid_share", 0) > 0.3:
        props.append({"key": "router.prefer_free", "value": True, "metric": "paid_share",
                      "direction": "down", "baseline": m["paid_share"],
                      "rollback_value": get_path(cfg, "router.prefer_free", False),
                      "expected_effect": "paid share of tokens drops below 30%"})
    if m.get("failure_rate", 0) > 0.1:
        props.append({"key": "router.max_retries", "value": 3, "metric": "failure_rate",
                      "direction": "down", "baseline": m["failure_rate"],
                      "rollback_value": get_path(cfg, "router.max_retries", 1),
                      "expected_effect": "failure rate drops below 10%"})
    if m.get("pinning_spread_enabled") and m.get("pinning_ratio", 1) < 0.9:
        props.append({"key": "router.pin_model_per_package", "value": True,
                      "metric": "pinning_ratio", "direction": "up", "baseline": m["pinning_ratio"],
                      "rollback_value": get_path(cfg, "router.pin_model_per_package", False),
                      "expected_effect": "packages served by a single model rise above 90%"})
    return props[:MAX_CHANGES]


def read_pipeline(path):
    d = _load(path)
    if not isinstance(d.get("proposals"), list):
        d = {"proposals": []}
    return d


def write_pipeline(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def cmd_propose(a):
    m = compute_metrics(read_dir(a.telemetry_dir), read_dir(a.usage_dir) if a.usage_dir else {})
    cfg = _load(a.config) if a.config else {}
    props = build_proposals(m, cfg)
    for p in props:
        p["status"] = "proposed"
    now = time.time()
    pipe = {"generated": now, "metrics": m, "proposals": props, "max_changes": MAX_CHANGES}
    write_pipeline(a.pipeline, pipe)
    dbg("%d proposal(s)" % len(props))
    print(json.dumps({"proposals": len(props), "pipeline": a.pipeline}))
    return 0


def cmd_check(a):
    m = compute_metrics(read_dir(a.telemetry_dir), read_dir(a.usage_dir) if a.usage_dir else {})
    pipe = read_pipeline(a.pipeline)
    rolled = 0
    for p in pipe["proposals"]:
        if p.get("status") != "proposed":
            continue
        cur, base = m.get(p.get("metric")), _num(p.get("baseline"))
        if cur is None or base is None:
            continue
        worse = cur > base if p.get("direction") == "down" else cur < base
        p["last_value"] = cur
        if worse:
            p["status"] = "rolled_back"
            p["apply_value"] = p.get("rollback_value")
            rolled += 1
    write_pipeline(a.pipeline, pipe)
    print(json.dumps({"rolled_back": rolled}))
    return 0


def main(argv=None):
    global DEBUG
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["propose", "check"])
    ap.add_argument("--telemetry-dir", required=True)
    ap.add_argument("--usage-dir")
    ap.add_argument("--config")
    ap.add_argument("--pipeline", required=True)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    DEBUG = a.debug
    return cmd_propose(a) if a.mode == "propose" else cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
