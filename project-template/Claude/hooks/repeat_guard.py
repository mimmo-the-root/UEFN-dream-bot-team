#!/usr/bin/env python3
"""repeat_guard.py - PostToolUseFailure hook: stops repeating the same failing call.
Key = tool name + args normalised + error normalised (numbers, paths, timestamps stripped).
Stores streak in Claude/logs/repeat-guard.json per session_id.
On 3rd identical failure in a row, answers with additionalContext:
"STOP: this call failed 3 times with the same error. Change the arguments or the approach, or report expected/seen/tried. Do not retry it."
A success of the same tool resets it.
Switch off with UEFN_KIT_GUARDS=0. Never fails loudly."""
import json, os, re, sys, hashlib
from pathlib import Path

LOG_DIR = "Claude/logs"
LOG_FILE = "repeat-guard.json"
MAX_FAILURES = 3

def normalise_error(err: str) -> str:
    """Normalise error message: strip numbers, paths, timestamps, uuids."""
    if not err:
        return ""
    # Replace numbers (including decimals)
    err = re.sub(r'\b\d+\.?\d*\b', 'N', err)
    # Replace file paths (Windows and Unix)
    err = re.sub(r'[A-Za-z]:\\[^\s]*', 'PATH', err)
    err = re.sub(r'/[^\s]*', 'PATH', err)
    # Replace timestamps like 2026-11-15, 14:30:00, etc.
    err = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', err)
    err = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', err)
    # Replace UUIDs
    err = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'UUID', err, flags=re.I)
    # Replace memory addresses
    err = re.sub(r'0x[0-9a-f]+', 'ADDR', err, flags=re.I)
    return err.strip()

def normalise_args(args: dict) -> str:
    """Normalise tool arguments for comparison."""
    if not args:
        return ""
    # Sort keys for consistent hashing
    items = sorted(args.items())
    parts = []
    for k, v in items:
        if isinstance(v, str):
            # Normalise string values
            v = normalise_error(v)
        elif isinstance(v, (int, float)):
            v = 'N'
        elif isinstance(v, dict):
            v = normalise_args(v)
        elif isinstance(v, list):
            v = '[' + ','.join(normalise_args(x) if isinstance(x, dict) else ('N' if isinstance(x, (int, float)) else (normalise_error(x) if isinstance(x, str) else str(x))) for x in v) + ']'
        parts.append(f"{k}={v}")
    return "&".join(parts)

def make_tool_args_key(tool_name: str, args: dict) -> str:
    """Create a key for tool+args without error (for success reset and indexing)."""
    raw = f"{tool_name}|{normalise_args(args)}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def make_error_key(error: str) -> str:
    """Create a key for the error part."""
    return hashlib.md5(normalise_error(error).encode()).hexdigest()[:16]

def load_log(project_root: Path) -> dict:
    log_path = project_root / LOG_DIR / LOG_FILE
    if log_path.exists():
        try:
            return json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_log(project_root: Path, data: dict):
    log_path = project_root / LOG_DIR / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def get_session_id() -> str:
    """Get session ID from environment or use a default."""
    return os.environ.get("CLAUDE_SESSION_ID", "default")

def main():
    try:
        if os.environ.get("UEFN_KIT_GUARDS") == "0":
            return 0

        # Use CLAUDE_PROJECT_DIR if set, otherwise find project root (where Claude/ folder is)
        project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", ""))
        if not project_root.exists() or not (project_root / "Claude").exists():
            cwd = Path.cwd()
            project_root = cwd
            while project_root != project_root.parent:
                if (project_root / "Claude").exists():
                    break
                project_root = project_root.parent

        p = json.loads(sys.stdin.read() or "{}")
        tool_name = p.get("tool_name", "")
        tool_input = p.get("tool_input", {})
        tool_result = p.get("tool_result", {})
        error = tool_result.get("error", "") or tool_result.get("stderr", "") or str(tool_result.get("exit_code", ""))

        session_id = get_session_id()

        # If no error, reset ALL streaks for this tool+args (a success resets the streak of whatever error was seen)
        if not error:
            log = load_log(project_root)
            session_data = log.get(session_id, {})
            tool_key = make_tool_args_key(tool_name, tool_input)
            # Remove all error-specific keys for this tool+args
            keys_to_remove = [k for k in list(session_data) if k.startswith(tool_key + ".")]
            for k in keys_to_remove:
                session_data.pop(k, None)
            log[session_id] = session_data
            save_log(project_root, log)
            return 0

        error_key = make_error_key(error)
        full_key = f"{make_tool_args_key(tool_name, tool_input)}.{error_key}"

        log = load_log(project_root)
        session_data = log.get(session_id, {})
        streak = session_data.get(full_key, 0) + 1
        session_data[full_key] = streak
        log[session_id] = session_data
        save_log(project_root, log)

        if streak >= MAX_FAILURES:
            msg = ("STOP: this call failed 3 times with the same error. "
                   "Change the arguments or the approach, or report expected/seen/tried. Do not retry it.")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": msg
            }}))
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())