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

# --- step 3: user-chosen paths (pack file to merge, directory to export into) ---
ud = tempfile.mkdtemp()
good = os.path.join(ud, "pack.json"); open(good, "w").write(json.dumps({"patterns": []}))
txt = os.path.join(ud, "pack.txt"); open(txt, "w").write("{}")
bad_json = os.path.join(ud, "broken.json"); open(bad_json, "w").write("{not json")
big = os.path.join(ud, "big.json"); open(big, "w").write(" " * (S._MAX_USER_FILE + 1))
ok(S._user_file(good) == os.path.realpath(good), "_user_file accepts an existing .json file anywhere")
for label, bad in [("missing file", os.path.join(ud, "nope.json")), ("a directory", ud), ("wrong extension", txt),
                   ("too large", big), ("empty string", ""), ("None", None), ("NUL byte", good + "\x00.json")]:
    ok(raises(S._user_file, bad), "_user_file rejects %s" % label)
ok(S._user_dir(ud) == os.path.realpath(ud), "_user_dir accepts a directory")
ok(S._user_dir(os.path.join(ud, "new", "sub")).endswith("sub"), "_user_dir accepts a directory that does not exist yet")
for label, bad in [("a file", good), ("empty string", ""), ("None", None), ("filesystem root", os.path.abspath(os.sep))]:
    ok(raises(S._user_dir, bad), "_user_dir rejects %s" % label)
r = S.export_pack("survival", good); ok(r["ok"] is False and r.get("error"), "export_pack into a file path -> readable error, no exception")
for label, f in [("missing", os.path.join(ud, "nope.json")), ("wrong extension", txt), ("broken json", bad_json), ("too large", big)]:
    rc, out, raw = cli("merge", "survival", f); ok(rc == 1 and out and out.get("ok") is False and out.get("error"), "cli merge %s -> exit 1 + error" % label)
rc, out, _ = cli("merge", "survival", pack); ok(rc == 0 and out and out.get("ok"), "cli merge of a valid external pack still works")
print("STEP 3 OK")

# --- step 4: validation regexes must not accept a trailing newline ---
ok(raises(S._slug, "survival\n"), "slug with trailing newline rejected")
r = S.act("survival", "pr-0123456789\n", "reject"); ok(r.get("ok") is False and "bad proposal id" in r.get("error", ""), "proposal id with trailing newline rejected")
r = S.propose("survival", map_name="Map Nl", variant="loop-100\n", condition="the first wave starts early", action="give a weapon pickup",
              statement="A short safe start helps players who join late."); ok(r.get("ok") is False, "variant with trailing newline rejected")
inc2 = {"schema": S.SCHEMA, "genre": "survival", "patterns": [dict(id="p-aaaaaaaaaaaa\n", variant="x", statement="A calm opening helps new players.",
        condition="a calm opening", action="slow the first wave", tier="hypothesis", status="active", support=1)]}
r = S.merge_pack("survival", inc2, "nl-test"); rj = r.get("rejected"); nrej = rj if isinstance(rj, int) else len(rj or [])
ok(nrej == 1 and r.get("new", 0) == 0, "pattern id with trailing newline rejected in a merged pack: %s" % r)
ok(S.consult_from_path(os.path.join(S.genre_root(), "survival\n", "SKILL.md")).get("ok") is False, "consult ignores a slug with trailing newline")
print("STEP 4 OK")

# --- step 5: a proposal file that is a symlink out of the inbox is refused visibly, outside file untouched ---
victim = os.path.join(outside, "victim.json"); open(victim, "w").write("{}")
ibx = S._inbox_dir("survival"); os.makedirs(ibx, exist_ok=True)
evil = os.path.join(ibx, "pr-aaaaaaaaaa.json")
try:
    os.symlink(victim, evil)
    r = S.act("survival", "pr-aaaaaaaaaa", "reject")
    ok(r.get("ok") is False and r.get("error"), "act refuses a symlinked proposal with a visible error")
    ok(os.path.exists(victim), "the file outside the inbox was not deleted")
    os.remove(evil)
except (OSError, NotImplementedError):
    print("SKIP symlink proposal test (no symlink privilege)")
print("STEP 5 OK")

# --- step 6: containment must not be fooled by a sibling directory that shares the prefix ---
sib_base = tempfile.mkdtemp(); sib = sib_base + "-evil"; os.makedirs(sib, exist_ok=True)
ok(raises(S._inside, sib_base, os.path.join(sib, "x.json")), "_inside rejects a sibling directory with the same name prefix")
ok(S._inside(sib_base, sib_base) == os.path.realpath(sib_base), "_inside accepts the base directory itself")
ok(S._inside(sib_base, os.path.join(sib_base, "a", "b.json")).endswith("b.json"), "_inside accepts a nested path")
print("STEP 6 OK")

# --- step 7: entry points (HTTP/CLI) resolve genre and proposal against what EXISTS on disk ---
ok(S.resolve_genre("survival") == "survival", "resolve_genre returns an existing genre")
for bad in ["nope", "../x", "survival\n", "", None, "SURVIVAL", "survival/../survival"]:
    ok(raises(S.resolve_genre, bad), "resolve_genre rejects %r" % (bad,))
ok(raises(S.act, "../../etc", "pr-0123456789", "reject"), "act on a hostile genre raises ValueError")
ok(raises(S.act, "nope", "pr-0123456789", "reject"), "act on an unknown genre raises ValueError")
ok(raises(S.check, "nope"), "check on an unknown genre raises ValueError")
ok(S.check("survival")["ok"] is True, "check on an existing genre works")
r = S.act("survival", "pr-0123456789", "reject"); ok(r.get("ok") is False and "not found" in r.get("error", ""), "well-formed but absent proposal -> 'not found'")
ok(S.init_genre("brand-new").get("ok", True) is not False and os.path.isdir(S.gdir("brand-new")), "a NEW genre can still be created with init_genre")
ok(S.resolve_genre("brand-new") == "brand-new", "the new genre is then resolvable")
print("STEP 7 OK")
