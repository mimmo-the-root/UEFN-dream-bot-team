"""What's new page: linked from every console page, served by both servers, reads the shipped summary, has an empty state and the issue link."""
import os, re, sys
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
hooks = os.path.join(root, "project-template", "Claude", "hooks")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
rd = lambda n: open(os.path.join(hooks, n), encoding="utf-8-sig").read()
for page in ("agent-console.html", "agent-console-stats.html", "agent-console-docs.html", "agent-console-flow.html", "agent-console-skills.html", "agent-console-news.html", "agent-console-score.html"):
    ok('href="agent-console-news.html"' in rd(page), "%s links to the What's new page" % page)
news = rd("agent-console-news.html")
ok('"/community-summary"' in news and '"/community-state"' in news, "the page reads the shipped summary and the local community state")
ok("No release summary is shipped with this kit yet" in news, "empty state when there is no summary")
ok(re.search(r"https://github\.com/'\+REPO\+'/issues/new/choose", news) is not None, "the page links to submit an issue on GitHub")
ok("Only lessons learned from a <b>published</b> map" in news, "the page carries the published-map note")
ok(len(re.findall(r"\bfunction render\(", news)) == 1 and news.count("<script>") == 2, "one render function, no external script")
ok("agent-console-news.html" in rd("agent-console-server.py") and "/news" in rd("agent-console-server.py"), "the Python server serves the page")
ok("agent-console-news.html" in rd("agent-console-server.ps1") and "NewsHtmlPath" in rd("agent-console-server.ps1"), "the PowerShell server serves the page")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import kit_sync as _ks
ok(all("Claude/" + n in _ks.MANAGED or any(("Claude/" + n).startswith(m) for m in _ks.MANAGED) for n in ("community/community-summary.json", "community-revoked.json")), "the kit update ships the release summary and the revoked list to the projects")
