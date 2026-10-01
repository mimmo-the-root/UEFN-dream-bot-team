"""Safety-net tests for skills_lib: CLI output shapes, user-chosen paths, hostile ids.

Behaviour-preserving: these must pass before AND after the path-hardening work.
Run: python tests/test_skills_safety.py
"""
import os, sys, json, subprocess, tempfile
HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
LIB = os.path.join(HOOKS, "skills_lib.py")
root = tempfile.mkdtemp()
os.environ["UEFN_SKILLS_DIR"] = root
sys.path.insert(0, HOOKS)
import skills_lib as S

ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))


def cli(*args):
    p = subprocess.run([sys.executable, LIB] + list(args), capture_output=True, text=True,
                       env=dict(os.environ, UEFN_SKILLS_DIR=root))
    try:
        out = json.loads(p.stdout)
    except ValueError:
        out = None
    return p.returncode, out, p.stdout


# --- CLI output shapes (agents and hooks parse these) ---
rc, out, _ = cli("init", "survival"); ok(rc == 0 and out and out.get("ok"), "cli init ok")
rc, out, _ = cli("summary"); ok(rc == 0 and isinstance(out, dict) and "genres" in out and "totals" in out, "cli summary keeps full payload")
rc, out, _ = cli("patterns", "survival"); ok(rc == 0 and isinstance(out, list), "cli patterns prints a JSON list")
rc, out, _ = cli("proposals"); ok(rc == 0 and isinstance(out, list), "cli proposals prints a JSON list")
rc, out, _ = cli("check", "survival"); ok(rc == 0 and isinstance(out, dict) and out.get("ok") is True, "cli check ok")
rc, out, _ = cli("check", "../x"); ok(rc == 1 and out and out.get("ok") is False and out.get("error"), "cli bad slug -> exit 1 + error")
rc, out, _ = cli("act", "survival", "pr-0123456789", "approve"); ok(rc == 1 and out and out.get("ok") is False, "cli act on unknown proposal -> exit 1")

# propose through the CLI, then see it in the list
args = ["propose", "survival", "--variant", "loop-100", "--condition", "the first wave starts before the player has a weapon",
        "--action", "give a weapon pickup and a short safe start", "--statement",
        "Players leave when wave 1 hits before they have a weapon; a short safe start helps.", "--map", "Harrow Zero"]
rc, out, _ = cli(*args); ok(rc == 0 and out and out.get("ok"), "cli propose ok")
rc, out, _ = cli("proposals", "survival"); ok(rc == 0 and isinstance(out, list) and len(out) == 1, "cli proposals lists the new proposal")
pid = out[0]["id"]

# secrets in user text never reach stdout
secret = "abcdef1234567890XYZ"
rc, out, raw = cli("propose", "survival", "--variant", "loop-100", "--condition", "c c c c c", "--action", "a a a a a",
                   "--statement", "api_key=" + secret, "--map", "Harrow Zero")
ok(secret not in raw, "cli output never echoes a secret-looking value")

# --- user-chosen paths must keep working (they live OUTSIDE the skills root) ---
ex = tempfile.mkdtemp()
ok(S.act("survival", pid, "approve")["ok"], "approve proposal")
r = S.export_pack("survival", ex); ok(r["ok"], "export_pack to an external directory works")
pack = os.path.join(ex, "survival", "patterns.json")
ok(os.path.isfile(pack), "exported pack file exists outside the skills root")
rc, out, _ = cli("export", "survival", tempfile.mkdtemp()); ok(rc == 0 and out and out.get("ok"), "cli export to external dir works")
rc, out, _ = cli("merge", "survival", pack, "--source", "demo"); ok(rc == 0 and out and out.get("ok"), "cli merge from an external pack file works")

# --- hostile ids and slugs are rejected with a readable error (no exception, no file access) ---
for bad in ["../x", "pr-0123456789/../../x", "pr-zzzzzzzzzz", "pr-01234567", "", "pr-0123456789.json", None, 5]:
    r = S.act("survival", bad, "reject")
    ok(isinstance(r, dict) and r.get("ok") is False, "act rejects hostile id %r" % (bad,))
for bad in ["../x", "a/b", "a\\b", "", ".hidden", "x" * 200, None]:
    try:
        S._slug(bad); ok(False, "slug %r should be rejected" % (bad,))
    except ValueError:
        ok(True, "slug rejects %r" % (bad,))
print("SAFETY NET OK")
