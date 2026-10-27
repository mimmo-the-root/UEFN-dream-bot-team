#!/usr/bin/env python3
"""Coherence check of spec, plan and tasks (v1.113): the engine of /coerenza. READ ONLY, it never edits a file.

  python Claude/hooks/plan_check.py [Content folder] [--stage plan|tasks] [--today YYYY-MM-DD]

Reads Claude/docs/GAME-SPEC.md, CONSTITUTION.md, PLAN.md and the Tasks table of ROADMAP.md. Findings are CRITICAL, HIGH, MEDIUM or LOW
(at most 50). A conflict with the constitution is always CRITICAL. Exit 1 when something is CRITICAL or HIGH.
Task rows keep the ROADMAP columns (ID | Feature | Status | Acceptance criteria | Priority | Release); the story, the order and
the risk live in the Feature cell: [S1] the story, [P] can run in parallel, (after T-001, T-002) dependencies, [R1] reduces risk 1."""
import datetime, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec_check

ORDER = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def docs_dir(base):
    for c in (os.path.join(base, "Claude", "docs"), os.path.join(base, "docs"), base, os.path.join(base, "Content", "Claude", "docs"),
              os.path.join(HERE, "..", "docs")):
        if os.path.isfile(os.path.join(c, "GAME-SPEC.md")):
            return c
    return os.path.join(base, "Claude", "docs")


def stories(spec):
    return [(int(n), t.strip(), p) for n, t, p in re.findall(r"###\s+Story\s+(\d+)\s*-\s*(.+?)\s*\((P\d)\)", spec)]


def risks(spec):
    sec = spec_check.sections(spec).get("technical risks", "")
    rows = [l for l in sec.splitlines() if l.strip().startswith("|") and not re.match(r"\|\s*(-|Risk)", l.strip())]
    out = []
    for r in rows:
        cells = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"low|medium|high", cells[1], re.I) and "<" not in r:
            out.append((len(out) + 1, cells[0], cells[1].lower()))
    return out


def plan_sections(plan):
    parts = re.split(r"(?m)^##\s+(?=S\d+\b)", plan)
    out = {}
    for p in parts[1:]:
        m = re.match(r"S(\d+)\b", p)
        if m:
            out[int(m.group(1))] = p
    return out


def island_settings(plan):
    m = re.search(r"(?ms)^##\s+Island settings\s*$(.*?)(?=^##\s|\Z)", plan)
    out = []
    for l in (m.group(1) if m else "").splitlines():
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.strip().startswith("|") and len(c) >= 2 and not re.match(r"-+$|Setting$", c[0]) and "<" not in l:
            out.append(c)
    return out


def table_rows(text, heading):
    m = re.search(r"###\s+%s\s*\n(.*?)(?=\n###|\n##|\Z)" % re.escape(heading), text, re.S)
    if not m:
        return None
    rows = [l for l in m.group(1).splitlines() if l.strip().startswith("|") and not re.match(r"\|\s*(-|Device|Asset)", l.strip())]
    return [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]


def tasks(roadmap):
    m = re.search(r"(?m)^##\s+Tasks\s*$(.*?)(?=^##\s|\Z)", roadmap, re.S)
    out = []
    if not m:
        return out
    for l in m.group(1).splitlines():
        if not l.strip().startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) >= 4 and re.fullmatch(r"T-\d{3}", c[0]):
            feat = c[1]
            out.append(dict(id=c[0], feature=feat, status=c[2], acc=c[3],
                            story=[int(x) for x in re.findall(r"\[S(\d+)\]", feat)],
                            par="[P]" in feat,
                            deps=re.findall(r"T-\d{3}", " ".join(re.findall(r"\(after ([^)]*)\)", feat))),
                            risk=[int(x) for x in re.findall(r"\[R(\d+)\]", feat)], text=feat + " " + c[3]))
    return out


def cycle(ts):
    deps = {t["id"]: t["deps"] for t in ts}
    seen, stack = set(), set()

    def go(n):
        if n in stack:
            return True
        if n in seen or n not in deps:
            return False
        seen.add(n); stack.add(n)
        r = any(go(d) for d in deps[n])
        stack.discard(n)
        return r
    return any(go(n) for n in deps)


