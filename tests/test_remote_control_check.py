#!/usr/bin/env python3
"""Tests for tools/remote_control_check.py and docs/REMOTE-CONTROL.md."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "remote_control_check.py"
DOC = ROOT / "docs" / "REMOTE-CONTROL.md"

sys.path.insert(0, str(ROOT / "tools"))
import remote_control_check as rcc  # noqa: E402


class TestModes(unittest.TestCase):
    def test_modes_with_login_are_ok(self):
        for mode in ("auto", "safe", "paid", "plan"):
            works, _ = rcc.check(mode)
            self.assertTrue(works, "%s should keep the plan login" % mode)

    def test_free_is_not_ok(self):
        works, fix = rcc.check("free")
        self.assertFalse(works)
        self.assertIn("auto", fix)

    def test_unknown_mode_is_not_ok(self):
        works, fix = rcc.check("nope")
        self.assertFalse(works)
        self.assertTrue(fix)

    def test_case_insensitive(self):
        self.assertTrue(rcc.check("AUTO")[0])


class TestEnv(unittest.TestCase):
    def test_settings_dict_with_mode(self):
        self.assertTrue(rcc.check_env({"mode": "safe"})[0])
        self.assertFalse(rcc.check_env({"mode": "free"})[0])

    def test_placeholder_token_env(self):
        works, fix = rcc.check_env({"ANTHROPIC_AUTH_TOKEN": "dream-router-local"})
        self.assertFalse(works)
        self.assertIn("ANTHROPIC_AUTH_TOKEN", fix)

    def test_login_env_has_no_placeholder(self):
        self.assertTrue(rcc.check_env({"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"})[0])

    def test_free_mode_env_flags(self):
        env = {
            "ANTHROPIC_AUTH_TOKEN": "dream-router-local",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        }
        self.assertFalse(rcc.check_env(env)[0])


class TestCli(unittest.TestCase):
    def run_tool(self, args, stdin=None):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(TOOL)] + args,
            capture_output=True, text=True, input=stdin, env=env,
        )

    def test_cli_free(self):
        p = self.run_tool(["free"])
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("NO uses the placeholder token"))

    def test_cli_paid(self):
        p = self.run_tool(["paid"])
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("OK keeps login"))

    def test_cli_env_json(self):
        p = self.run_tool(["--env", json.dumps({"mode": "auto"})])
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("OK keeps login"))

    def test_cli_env_stdin(self):
        p = self.run_tool(["--env", "-"], stdin=json.dumps({"mode": "free"}))
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("NO uses the placeholder token"))

    def test_cli_one_line_only(self):
        p = self.run_tool(["auto"])
        self.assertEqual(len(p.stdout.strip().splitlines()), 1)


class TestDoc(unittest.TestCase):
    def test_doc_exists(self):
        self.assertTrue(DOC.exists(), "docs/REMOTE-CONTROL.md is missing")

    def test_doc_has_all_four_modes(self):
        text = DOC.read_text(encoding="utf-8").lower()
        for mode in ("free", "paid", "auto", "safe"):
            self.assertIn(mode, text, "mode %s missing from the table" % mode)

    def test_doc_under_40_lines(self):
        self.assertLessEqual(len(DOC.read_text(encoding="utf-8").splitlines()), 40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
