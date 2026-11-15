#!/usr/bin/env python3
"""
Verse in-game test utilities.

Commands:
  scaffold <folder>    Copy the test device template into the project's Verse folder (never overwrites)
  read [log]           Parse the UEFN log for [KIT-TEST] lines of the last session and print JSON summary
                       Exit code 1 if any FAIL or no DONE line found.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional


def find_template_path() -> Path:
    """Find the verse-test-device.verse.txt template in the kit."""
    # First check project-template/Claude/reference/
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    template_path = project_root / "Claude" / "reference" / "verse-test-device.verse.txt"
    if template_path.exists():
        return template_path
    # Fallback to ~/.claude/kit-template/
    home_template = Path.home() / ".claude" / "kit-template" / "Claude" / "reference" / "verse-test-device.verse.txt"
    if home_template.exists():
        return home_template
    raise FileNotFoundError("Could not find verse-test-device.verse.txt template")


def find_uefn_logs() -> list[Path]:
    """Find UEFN log files under %LOCALAPPDATA%."""
    localappdata = os.environ.get("LOCALAPPDATA")
    if not localappdata:
        raise RuntimeError("LOCALAPPDATA not set")

    log_root = Path(localappdata) / "UnrealEditorFortnite" / "Saved" / "Logs"
    if not log_root.exists():
        # Try alternate path
        log_root = Path(localappdata) / "FortniteGame" / "Saved" / "Logs"

    if not log_root.exists():
        return []

    # Find all log files, sort by modification time (newest first)
    logs = list(log_root.glob("*.log"))
    logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return logs


def parse_test_log(log_content: str) -> dict:
    """Parse [KIT-TEST] lines from log content."""
    pass_count = 0
    fail_count = 0
    tests = []
    done_found = False
    last_done_pass = 0
    last_done_fail = 0

    # Pattern for PASS/FAIL lines
    test_pattern = re.compile(r'\[KIT-TEST\]\s+(PASS|FAIL)\s+(\w+):\s+(.+)')
    # Pattern for DONE line
    done_pattern = re.compile(r'\[KIT-TEST\]\s+DONE\s+pass=(\d+)\s+fail=(\d+)')

    for line in log_content.splitlines():
        test_match = test_pattern.search(line)
        if test_match:
            status, name, detail = test_match.groups()
            tests.append({
                "name": name,
                "status": status,
                "detail": detail
            })
            if status == "PASS":
                pass_count += 1
            else:
                fail_count += 1
            continue

        done_match = done_pattern.search(line)
        if done_match:
            done_found = True
            last_done_pass = int(done_match.group(1))
            last_done_fail = int(done_match.group(2))

    return {
        "tests": tests,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "done_found": done_found,
        "done_pass": last_done_pass,
        "done_fail": last_done_fail,
        "has_failures": fail_count > 0
    }


def cmd_scaffold(folder: str) -> int:
    """Copy the test device template into the project's Verse folder."""
    template_path = find_template_path()
    target_dir = Path(folder)

    if not target_dir.exists():
        print(f"Error: Target folder does not exist: {folder}", file=sys.stderr)
        return 1

    target_file = target_dir / "verse_test_device.verse"

    if target_file.exists():
        print(f"Error: Target file already exists, refusing to overwrite: {target_file}", file=sys.stderr)
        return 1

    # Copy and rename from .verse.txt to .verse
    shutil.copy2(template_path, target_file)
    print(f"Created: {target_file}")
    return 0


def cmd_read(log_file: Optional[str] = None) -> int:
    """Parse UEFN log for [KIT-TEST] lines and print JSON summary."""
    # Find the log file
    if log_file:
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Error: Log file not found: {log_file}", file=sys.stderr)
            return 1
    else:
        logs = find_uefn_logs()
        if not logs:
            print("Error: No UEFN log files found", file=sys.stderr)
            return 1
        log_path = logs[0]
        print(f"Using log: {log_path}", file=sys.stderr)

    # Read and parse
    log_content = log_path.read_text(encoding="utf-8", errors="ignore")
    result = parse_test_log(log_content)

    # Print JSON summary
    print(json.dumps(result, indent=2))

    # Exit code: 1 if any FAIL or no DONE line
    if result["has_failures"] or not result["done_found"]:
        return 1
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    cmd = sys.argv[1]

    if cmd == "scaffold":
        if len(sys.argv) < 3:
            print("Usage: verse_tests.py scaffold <folder>", file=sys.stderr)
            return 1
        return cmd_scaffold(sys.argv[2])

    elif cmd == "read":
        log_file = sys.argv[2] if len(sys.argv) > 2 else None
        return cmd_read(log_file)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())