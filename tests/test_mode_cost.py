#!/usr/bin/env python3
"""Tests for T-108: mode cost calculator."""
import json
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from mode_cost import load, shares

# Fake usage.json with mixed models - format matches dream_router.py
USAGE_MIXED = {
    "models": {
        "claude-plan/opus": {"provider": "claude-plan", "model": "opus", "input": 600000, "output": 400000, "requests": 10, "errors": 0, "last": 1795082400},
        "claude-plan/sonnet": {"provider": "claude-plan", "model": "sonnet", "input": 300000, "output": 200000, "requests": 5, "errors": 0, "last": 1795082400},
        "groq/llama-3.1": {"provider": "groq", "model": "llama-3.1", "input": 120000, "output": 80000, "requests": 20, "errors": 0, "last": 1795082400},
        "anthropic/claude-3.5": {"provider": "anthropic", "model": "claude-3.5", "input": 180000, "output": 120000, "requests": 8, "errors": 0, "last": 1795082400},
    },
    "month": "2026-11"
}

# Fake usage-72h.json with 3 days - format matches dream_router.py (hour buckets as unix timestamps)
# Nov 17-19 2026 (hour timestamps: 1794909600 = Nov 17 10:00, etc.)
USAGE_72H_MIXED = {
    "1794909600": {  # 2026-11-17
        "provider": "claude-plan",
        "model": "opus",
        "hours": {
            "1794909600": [400000, 0, 10, 0],
        }
    },
    "1794996000": {  # 2026-11-18
        "provider": "claude-plan",
        "model": "sonnet",
        "hours": {
            "1794996000": [300000, 200000, 5, 0],
        }
    },
    "1795082400": {  # 2026-11-19
        "provider": "claude-plan",
        "model": "opus",
        "hours": {
            "1795082400": [100000, 0, 2, 0],
        }
    },
    "1794909601": {  # 2026-11-17
        "provider": "groq",
        "model": "llama-3.1",
        "hours": {
            "1794909600": [150000, 0, 15, 0],
        }
    },
}

# Free-only
USAGE_FREE = {
    "models": {
        "groq/llama-3.1": {"provider": "groq", "model": "llama-3.1", "input": 600000, "output": 400000, "requests": 20, "errors": 0, "last": 1795082400},
        "anthropic/claude-3.5": {"provider": "anthropic", "model": "claude-3.5", "input": 300000, "output": 200000, "requests": 8, "errors": 0, "last": 1795082400},
    },
    "month": "2026-11"
}

USAGE_72H_FREE = {
    "1794909600": {
        "provider": "groq",
        "model": "llama-3.1",
        "hours": {
            "1794909600": [400000, 0, 10, 0],
        }
    },
    "1794996000": {
        "provider": "groq",
        "model": "llama-3.1",
        "hours": {
            "1794996000": [300000, 0, 8, 0],
        }
    },
    "1795082400": {
        "provider": "groq",
        "model": "llama-3.1",
        "hours": {
            "1795082400": [300000, 0, 8, 0],
        }
    },
}

# Paid-only
USAGE_PAID = {
    "models": {
        "claude-plan/opus": {"provider": "claude-plan", "model": "opus", "input": 900000, "output": 600000, "requests": 15, "errors": 0, "last": 1795082400},
        "claude-plan/sonnet": {"provider": "claude-plan", "model": "sonnet", "input": 200000, "output": 100000, "requests": 3, "errors": 0, "last": 1795082400},
    },
    "month": "2026-11"
}

USAGE_72H_PAID = {
    "1794909600": {
        "provider": "claude-plan",
        "model": "opus",
        "hours": {
            "1794909600": [800000, 0, 10, 0],
        }
    },
    "1794996000": {
        "provider": "claude-plan",
        "model": "opus",
        "hours": {
            "1794996000": [500000, 0, 6, 0],
        }
    },
    "1795082400": {
        "provider": "claude-plan",
        "model": "opus",
        "hours": {
            "1795082400": [200000, 0, 2, 0],
        }
    },
}


