#!/usr/bin/env python3
"""Concept card with a score (v1.108): decide fast whether an idea is worth building for the jam.

  python Claude/hooks/concept_card.py --title "Name" --pitch "one sentence" \
      --scores ambition=4,theme=4,fun=5,gameplay=4,visuals=3,level=3,audio=2,feasibility=4,scope=3 [--days-left 14] [--write]

Every score is 1-5 (5 = best). Two groups, 100 points in all:

 JUDGING (70 points): Epic's seven criteria of the 2026 Epic AI MegaJam, up to 5 points each
   ambition (Ambition and Innovation), theme (Use of Contest Theme), fun (Fun Factor), gameplay,
   visuals, level (Level Design), audio. Score what the idea can realistically reach, not a dream.
   Before the theme is announced leave `theme` out: the group is then scaled over the six others
   and the card says the theme is not scored yet.
 BUILDABLE (30 points): our own two checks, 15 points each
   feasibility (can UEFN and Verse really do it), scope (5 = small, easy to finish in the days left).

Verdict: 75+ build it, 55-74 build it only with a smaller scope, below 55 pick another idea.
A 1 in feasibility or scope caps the verdict at 'smaller scope'. A 1 in theme means the idea does not
use the contest theme, which the rules require: the verdict is then 'pick another idea'. --write saves Claude/docs/concept-card.md.
"""
import os, sys

JUDGE = (("ambition", "Ambition and Innovation"), ("theme", "Use of Contest Theme"), ("fun", "Fun Factor"),
         ("gameplay", "Gameplay"), ("visuals", "Visuals"), ("level", "Level Design"), ("audio", "Audio"))
BUILD = (("feasibility", "Feasibility in UEFN and Verse", 15), ("scope", "Scope for the days left (5 = small)", 15))
JUDGE_POINTS = 70
NAMES = [k for k, _ in JUDGE] + [k for k, _, _ in BUILD]


def score(s):
    for k, v in s.items():
        if k not in NAMES:
            raise ValueError("unknown criterion: " + k)
        if not 1 <= v <= 5:
            raise ValueError("%s must be 1-5" % k)
    need = [k for k, _ in JUDGE if k != "theme"] + [k for k, _, _ in BUILD]
    miss = [k for k in need if k not in s]
    if miss:
        raise ValueError("missing score(s): " + ", ".join(miss))
    j = [k for k, _ in JUDGE if k in s]
    total = JUDGE_POINTS * sum(s[k] for k in j) / (5.0 * len(j)) + sum(w * s[k] / 5.0 for k, _, w in BUILD)
    total = int(round(total))
    v = "build it" if total >= 75 else ("build it only with a smaller scope" if total >= 55 else "pick another idea")
    if (s["feasibility"] == 1 or s["scope"] == 1) and v == "build it":
        v = "build it only with a smaller scope"
    if s.get("theme") == 1:
        v = "pick another idea"
    return total, v


def card(title, pitch, s, days_left=None):
    total, v = score(s)
    rows = ["| %s | %s | %d/5 |" % ("Judging", n, s[k]) for k, n in JUDGE if k in s]
    if "theme" not in s:
        rows.append("| Judging | Use of Contest Theme | not scored yet |")
    rows += ["| Buildable | %s | %d/5 (%d points) |" % (n, s[k], w) for k, n, w in BUILD]
    extra = "\n- Days left: %s" % days_left if days_left else ""
    return ("# Concept card: %s\n\n%s\n\n| Group | Criterion | Score |\n|---|---|---|\n%s\n\n- Score: **%d / 100** (judging 70 + buildable 30)\n- Verdict: **%s**%s\n"
            % (title, pitch, "\n".join(rows), total, v, extra))


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
