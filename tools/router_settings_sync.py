#!/usr/bin/env python3
"""Turns the kit-settings 'routing' keys into the payload of the router POST /router/settings (T-098).

Pure: no network, no file writes. The router accepts: mode (auto/plan/free/safe/paid), free_accept_edits (bool),
spread (bool), safety_check ("short" | "full") and chain (list of str).
safety_check mapping (the router has no 'off'): short -> short; off and mixed-safe -> full (the safety check is
not shrunk; mixed-safe routing itself is the 'safe' mode, set through routing.mode).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_config  # noqa: E402

_SAFETY_TO_ROUTER = {"off": "full", "short": "short", "mixed-safe": "full"}


def build_payload(routing):
    """routing: the 'routing' dict of the kit settings (may be partial or invalid). Returns the payload dict."""
    d = kit_config.defaults()["routing"]
    r = routing if isinstance(routing, dict) else {}
    cfg = {k: r[k] for k in d if k in r}
    bad = kit_config._bad_keys({"routing": cfg})
    out = {}
    for k in ("mode", "safety_check", "free_accept_edits", "spread", "chain"):
        v = cfg.get(k, d[k])
        if "routing." + k in bad:
            v = d[k]
        out[k] = list(v) if k == "chain" else v
    out["safety_check"] = _SAFETY_TO_ROUTER[out["safety_check"]]
    return out


def payload_for_project(project=None):
    """Payload from the merged kit settings of a project (invalid values already fall back in kit_config.load)."""
    cfg, _note = kit_config.load(project)
    return build_payload(cfg.get("routing"))


if __name__ == "__main__":
    import json
    print(json.dumps(payload_for_project(sys.argv[1] if len(sys.argv) > 1 else None), indent=2))
