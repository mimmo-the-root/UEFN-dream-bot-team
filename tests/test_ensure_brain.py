"""Acceptance tests for the second-brain autostart: temp HOME and temp project only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "project-template"
TEMPLATE_HOOKS = TEMPLATE / "Claude" / "hooks"
TOOLS = ROOT / "tools"
PS = shutil.which("powershell") or shutil.which("powershell.exe")


class EnsureBrain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ensure-brain-test-"))
        self.home = self.tmp / "home"
        self.claude = self.home / ".claude"
        self.project = self.tmp / "project"
        self.hooks = self.project / "Claude" / "hooks"
        self.vault = self.tmp / "vault"
        self.hooks.mkdir(parents=True)
        (self.project / "Claude" / "logs").mkdir()
        (self.project / "Claude" / "plan").mkdir()
        (self.project / ".claude").mkdir()
        (self.claude).mkdir(parents=True)
        for name in ("ensure-brain.ps1", "brain_brief.py", "brain_upkeep.py", "short_cache.py"):
            shutil.copy2(TEMPLATE_HOOKS / name, self.hooks / name)
        shutil.copy2(TOOLS / "brain_hot.py", self.hooks / "brain_hot.py")
        settings = json.loads((TEMPLATE / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
        (self.project / ".claude" / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
        self.rules = self.claude / "CLAUDE.md"
        self.rules.write_text("**Second brain path**: `<SECOND_BRAIN_PATH>` (while it is this placeholder the feature is off: skip it).\n", encoding="utf-8")
        self.log = self.project / "Claude" / "logs" / "console-start.log"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_ensure(self, vault=None):
        env = dict(os.environ)
        env.update({"USERPROFILE": str(self.home), "HOME": str(self.home),
                    "UEFN_HOME": str(self.claude), "CLAUDE_PROJECT_DIR": str(self.project)})
        env.pop("SECOND_BRAIN", None)
        if vault is not None:
            env["SECOND_BRAIN"] = str(vault)
        if not PS:
            self.skipTest("PowerShell is required")
        return subprocess.run([PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               str(self.hooks / "ensure-brain.ps1"), "-ProjectDir", str(self.project)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)

    def test_placeholder_replaced_once_and_second_run_is_idempotent(self):
        self.vault.mkdir()
        result = self.run_ensure(self.vault)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        first = self.rules.read_text(encoding="utf-8")
        self.assertIn(str(self.vault), first)
        self.assertNotIn("<SECOND_BRAIN_PATH>", first)
        self.assertIn("while it is this placeholder", first)
        backup = self.rules.with_suffix(self.rules.suffix + ".backup")
        self.assertTrue(backup.is_file())
        self.assertIn("<SECOND_BRAIN_PATH>", backup.read_text(encoding="utf-8"))
        self.assertIn("brain:", self.log.read_text(encoding="utf-8"))
        second = self.run_ensure(self.vault)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.rules.read_text(encoding="utf-8"), first)
        self.assertIn("<SECOND_BRAIN_PATH>", backup.read_text(encoding="utf-8"))

    def test_missing_vault_is_silent_exit_zero(self):
        result = self.run_ensure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("<SECOND_BRAIN_PATH>", self.rules.read_text(encoding="utf-8"))
        self.assertFalse(self.rules.with_suffix(self.rules.suffix + ".backup").exists())

    def test_vault_file_sets_rule_11(self):
        self.vault.mkdir()
        (self.project / "Claude" / "brain-vault.txt").write_text(str(self.vault) + "\n", encoding="utf-8")
        result = self.run_ensure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.vault), self.rules.read_text(encoding="utf-8"))

    def test_template_settings_are_valid_and_wired(self):
        settings = json.loads((TEMPLATE / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
        session = settings["hooks"]["SessionStart"]
        commands = [h["command"] for entry in session for h in entry["hooks"]]
        self.assertTrue(any("brain_brief.py\" start" in c for c in commands))
        self.assertTrue(any("short_cache.py" in c for c in commands))
        self.assertTrue(any("session-start-reminder.ps1" in c for c in commands))
        post = [c for entry in settings["hooks"]["PostToolUse"] for c in
                (h["command"] for h in entry["hooks"])]
        self.assertTrue(any("brain_brief.py\" after-edit" in c for c in post))
        self.assertTrue(any(entry.get("matcher") == "Edit|Write" for entry in settings["hooks"]["PostToolUse"]))
        json.loads((self.project / ".claude" / "settings.json").read_text(encoding="utf-8"))
        reminder = (TEMPLATE_HOOKS / "session-start-reminder.ps1").read_text(encoding="utf-8")
        self.assertEqual(reminder.count("ensure-brain.ps1"), 2)

    def test_hot_update_copies_newer_hooks_with_old_backup(self):
        sys.path.insert(0, str(TOOLS))
        import brain_hot
        target = self.claude / "hooks"
        target.mkdir()
        for name in ("brain_brief.py", "brain_upkeep.py"):
            (target / name).write_text("old " + name, encoding="utf-8")
            os.utime(target / name, (1000, 1000))
            (self.hooks / name).write_text("new " + name, encoding="utf-8")
            os.utime(self.hooks / name, (2000, 2000))
        copied = brain_hot.brain_hot_update(home=str(self.claude), kit=str(self.hooks))
        self.assertEqual(copied, ["brain_brief.py", "brain_upkeep.py"])
        for name in ("brain_brief.py", "brain_upkeep.py"):
            self.assertEqual((target / name).read_text(encoding="utf-8"), "new " + name)
            self.assertEqual((target / (name + ".old")).read_text(encoding="utf-8"), "old " + name)
        self.assertEqual(brain_hot.brain_hot_update(home=str(self.claude), kit=str(self.hooks)), [])

    def test_guardian_resolves_the_hot_update_script(self):
        sys.path.insert(0, str(TOOLS))
        import pipeline_guardian
        found = pipeline_guardian.brain_hot_script(str(self.project / "Claude"))
        self.assertEqual(found, str(self.hooks / "brain_hot.py"))
        command = pipeline_guardian.resolve_component("brain_hot_update", str(self.project / "Claude"))[1]
        self.assertIn(str(self.hooks / "brain_hot.py"), command)

    def test_short_cache_is_read_only_bounded_and_after_compact(self):
        sys.path.insert(0, str(TEMPLATE_HOOKS))
        import short_cache
        (self.project / "Claude" / "plan" / "HOT.md").write_text(
            "hot line\n" * 60, encoding="utf-8")
        (self.project / "Claude" / "plan" / "NUDGE.md").write_text(
            "Release: test\n>>> do the first thing\n", encoding="utf-8")
        text = short_cache.short_cache(str(self.project))
        self.assertLessEqual(len(text.splitlines()), 40)
        self.assertIn("hot line", text)
        self.assertIn("DO FIRST: do the first thing", text)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.project))
        result = subprocess.run([sys.executable, str(self.hooks / "short_cache.py")],
                                capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(result.stdout.splitlines()), 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
