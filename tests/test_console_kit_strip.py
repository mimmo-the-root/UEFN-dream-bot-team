"""The Console shows the kit's numbers (skills, genre lessons, proven recipes, MCP tools) and the README badges; both servers answer /kit-numbers."""
import json, os, sys
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
def rd(*p): return open(os.path.join(root, *p), encoding="utf-8").read()
bad = []
page = rd("project-template", "Claude", "hooks", "agent-console.html")
for needle in ('id="kitChips"', 'id="kcSkills"', 'id="kcLessons"', 'id="kcRecipes"', 'id="kitBar"', 'id="kcMcp"', '/kit-numbers', 'id="kcBrain"'):
    if needle not in page: bad.append("agent-console.html lacks " + needle)
# no duplicates: the strip must not repeat the numbers shown in the legend
bar = page[page.index('id="kitBar"'):page.index('<!-- Miniflow')]
for dup in ("AI agents", "genre lessons", "proven recipes", ">skills<"):
    if dup in bar: bad.append("the badge strip repeats " + dup)
for srv in ("agent-console-server.py", "agent-console-server.ps1"):
    if "/kit-numbers" not in rd("project-template", "Claude", "hooks", srv): bad.append(srv + " has no /kit-numbers")
stats = json.loads(rd("docs", "kit-stats.json"))
if not isinstance(stats.get("lessons"), int) or stats["lessons"] < 1: bad.append("kit-stats.json has no lessons number")
if json.loads(rd("project-template", "Claude", "community", "kit-stats.json")) != stats: bad.append("the Console copy of kit-stats.json differs from docs/kit-stats.json")
if "query=%24.lessons" not in rd("README.md"): bad.append("README has no genre lessons badge")
print(("PASS " if not bad else "FAIL ") + "Console kit strip, /kit-numbers and README badge" + ("" if not bad else ": " + "; ".join(bad)))
sys.exit(1 if bad else 0)
