#!/usr/bin/env python3
"""Model history - daily JSONL files and weekly Markdown summary for the Dream Router.

Usage:
    python model_history.py summary [--weeks 4]
    python model_history.py daily <date> [--provider provider] [--model model]
"""

import argparse
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

HOME = os.environ.get("DREAM_ROUTER_HOME") or os.path.join(os.path.expanduser("~"), ".dream-router")
HISTORY_DIR = os.path.join(HOME, "history")
PERF_FILE = os.path.join(HOME, "perf.json")
USAGE_FILE = os.path.join(HOME, "usage.json")


def _read_json(name, default):
    try:
        with open(name, encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, type(default)) else default
    except (OSError, ValueError):
        return default


def _read_jsonl(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, ValueError):
        pass
    return rows


def _write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")


def history_file_for(date_str):
    """Return the history file path for a given YYYY-MM date string."""
    return os.path.join(HISTORY_DIR, f"{date_str}.jsonl")


def daily_history(date_str=None):
    """Build one daily history line per model for a given date (YYYY-MM-DD)."""
    if date_str is None:
        date_str = time.strftime("%Y-%m-%d")
    month_str = date_str[:7]
    usage = _read_json(USAGE_FILE, {"models": {}})
    perf = _read_json(PERF_FILE, {})

    rows = []
    for k, m in usage.get("models", {}).items():
        if m.get("last") and time.strftime("%Y-%m-%d", time.localtime(m["last"])) == date_str:
            provider = m.get("provider", k.split("/")[0])
            model = m.get("model", k.split("/")[-1])
            requests = m.get("requests", 0)
            failures = m.get("errors", 0)
            tin = m.get("input", 0)
            tout = m.get("output", 0)
            p = perf.get(k, {})
            ok = p.get("ok", 0)
            ms_list = []
            if "ms" in p and p["ms"] is not None:
                ms_list = [p["ms"]]
            median_ms = int(statistics.median(ms_list)) if ms_list else None
            rows.append({
                "date": date_str,
                "provider": provider,
                "model": model,
                "requests": requests,
                "failures": failures,
                "tokens_in": tin,
                "tokens_out": tout,
                "median_ms": median_ms,
            })
    return rows


def write_daily_history(date_str=None):
    """Write one line per model per day to the monthly JSONL file."""
    if date_str is None:
        date_str = time.strftime("%Y-%m-%d")
    month_str = date_str[:7]
    rows = daily_history(date_str)
    if not rows:
        return False
    path = history_file_for(month_str)
    existing = _read_jsonl(path)
    existing_keys = {(r["provider"], r["model"], r["date"]) for r in existing}
    new_rows = [r for r in rows if (r["provider"], r["model"], r["date"]) not in existing_keys]
    if new_rows:
        _write_jsonl(path, existing + new_rows)
    return True


def load_history_months(weeks=4):
    """Load history from the last N weeks (approx 4 weeks = 1 month)."""
    cutoff = time.time() - weeks * 7 * 86400
    all_rows = []
    try:
        for fname in sorted(os.listdir(HISTORY_DIR)):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(HISTORY_DIR, fname)
            for r in _read_jsonl(fpath):
                ts = time.mktime(time.strptime(r["date"], "%Y-%m-%d"))
                if ts >= cutoff:
                    all_rows.append(r)
    except OSError:
        pass
    return all_rows


def summary(weeks=4):
    """Generate Markdown summary of model history."""
    rows = load_history_months(weeks)
    if not rows:
        return "No history data for the last {} weeks.".format(weeks)

    # Group by model
    by_model = defaultdict(list)
    for r in rows:
        key = (r["provider"], r["model"])
        by_model[key].append(r)

    # Best models: answered / failed / average time
    model_stats = []
    for (provider, model), mrows in by_model.items():
        total_req = sum(r["requests"] for r in mrows)
        total_fail = sum(r["failures"] for r in mrows)
        total_ms = [r["median_ms"] for r in mrows if r["median_ms"] is not None]
        avg_ms = int(statistics.mean(total_ms)) if total_ms else None
        last_date = max(r["date"] for r in mrows)
        model_stats.append({
            "provider": provider,
            "model": model,
            "requests": total_req,
            "failures": total_fail,
            "success_rate": (total_req - total_fail) / total_req * 100 if total_req else 0,
            "avg_ms": avg_ms,
            "last_used": last_date,
        })

    # Sort by success rate, then by avg_ms
    model_stats.sort(key=lambda x: (-x["success_rate"], x["avg_ms"] or 999999))

    # Providers that worked
    by_provider = defaultdict(lambda: {"requests": 0, "failures": 0, "models": set()})
    for r in rows:
        p = r["provider"]
        by_provider[p]["requests"] += r["requests"]
        by_provider[p]["failures"] += r["failures"]
        by_provider[p]["models"].add(r["model"])

    providers_md = []
    for p, s in sorted(by_provider.items(), key=lambda x: -x[1]["requests"]):
        sr = (s["requests"] - s["failures"]) / s["requests"] * 100 if s["requests"] else 0
        providers_md.append(f"- **{p}**: {s['requests']} requests, {s['failures']} failures ({sr:.1f}% success), {len(s['models'])} models")

    # Models that stopped working (had requests but 0 in last week)
    one_week_ago = time.time() - 7 * 86400
    recent_keys = set()
    for r in rows:
        ts = time.mktime(time.strptime(r["date"], "%Y-%m-%d"))
        if ts >= one_week_ago:
            recent_keys.add((r["provider"], r["model"]))
    all_keys = set(by_model.keys())
    stopped = all_keys - recent_keys

    out = []
    out.append(f"# Free Models History (last {weeks} weeks)")
    out.append(f"_Generated: {time.strftime('%Y-%m-%d %H:%M')}_\n")

    out.append("## Best Models (by success rate, then speed)")
    out.append("| Provider | Model | Requests | Failures | Success Rate | Avg Time (ms) | Last Used |")
    out.append("|----------|-------|----------|----------|--------------|---------------|-----------|")
    for s in model_stats[:15]:
        avg = f"{s['avg_ms']} ms" if s['avg_ms'] else "n/a"
        out.append(f"| {s['provider']} | {s['model']} | {s['requests']} | {s['failures']} | {s['success_rate']:.1f}% | {avg} | {s['last_used']} |")

    out.append("\n## Providers That Worked")
    out.extend(providers_md)

    if stopped:
        out.append("\n## Models That Stopped Working")
        out.append("| Provider | Model | Last Seen |")
        out.append("|----------|-------|-----------|")
        for provider, model in sorted(stopped):
            mrows = by_model[(provider, model)]
            last = max(r["date"] for r in mrows)
            out.append(f"| {provider} | {model} | {last} |")
    else:
        out.append("\n## Models That Stopped Working")
        out.append("_None_")

    return "\n".join(out)


