#!/usr/bin/env python3
"""Structured signals in the map's logs (v1.109). Lives in your profile (~/.claude/hooks).

The Verse code prints one line per important event:   Print("[SIGNAL] round_end winner=3 seconds=212")
This script reads log text and answers questions a human would otherwise answer by scrolling:

  python log_signals.py summary <logfile|-> [more files] [--rules Claude/docs/signals.json] [--json] [--record <project folder>]

  - how many times each signal appeared and the min / max / average of every numeric field
  - how many Error / Warning lines the log has
  - rule findings, when a rules file exists:  {"expect": {"round_end": {"min": 1}}, "never": ["double_reward"],
                                              "range": {"round_end.seconds": [30, 600]}}
  --record appends one row to <project>/Claude/logs/signals.jsonl (so a later session can compare with this one).

`-` reads standard input. Nothing is guessed: a signal that was never printed is reported as missing, not as fine.
"""
import json
import os
import re
import sys
import time

SIG = re.compile(r"\[SIGNAL\]\s+(\w+)(.*)$")
KV = re.compile(r"(\w+)=(\"[^\"]*\"|\S+)")
ERR = re.compile(r"\bError\b|: Error:|\bFATAL\b", re.I)
WARN = re.compile(r"\bWarning\b", re.I)


def parse(text):
    sig, errors, warns = {}, 0, 0
    for line in text.splitlines():
        m = SIG.search(line)
        if m:
            d = sig.setdefault(m.group(1), {"count": 0, "fields": {}})
            d["count"] += 1
            for k, v in KV.findall(m.group(2)):
                v = v.strip('"')
                try:
                    d["fields"].setdefault(k, []).append(float(v))
                except ValueError:
                    d["fields"].setdefault(k, []).append(v)
            continue
        if ERR.search(line):
            errors += 1
        elif WARN.search(line):
            warns += 1
    out = {}
    for name, d in sig.items():
        fields = {}
        for k, vals in d["fields"].items():
            nums = [v for v in vals if isinstance(v, float)]
            if nums and len(nums) == len(vals):
                fields[k] = {"min": min(nums), "max": max(nums), "avg": round(sum(nums) / len(nums), 3)}
            else:
                fields[k] = {"values": sorted(set(str(v) for v in vals))[:8]}
        out[name] = {"count": d["count"], "fields": fields}
    return {"signals": out, "errors": errors, "warnings": warns}


def judge(res, rules):
    """List of findings from the rules file. Missing signals are findings, never silently fine."""
    f = []
    sig = res["signals"]
    for name, r in (rules.get("expect") or {}).items():
        n = sig.get(name, {}).get("count", 0)
        if "min" in r and n < r["min"]:
            f.append("expected signal '%s' at least %s time(s), saw %d" % (name, r["min"], n))
        if "max" in r and n > r["max"]:
            f.append("signal '%s' seen %d time(s), at most %s expected" % (name, n, r["max"]))
    for name in rules.get("never") or []:
        if name in sig:
            f.append("signal '%s' must never appear, seen %d time(s)" % (name, sig[name]["count"]))
    for key, (lo, hi) in (rules.get("range") or {}).items():
        name, _, field = key.partition(".")
        s = sig.get(name, {}).get("fields", {}).get(field)
        if not s or "min" not in s:
            f.append("range rule %s: no numeric values in the log" % key)
        elif s["min"] < lo or s["max"] > hi:
            f.append("%s ranges %g..%g, expected %g..%g" % (key, s["min"], s["max"], lo, hi))
    return f


def main(argv):
    if not argv or argv[0] != "summary" or len(argv) < 2:
        print(__doc__)
        return 2
    args, rules_path, record = [], None, None
    it = iter(argv[1:])
    for a in it:
        if a == "--rules":
            rules_path = next(it, None)
        elif a == "--record":
            record = next(it, None)
        elif not a.startswith("--"):
            args.append(a)
    text = ""
    for a in args:
        try:
            text += (sys.stdin.read() if a == "-" else open(a, encoding="utf-8", errors="replace").read()) + "\n"
        except OSError as e:
            print("cannot read %s: %s" % (a, e))
            return 2
    res = parse(text)
    if rules_path is None and record:
        cand = os.path.join(record, "Claude", "docs", "signals.json")
        rules_path = cand if os.path.isfile(cand) else None
    findings = []
    if rules_path:
        try:
            findings = judge(res, json.load(open(rules_path, encoding="utf-8")))
        except Exception as e:
            findings = ["rules file %s is not readable: %s" % (rules_path, e)]
    res["findings"] = findings
    if record:
        p = os.path.join(record, "Claude", "logs", "signals.jsonl")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        row = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "errors": res["errors"], "warnings": res["warnings"],
               "signals": {k: v["count"] for k, v in res["signals"].items()}, "findings": findings}
        open(p, "a", encoding="utf-8", newline="\n").write(json.dumps(row) + "\n")
    if "--json" in argv:
        print(json.dumps(res, indent=2))
        return 1 if findings else 0
    if not res["signals"]:
        print("no [SIGNAL] lines in the log (the code prints none, or the log is not the right one)")
    for k, v in sorted(res["signals"].items()):
        parts = []
        for fk, fv in v["fields"].items():
            parts.append("%s %s" % (fk, ("%g..%g avg %g" % (fv["min"], fv["max"], fv["avg"])) if "min" in fv else "/".join(fv["values"])))
        print("  %-18s x%-4d %s" % (k, v["count"], "; ".join(parts)))
    print("errors: %d, warnings: %d" % (res["errors"], res["warnings"]))
    for x in findings:
        print("FINDING: " + x)
    if rules_path and not findings:
        print("rules: all satisfied")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
