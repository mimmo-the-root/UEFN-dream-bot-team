#!/usr/bin/env python3
"""T-090/T-098: every agent-console page has the Configurazione tab, lists every kit_config key, has editable cards, and its scripts pass node --check."""
import glob, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kit_config  # noqa: E402

HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
pages = sorted(glob.glob(os.path.join(HOOKS, "agent-console*.html")))


def leaves(node, prefix=""):
    """Every writable leaf of kit_config.defaults(), as dotted keys."""
    out = []
    for key, value in node.items():
        if key == "description":
            continue
        dotted = prefix + key
        if isinstance(value, dict):
            out.extend(leaves(value, dotted + "."))
        else:
            out.append(dotted)
    return out


KEYS = leaves(kit_config.defaults())
MARKERS = ['type="number"', "data-list=", "routing.chain", "skills.enabled",
           "/config/undo", "/config/reset", "/config/history?n=10", "window.confirm",
           "off", "errors", "full"]
bad = []
if len(pages) != 9:
    bad.append("expected 9 agent-console pages, found %d" % len(pages))
node = shutil.which("node")
for p in pages:
    name = os.path.basename(p)
    t = open(p, encoding="utf-8").read()
    m = re.search(r"<!-- config-tab:begin -->(.*?)<!-- config-tab:end -->", t, re.S)
    if not m:
        bad.append(name + ": no config-tab block")
        continue
    blk = m.group(1)
    if "Configurazione" not in blk or "/config" not in blk or "X-Router-Action" not in blk:
        bad.append(name + ": tab block incomplete")
    for f in kit_config.DEBUG_FLAGS:
        if '"%s"' % f not in blk:
            bad.append("%s: debug switch %s missing" % (name, f))
    for key in KEYS:
        if '"%s"' % key not in blk:
            bad.append("%s: kit_config key %s missing" % (name, key))
    for marker in MARKERS:
        if marker not in blk:
            bad.append("%s: edit control %s missing" % (name, marker))
    rev = re.search(r"<!-- kit-console-rev: (\d+) -->", t)
    if not rev or int(rev.group(1)) < 8:
        bad.append(name + ": kit-console-rev not bumped")
    if node:
        for i, s in enumerate(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", t, re.S)):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
                fh.write(s)
            r = subprocess.run([node, "--check", fh.name], capture_output=True, text=True)
            os.unlink(fh.name)
            if r.returncode:
                bad.append("%s: script %d: %s" % (name, i, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "syntax error"))
if bad:
    print("test_config_page: FAIL\n  " + "\n  ".join(bad))
    sys.exit(1)
print("test_config_page: ok (%d pages%s)" % (len(pages), "" if node else ", node missing: syntax check skipped"))