def write_weekly_vault_page(vault_path, weeks=4):
    """Write the weekly summary to the vault wiki."""
    if not vault_path or vault_path.strip() == "C:\\SecondBrainOssidian":
        return False, "Vault path is placeholder, skipped"

    md = summary(weeks)
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())  # Monday
    week_str = week_start.strftime("%Y-W%U")

    # Frontmatter for the vault
    frontmatter = f"""---
title: "Modelli Gratuiti — {week_str}"
tags: [kit, free-models, router, history, weekly]
generated_by: dream-router
date: {now.strftime('%Y-%m-%d')}
week: {week_str}
---

"""
    content = frontmatter + md

    wiki_kit = os.path.join(vault_path, "wiki", "kit")
    os.makedirs(wiki_kit, exist_ok=True)
    page_path = os.path.join(wiki_kit, "modelli-gratuiti.md")

    # Write the page (replaces itself each week)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Update wiki/indice.md if missing
    indice_path = os.path.join(vault_path, "wiki", "indice.md")
    if not os.path.exists(indice_path):
        with open(indice_path, "w", encoding="utf-8") as f:
            f.write("# Indice\n\n")
    with open(indice_path, "r", encoding="utf-8") as f:
        idx = f.read()
    link = f"- [[kit/modelli-gratuiti|Modelli Gratuiti]] — weekly free models summary (updated {now.strftime('%Y-%m-%d')})"
    if link not in idx:
        with open(indice_path, "a", encoding="utf-8") as f:
            f.write(f"\n{link}\n")

    # One line in wiki/log.md
    log_path = os.path.join(vault_path, "wiki", "log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{now.strftime('%Y-%m-%d %H:%M')} — Updated weekly free models page (week {week_str})\n")

    return True, f"Written to {page_path}"


def main():
    parser = argparse.ArgumentParser(description="Dream Router model history")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sum = sub.add_parser("summary", help="Print Markdown summary")
    p_sum.add_argument("--weeks", type=int, default=4, help="Weeks of history to include")

    p_daily = sub.add_parser("daily", help="Write daily history for a date")
    p_daily.add_argument("date", nargs="?", help="Date YYYY-MM-DD (default: today)")
    p_daily.add_argument("--provider", help="Filter by provider")
    p_daily.add_argument("--model", help="Filter by model")

    p_vault = sub.add_parser("vault", help="Write weekly vault page")
    p_vault.add_argument("--weeks", type=int, default=4)
    p_vault.add_argument("--vault-path", help="Vault path (default: rule 11 of ~/.claude/CLAUDE.md)")

    args = parser.parse_args()

    if args.cmd == "summary":
        print(summary(args.weeks))
    elif args.cmd == "daily":
        date_str = args.date or time.strftime("%Y-%m-%d")
        ok = write_daily_history(date_str)
        print("Daily history written" if ok else "No data for that day")
    elif args.cmd == "vault":
        vault_path = args.vault_path
        if not vault_path:
            # Try to read from ~/.claude/CLAUDE.md rule 11
            claude_md = os.path.join(os.path.expanduser("~"), ".claude", "CLAUDE.md")
            try:
                with open(claude_md, encoding="utf-8") as f:
                    for line in f:
                        if "Second brain path" in line and ":" in line:
                            vault_path = line.split(":", 1)[1].strip()
                            break
            except OSError:
                pass
        ok, msg = write_weekly_vault_page(vault_path, args.weeks)
        print(msg)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()