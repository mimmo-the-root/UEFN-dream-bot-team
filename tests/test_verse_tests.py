"""Tests for verse_tests.py — scaffold and read commands."""
import json
import os
import shutil
import sys
import tempfile

# Add the hooks directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import verse_tests as vt


def test_parse_test_log_pass_fail_done():
    """Parser correctly counts PASS, FAIL, and finds DONE line."""
    log = """LogVerse: [KIT-TEST] PASS IntEquality: expected 100, got 100
LogVerse: [KIT-TEST] FAIL FloatNear: expected ~50.0, got 51.0 (diff 1.0 > tol 0.1)
LogVerse: [KIT-TEST] PASS BooleanCondition: condition is true
LogVerse: [KIT-TEST] DONE pass=2 fail=1"""
    result = vt.parse_test_log(log)
    assert result["pass_count"] == 2
    assert result["fail_count"] == 1
    assert result["done_found"] is True
    assert result["done_pass"] == 2
    assert result["done_fail"] == 1
    assert result["has_failures"] is True
    assert len(result["tests"]) == 3
    assert result["tests"][0]["status"] == "PASS"
    assert result["tests"][1]["status"] == "FAIL"
    print("PASS test_parse_test_log_pass_fail_done")


def test_parse_test_log_all_pass():
    """Parser works when all tests pass."""
    log = """LogVerse: [KIT-TEST] PASS Test1: ok
LogVerse: [KIT-TEST] PASS Test2: ok
LogVerse: [KIT-TEST] DONE pass=2 fail=0"""
    result = vt.parse_test_log(log)
    assert result["pass_count"] == 2
    assert result["fail_count"] == 0
    assert result["done_found"] is True
    assert result["has_failures"] is False
    print("PASS test_parse_test_log_all_pass")


def test_parse_test_log_missing_done():
    """Parser reports missing DONE line."""
    log = """LogVerse: [KIT-TEST] PASS Test1: ok
LogVerse: [KIT-TEST] PASS Test2: ok"""
    result = vt.parse_test_log(log)
    assert result["pass_count"] == 2
    assert result["fail_count"] == 0
    assert result["done_found"] is False
    assert result["has_failures"] is False
    print("PASS test_parse_test_log_missing_done")


def test_parse_test_log_only_fail():
    """Parser works when only failures."""
    log = """LogVerse: [KIT-TEST] FAIL Test1: expected 1, got 2
LogVerse: [KIT-TEST] DONE pass=0 fail=1"""
    result = vt.parse_test_log(log)
    assert result["pass_count"] == 0
    assert result["fail_count"] == 1
    assert result["done_found"] is True
    assert result["has_failures"] is True
    print("PASS test_parse_test_log_only_fail")


def test_scaffold_creates_file():
    """scaffold command creates the test device file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = os.path.join(tmpdir, "Verse")
        os.makedirs(target_dir)

        # Run scaffold
        exit_code = vt.cmd_scaffold(target_dir)
        assert exit_code == 0

        target_file = os.path.join(target_dir, "verse_test_device.verse")
        assert os.path.exists(target_file)

        content = open(target_file).read()
        assert "ExpectEqual" in content
        assert "ExpectTrue" in content
        assert "ExpectNear" in content
        assert "[KIT-TEST]" in content
        print("PASS test_scaffold_creates_file")


def test_scaffold_refuses_overwrite():
    """scaffold refuses to overwrite existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = os.path.join(tmpdir, "Verse")
        os.makedirs(target_dir)

        # Create existing file
        target_file = os.path.join(target_dir, "verse_test_device.verse")
        open(target_file, "w").write("existing content")

        # Run scaffold - should fail
        exit_code = vt.cmd_scaffold(target_dir)
        assert exit_code == 1

        # Content unchanged
        content = open(target_file).read()
        assert content == "existing content"
        print("PASS test_scaffold_refuses_overwrite")


def test_read_with_fake_log():
    """read command parses a fake log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        log_content = """LogVerse: [KIT-TEST] PASS Test1: ok
LogVerse: [KIT-TEST] FAIL Test2: mismatch
LogVerse: [KIT-TEST] DONE pass=1 fail=1"""
        open(log_file, "w").write(log_content)

        # Capture stdout
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exit_code = vt.cmd_read(log_file)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert exit_code == 1  # Has failures
        result = json.loads(output)
        assert result["pass_count"] == 1
        assert result["fail_count"] == 1
        assert result["done_found"] is True
        assert result["has_failures"] is True
        print("PASS test_read_with_fake_log")


def test_read_all_pass_exit_zero():
    """read exits 0 when all tests pass and DONE found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        log_content = """LogVerse: [KIT-TEST] PASS Test1: ok
LogVerse: [KIT-TEST] PASS Test2: ok
LogVerse: [KIT-TEST] DONE pass=2 fail=0"""
        open(log_file, "w").write(log_content)

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exit_code = vt.cmd_read(log_file)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert exit_code == 0
        result = json.loads(output)
        assert result["has_failures"] is False
        print("PASS test_read_all_pass_exit_zero")


def test_read_no_done_exit_one():
    """read exits 1 when DONE line is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = os.path.join(tmpdir, "test.log")
        log_content = """LogVerse: [KIT-TEST] PASS Test1: ok
LogVerse: [KIT-TEST] PASS Test2: ok"""
        open(log_file, "w").write(log_content)

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            exit_code = vt.cmd_read(log_file)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert exit_code == 1
        result = json.loads(output)
        assert result["done_found"] is False
        print("PASS test_read_no_done_exit_one")


if __name__ == "__main__":
    test_parse_test_log_pass_fail_done()
    test_parse_test_log_all_pass()
    test_parse_test_log_missing_done()
    test_parse_test_log_only_fail()
    test_scaffold_creates_file()
    test_scaffold_refuses_overwrite()
    test_read_with_fake_log()
    test_read_all_pass_exit_zero()
    test_read_no_done_exit_one()
    print("\nAll tests passed!")