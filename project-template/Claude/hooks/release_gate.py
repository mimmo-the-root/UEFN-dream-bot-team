#!/usr/bin/env python3
"""Pre-delivery gate (v1.114): what Claude cannot do itself, a private release, the memory check, and the owner's flags. Engine of /delivery. Compliance (Fab rules, island rules, privacy) is part of it.

  python Claude/hooks/release_gate.py init [Content folder]     # write Claude/docs/DELIVERY-GATE.md from PLAN.md (never overwrites)
  python Claude/hooks/release_gate.py check [Content folder]    # exit 1 until the owner confirmed everything

DELIVERY-GATE.md has three lists, each line `- [ ]` that ONLY the owner turns into `- [x]`: (1) configuration Claude cannot do (the manual steps of
the plan, the Island settings, Beta Access, Python scripting), (2) the private release (publish as private, test with the code), (3) memory:
`- Memory used: NN%` written by the owner from UEFN (Project Size in the toolbar and Memory Usage in Publishing Validation). Claude never ticks a box. 100% or more blocks; 85% or more warns."""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import env_check, plan_check, spec_check

COMPLIANCE = ("Third-party content (Fab assets, other authors, music) is declared in the island description and every licence allows use in a published island",
              "Island name, description, thumbnail and tags are ready, and every step the Creator Portal asks (including the rating questionnaire) is complete",
              "No personal data in the project files: names and paths are ***anonymized*** (GDPR, Regulation (EU) 2016/679); Epic's own assets were not touched")
VALIDATION = ("Experimental Features", "Memory Usage", "Download Size", "Asset Status", "Cooked for Platforms")
PRIVATE = ("Publish the island as PRIVATE (Fortnite > Publish, visibility private) for the test. The private code is only for you and your testers: do not write it anywhere in the kit; the island code the kit shows comes only from the official publication",
           "Open the island from the Fortnite client with the private code and check that it starts",
           "The private release is NOT made public before the playtest below passes")


def build(d):
    e = env_check.environment(d)
    if e is None:
        return None
    L = ["# Delivery gate", "", "<!-- Only the owner ticks a box. Claude writes the list and reads it back; it never ticks. -->", "",
         "## 1. Configuration Claude cannot do"]
    for s in e["owner"]:
        L.append("- [ ] " + s)
    for n, s in e["manual"]:
        L.append("- [ ] S%d: %s" % (n, s))
    L += ["", "## 2. Compliance (Fab rules and island rules)", "<!-- Claude runs the read-only scan (fab_assets.py) and writes its result under `Scan`; the boxes are yours. -->",
          "- Scan: pending (`/audit` runs `fab_assets.py` by itself and writes N blocks, M warnings here)"]
    for s_ in COMPLIANCE:
        L.append("- [ ] " + s_)
    L += ["", "## 3. Private release"] + ["- [ ] " + s_ for s_ in PRIVATE]
    L += ["", "## 4. Publishing Validation and memory",
          "<!-- In UEFN the panel Publishing Validation lists five checks after you upload the private build. -->"]
    for s_ in VALIDATION:
        L.append("- [ ] Publishing Validation: " + s_ + " is green")
    L += ["- Memory used: <NN>%", "", "## 5. Playtest",
          "- [ ] PLAYTEST.md filled with %s player(s), every row ok or turned into a task" % (e.get("players") or "the planned number of"), ""]
    return "\n".join(L)


def check(text):
    block, warn = [], []
    secs = re.split(r"(?m)^## ", text)
    for s in secs[1:]:
        for l in s.splitlines():
            if l.startswith("- [ ]"):
                block.append("not confirmed by the owner: " + l[6:].strip())
    m = re.search(r"Memory used:\s*(\d+(?:\.\d+)?)\s*%", text)
    if not m:
        block.append("Memory used: the owner has not written the percentage")
    else:
        v = float(m.group(1))
        if v >= 100:
            block.append("Memory used %.0f%%: over the limit, reduce the map" % v)
        elif v >= 85:
            warn.append("Memory used %.0f%%: close to the limit" % v)
    return block, warn


def line_hash(text):
    """djb2 of the ASCII part of a gate line (after the checkbox): the console page computes the same, so a click can never tick another line after the file changed."""
    h = 5381
    for ch in re.sub(r"[^\x20-\x7e]", "", text.strip()):
        h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
    return str(h)


def tick(path, line_no, on, expect):
    """The OWNER's click on the console page: turn one `- [ ]` into `- [x]` (or back). Claude itself never calls this."""
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError:
        return {"ok": False, "error": "no DELIVERY-GATE.md"}
    i = int(line_no) - 1
    if i < 0 or i >= len(lines):
        return {"ok": False, "error": "line not found"}
    m = re.match(r"^(\s*- \[)([ xX])(\]\s*)(.*)$", lines[i])
    if not m:
        return {"ok": False, "error": "that line is not a box any more: reload the page"}
    if expect and line_hash(m.group(4)) != str(expect):
        return {"ok": False, "error": "the file changed: reload the page"}
    lines[i] = m.group(1) + ("x" if on else " ") + m.group(3) + m.group(4)
    tmp = path + ".tmp"
    open(tmp, "w", encoding="utf-8", newline="").write("\n".join(lines))
    os.replace(tmp, path)
    return {"ok": True, "line": i + 1, "on": bool(on)}


