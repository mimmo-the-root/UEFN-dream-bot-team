#!/usr/bin/env python3
"""Check before handing in a jam entry (v1.108). Automatic checks plus the manual list.

  python Claude/hooks/jam_check.py [Content folder]

Automatic: every Verse file header (Summary + real date/version, no change history), asset file names
(letters, digits, underscore) and path length (project folder name included, 140 at most), a dev log, a
concept card. Exit 1 when something blocks. Then it prints what only YOU can confirm.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SKIP = {"Claude", ".claude", "__ExternalActors__", "__ExternalObjects__", "Saved", "Intermediate", ".git"}
ASSET_EXT = (".uasset", ".umap")
MAX_PATH = 140

MANUAL = [
    "Private version code (NOT a live or playtest code): made during the contest period, from the final build you want judged",
    "Video: 30-60 seconds of recorded gameplay, 1920x1080 or higher, in English",
    "Everything players and judges see is in English: in-game text, audio, the video and the entry form",
    "The game demonstrates the contest theme (announced at the start of the jam)",
    "Gameplay, levels and art were made during the contest period; only AI tools, agent setups, MCP settings, prompts and scripts may be older (Epic can ask for them or for your version history)",
    "Sourced (non-original) assets are listed in the submission, with licences you cleared; AI-generated content does not count as sourced",
    "Suitable for players aged 13 and over (Teen); no trademarks or logos except the Developed in Fortnite logo",
    "Team of 1 to 5 with names and emails, one team owner; one entry per team; the entry is sent by a person, not by an AI agent",
    "Glass Box prize only: the dev log is submitted together with the entry (Claude/docs/devlog.md, 'How AI was used' filled in by you)",
]


def check(content):
    import verse_changes as vc
    block, warn = [], []
    proj = os.path.basename(os.path.dirname(os.path.abspath(content)))
    for base, dirs, files in os.walk(content):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            p = os.path.join(base, f)
            rel = os.path.relpath(p, content).replace(os.sep, "/")
            if f.endswith(".verse"):
                for pr in vc.check_header(open(p, encoding="utf-8", errors="replace").read()):
                    block.append("%s: header: %s" % (rel, pr))
            if f.endswith(ASSET_EXT) or f.endswith(".verse"):
                stem = os.path.splitext(f)[0]
                if not re.fullmatch(r"[A-Za-z0-9_]+", stem):
                    warn.append("%s: name has characters other than letters, digits, underscore" % rel)
                full = proj + "/" + rel
                if len(full) > MAX_PATH:
                    block.append("%s: path is %d characters with the project folder name (limit %d)" % (rel, len(full), MAX_PATH))
    docs = os.path.join(content, "Claude", "docs")
    if not os.path.isfile(os.path.join(docs, "devlog.md")):
        warn.append("no Claude/docs/devlog.md yet: run /devlog")
    if not os.path.isfile(os.path.join(docs, "concept-card.md")):
        warn.append("no Claude/docs/concept-card.md yet: run /concept-card")
    return block, warn


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    b, w = check(c)
    for x in b:
        print("BLOCKS: " + x)
    for x in w:
        print("warning: " + x)
    if not b and not w:
        print("automatic checks: all clear")
    print("\nOnly you can confirm:")
    for m in MANUAL:
        print("  [ ] " + m)
    sys.exit(1 if b else 0)
