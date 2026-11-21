import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-models.html")
text = open(PAGE, encoding="utf-8").read()
providers = text.split("function renderProviders(p){", 1)[-1].split("var MPAGE=", 1)[0]
summary = text.split("function renderProvSum(p){", 1)[-1].split("function renderAvail", 1)[0]
checks = []
for field in ("models_ok", "models_bad", "models_untested"):
    checks.append(("page has " + field, field in text))
    checks.append(("renderProviders has " + field, field in providers))
checks.append(("renderProviders has red md-bad count", "md-dot md-bad" in providers and "var(--bad)" in providers))
checks.append(("renderProviders has green md-ok count", "md-dot md-ok" in providers and "working" in providers))
checks.append(("renderProviders has untested line", "untested" in providers))
checks.append(("renderProviders has models fallback", " models</span>" in providers))
checks.append(("renderProvSum has X and Y counts", "models_ok" in summary and "models_bad" in summary and "md-dot md-ok" in summary and "md-dot md-bad" in summary))
rev = re.search(r"<!-- kit-console-rev: (\d+) -->", text)
checks.append(("kit-console-rev >= 11", rev is not None and int(rev.group(1)) >= 11))
node = shutil.which("node")
if node:
    for index, js in enumerate(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(js)
        try:
            result = subprocess.run([node, "--check", fh.name], capture_output=True, text=True, timeout=30)
            checks.append(("script %d parses" % index, result.returncode == 0))
        finally:
            os.unlink(fh.name)
failed = [name for name, ok in checks if not ok]
if failed:
    print("FAIL models counts UI: " + ", ".join(failed))
    sys.exit(1)
print("models counts UI tests OK%s" % ("" if node else " (node missing: syntax check skipped)"))
