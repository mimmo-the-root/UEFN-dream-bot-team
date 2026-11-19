#!/usr/bin/env python3
"""
Deterministic MCP result writer — appends each tool result to tests.json
atomically with try/finally so a timeout never loses a result.

Value format matches mcp_map.py's existing tests.json: plain string values.
ok -> "ok"
refused -> "refused:<short reason>"
err -> "err:<short reason>"
no_answer -> "no_answer"
classifier_blocked -> "classifier_blocked"

A tool never loses its "ok": overwriting an existing "ok" with a worse value
keeps the old one in the "history" list.

Usage: python mcp_result_writer.py <tool_name> <status> [--args-hash HASH] [--error MSG] [--refused MSG] [--dir DIR]
Status values: ok | refused | err | no_answer | classifier_blocked
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Windows compatibility for file locking
if sys.platform == "win32":
    import msvcrt
    def lock_file(f, exclusive=True):
        # LK_NBLCK raises at once when another process holds the lock (a lost result): retry for up to 30 s
        import time
        for _ in range(300):
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.1)
        raise OSError("tests.json lock busy for 30 s")
    def unlock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def lock_file(f, exclusive=True):
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    def unlock_file(f):
        fcntl.flock(f, fcntl.LOCK_UN)


def default_dir() -> Path:
    """Default directory for tests.json (skill map directory)."""
    return Path(os.environ.get("UEFN_KIT_MCP_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "skills", "mcp-tool-contracts", "references", "map"))


def atomic_write(path: Path, data: dict):
    """Write JSON atomically: temp file + rename."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    tmp.replace(path)


def compute_args_hash(args: dict) -> str:
    """Compute stable hash of arguments for deduplication."""
    serialized = json.dumps(args, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def load_tests_json(path: Path) -> dict:
    """Load tests.json, creating structure if missing."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "results" not in data:
                data["results"] = {}
            if "history" not in data:
                data["history"] = {}
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"results": {}, "history": {}, "date": None, "updated": None}


def status_value(status: str, error_msg: str = "", refused_msg: str = "") -> str:
    """Return the plain-string value for the given status."""
    if status == "ok":
        return "ok"
    if status == "no_answer":
        return "no_answer"
    if status == "classifier_blocked":
        return "classifier_blocked"
    if status == "refused":
        return "refused:" + (refused_msg or "guard")[:60]
    if status == "err":
        return "err:" + (error_msg or "call error")[:60]
    return status


def write_result(
    tool_name: str,
    status: str,
    args: dict | None = None,
    error_msg: str = "",
    refused_msg: str = "",
    dirpath: Path | None = None,
) -> dict:
    """
    Append a tool result to tests.json atomically with locking.

    Never overwrites an existing 'ok' without keeping the old one in history.
    Returns the updated entry value.
    """
    d = dirpath or default_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / "tests.json"
    lock_path = d / "tests.json.lock"

    args_hash = compute_args_hash(args) if args else ""

    # Valid statuses
    valid_statuses = {"ok", "refused", "err", "no_answer", "classifier_blocked"}
    if status not in valid_statuses:
        raise ValueError("Invalid status: %s. Must be one of %s" % (status, valid_statuses))

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    value = status_value(status, error_msg=error_msg, refused_msg=refused_msg)

    # Lock and update atomically
    with open(lock_path, "a+") as lock_f:
        lock_file(lock_f, exclusive=True)
        try:
            data = load_tests_json(path)

            existing = data["results"].get(tool_name)
            if existing == "ok" and value != "ok":
                # A tool that once worked keeps its ok; the worse result goes to history only
                history = data["history"].setdefault(tool_name, [])
                history.append("%s %s" % (now_iso, value))
                value = "ok"

            data["results"][tool_name] = value
            if args_hash:
                data.setdefault("args_hash", {})[tool_name] = args_hash
            data["date"] = now_iso
            data["updated"] = now_iso

            atomic_write(path, data)
            return {"tool": tool_name, "status": status, "value": value, "date": now_iso}
        finally:
            unlock_file(lock_f)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Write MCP tool result to tests.json")
    parser.add_argument("tool", help="Tool name (e.g., EditorToolset/FindActors)")
    parser.add_argument("status", choices=["ok", "refused", "err", "no_answer", "classifier_blocked"],
                        help="Result status")
    parser.add_argument("--args-hash", help="Precomputed args hash (optional)")
    parser.add_argument("--args-json", help="JSON args to hash (optional)")
    parser.add_argument("--error", default="", help="Error message for err status")
    parser.add_argument("--refused", default="", help="Refused message for refused status")
    parser.add_argument("--dir", help="Directory containing tests.json (default: skill map dir)")

    args = parser.parse_args()

    args_dict = None
    if args.args_json:
        try:
            args_dict = json.loads(args.args_json)
        except json.JSONDecodeError:
            pass

    try:
        result = write_result(
            tool_name=args.tool,
            status=args.status,
            args=args_dict,
            error_msg=args.error,
            refused_msg=args.refused,
            dirpath=Path(args.dir) if args.dir else None,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())