#!/usr/bin/env python3
"""Pre-delivery gate (v1.114): what Claude cannot do itself, a private release, the memory check, and the owner's flags. Engine of /consegna. Compliance (Fab rules, island rules, privacy) is part of it.

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
PRIVATE = ("Publish the island as PRIVATE (Fortnite > Publish, visibility private); write the island code here: ",
           "Open the island with the code, from the Fortnite client, and check it starts",
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
          "- Scan: <not run yet: Claude runs `python ~/.claude/hooks/fab_assets.py <project>` and writes N blocks, M warnings here>"]
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


def main(argv):
    base = next((a for a in argv[1:] if not a.startswith("--")), os.getcwd())
    d = plan_check.docs_dir(base)
    p = os.path.join(d, "DELIVERY-GATE.md")
    cmd = argv[0] if argv else "check"
    if cmd == "init":
        if os.path.exists(p):
            print("DELIVERY-GATE.md already exists: it is not overwritten.")
            return 0
        t = build(d)
        if t is None:
            print("No PLAN.md: run /piano first.")
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
