"""PR path rules for community lessons, and the safety shape of the workflow."""
import os, sys
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "tool"))
from check_pr_paths import check_pr_paths as C
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
P = "contributions/survival/p-0123456789ab/ada.json"
ok(C([P], "ada") == [] and C([P], "Ada") == [], "one lesson file of the author passes")
ok(C([P, "tool/screen_contribution.py"], "ada") != [], "a file outside contributions/ is refused")
ok(C([P, ".github/workflows/x.yml"], "ada") != [], "a workflow change is refused")
ok(C([P], "eve") != [], "a file named after another handle is refused")
ok(C(["contributions/survival/p-0123456789ab/../x.json"], "ada") != [], "path tricks are refused")
ok(C(["contributions/INTAKE.json"], "ada") != [], "the intake files cannot be edited by a PR")
ok(C(["contributions/survival/p-%012x/ada.json" % i for i in range(21)], "ada") != [], "more than 20 files is refused")
ok(C([], "ada") != [], "an empty change is refused")
ok(C([P + " "], "ada") != [] and C([" " + P], "ada") != [] and C([P + "\n"], "ada") != [], "a name with a space or a newline is refused, never cleaned into a valid one")
ok(C(["contributions/survival/p-0123456789ab/ada.json", "contributions/survival/p-0123456789ab/alice.json"], "ada") != [], "touching (deleting, renaming away) another handle's file is refused")
w = open(os.path.join(root, ".github", "workflows", "contributions.yml"), encoding="utf-8").read()
body = w.split("\njobs:")[0].split("\non:")[1]
ok("pull_request_target:" in body, "the check cannot be edited by the PR it judges (pull_request_target)")
ok("secrets." not in w, "the workflow uses no secrets")
ok("permissions:\n  contents: read\n  pull-requests: read" in w, "read-only permissions")
ok(w.count("persist-credentials: false") == 2, "neither checkout keeps the token")
runs = [l for l in w.splitlines() if "python " in l]
ok(runs and all("trusted/tool/" in l for l in runs), "every python call runs a script from the BASE commit, never from the PR (%d calls)" % len(runs))
ok("pr/" not in "".join(l for l in runs), "no script path points into the PR checkout")
ok("--no-renames" in w and "-z" in w and "120000" in w, "renames are expanded, names are NUL separated, symlinks are refused")
ok("${{" not in "\n".join(l for l in w.splitlines() if l.strip().startswith(("git ", "python ", "if ", "cd ", "while ", "[ "))), "no ${{ }} expression inside a command")
