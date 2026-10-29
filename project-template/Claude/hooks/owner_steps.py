#!/usr/bin/env python3
"""OWNER-STEPS.md: the checklist of what only the owner can do, with two sections.

  ## Setup      the build waits for these (a device field the tools cannot fill, a choice)
  ## Gameplay   the final confirmation: the owner plays and says it works

The agents WRITE items here (add) and WAIT for the ticks (wait); the owner ticks them with the
Done button on the console's "Your turn" step. An agent never ticks a box.

  python owner_steps.py add setup "Assign RoundTimer" "Details of chicken_roundup_manager: drag Timer_V2" [project]
  python owner_steps.py add gameplay "Play one round" "Tame 2 chickens, bring them to the pen, check the score" [project]
  python owner_steps.py from-spec [project]      (one Gameplay box per player action of GAME-SPEC.md "Loop (MVP)")
  python owner_steps.py status [project]
  python owner_steps.py wait setup [--timeout 540] [project]   (exit 0 all ticked, 2 timeout)
"""
import os, re, sys, time

SECTIONS = {"setup": "Setup", "gameplay": "Gameplay"}
HEAD = ("# Owner steps\n\n<!-- Written by the agents with owner_steps.py, ticked ONLY by the owner on the console (Your turn).\n"
        "     Setup = the build waits for these. Gameplay = the final confirmation after a real play. -->\n\n")


def docs_dir(base):
    for c in (os.path.join(base, "Claude", "docs"), os.path.join(base, "Content", "Claude", "docs"), base):
        if os.path.isdir(c) and os.path.basename(c) == "docs":
            return c
    return os.path.join(base, "Claude", "docs")


def path_for(base):
    return os.path.join(docs_dir(base), "OWNER-STEPS.md")


def read(p):
    try:
        return open(p, encoding="utf-8-sig").read()
    except OSError:
        return ""


def items(text):
    out, sec = [], None
    for l in text.split("\n"):
        h = re.match(r"^##\s+(\w+)", l)
        if h:
            sec = h.group(1).lower()
            continue
        b = re.match(r"^- \[([ xX])\]\s*(.*)$", l)
        if b and sec in SECTIONS:
            out.append({"section": sec, "done": b.group(1) != " ", "text": b.group(2)})
    return out


def add(base, section, title, how=""):
    section = section.lower()
    if section not in SECTIONS:
        raise ValueError("section must be setup or gameplay")
    p = path_for(base)
    t = read(p) or HEAD
    for sec in SECTIONS:
        if not re.search(r"^##\s+%s\b" % SECTIONS[sec], t, re.M):
            t = t.rstrip("\n") + "\n\n## %s\n" % SECTIONS[sec]
    line = "- [ ] **%s**" % title.strip().rstrip(".")
    if line in t:
        return p
    new = line + "\n" + ("  - %s\n" % how.strip() if how.strip() else "")
    m = re.search(r"^##\s+%s\b.*$" % SECTIONS[section], t, re.M)
    rest = t[m.end():]
    nx = re.search(r"^##\s", rest, re.M)
    end = m.end() + (nx.start() if nx else len(rest))
    body = t[m.end():end].rstrip("\n")
    t = t[:m.end()] + body + "\n" + new + "\n" + t[end:].lstrip("\n")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="").write(t.rstrip("\n") + "\n")
    return p


LOOP_LABELS = (("Action", "Do it"), ("Rule", "Check the rule"), ("Reward", "Check the reward"), ("End", "Check the end"), ("Replay", "Check the replay"))


def loop_items(base):
    """The player's own actions, from GAME-SPEC.md '## Loop (MVP)': what the owner must see working in a real play (not every task)."""
    t = read(os.path.join(docs_dir(base), "GAME-SPEC.md"))
    m = re.search(r"^##\s+Loop \(MVP\)\s*$", t, re.M)
    if not m:
        return []
    rest = t[m.end():]
    nx = re.search(r"^##\s", rest, re.M)
    sec = rest[:nx.start()] if nx else rest
    out = []
    for key, verb in LOOP_LABELS:
        f = re.search(r"^[-*]\s*%s\s*:\s*(.+)$" % key, sec, re.M | re.I)
        if f and not f.group(1).strip().startswith("<"):
            out.append((verb + ": " + f.group(1).strip().rstrip("."), ""))
    return out


def open_count(base, section):
    return len([i for i in items(read(path_for(base))) if i["section"] == section and not i["done"]])


def wait(base, section, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if open_count(base, section) == 0:
            return True
        time.sleep(5)
    return False


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    rest = [a for a in argv[1:]]
    tout = 540.0
    if "--timeout" in rest:
        i = rest.index("--timeout")
        tout = float(rest[i + 1])
        del rest[i:i + 2]
    if cmd == "add":
        if len(rest) < 2:
            print("usage: add setup|gameplay <title> [how] [project]")
            return 1
        base = rest[3] if len(rest) > 3 else os.getcwd()
        print("Written: " + add(base, rest[0], rest[1], rest[2] if len(rest) > 2 else ""))
        return 0
    if cmd == "from-spec":
        base = rest[0] if rest else os.getcwd()
        its = loop_items(base)
        if not its:
            print("No Loop (MVP) in GAME-SPEC.md: write the spec first.")
            return 1
        for title, how in its:
            add(base, "gameplay", title, how or "Play it in the editor (Play) and watch it happen; press Done only if it works")
        print("Gameplay checks written: %d (one per player action)" % len(its))
        return 0
    if cmd == "status":
        base = rest[0] if rest else os.getcwd()
        its = items(read(path_for(base)))
        for sec in SECTIONS:
            o = [i for i in its if i["section"] == sec]
            print("%s: %d of %d done" % (SECTIONS[sec], len([i for i in o if i["done"]]), len(o)))
        return 0
    if cmd == "wait":
        sec = (rest[0] if rest else "setup").lower()
        base = rest[1] if len(rest) > 1 else os.getcwd()
        if wait(base, sec, tout):
            print("All %s steps are ticked by the owner: go on." % sec)
            return 0
        print("Still waiting for the owner (%d open). Run wait again; do not tick anything yourself." % open_count(base, sec))
        return 2
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
