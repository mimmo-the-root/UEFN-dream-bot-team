#!/usr/bin/env python3
"""Check the game spec before planning (v1.112).

  python Claude/hooks/spec_check.py [GAME-SPEC.md | Content folder] [--gate] [--jam] [--today YYYY-MM-DD]

Quality checks (always): the idea, the 5-line loop, a P1 story with an independent test and a Given/When/Then,
measurable success criteria, assumptions, a risk table, no open [NEEDS CLARIFICATION], no template placeholder left.
--gate (what /game-plan runs): also needs `Approved: yes` and `Score` of 60 or more (or `Forced: yes`, the owner's decision).
--jam (or `Mode: jam`): the line "How the theme enters the game" is checked: empty is a warning before the theme is
announced (2026-11-11) and blocks after it.
Exit 1 when something blocks. The spec says WHAT and WHY; nothing here judges how the game is built."""
import datetime, os, re, sys

THEME_DAY = datetime.date(2026, 11, 11)
THRESHOLD = 60
LOOP = ("Action", "Rule", "Reward", "End", "Replay")


def find_spec(arg):
    if arg and os.path.isfile(arg):
        return arg
    base = arg or os.getcwd()
    for cand in (os.path.join(base, "Claude", "docs", "GAME-SPEC.md"), os.path.join(base, "docs", "GAME-SPEC.md"),
                 os.path.join(base, "GAME-SPEC.md"), os.path.join(base, "Content", "Claude", "docs", "GAME-SPEC.md"),
                 os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "GAME-SPEC.md")):
        if os.path.isfile(cand):
            return cand
    return None


def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"##\s+(.+?)\s*$", line)
        if m and not line.startswith("###"):
            cur = m.group(1).strip().lower()
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def field(text, name):
    m = re.search(r"^[-*]\s*%s\s*:\s*(.*)$" % re.escape(name), text, re.I | re.M)
    return m.group(1).strip() if m else ""


def placeholder(s):
    return (not s) or bool(re.fullmatch(r"<[^>]*>.*|<[^>]*>", s.strip())) or s.strip().startswith("<")


def check(text, gate=False, jam=False, today=None):
    today = today or datetime.date.today()
    block, warn, info = [], [], []
    sec = sections(text)
    head = text.split("\n## ", 1)[0]
    jam = jam or field(head, "Mode").lower() == "jam"
    if field(head, "Status") == "" or "## loop (mvp)" not in "\n".join("## " + k for k in sec):
        return ["This is not a game spec (no Loop section): run /spec"], [], []

    idea = sec.get("idea", "")
    if placeholder(idea):
        block.append("Idea: write one sentence")
    if placeholder(field(head, "Genre")):
        warn.append("Genre: not confirmed yet (the owner decides; in a jam the AI proposes one from the theme)")

    pl = field(head, "Players")
    if placeholder(pl) or not re.search(r"\d", pl):
        block.append("Players: write how many players the game is for (ask the owner; it decides the Island settings and the tests)")
    else:
        n = int(re.search(r"\d+", pl).group(0))
        if n > 1:
            info.append("multiplayer (%d players): the plan needs the Island settings and the playtest uses %d players" % (n, n))
            if "player" not in sec.get("success criteria", "").lower():
                warn.append("Success criteria: none mentions the players (for example 'with 4 players the score counts all of them')")
    loop = sec.get("loop (mvp)", "")
    for k in LOOP:
        v = field(loop, k)
        if placeholder(v):
            block.append("Loop: the line '%s' is empty" % k)

    stories = sec.get("stories", "")
    p1 = re.search(r"###\s+[^\n]*\(P1\)(.*?)(?=\n###|\Z)", stories, re.S)
    if not p1:
        block.append("Stories: a P1 story is needed (the playable loop)")
    else:
        body = p1.group(1)
        if placeholder(field(body, "Independent test")):
            block.append("Story P1: the independent test is missing")
        if not re.search(r"given\s+[^,\n]+,\s*when\s+[^,\n]+,\s*then\s+\S", body, re.I) or "<" in re.search(r"given.*", body, re.I | re.S).group(0).split("\n")[0]:
            block.append("Story P1: a Given/when/then scenario is missing")

    sc = [l for l in sec.get("success criteria", "").splitlines() if re.match(r"[-*]\s*SC-\d+\s*:\s*\S", l) and "<" not in l]
    if not sc:
        block.append("Success criteria: none written (measurable, in game)")
    elif len(sc) < 3:
        warn.append("Success criteria: %d written, 3 to 5 is better" % len(sc))

    ass = [l for l in sec.get("assumptions", "").splitlines() if l.strip().startswith(("-", "*")) and "<" not in l]
    if not ass:
        warn.append("Assumptions: none. Write every choice the AI made instead of the owner")

    src = [l for l in sec.get("sources consulted", "").splitlines() if l.strip().startswith(("-", "*")) and "<" not in l]
    if not src:
        warn.append("Sources consulted: none written (the study step uses the second brain, the genre skill and its lessons, the retention and feasibility skills)")

    rows = [l for l in sec.get("technical risks", "").splitlines() if l.strip().startswith("|") and not re.match(r"\|\s*(-|Risk)", l.strip())]
    real = [r for r in rows if re.search(r"\|\s*(low|medium|high)\s*\|", r, re.I) and "<" not in r]
    if not real:
        block.append("Technical risks: write at least one risk with level low, medium or high")
    for r in real:
        if re.search(r"\|\s*high\s*\|", r, re.I):
            info.append("High risk to see before approving: " + r.split("|")[1].strip())

    open_marks = len(re.findall(r"\[NEEDS CLARIFICATION", text))
    if open_marks:
        block.append("%d [NEEDS CLARIFICATION] left open" % open_marks)

    if jam:
        theme = field(sec.get("theme", ""), "How the theme enters the game")
        if placeholder(theme):
            (block if today >= THEME_DAY else warn).append(
                "Theme: 'How the theme enters the game' is empty" + ("" if today >= THEME_DAY else " (theme not announced yet, 11 November)"))

    if gate:
        sc_txt = field(sec.get("score and approval", ""), "Score")
        m = re.match(r"(\d+)\s*/\s*100", sc_txt)
        forced = field(sec.get("score and approval", ""), "Forced").lower().startswith("y")
        if not m:
            block.append("Score: not written (run /concept-card and write the score)")
        elif int(m.group(1)) < THRESHOLD and not forced:
            block.append("Score %s is below %d: raise it or write 'Forced: yes' (the owner's decision)" % (m.group(1), THRESHOLD))
        elif int(m.group(1)) < THRESHOLD:
            info.append("Score below %d, forced by the owner" % THRESHOLD)
        if not field(sec.get("score and approval", ""), "Approved").lower().startswith("y"):
            block.append("Not approved: the owner approves spec and score together")
    return block, warn, info


def main(argv):
    gate, jam, today, args = False, False, None, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--gate": gate = True
        elif a == "--jam": jam = True
        elif a == "--today": i += 1; today = datetime.date.fromisoformat(argv[i])
        else: args.append(a)
        i += 1
    path = find_spec(args[0] if args else None)
    if not path:
        print("No GAME-SPEC.md found: run /spec")
        return 1
    with open(path, encoding="utf-8") as f:
        text = f.read()
    r = check(text, gate, jam, today)
    block, warn, info = r
    for l in block: print("BLOCK  " + l)
    for l in warn: print("warn   " + l)
    for l in info: print("note   " + l)
    print("Spec %s" % ("is ready" if not block else "is NOT ready: %d blocking" % len(block)) + (" for planning" if gate and not block else ""))
    return 1 if block else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
