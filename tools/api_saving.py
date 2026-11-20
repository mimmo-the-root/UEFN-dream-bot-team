#!/usr/bin/env python3
"""API-equivalent dollar saving: tokens served by FREE models times a reference price (tools/data/api_prices.json).

It is what the same tokens would have cost on a paid API, not money the owner actually kept. While the price file still
has "owner_set": false the figure is an EXAMPLE and is flagged "estimate_only": true; never show it as a real price.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mode_cost import load  # noqa: E402

PRICES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "api_prices.json")
PAID_PROVIDERS = {"claude-plan", "anthropic"}


def load_prices(path=None):
    try:
        with open(path or PRICES_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and isinstance(d.get("prices"), dict) else {"prices": {}}
    except (OSError, ValueError):
        return {"prices": {}}


def _tok(v):
    try:
        return max(0, int(v))
    except (TypeError, ValueError):
        return 0


def saving(usage, prices=None, price_key=None, paid_providers=None):
    """Dollar saving for the tokens of non-paid providers in usage (usage.json shape)."""
    prices = prices if prices is not None else load_prices()
    paid_set = PAID_PROVIDERS if paid_providers is None else set(paid_providers)
    table = prices.get("prices", {})
    key = price_key or prices.get("default")
    p = table.get(key) if key else None
    tin = tout = 0
    for m in (usage or {}).get("models", {}).values():
        if not isinstance(m, dict) or m.get("provider") in paid_set:
            continue
        tin += _tok(m.get("input"))
        tout += _tok(m.get("output"))
    res = {"free_input_tokens": tin, "free_output_tokens": tout, "price_key": key,
           "estimate_only": not prices.get("owner_set", False), "saving_usd": None,
           "note": ("API-equivalent, not money kept. " +
                    ("Prices are EXAMPLES: the owner must set real ones in tools/data/api_prices.json." if not prices.get("owner_set", False) else "Prices set by the owner."))}
    if not p:
        res["note"] += " No price found: no dollar figure."
        return res
    res["saving_usd"] = round((tin * float(p.get("input", 0)) + tout * float(p.get("output", 0))) / 1e6, 4)
    return res


def cli(argv=None):
    path = (argv or sys.argv[1:] or [os.path.expanduser("~/.dream-router/usage.json")])[0]
    usage, _ = load(path, os.path.join(os.path.dirname(path), "usage-72h.json"))
    print(json.dumps(saving(usage), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
