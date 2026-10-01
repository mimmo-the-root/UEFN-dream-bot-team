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

# --- step 2: one gate (_inside) for every internal file access ---
outside = tempfile.mkdtemp()
def raises(fn, *a, **k):
    try:
        fn(*a, **k); return False
    except ValueError:
        return True
gd = S.gdir("survival")
ok(S._inside(gd, os.path.join(gd, "SKILL.md")).endswith("SKILL.md"), "_inside accepts a path inside base")
ok(raises(S._inside, gd, os.path.join(gd, "..", "..", "x")), "_inside rejects '..' escape")
ok(raises(S._inside, gd, os.path.join(outside, "x.json")), "_inside rejects an unrelated directory")
ok(raises(S._read_json, os.path.join(outside, "x.json"), None), "_read_json: blocked path is an error, not 'missing'")
ok(S._read_json(os.path.join(gd, "no-such.json"), "dflt") == "dflt", "_read_json: genuinely missing file -> default")
ok(raises(S._write_json, os.path.join(outside, "x.json"), {}), "_write_json refuses to write outside the skills root")
ok(raises(S._append_jsonl, os.path.join(outside, "x.jsonl"), {}), "_append_jsonl refuses outside the skills root")
ok(raises(S._read_jsonl, os.path.join(outside, "x.jsonl")), "_read_jsonl: blocked path is an error")
ok(raises(S._listdir, outside), "_listdir refuses outside the skills root")
ok(raises(S._remove_file, os.path.join(outside, "x.json")), "_remove_file refuses outside the skills root")
ok(S._isfile(os.path.join(outside, "x.json")) is False, "_isfile outside root -> False")
ok(not os.path.exists(os.path.join(outside, "x.json")), "nothing was written outside")
# symlink inside the skills tree pointing outside must be refused
link = os.path.join(gd, "evil-link")
try:
    os.symlink(outside, link)
    ok(raises(S._write_json, os.path.join(link, "pwn.json"), {}), "_write_json refuses to follow a symlink out of the root")
    ok(not os.path.exists(os.path.join(outside, "pwn.json")), "symlink escape wrote nothing")
    os.remove(link)
except (OSError, NotImplementedError):
    print("SKIP symlink test (no symlink privilege)")
# user-chosen export dir: the pack must land inside THAT dir
ex2 = tempfile.mkdtemp()
r = S.export_pack("survival", ex2); ok(r["ok"] and os.path.realpath(r["path"]).startswith(os.path.realpath(ex2)), "export lands inside the chosen directory")
print("STEP 2 OK")