def tick_task(path, line_no, on, expect):
    """The OWNER confirms a task of ROADMAP.md from the console: the status cell becomes `Done - confirmed by the owner <date> (was: ...)`; unticking restores the old status."""
    import datetime
    try:
        lines = open(path, encoding="utf-8").read().split("\n")
    except OSError:
        return {"ok": False, "error": "no ROADMAP.md"}
    i = int(line_no) - 1
    if i < 0 or i >= len(lines) or not re.match(r"^\|\s*T-\d+", lines[i]):
        return {"ok": False, "error": "that line is not a task any more: reload the page"}
    cells = lines[i].strip().strip("|").split("|")
    if len(cells) < 3:
        return {"ok": False, "error": "unexpected task row"}
    if expect and line_hash(cells[0] + "|" + cells[1]) != str(expect):
        return {"ok": False, "error": "the file changed: reload the page"}
    st = cells[2].strip()
    if on:
        cells[2] = " Done - confirmed by the owner %s (was: %s) " % (datetime.date.today().isoformat(), st)
    else:
        m = re.search(r"\(was: (.*)\)\s*$", st)
        cells[2] = " " + (m.group(1) if m else "To do") + " "
    lines[i] = "|" + "|".join(cells) + "|"
    tmp = path + ".tmp"
    open(tmp, "w", encoding="utf-8", newline="").write("\n".join(lines))
    os.replace(tmp, path)
    return {"ok": True, "line": i + 1, "on": bool(on)}


def tick_audit(path, line_no, on, expect):
    """The OWNER confirms an audit finding from the console: the State cell becomes `confirmed by the owner` (and the same in the data comment); unticking gives `for the owner` back."""
    import json
    try:
        raw = open(path, encoding="utf-8-sig").read()
    except OSError:
        return {"ok": False, "error": "no AUDIT.md"}
    lines = raw.split("\n")
    i = int(line_no) - 1
    if i < 0 or i >= len(lines) or not re.match(r"^\|\s*\d+\s*\|", lines[i]):
        return {"ok": False, "error": "that line is not a finding any more: reload the page"}
    cells = lines[i].strip().strip("|").split("|")
    if len(cells) < 6:
        return {"ok": False, "error": "unexpected finding row"}
    if expect and line_hash(cells[0] + "|" + cells[3]) != str(expect):
        return {"ok": False, "error": "the file changed: reload the page"}
    new = "confirmed by the owner" if on else "for the owner"
    cells[-1] = " " + new + " "
    lines[i] = "|" + "|".join(cells) + "|"
    out = "\n".join(lines)
    m = re.search(r"<!-- data:(\[[\s\S]*?\]) -->", out)
    if m:
        try:
            arr = json.loads(m.group(1)); n = int(cells[0].strip()) - 1
            if 0 <= n < len(arr):
                arr[n]["state"] = new
                out = out[:m.start(1)] + json.dumps(arr, ensure_ascii=False, separators=(",", ":")) + out[m.end(1):]
        except ValueError:
            pass
    tmp = path + ".tmp"
    open(tmp, "w", encoding="utf-8", newline="").write(out)
    os.replace(tmp, path)
    return {"ok": True, "line": i + 1, "on": bool(on)}


def main(argv):
    base = next((a for a in argv[1:] if not a.startswith("--")), os.getcwd())
    d = plan_check.docs_dir(base)
    p = os.path.join(d, "DELIVERY-GATE.md")
    cmd = argv[0] if argv else "check"
    if cmd == "tick":  # tick <project> <line> <on|off> <hash>
        import json
        if len(argv) > 5 and argv[5] == "audit":
            print(json.dumps(tick_audit(os.path.join(d, "AUDIT.md"), argv[2], argv[3] == "on", argv[4])))
        elif len(argv) > 5 and argv[5] == "roadmap":
            print(json.dumps(tick_task(os.path.join(d, "ROADMAP.md"), argv[2], argv[3] == "on", argv[4])))
        else:
            print(json.dumps(tick(p, argv[2], argv[3] == "on", argv[4] if len(argv) > 4 else "")))
        return 0
    if cmd == "init":
        if os.path.exists(p):
            print("DELIVERY-GATE.md already exists: it is not overwritten.")
            return 0
        t = build(d)
        if t is None:
            print("No PLAN.md: run /game-plan first.")
            return 1
        open(p, "w", encoding="utf-8").write(t)
        print("Written DELIVERY-GATE.md: give it to the owner, who ticks it.")
        return 0
    try:
        t = open(p, encoding="utf-8").read()
    except OSError:
        print("No DELIVERY-GATE.md: run init.")
        return 1
    b, w = check(t)
    for x in b:
        print("BLOCK " + x)
    for x in w:
        print("warn  " + x)
    print("Ready to deliver" if not b else "%d to confirm before delivery" % len(b))
    return 1 if b else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
