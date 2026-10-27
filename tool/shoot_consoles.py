#!/usr/bin/env python3
"""Console proof and screenshots (v1.110): start the real console server on a demo project, open every page in a real browser,
fail on JavaScript errors or an empty page, and save dark-theme screenshots.

  python tool/shoot_consoles.py [--out DIR] [--only score,news] [--check-only]

Needs Playwright with Chromium (pip install playwright; playwright install chromium). Without it the script says so and exits 2.
The demo project is built in a temporary folder with invented but consistent data (a roadmap, bugs, a call ledger, the pilot game docs): nothing
from a real project is read. Screenshots go to docs/manual/images/shot-<page>.png unless --out says otherwise.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
PAGES = {"console": "/", "stats": "/stats", "docs": "/docs", "flow": "/flow", "skills": "/skills", "news": "/news", "score": "/score"}


def demo_project(d):
    docs = os.path.join(d, "Claude", "docs")
    logs = os.path.join(d, "Claude", "logs")
    os.makedirs(docs)
    os.makedirs(logs)
    os.makedirs(os.path.join(d, "Content"))
    open(os.path.join(d, "Claude", "KIT-VERSION"), "w").write(open(os.path.join(ROOT, "project-template", "Claude", "KIT-VERSION")).read())
    hdr = "| ID | Feature | Status | Acceptance criteria | Priority | Release |\n|---|---|---|---|---|---|\n"
    rows = [("T-001", "Core gameplay loop with rounds", "Done", "A round starts and ends", "P1", "P0-R1"),
            ("T-002", "Level layout and landmarks", "Done", "Players find the route", "P1", "P0-R1"),
            ("T-003", "Music loop and sound effects", "In progress", "Audio plays per phase", "P2", "P0-R2"),
            ("T-004", "Daily reward and leaderboard", "To do", "Players come back", "P2", "P0-R2"),
            ("T-005", "Visual polish: lighting and materials", "To do", "Readable at a glance", "P2", "P0-R3")]
    open(os.path.join(docs, "ROADMAP.md"), "w").write("# Roadmap\n\n## Tasks\n\n" + hdr + "\n".join("| %s | %s | %s | %s | %s | %s |" % r for r in rows) + "\n")
    open(os.path.join(docs, "BUGS.md"), "w").write("# Bugs\n\n| Title | Where | Severity | Probable cause | Status |\n|---|---|---|---|---|\n| B-001: score resets after a round | game.verse | medium | state not kept | Open |\n")
    # the pilot demo (v1.114): spec, constitution, plan and its tasks, so the Docs page shows Idea, Spec and Plan filled
    demo = os.path.join(ROOT, "project-template", "Claude", "reference", "demo-chicken-roundup")
    for n in ("GAME-SPEC.md", "CONSTITUTION.md", "PLAN.md"):
        shutil.copyfile(os.path.join(demo, n), os.path.join(docs, n))
    if "--plain" not in sys.argv:
        road = open(os.path.join(demo, "ROADMAP.md"), encoding="utf-8").read()
        for t, st in (("T-001", "Done"), ("T-002", "Done"), ("T-003", "Done"), ("T-004", "In progress")):  # a game under way, for the progress graphics
            road = road.replace("| %s |" % t, "| %s |" % t, 1)
            lines = road.splitlines()
            road = "\n".join(l.replace("| To do |", "| %s |" % st, 1) if l.startswith("| %s |" % t) else l for l in lines) + "\n"
        open(os.path.join(docs, "ROADMAP.md"), "w", encoding="utf-8").write(road)
    open(os.path.join(docs, "STATUS.md"), "w").write("# Status\n\nDemo project for the console screenshots.\n")
    now = time.time()
    led = [{"d": time.strftime("%Y-%m-%d"), "sid": "demo", "t": "10:%02d:00" % i, "toolset": "Demo.Level", "tool": t, "args": "{}", "r": "ok", "src": "work"}
           for i, t in enumerate(["GetActors", "SpawnActor", "SetProperty", "GetActors"])]
    open(os.path.join(logs, "explore-ledger.jsonl"), "w").write("\n".join(json.dumps(x) for x in led) + "\n")
    ev = [{"ts": now - 300 + i * 20, "event": e, "agent": a} for i, (e, a) in enumerate([("start", "coder"), ("stop", "coder"), ("start", "qa-regression"), ("stop", "qa-regression")])]
    open(os.path.join(logs, "agent-console.jsonl"), "w").write("\n".join(json.dumps(x) for x in ev) + "\n")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main(argv):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed (pip install playwright && playwright install chromium)")
        return 2
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(ROOT, "docs", "manual", "images")
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else list(PAGES)
    check_only = "--check-only" in argv
    d = tempfile.mkdtemp()
    proc = None
    bad = []
    try:
        demo_project(d)
        shutil.copytree(HOOKS, os.path.join(d, "Claude", "hooks"), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(ROOT, "project-template", "Claude", "reference"), os.path.join(d, "Claude", "reference"))
        port = free_port()
        env = dict(os.environ, CLAUDE_PROJECT_DIR=d, UEFN_KIT_TEMPLATE=os.path.join(d, "no-template"))
        proc = subprocess.Popen([sys.executable, os.path.join(d, "Claude", "hooks", "agent-console-server.py"), str(port)], cwd=d, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", port), 0.2).close()
                break
            except OSError:
                time.sleep(0.2)
        os.makedirs(out, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={"width": 1400, "height": 900}, color_scheme="dark")
            for name in only:
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e, errors=errors: errors.append(str(e)[:160]))
                page.goto("http://127.0.0.1:%d%s" % (port, PAGES[name]), wait_until="networkidle")
                page.wait_for_timeout(1200)
                text = page.inner_text("body")
                if errors:
                    bad.append("%s: JavaScript error: %s" % (name, errors[0]))
                if name == "score" and ("no tasks found" in text or "not running" in text):
                    bad.append("score: the page shows its empty state although the demo project has a roadmap")
                if len(text.strip()) < 80:
                    bad.append("%s: the page is empty" % name)
                if not check_only:
                    page.screenshot(path=os.path.join(out, "shot-%s.png" % name), full_page=False)
                if name == "docs" and not check_only:
                    for tab in ("idea", "spec", "plan", "road", "docs"):
                        page.click('#pageTabs .tab[data-t="%s"]' % tab)
                        page.wait_for_timeout(300)
                        page.screenshot(path=os.path.join(out, "shot-docs-%s.png" % tab), full_page=False)
                    if not page.is_visible('#demoCard'):
                        bad.append("docs: the pilot demo card is not visible on the Documents tab")
                page.close()
            br.close()
    finally:
        if proc:
            proc.terminate()
        shutil.rmtree(d, ignore_errors=True)
    for b in bad:
        print("FAIL " + b)
    print("console proof: %d page(s) checked, %d problem(s)" % (len(only), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
