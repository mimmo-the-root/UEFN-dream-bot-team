#!/usr/bin/env python3
"""Unit tests for dream_router.lookup_tier() using fake providers."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "user-level-hooks"))
import dream_router


class FakeTierLookupTests(unittest.TestCase):
    """Test tier lookup with fake tier tables."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tiers_file = os.path.join(self.tmpdir, "tiers.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_tiers(self, data):
        with open(self.tiers_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _patch_tier_path(self):
        return patch.object(dream_router, "_tier_path", return_value=self.tiers_file)

    def test_known_skill_returns_correct_tier(self):
        self._write_tiers({"skills": {"code-review": "T1", "planner-docs": "T2"}, "agents": {}})
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("code-review"), "T1")
            self.assertEqual(dream_router.lookup_tier("planner-docs"), "T2")

    def test_known_agent_returns_correct_tier(self):
        self._write_tiers({"skills": {}, "agents": {"coder": "T1", "explore": "T3"}})
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("coder"), "T1")
            self.assertEqual(dream_router.lookup_tier("explore"), "T3")

    def test_unknown_name_falls_back_to_T2(self):
        self._write_tiers({"skills": {"code-review": "T1"}, "agents": {"coder": "T1"}})
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("nonexistent"), "T2")
            self.assertEqual(dream_router.lookup_tier("also-missing"), "T2")

    def test_missing_tiers_json_falls_back_to_T2(self):
        with patch.object(dream_router, "_tier_path", return_value="/nonexistent/path/tiers.json"):
            self.assertEqual(dream_router.lookup_tier("any-name"), "T2")

    def test_corrupted_tiers_json_falls_back_to_T2(self):
        with open(self.tiers_file, "w", encoding="utf-8") as f:
            f.write("{ not valid json }")
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("any-name"), "T2")

    def test_unreadable_tiers_json_falls_back_to_T2(self):
        self._write_tiers({"skills": {"test": "T1"}, "agents": {}})
        with self._patch_tier_path():
            with patch("builtins.open", side_effect=OSError("Permission denied")):
                self.assertEqual(dream_router.lookup_tier("test"), "T2")

    def test_empty_tiers_json_falls_back_to_T2(self):
        self._write_tiers({})
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("any-name"), "T2")

    def test_skills_and_agents_both_searched(self):
        self._write_tiers({
            "skills": {"shared-name": "T1"},
            "agents": {"shared-name": "T3"}
        })
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("shared-name"), "T1")

    def test_case_sensitivity(self):
        self._write_tiers({"skills": {"Code-Review": "T1"}, "agents": {}})
        with self._patch_tier_path():
            self.assertEqual(dream_router.lookup_tier("code-review"), "T2")
            self.assertEqual(dream_router.lookup_tier("Code-Review"), "T1")

    def test_real_tiers_file_lookup(self):
        tier = dream_router.lookup_tier("code-review")
        self.assertIn(tier, ("T1", "T2", "T3"))
        self.assertEqual(dream_router.lookup_tier("definitely-not-a-real-skill"), "T2")


if __name__ == "__main__":
    unittest.main()
