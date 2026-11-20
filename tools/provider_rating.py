#!/usr/bin/env python3
"""Provider rating: 1-5 stars per provider from the router usage ledger (usage.json as written by dream_router.py).

Real shape of the ledger: {"models": {"provider/model": {"provider", "model", "input", "output", "requests", "errors", "last"}}}.
The router does NOT record latency or the HTTP status of a failure today. This module therefore uses what exists
(requests, errors, tokens) and reads these OPTIONAL per-model fields when a later router writes them:
  "rate_limited" (count of 429), "server_errors" (count of 5xx), "latency_ms_total" (sum over requests).
A missing metric is reported as None and is left out of the score; the reason says so. No guessing.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mode_cost import load  # noqa: E402  (reuse the readers)

PAID_PROVIDERS = {"claude-plan", "anthropic"}  # the free-vs-paid flag; callers can pass their own set
MIN_REQUESTS = 5  # below this the rating is marked low-confidence


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def rate_provider(provider, models, paid=False):
    """models: list of per-model ledger dicts of ONE provider. Returns the rating dict."""
    req = sum(int(_num(m.get("requests"))) for m in models)
    err = sum(int(_num(m.get("errors"))) for m in models)
    tokens = sum(int(_num(m.get("input")) + _num(m.get("output"))) for m in models)
    has429 = any("rate_limited" in m or "server_errors" in m for m in models)
    r429 = sum(int(_num(m.get("rate_limited"))) for m in models) if has429 else None
    r5xx = sum(int(_num(m.get("server_errors"))) for m in models) if has429 else None
    lat = None
    if req and any("latency_ms_total" in m for m in models):
        lat = round(sum(_num(m.get("latency_ms_total")) for m in models) / req, 1)
    out = {"provider": provider, "paid": bool(paid), "requests": req, "errors": err, "tokens": tokens,
           "success_rate": None, "share_429": None, "share_5xx": None, "mean_latency_ms": lat,
           "rating": None, "reason": ""}
    if req <= 0:
        out["reason"] = "no requests recorded: not rated"
        return out
    ok = max(0.0, 1.0 - err / req)
    out["success_rate"] = round(ok, 4)
    score = 1.0 + 4.0 * ok  # 100% success -> 5, 0% -> 1
    notes = ["success %d%% (%d of %d requests)" % (round(ok * 100), req - err, req)]
    if r429 is not None:
        out["share_429"], out["share_5xx"] = round(r429 / req, 4), round(r5xx / req, 4)
        score -= min(1.0, 2.0 * (r429 + r5xx) / req)
        notes.append("429 %d%%, 5xx %d%%" % (round(100 * r429 / req), round(100 * r5xx / req)))
    else:
        notes.append("429/5xx share not recorded")
    if lat is not None:
        if lat > 20000:
            score -= 1.0
        elif lat > 8000:
            score -= 0.5
        notes.append("mean latency %d ms" % lat)
    else:
        notes.append("latency not recorded")
    if req < MIN_REQUESTS:
        notes.append("only %d requests: low confidence" % req)
    notes.append("paid" if paid else "free")
    out["rating"] = int(max(1, min(5, round(score))))
    out["reason"] = ", ".join(notes)
    return out


def rate_all(usage, paid_providers=None):
    """usage: dict from usage.json. Returns a list of rating dicts, best first (unrated last)."""
    paid_set = PAID_PROVIDERS if paid_providers is None else set(paid_providers)
    by = {}
    for key, m in (usage or {}).get("models", {}).items():
        if not isinstance(m, dict):
            continue
        by.setdefault(m.get("provider") or str(key).split("/")[0], []).append(m)
    rows = [rate_provider(p, ms, p in paid_set) for p, ms in by.items()]
    return sorted(rows, key=lambda r: (r["rating"] is None, -(r["rating"] or 0), -r["requests"], r["provider"]))


def cli(argv=None):
    path = (argv or sys.argv[1:] or [os.path.expanduser("~/.dream-router/usage.json")])[0]
    usage, _ = load(path, os.path.join(os.path.dirname(path), "usage-72h.json"))
    print(json.dumps(rate_all(usage), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
