#!/usr/bin/env python3
"""T-108: cost of the modes — read usage.json and usage-72h.json, return per-day tokens on paid models vs free models."""
import json
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

LEDGER_POLL_SECONDS = 5
ROUTER_STATE_URL = "http://127.0.0.1:8765/models"


def _read_json(path, default=None, keep=False):
    """Read a JSON file, keep=True means the file is not deleted even if it's corrupted."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        if keep:
            # move to a backup name
            backup = path + ".bad-" + str(int(time.time()))
            try:
                os.replace(path, backup)
            except:
                pass
        return default or {}


def _write_json(path, data):
    """Write JSON with a temporary file and atomic replace."""
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def load(usage_path, usage72_path):
    """Read both usage files and return two dicts: usage and usage_72h."""
    usage = _read_json(usage_path, {"models": {}, "month": None}, keep=True)
    usage_72h = _read_json(usage72_path, {}, keep=True)
    return usage, usage_72h


def shares(usage, usage_72h, days=7):
    """
    Return per-day token breakdown and plan share.

    Args:
        usage: dict from usage.json with keys "models" and "month"
        usage_72h: dict from usage-72h.json (hour buckets)
        days: number of days to show (default 7)

    Returns:
        dict with keys:
            - "daily": list of dicts with "date", "paid", "free", "total"
            - "week": {"paid": int, "free": int, "total": int, "share_percent": float}
            - "models": list of dicts with "provider/model", "paid", "free", "total"
    """
    models = usage.get("models", {})

    # Build per-model totals (sum input+output)
    model_totals = defaultdict(int)
    for key, value in models.items():
        try:
            # value is {provider, model, input, output, requests, errors, last}
            model_totals[key] = int(value.get("input", 0) + value.get("output", 0))
        except (TypeError, ValueError, AttributeError):
            continue

    # Build 72h buckets: {date_str: {key: count}}
    buckets = {}
    now = datetime.now(timezone.utc)
    for bucket_key, bucket_data in usage_72h.items():
        try:
            # bucket_key is hour as int (unix timestamp)
            bucket_time = datetime.fromtimestamp(int(bucket_key), tz=timezone.utc)
            if (now - bucket_time) <= timedelta(days=72):
                date_str = bucket_time.date().isoformat()
                buckets.setdefault(date_str, defaultdict(int))
                # bucket_data is {provider, model, hours: {hour: [input, output, requests, errors]}}
                for hour_key, hour_data in bucket_data.get("hours", {}).items():
                    # hour_data is [input, output, requests, errors]
                    input_tokens = int(hour_data[0]) if len(hour_data) > 0 else 0
                    output_tokens = int(hour_data[1]) if len(hour_data) > 1 else 0
                    key = bucket_data["provider"] + "/" + bucket_data["model"]
                    buckets[date_str][key] += (input_tokens + output_tokens)
        except (TypeError, ValueError, AttributeError):
            continue

    # Sort dates descending and take last 'days'
    sorted_dates = sorted(buckets.keys(), reverse=True)[:days]
    daily = []

    for date_str in sorted_dates:
        bucket = buckets.get(date_str, {})
        paid = free = 0
        for key, count in bucket.items():
            try:
                if key.startswith("claude-plan/"):
                    paid += int(count)
                else:
                    free += int(count)
            except (TypeError, ValueError):
                continue
        daily.append({
            "date": date_str,
            "paid": paid,
            "free": free,
            "total": paid + free
        })

    # Week totals (last 'days')
    week_paid = sum(d["paid"] for d in daily)
    week_free = sum(d["free"] for d in daily)
    week_total = week_paid + week_free
    share_percent = round(week_paid / week_total * 100) if week_total else 0

    # Per-model breakdown for the week
    models_data = []
    for key, total in model_totals.items():
        if key.startswith("claude-plan/"):
            paid = total
            free = 0
        else:
            paid = 0
            free = total
        models_data.append({
            "provider_model": key,
            "paid": paid,
            "free": free,
            "total": total
        })

    return {
        "daily": daily,
        "week": {
            "paid": week_paid,
            "free": week_free,
            "total": week_total,
            "share_percent": share_percent
        },
        "models": models_data
    }


def cli():
    """CLI: print a small table for the last 7 days and a JSON option."""
    import argparse
    parser = argparse.ArgumentParser(description="Show token cost per mode.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of table")
    parser.add_argument("--days", type=int, default=7, help="Number of days (default 7)")
    args = parser.parse_args()

    # Locate usage files
    user_hooks_dir = os.path.expanduser("~/.claude/user-level-hooks")
    usage_path = os.path.join(user_hooks_dir, "usage.json")
    usage72_path = os.path.join(user_hooks_dir, "usage-72h.json")

    if not os.path.exists(usage_path):
        print(f"usage.json not found at {usage_path}")
        return 1

    usage, usage_72h = load(usage_path, usage72_path)
    result = shares(usage, usage_72h, args.days)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        # Table header
        print(f"{'Date':<12} {'Paid':>10} {'Free':>10} {'Total':>10}")
        print("-" * 44)
        for d in result["daily"]:
            print(f"{d['date']:<12} {d['paid']:>10} {d['free']:>10} {d['total']:>10}")
        print("-" * 44)
        w = result["week"]
        print(f"{'Week total':<12} {w['paid']:>10} {w['free']:>10} {w['total']:>10}")
        print(f"Plan share: {w['share_percent']}%")
        print()
        print("Per model:")
        for m in result["models"]:
            print(f"  {m['provider_model']:<30} paid={m['paid']:>8} free={m['free']:>8} total={m['total']:>8}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cli())
