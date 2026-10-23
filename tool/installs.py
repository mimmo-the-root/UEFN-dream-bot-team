#!/usr/bin/env python3
"""installs.py - how many times each kit release was downloaded (GitHub counts the kit.zip downloads of the automatic update).
Usage: python tool/installs.py    (public GitHub API, no sign-in; a download is roughly one machine taking that version)"""
import json, urllib.request
REPO = "mimmo-the-root/UEFN-dream-bot-team"
req = urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=100" % REPO, headers={"User-Agent": "uefn-kit-installs"})
total = 0
for r in json.load(urllib.request.urlopen(req, timeout=30)):
    n = sum(a["download_count"] for a in r.get("assets", []) if a["name"] == "kit.zip")
    total += n
    print("%-10s %5d  %s" % (r["tag_name"], n, r["published_at"][:10]))
print("%-10s %5d" % ("total", total))
