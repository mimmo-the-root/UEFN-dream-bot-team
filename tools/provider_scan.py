#!/usr/bin/env python3
"""Provider scan tool for airforce and orcarouter.
Scans free models only, max 40 pings per provider.
Uses base URLs from dream_router.py config (no keys stored or printed).
Never prints or stores keys. Stops on 401/403.
Outputs: plan/PROVIDER-SCAN-<name>.md and plan/PROVIDER-SCAN-<name>.json
"""

import json, os, sys, time
from pathlib import Path

PROVIDERS = {
    "airforce": {
        "base_url": "https://api.airforce/v1",
        "key_env": "AIRFORCE_API_KEY",
        "models": ["grok-4.1-mini:free"],
        "max_tokens": 8192,
    },
    "orcarouter": {
        "base_url": "https://api.orcarouter.ai/v1",
        "key_env": "ORCAROUTER_API_KEY",
        "models": ["orcarouter/free"],
        "max_tokens": 8192,
    },
}

def _read_router_key(name):
    """Read one key from the router's keys.env (same file the router uses). Never printed or stored."""
    import os as _o
    path = _o.path.join(_o.path.expanduser("~"), ".dream-router", "keys.env")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def ping_model(base_url, api_key_env, model, timeout=20):
    """Ping one free model with tiny prompt 'ok'. Never prints/returns the key."""
    import urllib.request, urllib.error, os as _os
    url = f"{base_url}/chat/completions"
    key = _os.environ.get(api_key_env, "") or _read_router_key(api_key_env)
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ok"}],
        "max_tokens": 8,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": "working", "http": resp.status, "body": resp.read(200).decode()}
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return {"status": "auth_failed", "http": e.code, "body": str(e.code)}
        return {"status": "error", "http": e.code, "body": str(e.code)}
    except Exception as e:
        return {"status": "error", "http": None, "body": str(e)}

def scan_provider(provider_name, max_pings=40):
    config = PROVIDERS.get(provider_name)
    if not config:
        return 0, 0, []
    working, not_working, details = 0, 0, []
    key_env = config.get("key_env", "")
    for model in config["models"]:
        if working + not_working >= max_pings:
            break
        res = ping_model(config["base_url"], key_env, model, timeout=20)
        if res["status"] == "working":
            working += 1
            details.append({"model": model, "status": "working", "http": res["http"], "detail": "ok"})
        elif res["status"] == "auth_failed":
            not_working += 1
            details.append({"model": model, "status": "auth_failed", "http": res["http"], "detail": "auth failed - key missing?"})
        else:
            not_working += 1
            details.append({"model": model, "status": "error", "http": res["http"], "detail": res["body"][:100]})
    return working, not_working, details

def write_outputs(provider_name, working, not_working, details):
    plan_dir = Path(__file__).parent.parent / "plan"
    plan_dir.mkdir(exist_ok=True)
    md_path = plan_dir / f"PROVIDER-SCAN-{provider_name}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Provider Scan: {provider_name}\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total models scanned:** {len(details)}\n")
        f.write(f"- **Working:** {working}\n")
        f.write(f"- **Not working:** {not_working}\n\n")
        f.write(f"## Model Details\n\n")
        f.write(f"| Model | Status | HTTP | Detail |\n")
        f.write(f"|-------|--------|------|--------|\n")
        for d in details:
            f.write(f"| {d['model']} | {d['status']} | {d.get('http') or 'N/A'} | {d.get('detail','N/A')} |\n")
    json_path = plan_dir / f"PROVIDER-SCAN-{provider_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"provider": provider_name, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "total_models": len(details), "working": working, "not_working": not_working, "models": details},
                  f, indent=2, ensure_ascii=False)
    return str(md_path), str(json_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python provider_scan.py <provider_name> [max_pings]")
        print("Providers: airforce, orcarouter")
        sys.exit(1)
    provider_name = sys.argv[1]
    max_pings = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    if provider_name not in PROVIDERS:
        print(f"Unknown provider: {provider_name}")
        sys.exit(1)
    print(f"Scanning {provider_name} (max {max_pings} pings)...")
    working, not_working, details = scan_provider(provider_name, max_pings)
    md_path, json_path = write_outputs(provider_name, working, not_working, details)
    print(f"Done: {working} working, {not_working} not working")
    print(f"Markdown: {md_path}")
    print(f"JSON: {json_path}")

if __name__ == "__main__":
    main()