def test_mixed():
    """Test mixed usage: both paid and free models."""
    result = shares(USAGE_MIXED, USAGE_72H_MIXED, days=3)

    # Check daily totals (sorted desc: Nov 19, 18, 17)
    assert len(result["daily"]) == 3
    assert result["daily"][0]["date"] == "2026-11-19"
    assert result["daily"][0]["paid"] == 100000
    assert result["daily"][0]["free"] == 0
    assert result["daily"][0]["total"] == 100000

    assert result["daily"][1]["date"] == "2026-11-18"
    assert result["daily"][1]["paid"] == 500000
    assert result["daily"][1]["free"] == 0
    assert result["daily"][1]["total"] == 500000

    assert result["daily"][2]["date"] == "2026-11-17"
    assert result["daily"][2]["paid"] == 400000
    assert result["daily"][2]["free"] == 150000
    assert result["daily"][2]["total"] == 550000

    # Check week totals
    assert result["week"]["paid"] == 1000000
    assert result["week"]["free"] == 150000
    assert result["week"]["total"] == 1150000
    assert result["week"]["share_percent"] == 87

    # Check models (from usage.json monthly totals)
    assert len(result["models"]) == 4
    paid_models = [m for m in result["models"] if m["paid"] > 0]
    free_models = [m for m in result["models"] if m["free"] > 0]
    assert len(paid_models) == 2
    assert len(free_models) == 2

    # Check paid-only models
    opus = next(m for m in result["models"] if m["provider_model"] == "claude-plan/opus")
    assert opus["paid"] == 1000000
    assert opus["free"] == 0
    assert opus["total"] == 1000000

    sonnet = next(m for m in result["models"] if m["provider_model"] == "claude-plan/sonnet")
    assert sonnet["paid"] == 500000
    assert sonnet["free"] == 0
    assert sonnet["total"] == 500000

    # Check free-only models
    llama = next(m for m in result["models"] if m["provider_model"] == "groq/llama-3.1")
    assert llama["paid"] == 0
    assert llama["free"] == 200000
    assert llama["total"] == 200000

    claude35 = next(m for m in result["models"] if m["provider_model"] == "anthropic/claude-3.5")
    assert claude35["paid"] == 0
    assert claude35["free"] == 300000
    assert claude35["total"] == 300000

    print("test_mixed: ok")


def test_free_only():
    """Test free-only usage."""
    result = shares(USAGE_FREE, USAGE_72H_FREE, days=3)

    # Daily totals
    assert len(result["daily"]) == 3
    for d in result["daily"]:
        assert d["paid"] == 0
        assert d["free"] > 0
        assert d["total"] == d["free"]

    # Week totals
    assert result["week"]["paid"] == 0
    assert result["week"]["free"] == 1000000
    assert result["week"]["share_percent"] == 0

    # Models
    assert len(result["models"]) == 2
    for m in result["models"]:
        assert m["paid"] == 0
        assert m["free"] > 0
        assert m["total"] == m["free"]

    print("test_free_only: ok")


def test_paid_only():
    """Test paid-only usage."""
    result = shares(USAGE_PAID, USAGE_72H_PAID, days=3)

    # Daily totals
    assert len(result["daily"]) == 3
    for d in result["daily"]:
        assert d["free"] == 0
        assert d["paid"] > 0
        assert d["total"] == d["paid"]

    # Week totals
    assert result["week"]["paid"] == 1500000
    assert result["week"]["free"] == 0
    assert result["week"]["share_percent"] == 100

    # Models
    assert len(result["models"]) == 2
    for m in result["models"]:
        assert m["free"] == 0
        assert m["paid"] > 0
        assert m["total"] == m["paid"]

    print("test_paid_only: ok")


def test_empty_data():
    """Test empty/missing data."""
    result = shares({}, {}, days=7)

    assert result["week"]["paid"] == 0
    assert result["week"]["free"] == 0
    assert result["week"]["total"] == 0
    assert result["week"]["share_percent"] == 0
    assert len(result["daily"]) == 0
    assert len(result["models"]) == 0

    print("test_empty_data: ok")


def test_file_io():
    """Test loading from actual files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        usage_path = os.path.join(tmpdir, "usage.json")
        usage72_path = os.path.join(tmpdir, "usage-72h.json")

        with open(usage_path, "w") as f:
            json.dump(USAGE_MIXED, f)
        with open(usage72_path, "w") as f:
            json.dump(USAGE_72H_MIXED, f)

        loaded_usage, loaded_72h = load(usage_path, usage72_path)
        assert loaded_usage == USAGE_MIXED
        assert loaded_72h == USAGE_72H_MIXED

        result = shares(loaded_usage, loaded_72h, days=3)
        assert result["week"]["total"] == 1150000

        print("test_file_io: ok")


if __name__ == "__main__":
    test_mixed()
    test_free_only()
    test_paid_only()
    test_empty_data()
    test_file_io()
    print("\nAll tests passed!")
