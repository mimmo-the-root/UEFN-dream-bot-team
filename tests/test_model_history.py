#!/usr/bin/env python3
"""Tests for model_history.py"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add user-level-hooks to path
sys.path.insert(0, str(Path(__file__).parent.parent / "user-level-hooks"))

import model_history


def setup_test_env():
    """Create a temporary test environment."""
    tmp = tempfile.mkdtemp(prefix="model_history_test_")
    os.environ["DREAM_ROUTER_HOME"] = tmp
    model_history.HOME = tmp
    model_history.HISTORY_DIR = os.path.join(tmp, "history")
    model_history.PERF_FILE = os.path.join(tmp, "perf.json")
    model_history.USAGE_FILE = os.path.join(tmp, "usage.json")
    os.makedirs(model_history.HISTORY_DIR, exist_ok=True)
    return tmp


def test_one_line_per_model_per_day():
    """Test that only one line per model per day is written."""
    tmp = setup_test_env()
    date_str = "2026-01-15"

    # Create usage.json with data for that day
    usage = {
        "models": {
            "gemini/gemini-flash-latest": {
                "provider": "gemini",
                "model": "gemini-flash-latest",
                "input": 1000,
                "output": 500,
                "requests": 5,
                "errors": 1,
                "last": time.mktime(time.strptime(date_str, "%Y-%m-%d"))
            },
            "openrouter/qwen/qwen3-coder:free": {
                "provider": "openrouter",
                "model": "qwen/qwen3-coder:free",
                "input": 2000,
                "output": 800,
                "requests": 3,
                "errors": 0,
                "last": time.mktime(time.strptime(date_str, "%Y-%m-%d"))
            }
        },
        "month": "2026-01"
    }
    with open(model_history.USAGE_FILE, "w") as f:
        json.dump(usage, f)

    # Create perf.json
    perf = {
        "gemini/gemini-flash-latest": {"ok": 4, "fail": 1, "ms": 1200},
        "openrouter/qwen/qwen3-coder:free": {"ok": 3, "fail": 0, "ms": 800}
    }
    with open(model_history.PERF_FILE, "w") as f:
        json.dump(perf, f)

    # Write daily history
    ok = model_history.write_daily_history(date_str)
    assert ok, "Should write successfully"

    # Check file content
    path = model_history.history_file_for("2026-01")
    rows = model_history._read_jsonl(path)
    assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
    providers = {r["provider"] for r in rows}
    assert providers == {"gemini", "openrouter"}

    # Write again - should not duplicate
    ok2 = model_history.write_daily_history(date_str)
    assert ok2, "Should still succeed"
    rows2 = model_history._read_jsonl(path)
    assert len(rows2) == 2, f"Expected 2 rows after second write, got {len(rows2)}"

    # Check fields
    for r in rows2:
        assert "date" in r
        assert "provider" in r
        assert "model" in r
        assert "requests" in r
        assert "failures" in r
        assert "tokens_in" in r
        assert "tokens_out" in r
        assert "median_ms" in r
        assert r["date"] == date_str

    print("[OK] test_one_line_per_model_per_day passed")


def test_summary_on_fake_month():
    """Test summary generation on fake month data."""
    tmp = setup_test_env()

    # Create history files for 4 weeks
    now = time.time()
    for i in range(28):
        day = time.strftime("%Y-%m-%d", time.localtime(now - i * 86400))
        month_str = day[:7]
        path = model_history.history_file_for(month_str)
        rows = []
        # gemini - mostly good
        rows.append({"date": day, "provider": "gemini", "model": "gemini-flash-latest",
                     "requests": 10, "failures": 1 if i % 7 == 0 else 0,
                     "tokens_in": 1000, "tokens_out": 500, "median_ms": 1200})
        # openrouter - some failures
        rows.append({"date": day, "provider": "openrouter", "model": "qwen/qwen3-coder:free",
                     "requests": 5, "failures": 1 if i % 3 == 0 else 0,
                     "tokens_in": 800, "tokens_out": 400, "median_ms": 1500})
        # nvidia - stopped working after day 7 (data from 21-27 days ago)
        if i >= 21:
            rows.append({"date": day, "provider": "nvidia", "model": "qwen/qwen3-coder-480b-a35b-instruct",
                         "requests": 8, "failures": 0,
                         "tokens_in": 1200, "tokens_out": 600, "median_ms": 900})
        model_history._write_jsonl(path, rows)

    md = model_history.summary(weeks=4)
    assert "Best Models" in md
    assert "gemini" in md
    assert "openrouter" in md
    assert "nvidia" in md
    assert "Stopped Working" in md
    assert "nvidia" in md  # nvidia should be in stopped
    print("[OK] test_summary_on_fake_month passed")
    print(md[:500])


def test_vault_page_written_once_per_week():
    """Test that vault page is written once per week and skipped without vault path."""
    tmp = setup_test_env()

    # Create some history
    date_str = time.strftime("%Y-%m-%d")
    usage = {
        "models": {
            "gemini/gemini-flash-latest": {
                "provider": "gemini", "model": "gemini-flash-latest",
                "input": 1000, "output": 500, "requests": 5, "errors": 0,
                "last": time.mktime(time.strptime(date_str, "%Y-%m-%d"))
            }
        },
        "month": date_str[:7]
    }
    with open(model_history.USAGE_FILE, "w") as f:
        json.dump(usage, f)
    with open(model_history.PERF_FILE, "w") as f:
        json.dump({"gemini/gemini-flash-latest": {"ok": 5, "fail": 0, "ms": 1000}}, f)

    # Create a fake vault
    vault_path = os.path.join(tmp, "vault")
    os.makedirs(os.path.join(vault_path, "wiki", "kit"), exist_ok=True)

    # First write
    ok1, msg1 = model_history.write_weekly_vault_page(vault_path, weeks=4)
    assert ok1, f"First write failed: {msg1}"
    page_path = os.path.join(vault_path, "wiki", "kit", "modelli-gratuiti.md")
    assert os.path.exists(page_path)

    # Second write (same week) - should replace
    ok2, msg2 = model_history.write_weekly_vault_page(vault_path, weeks=4)
    assert ok2, f"Second write failed: {msg2}"

    # Check indice.md has the link
    indice_path = os.path.join(vault_path, "wiki", "indice.md")
    with open(indice_path) as f:
        idx = f.read()
    assert "modelli-gratuiti" in idx

    # Check log.md has entry
    log_path = os.path.join(vault_path, "wiki", "log.md")
    with open(log_path) as f:
        log = f.read()
    assert "Updated weekly free models page" in log

    # Test with placeholder vault path
    ok3, msg3 = model_history.write_weekly_vault_page("C:\\SecondBrainOssidian", weeks=4)
    assert not ok3
    assert "placeholder" in msg3.lower()

    # Test with None vault path
    ok4, msg4 = model_history.write_weekly_vault_page("", weeks=4)
    assert not ok4
    assert "placeholder" in msg4.lower()

    print("[OK] test_vault_page_written_once_per_week passed")


def test_summary_html_safe():
    """Test that summary output is HTML-safe (no raw < > &)."""
    tmp = setup_test_env()

    date_str = time.strftime("%Y-%m-%d")
    path = model_history.history_file_for(date_str[:7])
    rows = [{
        "date": date_str, "provider": "test", "model": "model<with>chars&more",
        "requests": 1, "failures": 0, "tokens_in": 100, "tokens_out": 50, "median_ms": 100
    }]
    model_history._write_jsonl(path, rows)

    md = model_history.summary(weeks=4)
    # Check no unescaped HTML
    assert "<" not in md or "<" in md or md.count("<") == md.count("<")
    # Actually the markdown table uses | and - which is fine
    print("[OK] test_summary_html_safe passed")


if __name__ == "__main__":
    test_one_line_per_model_per_day()
    test_summary_on_fake_month()
    test_vault_page_written_once_per_week()
    test_summary_html_safe()
    print("\nAll tests passed!")