#!/usr/bin/env python3
"""Retro agent (free): weekly read of telemetry, proposes at most 3 config changes.

Reads (read-only): <telemetry-dir>/*.json and <usage-dir>/*.json (e.g. token-ledger.json).
Writes ONLY the one pipeline JSON given with --pipeline. Never edits the real config.
The current config (optional --config) is only read, to fill rollback values.

  retro.py propose --telemetry-dir D [--usage-dir D] [--config F] --pipeline P [--debug]
  retro.py check   --telemetry-dir D [--usage-dir D] [--pipeline P] [--golden G] [--debug]
  retro.py real    --telemetry-dir D [--usage-72h F] [--golden G] [--config F] --pipeline P [--debug]

"real" reads the actual telemetry shapes (plan/telemetry/*.json, router usage-72h.json
with hour buckets and golden nightly results) instead of the simple test shape.
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
PAID_PROVIDERS = {"claude-plan", "anthropic"}


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


def golden_metrics(path):
    """Read a golden nightly result: (metrics, degraded names, passed, total, models)."""
    d = _load(path) if path else {}
    models = d.get("models") if isinstance(d, dict) else None
    models = models if isinstance(models, dict) else {}
    passed = total = 0
    summary = {}
    for name, res in models.items():
        if not isinstance(res, dict):
            continue
        p, t = _num(res.get("passed")), _num(res.get("total"))
        if p is not None and t:
            passed += p
            total += t
            summary[str(name)] = {"passed": p, "total": t}
    comp = d.get("comparison") if isinstance(d, dict) else None
    alerts = comp.get("degradation") if isinstance(comp, dict) else None
    degraded = sorted({str(a.get("model")) for a in (alerts or [])
                       if isinstance(a, dict) and a.get("model")})
    m = {"golden_degraded_count": float(len(degraded))}
    if total:
        m["golden_pass_rate"] = passed / total
    return m, degraded, passed, total, summary


def compute_real_metrics(telemetry, usage72, golden=None):
    """Metrics from the real telemetry shapes; golden is the golden_metrics()[0] dict."""
    m = compute_metrics(telemetry, {})
    requests = errors = paid_tokens = free_tokens = 0
    for key, entry in (usage72 or {}).items():
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider") or str(key).split("/")[0])
        for bucket in (entry.get("hours") or {}).values():
            if not isinstance(bucket, (list, tuple)):
                continue
            vals = [_num(bucket[i]) or 0.0 for i in range(4)]
            paid_tokens += vals[0] + vals[1] if provider in PAID_PROVIDERS else 0
            free_tokens += vals[0] + vals[1] if provider not in PAID_PROVIDERS else 0
            requests += vals[2]
            errors += vals[3]
    if requests:
        m["failure_rate"] = errors / requests
    if paid_tokens + free_tokens:
        m["paid_share"] = paid_tokens / (paid_tokens + free_tokens)
    if golden:
        m.update(golden)
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
    if m.get("golden_degraded_count", 0) > 0:
        props.append({"key": "router.disabled_models", "value": m.get("golden_degraded_models", []),
                      "metric": "golden_degraded_count", "direction": "down",
                      "baseline": m["golden_degraded_count"],
                      "rollback_value": get_path(cfg, "router.disabled_models", []),
                      "expected_effect": "degraded free models leave the nightly golden set"})
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
    if getattr(a, "golden", None):
        m.update(golden_metrics(a.golden)[0])
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


def cmd_real(a):
    golden, degraded, passed, total, models = golden_metrics(a.golden)
    m = compute_real_metrics(read_dir(a.telemetry_dir), _load(a.usage_72h) if a.usage_72h else {}, golden)
    m["golden_degraded_models"] = degraded
    cfg = _load(a.config) if a.config else {}
    props = build_proposals(m, cfg)
    for p in props:
        p["status"] = "proposed"
    pipe = {"generated": time.time(), "mode": "real", "metrics": m,
            "golden": {"models": models, "degraded": degraded, "passed": passed, "total": total},
            "proposals": props, "max_changes": MAX_CHANGES}
    write_pipeline(a.pipeline, pipe)
    dbg("%d proposal(s) from real telemetry" % len(props))
    print(json.dumps({"mode": "real", "proposals": len(props), "pipeline": a.pipeline}))
    return 0


def main(argv=None):
    global DEBUG
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["propose", "check", "real"])
    ap.add_argument("--telemetry-dir", required=True)
    ap.add_argument("--usage-dir")
    ap.add_argument("--usage-72h")
    ap.add_argument("--golden")
    ap.add_argument("--config")
    ap.add_argument("--pipeline", required=True)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    DEBUG = a.debug
    if a.mode == "propose":
        return cmd_propose(a)
    if a.mode == "real":
        return cmd_real(a)
    return cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
