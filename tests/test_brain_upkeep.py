"""test_brain_upkeep.py - tests for brain_upkeep.py due/not-due rules, free check report, and inbox command."""
import json, os, shutil, subprocess, sys, tempfile, datetime

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
U = os.path.join(root, "project-template", "Claude", "hooks", "brain_upkeep.py")
SK = os.path.join(root, "user-level-skills", "second-brain-query")

ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

home, vault = tempfile.mkdtemp(), tempfile.mkdtemp()
try:
    shutil.copytree(SK, os.path.join(home, "skills", "second-brain-query"))
    hooks_dir = os.path.join(home, "project-template", "Claude", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    shutil.copy2(U, os.path.join(hooks_dir, "brain_upkeep.py"))

    def run_upkeep(mode, **env):
        e = dict(os.environ, UEFN_HOME=home); e.pop("SECOND_BRAIN", None); e.update(env)
        return subprocess.run([sys.executable, U, mode], capture_output=True, text=True, env=e)

    def w(rel, txt):
        p = os.path.join(vault, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(txt)

    def run_upkeep_vault(mode, vault_path=None, **env):
        e = dict(os.environ, UEFN_HOME=home); e.pop("SECOND_BRAIN", None); e.update(env)
        cmd = [sys.executable, U, mode]
        if vault_path:
            cmd += ["--vault", vault_path]
        return subprocess.run(cmd, capture_output=True, text=True, env=e)

    # Write the vault path in CLAUDE.md
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `%s`\n" % vault)

    # Test 1: free check creates report and returns OK
    r = run_upkeep_vault("free", vault_path=vault)
    ok(r.returncode == 0, "free mode returns 0")
    upkeep_dir = os.path.join(vault, "output", "upkeep")
    today = os.path.join(upkeep_dir, datetime.date.today().isoformat() + ".md")
    ok(os.path.isfile(today), "free check creates YYYY-MM-DD.md")
    with open(today, encoding="utf-8") as f:
        content = f.read()
    ok("Clippings to compile: 0" in content, "report shows 0 clippings to compile")

    # Test 2: check-due when never run returns due
    r = run_upkeep_vault("check-due", vault_path=vault)
    ok(r.returncode == 0 and "due=True" in r.stdout, "check-due reports due=True when never run")

    # Test 3: check-due when last run < 7 days ago returns not due
    state_file = os.path.join(vault, "output", "upkeep", "state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump({"last_run": datetime.date.today().isoformat()}, f)
    r = run_upkeep_vault("check-due", vault_path=vault)
    ok(r.returncode == 0 and "due=False" in r.stdout, "check-due reports due=False when last run < 7 days ago")

    # Test 4: check-due when last run > 7 days ago returns due
    old_date = (datetime.date.today() - datetime.timedelta(days=8)).isoformat()
    with open(state_file, "w") as f:
        json.dump({"last_run": old_date}, f)
    r = run_upkeep_vault("check-due", vault_path=vault)
    ok(r.returncode == 0 and "due=True" in r.stdout, "check-due reports due=True when last run > 7 days ago")

    # Test 5: free check reports Clippings count
    os.makedirs(os.path.join(vault, "Clippings"), exist_ok=True)
    w("Clippings/note1.md", "some note\n")
    w("Clippings/note2.md", "another note\n")
    w("Clippings/note3_COMPILED.md", "already compiled\n")  # should not count
    r = run_upkeep_vault("free", vault_path=vault)
    ok(r.returncode == 0, "free mode returns 0 with clippings")
    with open(today, encoding="utf-8") as f:
        content = f.read()
    ok("Clippings to compile: 2" in content, "report shows 2 clippings to compile (excluding _COMPILED)")

    # Test 6: free check reports broken links
    os.makedirs(os.path.join(vault, "wiki", "test"), exist_ok=True)
    w("wiki/test/page.md", "# Test\nSee [[missing-page]]\n")
    r = run_upkeep_vault("free", vault_path=vault)
    ok(r.returncode == 0, "free mode returns 0 with broken links")
    with open(today, encoding="utf-8") as f:
        content = f.read()
    ok("links: issues" in content or "broken" in content.lower(), "report mentions broken links issue")

    # Test 7: maybe-start does not start when inbox doesn't exist
    r = run_upkeep_vault("maybe-start", vault_path=vault)
    ok(r.returncode == 0 and "not started" in r.stdout, "maybe-start does not start when inbox missing")

    # Test 8: maybe-start does not start when inbox not empty
    inbox_dir = os.path.join(home, "Claude", "relay", "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    with open(os.path.join(inbox_dir, "some-command.json"), "w") as f:
        f.write('{"command": "test"}\n')
    r = run_upkeep_vault("maybe-start", vault_path=vault)
    ok(r.returncode == 0 and "not started" in r.stdout and "inbox not empty" in r.stdout, "maybe-start does not start when inbox not empty")

    # Test 9: maybe-start writes command when inbox empty and due
    os.remove(os.path.join(inbox_dir, "some-command.json"))
    # Make state old so it's due
    with open(state_file, "w") as f:
        json.dump({"last_run": old_date}, f)
    r = run_upkeep_vault("maybe-start", vault_path=vault)
    ok(r.returncode == 0 and "started" in r.stdout, "maybe-start writes command when inbox empty and due")

    # Verify command file was created
    cmd_files = [f for f in os.listdir(inbox_dir) if f.startswith("brain-upkeep-") and f.endswith(".json")]
    ok(len(cmd_files) == 1, "exactly one command file created")
    with open(os.path.join(inbox_dir, cmd_files[0]), encoding="utf-8") as f:
        cmd = json.load(f)
    ok(cmd.get("command") == "second_brain_upkeep" and cmd.get("mode") == "free" and cmd.get("parallel") == True, "command has correct structure")

finally:
    shutil.rmtree(home, ignore_errors=True); shutil.rmtree(vault, ignore_errors=True)
print("brain_upkeep tests OK")