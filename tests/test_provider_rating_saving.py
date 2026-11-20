#!/usr/bin/env python3
"""Tests for provider_rating and api_saving, fake usage data only (temp dir, nothing real touched)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import provider_rating as pr
import api_saving as sv

USAGE = {"month": "2026-11", "models": {
    "groq/a": {"provider": "groq", "model": "a", "input": 1000000, "output": 500000, "requests": 100, "errors": 2, "last": 1},
    "bad/b": {"provider": "bad", "model": "b", "input": 10, "output": 10, "requests": 40, "errors": 36, "last": 1,
              "rate_limited": 30, "server_errors": 6, "latency_ms_total": 40 * 25000},
    "new/c": {"provider": "new", "model": "c", "input": 0, "output": 0, "requests": 0, "errors": 0},
    "claude-plan/opus": {"provider": "claude-plan", "model": "opus", "input": 2000000, "output": 1000000, "requests": 50, "errors": 0}}}


class T(unittest.TestCase):
    def test_rating(self):
        rows = {r["provider"]: r for r in pr.rate_all(USAGE)}
        self.assertEqual(rows["groq"]["rating"], 5)
        self.assertFalse(rows["groq"]["paid"])
        self.assertIsNone(rows["groq"]["mean_latency_ms"])
        self.assertIn("not recorded", rows["groq"]["reason"])
        self.assertEqual(rows["bad"]["rating"], 1)
        self.assertEqual(rows["bad"]["mean_latency_ms"], 25000.0)
        self.assertAlmostEqual(rows["bad"]["share_429"], 0.75)
        self.assertIsNone(rows["new"]["rating"])
        self.assertTrue(rows["claude-plan"]["paid"])
        self.assertEqual(pr.rate_all(USAGE)[-1]["provider"], "new")

    def test_empty_and_garbage(self):
        self.assertEqual(pr.rate_all({}), [])
        self.assertEqual(pr.rate_all({"models": {"x": "junk"}}), [])

    def test_saving_example(self):
        r = sv.saving(USAGE)
        self.assertTrue(r["estimate_only"])
        self.assertEqual(r["free_input_tokens"], 1000010)
        self.assertEqual(r["free_output_tokens"], 500010)
        self.assertAlmostEqual(r["saving_usd"], (1000010 * 3.0 + 500010 * 15.0) / 1e6, places=4)
        self.assertIn("EXAMPLES", r["note"])

    def test_saving_owner_prices_and_missing(self):
        p = {"owner_set": True, "prices": {"k": {"input": 1, "output": 2}}, "default": "k"}
        r = sv.saving(USAGE, prices=p)
        self.assertFalse(r["estimate_only"])
        self.assertAlmostEqual(r["saving_usd"], (1000010 + 2 * 500010) / 1e6, places=4)
        self.assertIsNone(sv.saving(USAGE, prices={"prices": {}})["saving_usd"])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sv.load_prices(os.path.join(d, "nope.json")), {"prices": {}})

    def test_price_file_labelled(self):
        d = sv.load_prices()
        self.assertFalse(d["owner_set"])
        self.assertEqual(len(d["prices"]), 3)
        self.assertIn("NOT real", d["_note"])
        for v in d["prices"].values():
            self.assertIn("EXAMPLE", v["label"])


if __name__ == "__main__":
    unittest.main()