def check(d, stage="all", today=None):
    F = []

    def add(sev, msg):
        F.append((sev, msg))

    spec, const, plan, road = (read(os.path.join(d, n)) for n in ("GAME-SPEC.md", "CONSTITUTION.md", "PLAN.md", "ROADMAP.md"))
    if not spec:
        return [("CRITICAL", "No GAME-SPEC.md: run /spec")]
    b, _, _ = spec_check.check(spec, gate=True, today=today)
    for x in b:
        add("CRITICAL", "Spec is not ready for planning: " + x)
    st = stories(spec)
    if not const:
        add("HIGH", "No CONSTITUTION.md: /piano writes it first")
    else:
        if re.search(r"<[^>\n]+>", re.sub(r"<!--.*?-->", "", const, flags=re.S)):
            add("HIGH", "CONSTITUTION.md still has template placeholders")
        if not re.search(r"-\s*Approved:\s*yes", const, re.I):
            add("MEDIUM", "CONSTITUTION.md is not approved by the owner")
    if not plan:
        add("HIGH", "No PLAN.md: run /piano")
        return sorted(F, key=lambda f: ORDER.index(f[0]))[:50]
    if re.search(r"<[^>\n]+>", re.sub(r"<!--.*?-->", "", plan, flags=re.S)):
        add("HIGH", "PLAN.md still has template placeholders")
    secs = plan_sections(plan)
    isl = island_settings(plan)
    pm = re.search(r"\d+", spec_check.field(spec, "Players") or "")
    if not isl:
        add("HIGH", "PLAN.md: no Island settings table (max players, teams, round, respawn): they are set by hand in UEFN Island Settings")
    elif pm:
        mx = [r[1] for r in isl if r[0].lower().startswith("max players")]
        mn = re.search(r"\d+", mx[0]) if mx else None
        if not mn:
            add("HIGH", "Island settings: 'Max players' is missing")
        elif int(mn.group(0)) < int(pm.group(0)):
            add("HIGH", "Island settings: Max players (%s) is lower than the players of the spec (%s)" % (mn.group(0), pm.group(0)))
    for n, title, p in st:
        if n not in secs:
            add("HIGH", "Story %d (%s) has no section '## S%d' in PLAN.md" % (n, p, n))
            continue
        dev = table_rows(secs[n], "Devices")
        if not dev or not any(len(r) > 1 and re.fullmatch(r"recipe|skill|explore", r[1], re.I) for r in dev):
            add("MEDIUM", "S%d: the devices table has no row with status recipe, skill or explore" % n)
        ass = table_rows(secs[n], "Assets inventory")
        if ass is None or not any(len(r) > 1 and re.fullmatch(r"present|import|create", r[1], re.I) for r in ass):
            add("MEDIUM", "S%d: the assets inventory has no row with status present, import or create" % n)
    for n in secs:
        if n not in [s[0] for s in st]:
            add("MEDIUM", "PLAN.md has a section S%d that is not a story of the spec" % n)
    if not [l for l in re.sub(r"<!--.*?-->", "", plan, flags=re.S).split("## Sources consulted", 1)[-1].split("\n## ", 1)[0].splitlines() if l.strip().startswith(("-", "*")) and "<" not in l] or "## Sources consulted" not in plan:
        add("LOW", "PLAN.md: no sources consulted written (recipes, device skills, MCP lessons)")
    m1 = re.search(r"-\s*Pass 1[^:\n]*:\s*(.*)", plan)
    if not m1 or "S1" not in m1.group(1):
        add("HIGH", "Build order: Pass 1 must start with S1 (the playable loop)")
    if not re.search(r"-\s*Pass 2[^:\n]*:\s*\S", plan):
        add("MEDIUM", "Build order: Pass 2 (details) is missing")
    if not re.search(r"-\s*Try one sample first:\s*[^<\s]", plan):
        add("LOW", "Build order: no sample to try first")

    forb = []
    m = re.search(r"(?ms)^##\s+Forbidden\s*$(.*?)(?=^##\s|\Z)", const)
    if m:
        forb = [re.sub(r"^[-*]\s*", "", l).strip() for l in m.group(1).splitlines() if l.strip().startswith(("-", "*"))]
        forb = [x for x in forb if x and "<" not in x]

    ts = tasks(road) if stage != "plan" else []
    body = plan + "\n" + "\n".join(t["text"] for t in ts)
    for w in forb:
        if w.lower() in body.lower():
            add("CRITICAL", "Conflict with CONSTITUTION.md: '%s' is forbidden and appears in the plan or the tasks" % w)

    if stage != "plan":
        real = [t for t in ts if "example" not in t["feature"].lower()]
        if not real:
            add("HIGH", "No task in ROADMAP.md: run /compiti")
        ids = {t["id"] for t in real}
        for n, title, p in st:
            if not any(n in t["story"] for t in real):
                add("HIGH", "Story %d (%s) has no task" % (n, p))
        for t in real:
            if not t["story"]:
                add("MEDIUM", "%s has no story tag like [S1]" % t["id"])
            for s in t["story"]:
                if s not in [x[0] for x in st]:
                    add("MEDIUM", "%s points to a story that does not exist: S%d" % (t["id"], s))
            if not t["acc"] or t["acc"].startswith("(") or len(t["acc"]) < 12:
                add("HIGH", "%s has no verifiable acceptance criterion" % t["id"])
            for dd in t["deps"]:
                if dd not in ids:
                    add("HIGH", "%s depends on %s, which does not exist" % (t["id"], dd))
            if t["par"] and t["deps"]:
                add("LOW", "%s is marked [P] but has dependencies" % t["id"])
        if cycle(real):
            add("HIGH", "The task dependencies form a cycle")
        high = [r for r in risks(spec) if r[2] == "high"]
        first = sorted(real, key=lambda t: t["id"])[:3]
        for n, name, _ in high:
            if not any(n in t["risk"] for t in first):
                add("HIGH", "High risk R%d (%s) is not reduced by any of the first three tasks (tag it [R%d])" % (n, name[:50], n))
    F.sort(key=lambda f: ORDER.index(f[0]))
    return F[:50]


def main(argv):
    stage, today, args, i = "all", None, [], 0
    while i < len(argv):
        if argv[i] == "--stage": i += 1; stage = argv[i]
        elif argv[i] == "--today": i += 1; today = datetime.date.fromisoformat(argv[i])
        else: args.append(argv[i])
        i += 1
    d = docs_dir(args[0] if args else os.getcwd())
    F = check(d, stage, today)
    for sev, msg in F:
        print("%-8s %s" % (sev, msg))
    bad = [f for f in F if f[0] in ("CRITICAL", "HIGH")]
    print("Coherence: %s" % ("OK, nothing blocks" if not bad else "%d to fix before building (%d findings in all)" % (len(bad), len(F))))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
