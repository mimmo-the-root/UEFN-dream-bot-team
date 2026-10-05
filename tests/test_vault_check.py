import os, subprocess, sys, shutil, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = os.path.join(root, "user-level-skills", "second-brain-query", "scripts", "vault_check.py")
d = tempfile.mkdtemp()
def w(rel, txt):
    p = os.path.join(d, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(txt)
def run(*a):
    r = subprocess.run([sys.executable, S, *a, "--vault", d], capture_output=True, text=True); assert r.returncode == 0, r.stderr; return r.stdout
try:
    fm = "---\n%s: 2026-01-01\n%s:\n  - x\n---\n"
    w("wiki/meccaniche/a.md", fm % ("data_creazione", "fonti") + "## Fonti\n[[../pattern-verse/b]] [[missing-one]]\n## Implementazione Verse (ultima versione)\n")
    w("wiki/meccaniche/indice_wiki.md", "[[a]]")
    w("wiki/pattern-verse/b.md", fm % ("created", "sources") + "## Sources\n")
    w("wiki/pattern-verse/wiki-index.md", "[[b]]")
    w("wiki/mechanics/c.md", "x")  # English twin of an existing Italian folder
    o = run("names")
    assert "Italian name" in o and "duplicate folders for mechanics" in o, o
    o = run("links")
    assert "1 broken link" in o and "missing-one" in o, o
    o = run("stats")
    assert "with a Verse implementation section: 1" in o and "missing created/sources fields: 1" in o, o
    print("vault check tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
