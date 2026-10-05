import os, sys, tempfile, shutil
root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import docs_lint
tpl = os.path.join(root, "project-template", "Claude", "docs-template")
d = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(d, "Claude", "docs"))
    for n in ("ROADMAP.md", "BUGS.md"):
        shutil.copy(os.path.join(tpl, n), os.path.join(d, "Claude", "docs", n))
    assert docs_lint.lint(d) == [], docs_lint.lint(d)
    rp = os.path.join(d, "Claude", "docs", "ROADMAP.md")
    t = open(rp, encoding="utf-8").read()
    open(rp, "w", encoding="utf-8").write(t.replace("| P0-R1 |", "| v0.1 |"))
    assert any("must be P<phase>-R<n>" in x for x in docs_lint.lint(d))
    open(rp, "w", encoding="utf-8").write(t.replace("| P0-R1 |", "| Later |"))
    assert docs_lint.lint(d) == []
    open(rp, "w", encoding="utf-8").write(t.replace("| Active |", "| Planned |"))
    assert any("exactly one phase" in x for x in docs_lint.lint(d))
    # older project without Phases: legacy release names stay valid
    legacy = t.replace("## Phases", "## Notes").replace("| P0-R1 |", "| v0.1 |")
    open(rp, "w", encoding="utf-8").write(legacy)
    assert docs_lint.lint(d) == [], docs_lint.lint(d)
    print("delivery standard tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
