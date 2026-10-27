#!/usr/bin/env python3
"""Environment and playtest helper (v1.114): the engine of /ambiente. READ ONLY, it never edits a file.

  python Claude/hooks/env_check.py [Content folder]              # environment readout from the plan
  python Claude/hooks/env_check.py [Content folder] --playtest   # playtest checklist from the approved spec

Environment: lists what the plan needs (assets to import or create, manual steps), what is missing in the docs, and the steps only the
owner can do (Beta Access, Python scripting, MCP toolset). Playtest: one block per story (expected, observed) and one per success
criterion, taken from GAME-SPEC.md. Exit 1 when the plan or the spec is missing. Nothing is closed, opened or imported here."""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import plan_check, spec_check

OWNER_ONLY = (
    "Epic Games Launcher: UEFN installed and updated; your account has Beta Access if the plan uses it.",
    "UEFN: Project Settings, Python scripting enabled (Editor Preferences).",
    "UEFN: the MCP toolset is on and the project is open on the right map.",
)


def asset_rows(plan):
    out = []
    for n, body in sorted(plan_check.plan_sections(plan).items()):
        sec = re.search(r"### Assets inventory(.*?)(?=\n###|\Z)", body, re.S)
        for l in (sec.group(1) if sec else "").splitlines():
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            if l.strip().startswith("|") and len(c) >= 3 and re.fullmatch(r"present|import|create", c[1], re.I) and "<" not in l:
                out.append((n, c[0], c[1].lower(), c[2]))
    return out


def manual_steps(plan):
    out = []
    for n, body in sorted(plan_check.plan_sections(plan).items()):
        sec = re.search(r"### Manual steps[^\n]*\n(.*?)(?=\n###|\Z)", body, re.S)
        for l in (sec.group(1) if sec else "").splitlines():
            if l.strip().startswith("-") and "<" not in l:
                out.append((n, l.strip("- ").strip()))
    return out


def environment(d):
    plan = plan_check.read(os.path.join(d, "PLAN.md"))
    if not plan:
        return None
    a = asset_rows(plan)
    todo = [x for x in a if x[2] != "present"]
    spec = plan_check.read(os.path.join(d, "GAME-SPEC.md"))
    isl = ["Island Settings: %s = %s" % (r[0], r[1]) for r in plan_check.island_settings(plan)]
    return {"assets": a, "to_get": todo, "manual": manual_steps(plan), "owner": OWNER_ONLY + tuple(isl), "players": spec_check.field(spec, "Players"),
            "scenery": plan_check.environment_rows(plan), "approved": spec_check.field(plan, "Approved").lower() == "yes", "lore": "Save a Lore checkpoint before the first playtest."}


def playtest(d):
    spec = plan_check.read(os.path.join(d, "GAME-SPEC.md"))
    if not spec:
        return None
    pl = spec_check.field(spec, "Players")
    lines = ["# Playtest checklist", "", "Fill 'observed' while you play. A failed row becomes a regression task (T-xxx) in ROADMAP.md.", ""]
    if re.search(r"\d+", pl or "") and int(re.search(r"\d+", pl).group(0)) > 1:
        n = int(re.search(r"\d+", pl).group(0))
        lines += ["## Players (%d)" % n, "- [ ] Play with 1 player alone: the round starts and ends", "- [ ] Play with %d players: everyone can join, the round starts, the shared state is correct" % n,
                  "- [ ] A player joins a running round (if Join in progress is on) and one leaves: nothing breaks", "- [ ] Island Settings in UEFN match the plan (max players, teams, respawn)", ""]
    for n, title, pr in plan_check.stories(spec):
        m = re.search(r"###\s+Story\s+%d\b.*?(?=\n###|\n## |\Z)" % n, spec, re.S)
        body = m.group(0) if m else ""
        t = re.search(r"Independent test:\s*(.+)", body)
        lines += ["## S%d - %s (%s)" % (n, title, pr), "- Expected: " + (t.group(1).strip() if t else "see the story"), "- Observed: ", "- Result: ok / fail", ""]
        for g in re.findall(r"^- (Given .+)$", body, re.M):
            lines += ["- [ ] " + g]
        lines.append("")
    crit = re.findall(r"^- (SC-\d+:.+)$", spec_check.sections(spec).get("success criteria", ""), re.M)
    if crit:
        lines += ["## Success criteria"] + ["- [ ] %s | observed: " % c for c in crit] + [""]
    return "\n".join(lines)


def main(argv):
    base = next((a for a in argv if not a.startswith("--")), os.getcwd())
    d = plan_check.docs_dir(base)
    if "--playtest" in argv:
        out = playtest(d)
        if out is None:
            print("No GAME-SPEC.md: run /spec first.")
            return 1
        print(out)
        return 0
    e = environment(d)
    if e is None:
        print("No PLAN.md: run /piano first.")
        return 1
    print("Environment readout (nothing was changed)")
    print("Assets: %d in the plan, %d to import or create" % (len(e["assets"]), len(e["to_get"])))
    for n, name, st, src in e["to_get"]:
        print("  S%d %s: %s (%s)" % (n, name, st, src))
    print("Manual steps (only you can do them): %d" % len(e["manual"]))
    for n, s in e["manual"]:
        print("  S%d %s" % (n, s))
    print("Only the owner:")
    for s in e["owner"]:
        print("  - " + s)
    print(e["lore"])
    if not e["approved"]:
        print("The plan is not approved yet: /piano first.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
