#!/usr/bin/env python3
"""Concept card with a feasibility score (v1.108): decide fast whether an idea is worth building.

  python Claude/hooks/concept_card.py --title "Name" --pitch "one sentence" \
      --scores feasibility=4,scope=3,hook=5,retention=3,originality=4,showability=5 [--days-left 14] [--write]

Each score is 1-5 (5 = best). For 'scope', 5 means SMALL (easy to finish in the time left).
Weights (total 100): feasibility 25 (can UEFN + Verse really do it), scope 20, hook 20 (fun in the first
30 seconds), showability 15 (a clear 30-60 second video), retention 10, originality 10.
Verdict: 75+ build it, 55-74 build it only with a smaller scope, below 55 pick another idea.
Any score of 1 in feasibility or scope caps the verdict at 'smaller scope or another idea'.
--write saves Claude/docs/concept-card.md.
"""
import os, sys

W = {"feasibility": 25, "scope": 20, "hook": 20, "showability": 15, "retention": 10, "originality": 10}


def score(s):
    miss = [k for k in W if k not in s]
    if miss:
        raise ValueError("missing score(s): " + ", ".join(miss))
    for k, v in s.items():
        if k not in W:
            raise ValueError("unknown criterion: " + k)
        if not 1 <= v <= 5:
            raise ValueError("%s must be 1-5" % k)
    total = round(sum(W[k] * (s[k] / 5.0) for k in W))
    if total >= 75:
        v = "build it"
    elif total >= 55:
        v = "build it only with a smaller scope"
    else:
        v = "pick another idea"
    if (s["feasibility"] == 1 or s["scope"] == 1) and v == "build it":
        v = "build it only with a smaller scope"
    return total, v


def card(title, pitch, s, days_left=None):
    total, v = score(s)
    rows = "\n".join("| %s | %d/5 | %d |" % (k, s[k], W[k]) for k in W)
    extra = "\n- Days left: %s" % days_left if days_left else ""
    return ("# Concept card: %s\n\n%s\n\n| Criterion | Score | Weight |\n|---|---|---|\n%s\n\n- Score: **%d / 100**\n- Verdict: **%s**%s\n"
            % (title, pitch, rows, total, v, extra))


def _main(argv):
    o = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            if argv[i] == "--write":
                o["write"] = "1"; i += 1; continue
            o[argv[i][2:]] = argv[i + 1] if i + 1 < len(argv) else ""; i += 2
        else:
            i += 1
    try:
        s = {k: int(v) for k, v in (x.split("=") for x in o.get("scores", "").split(",") if x)}
        text = card(o.get("title", "Untitled"), o.get("pitch", ""), s, o.get("days-left"))
    except (ValueError, TypeError) as e:
        print("error: %s" % e); return 2
    print(text)
    if o.get("write"):
        base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        p = os.path.join(base, "Claude", "docs", "concept-card.md")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8", newline="\n").write(text)
        print("written: " + p)
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
